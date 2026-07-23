from datetime import datetime
from typing import TypedDict, Any, Literal


class TypingColumn(TypedDict, total=False):
    name: str
    type: type[str]|type[int]|type[float]|type[bool]|type[datetime]|Literal["str", "int", "float", "bool", "datetime"]
    options: dict[Literal["nullable", "unique"]|str, bool|Any]