from ast import literal_eval
from typing import Any
from warnings import warn

from sqlalchemy import Table, Engine, Executable, and_, or_, select, table as t, MetaData

from SQLRower.exceptions.InvalidQueryException import InvalidQueryException
from SQLRower.parsers.abstract_parser import AbstractParser
from SQLRower.validator import validator


class SelectionParser(AbstractParser):
    def __init__(self,
                 table: Table,
                 engine: Engine,
                 /, *,
                 autotype: bool = True):
        """
        Initializes a SelectionParser.

        :param engine: The engine that links to the table.
        :param autotype: Whether to change types(e.g., "True" -> True, "1.1" -> 1.1)
        """
        validator(
            (
                "table_name", table, Table
            ),
            (
                "engine", engine, Engine
            ),
            (
                "autotype", autotype, bool
            )
        )

        self.autotype = autotype

        self.table = table

        self.engine = engine

        self.mapping = {
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            'like': lambda x, y: x.like(y),
            'ilike': lambda x, y: x.ilike(y),
            'in': lambda x, y: x.in_(y),
            'is': lambda x, y: x.is_(y),
            'between': lambda x, y: x.between(y),
            'isn\'t': lambda x, y: x.isnot(y),
        }

    def __call__(self, queries: str|list[str], **kwargs):
        """
        Parses the given query and executes it.

        logic(kwargs): Which logic to use. and: all conditions must be true. or: one of conditions must be true.

        :param queries: The query to parse.
        :param kwargs: The arguments to give to the parser function(see: Parser.parser).
        :return: The executed query.
        """
        logic = kwargs.get("logic")
        if isinstance(queries, str):
            queries = [queries]
        if isinstance(logic, str):
            logic = logic.lower()
        # Validating
        validator(
            (
                "logic", logic, str, (
                    (lambda: logic in ["and", "or"]),
                    f"Expected logic to be 'and' or 'or', given {logic}."
                )
            ),
            (
                "queries", queries, list,
                (
                    (lambda: all(isinstance(q, str) for q in queries)),
                    "All items of queries must be strings."
                )
            )
        )

        # Parsing
        if not isinstance(queries, list):
            queries = [queries]

        try:
            parsed = self.parser(queries, **kwargs)
        except InvalidQueryException:
            raise
        except Exception as e:
            raise RuntimeError(f"Unknown error acquired when parsing the given query. It reads: {e}")

        with self.engine.connect() as conn:
            stmt = and_(*parsed) if logic == "and" else or_(*parsed)


            result = conn.execute(statement=select(self.table).where(stmt))
            rows = result.fetchall()

        return rows



    def parser(self, queries: list[str], **kwargs) -> list[Executable]:
        """
        Parses the given query.

        Here are some examples:
            - "t.id == 1" Searches for the rows that have the ID of 1.
            - "t.email like %@gmail.com" Searches for the rows that have a Gmail email address.
            - "t.intelligent between :b:", [1, 200]. Searches for the rows that have intelligent of 1 to 200.

        :param queries: The query to parse. Valid options are: ==, !=, >=, <=, >, <, like, ilike, in, is, between, isnot.
        :param kwargs: The arguments to give to the parser. e.g., you give "t.username == :uname:", then give the uname as an arg.
        :return: The parsed query.
        """
        validator(
            (
                "queries", queries, list, (
                    (lambda: isinstance(i, str) for i in queries),
                    "All items of queries must be string"
                )
            )
        )

        out = []

        for query in queries:
            splitted = query.split()
            if len(splitted) != 3 or \
                    splitted[1] not in self.mapping.keys() or \
                    not any(spl.startswith("t.") for spl in splitted):
                raise InvalidQueryException(query)

            tableq = list(filter(lambda x: x.startswith("t."), splitted))
            args = list(filter(lambda x: x.startswith(":") and
                                         x.endswith(":") and
                                         x[1:-1] in kwargs.keys(), splitted))
            normalv = list(filter(lambda x:
                                  not x.startswith("t.") and
                                  not (x.startswith(":") and x.endswith(":")) and
                                  x not in self.mapping.keys()
                                  , splitted))

            tableq_executed = []
            args_executed = []
            normalv_executed = []

            for q in tableq:
                tableq_executed.append(getattr(self.table.c, q[2:]))

            for a in args:
                args_executed.append(kwargs[a[1:-1]])

            for n in normalv:
                normalv_executed.append(self.getvalue(n))

            final = []
            final.extend(tableq_executed)
            final.extend(args_executed)
            final.extend(normalv_executed)

            if len(final) != 2:
                raise InvalidQueryException(query)

            appending = self.mapping[splitted[1]](*final)
            out.append(appending)

        return out

    def getvalue(self, item: str) -> Any:
        """
        Automatically maps string values to different built-in types.
        Supports integers, floats, and booleans.
        :param item: The item to map.
        """
        out: Any = item
        if not (self.autotype or isinstance(item, str)):
            return out

        if item in ["True", "False"]:
            out = literal_eval(item)
        elif item.isnumeric():
            out = int(item)
        elif "." in item and item.count(".") == 1 and all(x.isnumeric() for x in item.split(".")):
            out = float(item)

        return out