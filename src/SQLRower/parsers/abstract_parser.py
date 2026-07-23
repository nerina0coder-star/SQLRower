import abc
from abc import ABC
from typing import Any

from sqlalchemy import Executable


class AbstractParser(ABC):
    @abc.abstractmethod
    def __call__(self, queries: Any|list[Any], **kwargs): ... # Implicit

    @abc.abstractmethod
    def parser(self, queries: list[Any], **kwargs) -> list[Executable]: ... # Explicit