import abc
from typing import Literal

from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, DeclarativeMeta


class AbstractMaster(abc.ABC):
    @abc.abstractmethod
    def gettriple(self) -> tuple[Engine, sessionmaker, DeclarativeMeta]:
        """
        A method used to get an engine, session and declarative base, in that order.
        """

    @abc.abstractmethod
    def limit(self, type_: Literal["int", "str", "float", "bool", "datetime"]|type, given: int) -> bool:
        """
        Checks if the given number exceeds the limits of the DB.
        :param type_: The type of the column.
        :param given: The given limit.
        :return: True if it exceeds, False otherwise.
        """

    @abc.abstractmethod
    def mapping(self, type_: Literal["int", "str", "float", "bool", "datetime"]|type, given: int):
        """
        A method used to get the equivalent of a python object.

        :param type_: The type of the column.
        :param given: The given limit.
        :return:
        """

    @abc.abstractmethod
    def reflection_options(self):
        """
        The arguments to pass to reflector. Such as Schema.
        """