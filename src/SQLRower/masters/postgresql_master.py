from typing import Literal, Optional

from sqlalchemy import Engine, create_engine, text, MetaData, REAL, DOUBLE, SmallInteger, Integer, BigInteger, VARCHAR, \
    Text, DECIMAL, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, DeclarativeMeta, declarative_base

from SQLRower.masters.abstract_master import AbstractMaster
from SQLRower.validator import validator

import re2

class PostgresqlMaster(AbstractMaster):


    def __init__(self, *, host: str, port: int,
                 user: str, password: str,
                 name: str, schema: Optional[str] = None,
                 strict: bool = True,
                 prefix: Optional[str] = None,
                 preserve_case: bool = False):
        """
        Initializes a PostgresqlMaster, allowing to use executor on Postgresql Database.
        :param host: The host of the Postgresql Database.
        :param port: The port to the Postgresql Database.
        :param user: The user to access the Postgresql Database as.
        :param password: The password that the user uses.
        :param name: The name of the database.
        :param schema: Optional, a schema to access the database as.
        :param strict: Whether to be strict about schema names(must start with a-z, A-Z, or _, and must contain 0-9, a-z, A-Z, and _ only.)
        It's actually recommended for all kinds of work.
        :param prefix: The prefix to add to the schema name(Only a-zA-Z if strict is true).
        :param preserve_case: whether to preserve the case of the schema name. Recommended to set to False.
        """

        validator(
            (
                "host",
                host,
                str
            ),
            (
                "port",
                port,
                int,
                (
                    (lambda: port > 999),
                    "Expected port to be above 999."
                )
            ),
            (
                "user",
                user,
                str
            ),
            (
                "password",
                password,
                str
            ),
            (
                "name",
                name,
                str
            ),
            (
                "schema",
                schema,
                (None, str),
                (
                    (lambda: not strict or
                             re2.match("[a-zA-Z_][a-zA-Z0-9_]*", prefix + schema
                             if isinstance(prefix, str) else schema) is not None or
                             len(prefix + schema if isinstance(prefix, str) else schema) <= 60),
                    "When strict is true, the schema name must contain characters a to z, A to Z,"
                    "underline at the start.\n Continuing, the schema name must contain a to z,"
                    "A to Z, 0 to 9, or underline at the rest of the name.\n And most importantly,"
                    "it must be less than or equal to 60 characters."
                )
            ),
            (
                "strict",
                strict,
                bool
            ),
            (
                "prefix",
                prefix,
                (None, str),
            ),
            (
                "preserve_case",
                preserve_case,
                bool
            )
        )

        def sanitize(string: str):
            """
            Basic URL encoding.
            :param string: The string to URL encode.
            :return: A URL encoded string.
            """
            return string.replace('/', '%2F').replace('@', '%40').replace(":", "%3A")

        engine = create_engine(
            f"postgresql+psycopg2://{sanitize(user)}"
            f":{sanitize(password)}@{sanitize(host)}:"
            f"{port}/{sanitize(name)}",
        )
        session = sessionmaker(bind=engine, expire_on_commit=False)

        if schema is not None:
            if prefix is not None:
                schema = prefix + schema
            if not preserve_case:
                schema = schema.lower()
            schema = schema.replace('"', '""')


            executing = text(f"CREATE SCHEMA IF NOT EXISTS \"{schema}\"")

            with engine.connect() as conn:
                conn.execute(executing)
                conn.commit()

        m = MetaData(schema=schema)

        Base: DeclarativeMeta = declarative_base(metadata=m)

        self._engine, self._session, self._base = [
            engine,
            session,
            Base
        ]

        self._limit = {
            int: lambda x: -2**63 < int(x) < 2**63 - 1,
            float: lambda x: -1.0e+131071 < float(x) < 1.0e+131071,
            str: lambda x: x < 10_485_760
        }

        self._int_types = {
            SmallInteger: lambda x: -32_768 < int(x) < 32_767,
            Integer: lambda x: -2_147_483_648 < int(x) < 2_147_483_647,
            BigInteger: lambda x: -2**63 < int(x) < 2**63 - 1
        }

        self._float_types = {
            REAL: lambda x: 0.000001 <= float(x),
            DOUBLE: lambda x: 5e-324 <= float(x),
            DECIMAL: lambda x: -1.0e+131071 < int(x) < 1.0e+131071,
        }

        self._str_types = {
            VARCHAR: lambda x: x < 10_485_760,
            Text: True
        }

        self._all_types = {
            "int": self._int_types,
            "float": self._float_types,
            "datetime": DateTime,
            "bool": Boolean,
        }

    def gettriple(self) -> tuple[Engine, sessionmaker, DeclarativeMeta]:
        return self._engine, self._session, self._base

    def limit(self, type_: Literal["int", "str", "float", "bool", "datetime"] | type, given: int) -> bool:
        if type_ in ["bool", "datetime"]:
            return False

        map_ = {
            "int": int,
            "str": str,
            "float": float,
        }

        type_ = map_[type_.lower()]
        return not self._limit[type_](given) # since it returns true if it doesn't surpass, we want the opposite.


    def mapping(self, type_: Literal["int", "str", "float", "bool", "datetime"] | type, given: int):
        type_ = type_.__name__ if isinstance(type_, type) else type_

        original = type_

        if type_ == "str":
            for k, v in self._str_types.items():
                if v(given):
                    return k(given)

            raise ValueError("Could not find a fitting type for str")

        type_ = self._all_types[type_.lower()]
        if isinstance(type_, dict):
            print(type_)
            for k, v in type_.items():
                if v(given):
                    return k
        if isinstance(type_, type_):
            return type_

        raise ValueError(f"Could not find a fitting type for {original}")

    def reflection_options(self):
        return {"schema": self._base.metadata.schema}