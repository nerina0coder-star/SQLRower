from functools import lru_cache
from typing import Callable
from warnings import warn

from sqlalchemy import MetaData, Table

from SQLRower.executors.read_only_executor import ReadOnlyExecutor
from SQLRower.executors.write_only_executor import WriteOnlyExecutor
from SQLRower.masters.abstract_master import AbstractMaster
from SQLRower.validator import validator


class Executor(ReadOnlyExecutor, WriteOnlyExecutor):
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

        engine, session, Base = master.gettriple()

        def default_report(_, e, /):
            raise e from e

        super().__init__(master, self._gettable, report_to=report_to if report_to is not None else default_report)

        self._engine = engine

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

            table = Table(table_name, meta, autoload_with=self._engine, **self._master.reflection_options())
        except:
            warn("Could not reflect Table, make sure the table exists.")
            raise
        return table
