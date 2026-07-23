import abc
from abc import ABC
from typing import Literal, Any

from sqlalchemy import Engine, Table
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from SQLRower.typing import TypingColumn
from SQLRower.typing.row import TypingRow


class AbstractExecutor(ABC):

    @abc.abstractmethod
    def select(self, table_name: str, queries: str|list[str], logic: str, **kw): ...
    @abc.abstractmethod
    def mktable(self, queries: TypingColumn|list[TypingColumn]|list[list[TypingColumn]], name: str): ...
    @abc.abstractmethod
    def mkrow(self, operation_type: str,
              table_data: dict[Literal["primary"] | str, Any],
              row_primary: int,
              /, *, table_name: str, primary_key_name: str): ...
    @abc.abstractmethod
    def makerow(self, queries: list[str|TypingRow],
              /, *, table_name: str, primary_key_name: str): ...
    @abc.abstractmethod
    def _getter(self, *args, **kwargs) -> tuple[Engine, sessionmaker[Session], DeclarativeBase]:
        """
        The only permissive method.
        """
    @abc.abstractmethod
    def _gettable(self, table_name: str) -> Table: ...