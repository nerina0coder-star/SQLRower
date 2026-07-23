import shutil
import unittest

from SQLRower.executors.sqlite_executor import SQLiteExecutor
from SQLRower.typing import TypingColumn


class TestSQLiteExecutor(unittest.TestCase):
    test_path = "./test_dbs/sqlite/"

    def test_table(self):
        sqlite_executor = SQLiteExecutor(self.test_path + "test.db")

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
        }
        cols.append(new_col)

        for k, v in details.items():
            new_col: TypingColumn = {
                "name": k,
                "type": v,
            }

            cols.append(new_col) # Do this instead, fixes the IDE-type hint issues.

        try:
            sqlite_executor.mktable(cols, name="test")
        finally:
            shutil.rmtree(self.test_path)

    def test_row(self):
        sqlite_executor = SQLiteExecutor(self.test_path + "test.db")

        col: TypingColumn = {
            "name": "id",
            "type": int,
            "options": {
                "primary_key": True,
                "unique": True,
            }
        }

        try:
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
        finally:
            shutil.rmtree(self.test_path)

    def test_select(self):
        executor = SQLiteExecutor(self.test_path + "test.db")

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

        try:
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

            result = executor.select("t.username ilike t%st",
                            table_name="test",
                            logic="and")

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
        finally:
            shutil.rmtree(self.test_path)