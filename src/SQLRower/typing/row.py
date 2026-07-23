from typing import TypedDict, Literal


class TypingRow(TypedDict):
    table_name: str
    information: list[
        Literal["add", "update", "delete"]
    ]