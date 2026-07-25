from functools import lru_cache
from typing import Literal, Any, Callable
from warnings import warn

from sqlalchemy import MetaData, Table

from SQLRower.masters.abstract_master import AbstractMaster
from SQLRower.parsers import RowParser
from SQLRower.parsers import SelectionParser
from SQLRower.parsers import TableParser
from SQLRower.typing import TypingColumn
from SQLRower.typing.row import TypingRow
from SQLRower.validator import validator


class Executor:
    """
    An executor made to control any database.
    """

    def __init__(self, master: AbstractMaster,
                 report_to: Callable[[str, Exception], None]|None = None,):
        """
        Initializes an Executor.

        :param master: A master to control the database from.
        :param report_to: Reports to the given function if anything went wrong.
        Must accept a str and an Exception.
        """
        validator(
            ("master", master, AbstractMaster),
        )

        if report_to and not callable(report_to):
            raise TypeError("report_to must be a callable.")

        engine, session, meta = master.gettriple()

        def default_report(_, e):
            raise e

        self._report_to = report_to if report_to is not None else default_report
        self._meta = meta
        self._engine = engine
        self._session = session
        self._master = master

    def select(self, queries: str | Literal["all"] | list[str],
               /, *, table_name: str, logic: str, **kw):
        """
        Select rows from a SQLite database.
        :param queries: The selection queries to use. (Refer to SelectionParser.parser)
        :param table_name: The name of the table to select from.
        :param logic: The logic to use. OR:
        At least one of the conditions must be satisfied.
        AND: All the conditions must be satisfied.
        :param kw: The arguments to use in the conditions. (Refer to SelectionParser.parser)
        :return: The result of the selection.
        """
        try:
            selector = SelectionParser(self._gettable(table_name), self._engine, autotype=True)
            selected = selector(queries, logic=logic, **kw)
        except Exception and Warning as e:
            self._report_to("select", e)
            return False
        return selected

    def select_all(self, table_name: str):
        """
        Select all rows from a SQLite database.

        :param table_name: The name of the table to select from.
        :return: The result of the selection.
        """
        try:
            selector = SelectionParser(
                self._gettable(table_name),
                self._engine,
                autotype=True
            )
        except Exception and Warning as e:
            self._report_to("select_all", e)
            return False
        return selector.getall()

    def mktable(self,
                queries: dict | list[dict] | list[list[dict]] | TypingColumn | list[TypingColumn] | list[list[TypingColumn]],
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
            self._report_to("mktable",  e)

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
                /, *, table_name: str, primary_key_name: str):
        """
        Create/Update/Delete multiple rows.
        The structure of the details are made clear in RowParser.parser.
        :param queries: The details of the operations.
        :param table_name: The name of out table.
        :param primary_key_name: The name of the primary key.
        """
        row = RowParser(self._gettable(table_name), self._engine, primary_key_name)
        try:
            row(queries)
        except Exception as e:
            self._report_to("makerow", e)

    def c(self, *, table_name: str):
        """
        Returns the columns as generator.

        :param table_name: The name of the table.
        """
        validator(("table_name", table_name, str))
        cols = self._gettable(table_name=table_name).c
        for i in cols:
            yield getattr(i, "name", None)

    def columns(self, *, table_name: str):
        """
        Returns a list of columns from the table.
        :param table_name: The name of the table.
        """
        return list(self.c(table_name=table_name))

    @lru_cache(64)
    def _gettable(self, table_name: str) -> Table:
        validator(
            (
                "table_name",
                table_name,
                str
            )
        )
        try:
            meta = MetaData()

            table = Table(table_name, meta, autoload_with=self._engine)
        except:
            warn("Could not create Table, make sure the table exists.")
            raise
        return table
