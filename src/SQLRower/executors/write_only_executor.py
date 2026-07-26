from typing import Callable, Literal, Any

from sqlalchemy import Table

from SQLRower.executors.abstract_only_executor import AbstractOnlyExecutor
from SQLRower.masters import AbstractMaster
from SQLRower.parsers import RowParser, TableParser
from SQLRower.typing import TypingColumn
from SQLRower.typing.row import TypingRow
from SQLRower.validator import validator


class WriteOnlyExecutor:
    def __init__(self, master: AbstractMaster,
                 table_reflector: Callable[[str], Table],
                 /, *, report_to: Callable):
        validator(
            (
                "master",
                master,
                AbstractMaster,
                (
                    (lambda: callable(table_reflector)),
                    "Table reflector must be callable",
                )
            )
        )

        if not callable(report_to):
            raise TypeError("report_to must be a callable.")

        if isinstance(super(), AbstractOnlyExecutor):
            super().__init__(master, table_reflector, report_to=report_to)

        self._report_to = report_to
        self._gettable = table_reflector
        self._master = master
        self._engine, self._session, self._meta = master.gettriple()

    def mktable(self,
                queries: dict | list[dict] | list[list[dict]] | TypingColumn | list[TypingColumn] | list[
                    list[TypingColumn]],
                /, *, name: str):
        """
        Creates a table in the SQLite database.

        :param queries: The tables to create. (Refer to TableParser.parser)
        :param name: The name of the table.
        """
        table = TableParser(self._meta, self._engine, self._master)
        try:
            table(queries, table_name=name)
        except Exception as e:
            self._report_to("mktable", e)

    def mkrow(self,
              operation_type: Literal["add", "delete", "update"],
              row_data: dict[str, Any] = None,
              row_primary: int = None,
              /, *, table_name: str, primary_key_name: str):
        """
        Create/Update/Delete a single row.
        :param operation_type: The type of the operation.
        :param row_data: The new replacing data(Used for update/add operations).
        :param row_primary: The primary key of the row(Used for update/delete operations).
        :param table_name: The name of our table.
        :param primary_key_name: The name of the primary key.
        """
        giving = [
            operation_type,
            {
                "primary": row_primary,
                "data": row_data
            }
        ]
        self.makerow(giving, table_name=table_name, primary_key_name=primary_key_name)

    def makerow(self, queries: list[str | TypingRow],
                /, *, table_name: str, primary_key_name: str,
                batches: int = 1):
        """
        Create/Update/Delete multiple rows.
        The structure of the details are made clear in RowParser.parser.
        :param queries: The details of the operations.
        :param table_name: The name of out table.
        :param primary_key_name: The name of the primary key.
        :param batches: In how many batches should the operations happen?
        """
        validator(
            (
                "batches",
                batches,
                int,
                (
                    (lambda: batches > 0),
                    "batches must be a positive integer"
                )
            )
        )
        row = RowParser(self._gettable(table_name), self._engine, primary_key_name)
        try:
            row(queries, safety=batches)
        except Exception as e:
            self._report_to("makerow", e)