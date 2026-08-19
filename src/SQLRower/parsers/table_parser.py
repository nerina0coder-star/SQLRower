from datetime import datetime
from typing import Literal, Any

from sqlalchemy import Integer, String, Boolean, DateTime, Column, Table, Engine, Double, DECIMAL, ForeignKey
from sqlalchemy.orm import DeclarativeMeta

from SQLRower.masters.abstract_master import AbstractMaster
from SQLRower.parsers.abstract_parser import AbstractParser
from SQLRower.utils import ColumnReference, Column as UtilColumn
from SQLRower.validator import validator


class TableParser(AbstractParser):

    def __init__(self, base: DeclarativeMeta, engine: Engine, master: AbstractMaster):
        """
        Initializes a table parser.

        :param base: a declarative base to work on.
        :param engine: an engine to work on.
        :param master: an abstract master to use the knowledge of.
        """
        validator(
            (
                "base",
                base,
                DeclarativeMeta
            ),
            (
                "engine",
                engine,
                Engine
            ),
            (
                "master",
                master,
                AbstractMaster
            )
        )
        self.master: AbstractMaster = master
        self.base: DeclarativeMeta = base
        self.engine: Engine = engine

    def __call__(self, queries: UtilColumn | dict | list[UtilColumn | dict] | list[list[UtilColumn | dict]], **kwargs):
        """
        Creates a tables based on the given queries. For more information please refer to TableParser.parser.

        queries(parameter): Structured details of each column.
            - Can be a Column for a table with a single column,
            - a list of Column for a table with multiple columns,
            - or a list of lists of Column for multiple tables with multiple columns.
        :param kwargs: Include the table name here.
        :returns: The created tables.
        """
        if isinstance(queries, (UtilColumn, dict)):
            queries = [[queries]]

        if not all(isinstance(i, list) for i in queries):
            queries = [queries]

        tables = []
        queries: list[list[UtilColumn]]

        for q in queries:
            tables.append(self.parser(q, **kwargs))

        with self.engine.connect() as conn:
            self.base.metadata.create_all(
                conn,
                tables,
            )
            conn.commit()  # just to make sure

        return tables

    def parser(self,
               queries: list[UtilColumn],
               **kwargs) -> Table:
        """
        Parses the given queries.

        The queries are structured details of each column.
        Every column is represented by a dict, for example:

        {
            "name": "id",

            "type": int,

            "options": {
                "nullable": False,

                "primary_key": True,

                "unique": True,
            }
        }, {
            "name": "username",

            "type": str,

            "options": {
                "limit": 40,

                "nullable": True,

                "default": None,

                "primary_key": False,
            }
        }, {
            "name": "salary",

            "type": float,

            "options": {
                "decimal-places": 3, # meaning 3 out of all 10 digits must be after decimal.

                "precision": 10,
            }
        }, {
            "name": "facility",

            "type": str,

            "options": {
                "foreign": "facilities.name", # Note that the using foreign key must be unique or primary key.
                And that the foreign must be a SQLRower.utils.ColumnReference or string. Column References
                Can be accessed via the executor's "c" or "columns" method.
            }
        }

        :param queries: a structured dict.
        :param kwargs: Include the table name(str).
        :return:
        """
        # Creating allowed types
        if not all(isinstance(i, dict) for i in queries):
            queries = list(dict(q) for q in queries)

        supported_strings = {
            "int": int,
            "str": str,
            "float": float,
            "bool": bool,
            "datetime": datetime,
        }
        supported_types = [
            int,
            str,
            float,
            bool,
            datetime,
        ]

        functions = [
            self.integer,
            self.string,
            self.float,
            self.boolean,
            self.datetime,
        ]

        type_mapping = dict(zip(supported_types, functions))

        required = [
            "name",
            "type",
        ]

        columns = []

        for column in queries:

            column: dict[Literal["name", "type", "options"], Any] = column  # Type hint

            # Validating
            validator \
                    (
                    (
                        "column",
                        column,
                        dict,
                        (
                            (lambda: all(i in column.keys() for i in required)),
                            "name and type are required in each column",
                        )
                    ),
                    (
                        "name",
                        column.get("name"),
                        str,
                        (
                            (lambda: len(column.get("name")) > 0),
                            "The name must be at least 1 characters long."
                        )
                    ),
                    (
                        "type",
                        column.get("type"),
                        tuple(type(i) for i in supported_types),
                        (
                            (lambda: column.get("type") in supported_types or column[
                                "type"] in supported_strings.keys()),
                            ("The type of the column must be a known type, such as: "
                             f"{list(supported_strings.keys())[0]}"
                             "".join(f", {i}" for i in list(supported_strings.keys())[1:]))
                        )
                    ),
                    (
                        "options",
                        column.get("options", {}),
                        dict,
                    )
                )

            # Setting each column's options
            name: str = column["name"]
            type_: Any = column["type"]
            options: dict = column.get("options")

            if isinstance(type_, str):
                type_ = supported_strings[type_]

            func = type_mapping[type_]

            base = self.general(options)

            for k, v in self.foreign(options):
                base[k] = v

            for k, v in func(options).items():
                if k == "kwargs":
                    for k2, v2 in v.items():
                        base.setdefault(k, {})[k2] = v2
                base[k] = v


            if "foreign" not in base:
                columns.append(Column(name, base["type"], **base["kwargs"]))
            else:
                columns.append(Column(name, base["type"], base["foreign"], **base["kwargs"]))
        # Validating table name
        validator(
            (
                "table_name",
                kwargs.get("table_name"),
                str,
            )
        )

        # Creating table

        return Table(
            kwargs.get("table_name"),
            self.base.metadata,
            *columns
        )

    def general(self, options: dict) -> dict:
        """
        Helps to parse general options.

        options(dict): The options available for the column.

        The ones accepted are:
            - nullable: Whether or not the general can be null.
            - unique: Whether or not the general must be unique.
        """
        available = {
            "nullable": bool,
            "unique": bool,
        }
        kwargs = {}
        for av in available.keys():
            if options is None or not av in options.keys():
                continue

            validator(
                (
                    av,
                    options[av],
                    available[av],
                )
            )

            kwargs[av] = options[av]

        return {"kwargs": kwargs}

    def foreign(self, options: dict):
        """
        Helps to parse general options.

        options(dict): The options available for the column.

        The ones accepted are:
            - foreign: must be a column reference or string reference.
        """

        if options is None:
            return {}

        if "foreign" in options:
            if not isinstance(options["foreign"], ColumnReference | str):
                raise ValueError("Expected a column reference or string reference for the foreign key.")

            foreign_key: ColumnReference | str = options["foreign"]

            return {
                "foreign": ForeignKey(foreign_key.name
                                      if isinstance(foreign_key, ColumnReference)
                                      else foreign_key),
            }

        return {}

    def string(self, options: dict) -> dict:
        """
        Helps to parse string-based options.

        options(dict): The options available for the column.

        The ones accepted are:
            - limit: The maximum count of characters the string can have.
            - default: The default value for the column.
        """
        available = {
            "limit": int,
            "default": str,
        }
        out = {}

        for av in available.keys():
            if options is None or not av in options.keys():
                continue

            if av == "limit":
                if self.master.limit("str", options[av]):
                    raise ValueError("The given limit bypasses the database's limit. (String Column)")

                out["type"] = self.master.mapping("str", options[av])
                continue

            extra_val = (
                (lambda: len(options[av]) <= options["limit"]),
                "The default must be less than the limit."
            ) if av == "default" and options.get("limit") is not None else None

            validating = [
                av,
                options[av],
                available[av],
            ]

            if extra_val is not None:
                validating.append(extra_val)

            validating = tuple(validating)

            validator(
                validating
            )

            out.setdefault("kwargs", {})[av] = options[av]

        if "type" not in out.keys():
            out["type"] = String

        return out

    def integer(self, options: dict) -> dict:
        """
        Helps to parse integer-based options.

        options(dict): The options available for the column.

        The ones accepted are:
            - limit: The maximum amount the int can have. (Helps in deciding INTEGER or BIGINT)
            - primary_key: Whether or not the integer is the primary key.
            - default: The default value for the column.
        """
        available = {
            "limit": int,
            "primary_key": bool,
            "default": int,
        }

        out = {}

        for av in available.keys():
            if options is None or not av in options.keys():
                continue

            if av == "limit":
                if self.master.limit("int", options[av]):
                    raise ValueError("The given limit bypasses the database's limit. (Integer Column)")
                type_ = self.master.mapping("str", options[av])

                out["type"] = type_
                continue

            extra_val = (
                (lambda: options[av] > options["limit"]),
                "The default must be less than the limit."
            ) if av == "default" and options.get("limit") is not None else None

            validating = [
                av,
                options[av],
                available[av],
            ]

            if extra_val is not None:
                validating.append(extra_val)

            validating = tuple(validating)

            validator(validating)

            out.setdefault("kwargs", {})[av] = options[av]

        if "type" not in out.keys():
            out["type"] = Integer

        return out

    def float(self, options: dict) -> dict:
        """
        Helps to parse float-based options.

        options(dict): The options available for the column.

        The ones accepted are:
            - precision: The precision of the float. (Helps in deciding FLOAT or REAL).
            - default: The default value for the column.
            - decimal-places: The places after the decimal(default is DB default, can cause error)
        """
        available = {
            "precision": int,
            "default": float,
        }

        out = {}

        for av in available.keys():
            if options is None or not av in options.keys():
                continue

            if av == "precision":
                if self.master.limit("float", options[av]):
                    raise ValueError("The given precision bypasses the database's limit. (Float Column)")

                type_ = self.master.mapping("float", options[av])

                if type_ == DECIMAL or isinstance(type_, DECIMAL):
                    type_ = DECIMAL(options[av], options.get("decimal-places"))

                out["type"] = type_
                continue

            extra_val = (
                (lambda: options[av] < options["precision"]),
                "The default must be less than the precision."
            ) if av == "default" and options.get("precision") is not None else None

            validating = [
                av,
                options[av],
                available[av],
            ]

            if extra_val is not None:
                validating.append(extra_val)

            validating = tuple(validating)

            validator(validating)

            out.setdefault("kwargs", {})[av] = options[av]

        if "type" not in out.keys():
            out["type"] = Double

        return out

    def boolean(self, options: dict) -> dict:
        """
        Helps to parse boolean-based options.

        options(dict): The options available for the column.

        The ones accepted are:
            - default: The default value for the column.
        """
        out: dict[str, Any] = {"type": Boolean}

        if options is not None and options.get("default") is not None:
            default = options.get("default")
            if isinstance(default, bool):
                out.setdefault("kwargs", {})["default"] = default

        return out

    def datetime(self, options: dict) -> dict:
        """
        Helps to parse datetime-based options.

        options(dict): The options available for the column.

        The ones accepted are:
            - default: The default value for the column(Can be callable).
        """
        available = {
            "default": datetime,
        }

        out = {}

        for av in available.keys():
            if options is None or not av in options.keys():
                continue

            validator(
                (
                    av,
                    options[av],
                    available[av],
                )
            )

            out.setdefault("kwargs", {})[av] = options[av]

        if "type" not in out.keys():
            out["type"] = DateTime

        return out
