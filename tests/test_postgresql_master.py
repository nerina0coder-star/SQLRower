import unittest

from SQLRower import Executor
from SQLRower.masters import PostgresqlMaster


class TestPostgreSQLMaster(unittest.TestCase):

    def test_table(self):

        executor = Executor(PostgresqlMaster(
            host='localhost',
            port=5432,
            user='myuser',
            password='mysecretpassword',
            name='mydb',
            schema='test',
            strict=True,
            prefix='test_',
            preserve_case=False
        ))

        executor.mktable(
            {
                'name': 'test',
                'type': float,
                'options': {
                    'precision': 10,
                    'decimal-places': 3
                }
            },
            name='testing'
        )

        result = executor.c(table_name="testing")

        for _ in result:
            pass