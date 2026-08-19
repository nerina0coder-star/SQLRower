import dataclasses
from typing import Literal

@dataclasses.dataclass
class RowDetails:
    primary: int = None
    """
    Only for update/delete.
    """

    data: dict = None
    """
    Only for add/update.
    """

    def __post_init__(self):
        if self.data is None and self.primary is None:
            raise ValueError("At least one option from data and primary key must be set.")

    def keys(self):
        out = {}
        if self.data is not None:
            out["data"] = self.data
        if self.primary is not None:
            out["primary"] = self.primary

        return out

    def __getitem__(self, item):
        if item in ["data", "primary"]:
            return getattr(self, item)
        raise KeyError

@dataclasses.dataclass
class Row:

    operation_type: Literal["add", "update", "delete"]
    details: RowDetails

    def __iter__(self):
        return [self.operation_type, dict(self.details)].__iter__()