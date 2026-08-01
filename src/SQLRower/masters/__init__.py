from typing import Literal

from .abstract_master import AbstractMaster
from .postgresql_master import PostgresqlMaster
from .sqlite_master import SQLiteMaster

def automaster(type_: Literal["SQLite","Postgres","MySQL","Oracle",], raw: bool = False,
               **keyword_arguments) -> AbstractMaster | type[AbstractMaster]:
    """
    Automatically returns a master fitting the task.
    :param type_: The type of the master.
    :param raw: Should return type[AbstractMaster] or AbstractMaster.
    :param keyword_arguments: The kwargs to give to the master if not asked for raw.
    :return: type[AbstractMaster] or AbstractMaster.
    """
    mapping = {
        "SQLite": SQLiteMaster,
        "PostgreSQL": PostgresqlMaster
    }
    mapped = mapping[type_]
    if raw:
        return mapped
    return mapped(**keyword_arguments)

__all__ = ["automaster"]