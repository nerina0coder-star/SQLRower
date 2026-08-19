import dataclasses

from sqlalchemy import Column


@dataclasses.dataclass
class ColumnReference:
    """
    Represents a column in the table.
    """

    column: Column
    name: str