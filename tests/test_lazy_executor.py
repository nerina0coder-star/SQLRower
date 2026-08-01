import time
import unittest

from SQLRower import Executor
from SQLRower.executors.lazy_executor import LazyExecutor
from SQLRower.masters import SQLiteMaster


class MyTestCase(unittest.TestCase):
    def test_normal(self):
        master = SQLiteMaster("m!")
        executor = Executor(master)
        lexecutor = LazyExecutor(executor=executor)

        lexecutor.mktable(
            {
                "name": "id",
                "type": int,
                "options": {
                    "nullable": False,
                    "primary_key": True,
                    "unique": True,
                }
            },
            name="test"
        )

        for i in range(2):
            lexecutor.mkrow(
                "add",
                {
                    "id": i
                },
                table_name="test",
                primary_key_name="id",
            )
        before_eval = time.time()

        lexecutor.evaluate_all()

        after_eval = time.time()

        self.assertAlmostEqual(after_eval, before_eval, delta=0.02)

        time.sleep(0.05)

        result = lexecutor.columns(
            table_name="test"
        )

        self.assertEqual(result, ["id"])

        result = lexecutor.select_all(
            table_name="test",
        )

        for i in range(2):
            self.assertEqual(result[i], (i,))