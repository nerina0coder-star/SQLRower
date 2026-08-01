import sqlite3
from pathlib import Path
from typing import Literal, Any
from warnings import warn

from sqlalchemy import Engine, create_engine, Integer, REAL, Text, Float, Boolean, DateTime, SmallInteger, BigInteger, \
    DECIMAL, VARCHAR
from sqlalchemy.orm import sessionmaker, declarative_base, DeclarativeMeta

from SQLRower.masters.abstract_master import AbstractMaster
from SQLRower.validator import validator


class SQLiteMaster(AbstractMaster):
    def __init__(self, path: str):
        """
        Creates a SQLiteMaster object.

        The given paths can be:
        /absolute/path/to/sqlite.db
        relative/path/to/sqlite.db
        m!

        Yes, the letter m that comes before a question mark.

        :param path: The path to the SQLite DB. Will be created if it doesn't exist.
        """
        validator(
            ("path", path, str)
        )
        in_memory = "m!"

        if path != in_memory:
            pathed = Path(path)
            if not pathed.exists():
                pathed.parent.mkdir(parents=True, exist_ok=True)
                sqlite3.connect(str(pathed)).close()
            try:
                sqlite3.connect(str(pathed)).close()
            except sqlite3.OperationalError:
                warn("Could not connect to database, please check the path.")
                raise

        self.path = path if path != in_memory else ":memory:"

        self._intmap = {
            SmallInteger: lambda x: False,
            Integer: lambda x: True,   # In SQLite, SmallInt and BigInt both refer to Integer
            BigInteger: lambda x: False,
        }

        self._floatmap = {
            REAL: lambda x: True,  # In SQLite, Float and DECIMAL both refer to REAL
            Float: lambda x: False,
            DECIMAL: lambda x: False,
        }

        self._boolmap = {
            Boolean: lambda x: True,
        }

        self._datetimemap = {
            DateTime: lambda x: True,
        }

        self._mapping = {
            "int": self._intmap,
            "float": self._floatmap,
            "str": "SPECIAL",
            "bool": self._boolmap,
            "datetime": self._datetimemap,
        }

        self._limiter = {
            "int": lambda x: 9.22e+18 > int(x) > -9.22e+18,
            "str": lambda x: int(x) < 1_000_000_000,
            "float": lambda x: False,
        }

    def gettriple(self) -> tuple[Engine, sessionmaker, DeclarativeMeta]:
        engine = create_engine(f"sqlite:///{self.path}")
        session = sessionmaker(bind=engine)
        Base: DeclarativeMeta = declarative_base()
        return engine, session, Base

    def limit(self, type_: Literal["int", "str", "float"]|Any, given: int) -> bool:
        """
        Processes and checks if the item exceeds the limit of SQLite.
        :param type_: The type of item to check.
        :param given: The given limit.
        :return: True if it exceeds, False otherwise.
        """
        if type_ in self._limiter:
            return self._limiter[type_](given)
        return False

    def mapping(self, type_: Literal["int", "str", "float", "bool", "datetime"]|type, given: int):
        """
        Returns the type of the item.
        :param given: The given limit.
        :param type_: The python equivalent of the item.
        :return: A SQLAlchemy type of the item.
        """
        validator(
            (
                "given",
                given,
                (int, None)
            ),
            (
                "type",
                type_,
                (type, str)
            )
        )

        if isinstance(type_, str):
            item =self._mapping.get(type_)
        else:
            item = self._mapping.get(type(type_).__name__)

        if item is None:
            raise ValueError("Unknown type: ", type_)

        if item == "SPECIAL": # Strings are special
            return VARCHAR(given) if given is not None else Text

        for k, v in reversed(item.items()):
            if v(given):
                return k

        raise ValueError("Unknown type: ", type_)

    def reflection_options(self):
        return {}