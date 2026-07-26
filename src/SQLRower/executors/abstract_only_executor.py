from abc import abstractmethod, ABC


class AbstractOnlyExecutor(ABC):
    @abstractmethod
    def __init__(self, master, table_reflector, /, *, report_to): ...