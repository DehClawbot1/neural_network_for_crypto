import tempfile
import unittest
from pathlib import Path

from db import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test_trading.db"
        self.db = Database(self.db_path)

    def tearDown(self):
        self.db.conn.close()
        self.tmp_dir.cleanup()

    def test_schema_initialization(self):
        tables_to_check = [
            "positions",
            "orders",
            "fills",
            "trade_events",
            "model_decisions",
            "risk_events",
        ]

        for table in tables_to_check:
            query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';"
            result = self.db.query_all(query)
            self.assertEqual(len(result), 1, f"Table {table} was not created.")

    def test_insert_and_query_all(self):
        insert_query = """
        INSERT INTO orders (order_id, token_id, status, price, size)
        VALUES (?, ?, ?, ?, ?)
        """
        params = ("ord-123", "tok-abc", "SUBMITTED", 0.55, 100.0)
        self.db.execute(insert_query, params)

        select_query = "SELECT * FROM orders WHERE order_id = ?"
        results = self.db.query_all(select_query, ("ord-123",))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["token_id"], "tok-abc")
        self.assertEqual(results[0]["status"], "SUBMITTED")
        self.assertEqual(results[0]["price"], 0.55)

    def test_update_record(self):
        self.db.execute("INSERT INTO orders (order_id, status) VALUES (?, ?)", ("ord-999", "OPEN"))
        self.db.execute("UPDATE orders SET status = ? WHERE order_id = ?", ("FILLED", "ord-999"))

        result = self.db.query_all("SELECT status FROM orders WHERE order_id = ?", ("ord-999",))
        self.assertEqual(result[0]["status"], "FILLED")

    def test_query_empty_results(self):
        results = self.db.query_all("SELECT * FROM orders WHERE order_id = ?", ("non-existent",))
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_persistence_between_connections(self):
        self.db.execute("INSERT INTO fills (fill_id, price) VALUES (?, ?)", ("fill-1", 0.42))
        self.db.conn.close()

        new_db = Database(self.db_path)
        results = new_db.query_all("SELECT price FROM fills WHERE fill_id = ?", ("fill-1",))
        self.assertEqual(results[0]["price"], 0.42)
        new_db.conn.close()


if __name__ == "__main__":
    unittest.main()
