import threading

from SQLRower import Executor
from SQLRower.executors.read_only_executor import ReadOnlyExecutor
from SQLRower.executors.write_only_executor import WriteOnlyExecutor
from SQLRower.masters import AbstractMaster
from SQLRower.validator import validator


class LazyExecutor(Executor):
    """
    The class that uses the executor to execute multiple write queries in separate threads.

    Expect no return value.
    """

    def __init__(self, master: AbstractMaster = None, executor: Executor = None):
        """
        Creates a LazyExecutor instance, great for doing multiple write(not read!) operations lazily.
        :param master: The AbstractMaster instance to use, optional if executor is given.
        :param executor: An executor instance to use instead of creating a new one, optional.
        """
        validator(
            (
                "master",
                master,
                (None, AbstractMaster),
                (
                    (lambda: (master is not None and executor is None) or (master is None and executor is not None)),
                    "Master or Executor must be given."
                )
            ),
            (
                "executor",
                executor,
                (None, Executor),
            )
        )

        if master is not None:
            super().__init__(master)

        self._executor = Executor(master) if executor is None else executor
        self._calls = []

    def __getattribute__(self, name):
        if name in dir(WriteOnlyExecutor):
            return lambda *args, **kwargs: self._calls.append(
                {
                    "name": name,
                    "args": args,
                    "kwargs": kwargs,
                }
            )
        if name in dir(ReadOnlyExecutor):
            self.evaluate_all()
            return getattr(self._executor, name)

        return object.__getattribute__(self, name)

    def eval(self):
        """
        Runs all write queries in a separate thread.
        """
        threading.excepthook = LazyExecutor._ehook_
        t = threading.Thread(
            target=self.evaluate_all,
            daemon=False
        )
        t.start()

    def evaluate_all(self):
        """
        Runs all write queries.
        """
        for i in self._calls:
            name = i["name"]
            args = i["args"]
            kwargs = i["kwargs"]

            getattr(self._executor, name)(*args, **kwargs)

        self._calls.clear()

    @staticmethod
    def _ehook_(_, err, __):
        raise err