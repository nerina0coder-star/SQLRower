import math

from sqlalchemy import Executable, Table, insert, update, delete, Engine, select

from SQLRower.parsers.abstract_parser import AbstractParser
from SQLRower.typing.row import TypingRow
from SQLRower.validator import validator


class RowParser(AbstractParser):
    def __init__(self, table: Table, engine: Engine, keyname: str):
        """
        Initializes the RowParser class.
        :param table: The table to query on.
        :param engine: The engine.
        :param keyname: The name of the primary key.
        """
        # Validating
        validator(
            (
                "table",
                table,
                Table,
            ),
            (
                "engine",
                engine,
                Engine,
            ),
            (
                "keyname",
                keyname,
                str,
                (
                    (lambda: hasattr(table.c, keyname)),
                    "Keyname MUST exist in the table."
                )
            )
        )

        self.engine = engine
        self._primary_message = "The ID column must exist in the table. And the given ID must be above or equal to 0."
        self.table = table
        self._keyname = keyname
        self._primary_checker = (lambda column_id: getattr(self.table.c, self._keyname, None) is not None
                                 and self._query_table_exists(column_id)
                                 and column_id > 0
                                 )

    def __call__(self, queries: list[str|TypingRow] | list[list[str|TypingRow]], **kwargs):
        """
        Executes the given queries. For more details, refer to RowParser.parser.
        :param queries: The queries to execute.
        :param kwargs: Level of safety(keyname: safety) can be added. The safer, the slower.
        :return:
        """
        if isinstance(queries, list) and not all(isinstance(q, list) for q in queries):
            queries = [queries]
        safety = kwargs.get("safety", 1)
        if not isinstance(safety, int):
            safety = 1

        executing = self.parser(queries, **kwargs)

        # Batching and execution
        chunk_size = math.ceil(len(executing) / safety)

        splitted = [
            executing[0:math.ceil(len(executing) / safety)],
            *[executing[chunk_size * (i + 1):chunk_size * (i + 2)]
              for i in range(safety - 1)]
        ]

        with self.engine.connect() as conn:
            for s in splitted:
                for e in s:
                    conn.execute(e)
                conn.commit()


    def parser(self, queries: list[list[str|TypingRow]], **kwargs) -> list[Executable]:
        """
        Controls the table's rows.

        queries(param): Defines the chances. It should be structured like this:

        {
            tablename: [operation, {data for add/update/delete}]
        }

        It can be also be put as:
        a dictionary with its keys as table names and values as operation types(strictly in a list).

        for add:
            - Row data.
            - Example structure for user:
                {
                    "data": {
                        "username": "Patrik",

                        "email": "anyone.other.than.patrik@gmail.com"
                    }
                }

        for update:
            - Row data.
            - Row primary key(Integer Only).
            - Example structure for user:
                {
                    "data": {...},

                    "primary": 1234
                }

        for delete:
            - Row primary key(Integer Only).
            - Example structure for user:
                {
                    "primary": 1234
                }

        Operation types are: add, update, delete

        primary must be the primary key (unique) of the row. and data must be the new replacing data.

        :param queries: Explained above.
        :param kwargs: Accepts nothing.
        :return: A list of Executables to execute, each doing different operations.
        """
        # Validation
        type_check = lambda: all(isinstance(i, list) for i in queries)
        check_details = lambda: all(len(i) == 2 for i in queries)
        check_inner_most = lambda: all(
                isinstance(i[0], str) and isinstance(i[1], dict)
                for i in queries
            )

        validator(
            (
                "queries",
                queries,
                list,
                (
                    (
                        lambda:
                        type_check()
                        and check_details()
                        and check_inner_most()
                    ),
                    "All elements of queries must be lists with two elements, operation type and operation details."
                )
            )
        )

        del type_check, check_details, check_inner_most

        # Creating mappings
        supported_types = [
            "add",
            "update",
            "delete",
        ]
        type_mapping = {
            "add": self._add,
            "update": self._update,
            "delete": self._delete,
        }

        out = []

        for operation in queries:
            operation_type = operation[0]
            operation_details = operation[1]

            # Validating operation type
            validator(
                (
                    "operation_type",
                    operation_type,
                    str,
                    (
                        (lambda: operation_type in supported_types),
                        f"Operation {operation_type} is not supported. \
                        \nPlease consider one of these: {supported_types}"
                    )
                )
            )

            # Appending
            item = type_mapping[operation_type](operation_details)

            out.append(item)
        return out

    def _add(self, details: dict) -> Executable:
        """
        Creates an INSERT statement based on the details.
        :param details: Must include data in this.
        :return: an Executable.
        """
        column_details = details["data"]

        validator(
            (
                "data",
                column_details,
                dict
            )
        )

        stmt = insert(self.table).values(**column_details)

        return stmt


    def _update(self, details: dict) -> Executable:
        """
        Creates an UPDATE statement based on the given details.
        :param details: Must include the data and the id(i.e., primary) in this.
        :return: an Executable.
        """
        column_details = details["data"]
        column_id = details["primary"]

        validator(
            (
                "data",
                column_details,
                dict
            ),
            (
                "primary",
                column_id,
                int,
                (
                    (lambda: self._primary_checker(column_id)),
                    self._primary_message
                )
            )
        )

        stmt = update(self.table).\
            where(getattr(self.table.c, self._keyname) == column_id).values(**column_details)

        return stmt

    def _delete(self, details: dict) -> Executable:
        """
        Creates a DELETE statement based on the given details.
        :param details: Must include id(i.e., primary) in this.
        :return: an Executable.
        """
        column_id = details["primary"]

        validator(
            (
                "primary",
                column_id,
                int,
                (
                    (lambda: self._primary_checker(column_id)),
                    self._primary_message
                )
            )
        )

        stmt = delete(self.table).where(
            getattr(self.table.c, self._keyname) == column_id
        )

        return stmt

    def _query_table_exists(self, id_):
        with self.engine.connect() as conn:
            row = conn.execute(
                select(self.table).where(getattr(self.table.c, self._keyname) == id_)
            ).fetchone()
        return row is not None