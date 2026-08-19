from typing import Callable, Literal, Any, Generator

from sqlalchemy import Table, Column

from SQLRower.executors.abstract_only_executor import AbstractOnlyExecutor
from SQLRower.masters import AbstractMaster
from SQLRower.parsers import SelectionParser
from SQLRower.utils import ColumnReference
from SQLRower.validator import validator


class ReadOnlyExecutor:
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
                    "The table reflector must be callable."
                )
            ),
        )

        if not callable(report_to):
            raise TypeError("report_to must be a callable.")

        if isinstance(super(), AbstractOnlyExecutor):
            super().__init__(master, table_reflector, report_to=report_to)

        self._report_to = report_to
        self._master = master
        self._gettable = table_reflector
        self._engine, self._session, self._Base = master.gettriple()

    def select(self, queries: str | Literal["all"] | list[str],
               /, *, table_name: str, logic: str, **kw):
        """
        Select rows from a database.
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

    def select_all(self, *, table_name: str):
        """
        Select all rows from a database.

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

    def c(self, *, table_name: str) -> Generator[ColumnReference, Any, None]:
        """
        Returns the columns as generator.

        :param table_name: The name of the table.
        :returns: A generator of ColumnReferences.
        """
        validator(("table_name", table_name, str))
        cols = self._gettable(table_name).c
        for i in cols: # type: Ignore
            i: Column = i
            yield ColumnReference(i, i.name)

    def columns(self, *, table_name: str) -> list[ColumnReference]:
        """
        Returns a list of columns from the table.
        :param table_name: The name of the table.
        :returns: A list of ColumnReferences.
        """
        return list(self.c(table_name=table_name))
