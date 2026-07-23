import sqlite3
from pathlib import Path
from typing import Literal, Any
from warnings import warn

from sqlalchemy import create_engine, Engine, MetaData, Table
from sqlalchemy.orm import declarative_base, sessionmaker, Session, DeclarativeBase

from SQLRower.executors.abstract_executor import AbstractExecutor
from SQLRower.parsers import SelectionParser
from SQLRower.parsers import TableParser
from SQLRower.parsers import RowParser
from SQLRower.typing import TypingColumn
from SQLRower.typing.row import TypingRow
from SQLRower.validator import validator


class SQLiteExecutor(AbstractExecutor):
    """
    An executor made to control a SQLite database.
    """

    def __init__(self, path: str):
        """
        Initializes a SQLiteExecutor.

        :param path: The path to SQLite Database(If not exists, will be created).
        """
        validator(
            ("path", path, str),
        )

        pathed = Path(path)
        if pathed.exists() and pathed.is_dir():
            raise FileExistsError("Found a directory matching the given path.")
        if not pathed.exists():
            pathed.parent.mkdir(parents=True, exist_ok=True)
            sqlite3.connect(pathed).close()

        try:
            sqlite3.connect(pathed).close()
        except sqlite3.OperationalError:
            warn("Could not connect to the database. Check if the database is a SQLite database.")
            raise

        engine, session, base = self._getter(pathed)

        self._base = base
        self._engine = engine
        self._session = session

    def select(self, queries: str|list[str],
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
        selector = SelectionParser(self._gettable(table_name), self._engine, autotype=True)
        selected = selector(queries, logic=logic, **kw)
        return selected

    def mktable(self, queries: TypingColumn|list[TypingColumn]|list[list[TypingColumn]],
                /, *, name: str):
        """
        Creates a table in the SQLite database.

        :param queries: The tables to create. (Refer to TableParser.parser)
        :param name: The name of the table.
        """
        table = TableParser(self._base, self._engine)
        table(queries, table_name=name)

    def mkrow(self,
              operation_type: Literal["add", "delete", "update"],
              row_data: dict[str, Any]=None,
              row_primary: int=None,
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
        row(queries)

    def _getter(self, path: Path) -> tuple[Engine, sessionmaker[Session], DeclarativeBase]:
        """
        Returns an Engine, Session, and DeclarativeBase object.
        :param path: The path to the DB.
        :return: tuple of Engine, Session, DeclarativeBase
        """
        engine = create_engine("sqlite:///" + str(path))
        session = sessionmaker(bind=engine)
        base: DeclarativeBase = declarative_base()
        return engine, session, base

    def _gettable(self, table_name: str) -> Table:
        try:
            meta = MetaData()

            table = Table(table_name, meta, autoload_with=self._engine)
        except:
            warn("Could not create Table, make sure the table exists.")
            raise
        return table