import shutil
import unittest

from SQLRower.executors.executor import Executor
from SQLRower.masters import SQLiteMaster
from SQLRower.typing import TypingColumn


class TestExecutor(unittest.TestCase):
    test_path = "./test_dbs/sqlite/"

    def test_table(self):
        sqlite_executor = Executor(SQLiteMaster(self.test_path + "test.db"))
        # Or, if you want it in-memory.
        shutil.rmtree(self.test_path)
        sqlite_executor = Executor(SQLiteMaster("m!"))

        cols = []
        details = {
            "name": str,
            "employed": bool,
            "salary": float
        }

        new_col: TypingColumn = {
            "name": "id",
            "type": int,
            "options": {
                "primary_key": True,
                "unique": True,
            }
        } # Instead of passing the object directly, which sometimes make the linter picky, just type-hint the dict to make the linter understand.
        cols.append(new_col)

        for k, v in details.items():
            new_col: TypingColumn = {
                "name": k,
                "type": v,
            }

            cols.append(new_col) # Do this instead, fixes the IDE-type hint issues.

        sqlite_executor.mktable(cols, name="test")

    def test_row(self):
        sqlite_executor = Executor(SQLiteMaster("m!"))

        col: TypingColumn = {
            "name": "id",
            "type": int,
            "options": {
                "primary_key": True,
                "unique": True,
            }
        }

        sqlite_executor.mktable(
            col,
            name="test",
        )
        sqlite_executor.mkrow(
            "add",
            {
                "id": 1,
            },
            table_name="test",
            primary_key_name="id"
        )
        sqlite_executor.mkrow(
            "update",
            {
                "id": 2
            },
            1,
            table_name="test",
            primary_key_name="id"
        )
        sqlite_executor.mkrow(
            "delete",
            None,
            2,
            table_name="test",
            primary_key_name="id"
        )

    def test_select(self):
        executor = Executor(SQLiteMaster("m!"))

        col: TypingColumn = {
            "name": "id",
            "type": int,
            "options": {
                "primary_key": True,
                "unique": True,
            }
        }

        col2: TypingColumn = {
            "name": "username",
            "type": str,
            "options": {
                "unique": False,
                "nullable": True,
            }
        }

        r = {
            "id": 1,
            "username": "test",
        }
        r2 = {
            "id": 2,
            "username": "example",
        }

        executor.mktable(
            [col, col2],
            name="test",
        )

        executor.mkrow(
            "add",
            r,
            table_name="test",
            primary_key_name="id"
        )
        executor.mkrow(
            "add",
            r2,
            table_name="test",
            primary_key_name="id"
        )

        result = executor.select("t.username ilike :tst:",
                        table_name="test",
                        logic="and",
                        tst="t%st") # Parameterized querying.

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

        result = executor.select_all(table_name="test")

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_columns(self):
        executor = Executor(SQLiteMaster("m!"))

        cols = [{
            "name": "id",
            "type": int,
            "options": {
                "primary_key": True,
                "unique": True,
            }
        }]

        details = {
            "name": str,
            "employed": bool,
            "salary": float
        }

        for k, v in details.items():
            cols.append(
                {
                    "name": k,
                    "type": v,
                }
            )

        executor.mktable(cols, name="test")

        lst = executor.columns(table_name="test")
        for i in lst:
            self.assertIsNotNone(i)
            self.assertIn(i, ["id", *details.keys()])