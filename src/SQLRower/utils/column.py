import dataclasses
from datetime import datetime
from typing import Literal, Any

from SQLRower.utils.column_reference import ColumnReference


@dataclasses.dataclass
class ColumnOptions:
    nullable: bool
    unique: bool
    foreign: str | ColumnReference

    default: Any

    limit: int = None
    """
    String/Integer only
    """

    primary_key: bool = None
    """
    Integer only
    """

    precision: int = None
    """
    Float only
    """

    decimal_places: int = None
    """
    Float only
    """

    def keys(self):
        out = ["nullable", "unique", "foreign", "default"]

        if isinstance(self.default, float):
            out.extend(["precision", "decimal_places"])
        elif isinstance(self.default, int):
            out.extend(["limit", "primary_key"])
        elif isinstance(self.default, str):
            out.extend(["limit"])

        return out

    def __getitem__(self, item):
        if item in ["nullable", "unique", "foreign", "default"
                    "precision", "decimal_places",
                    "limit", "primary_key"]:
            return getattr(self, item)
        raise KeyError

@dataclasses.dataclass
class Column:
    name: str
    type: type[str | int | float | bool | datetime] | Literal["str", "int", "float", "bool", "datetime"]
    options: ColumnOptions | dict = dataclasses.field(default_factory={})

    def keys(self):
        return [self.name, self.type, dict(self.options)]

    def __getitem__(self, item):
        if item in ["name", "type", "options"]:
            return getattr(self, item)
        raise KeyError