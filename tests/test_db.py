"""
Tests unitarios para la base de datos, snapshots criptográficos y pragmas WAL (V-07, V-16).
"""

import unittest
from src.core.db import init_db, save_raw_snapshot, get_db_connection


class TestDatabaseSnapshots(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_database_snapshots_deduplication(self):
        test_payload = '{"status": "ok", "models": 42, "secret": "AIzaSyFakeSecretKey12345"}'
        hash_1 = save_raw_snapshot("TestCollector", "https://api.test/models", test_payload)
        self.assertEqual(len(hash_1), 64)

        # Intentar guardar el mismo snapshot (debe deduplicar por SHA256)
        hash_2 = save_raw_snapshot("TestCollector", "https://api.test/models", test_payload)
        self.assertEqual(hash_1, hash_2)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT payload FROM snapshots_raw WHERE sha256_hash = ?", (hash_1,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            # Verificar saneamiento de secreto (Fix V-16)
            self.assertNotIn("AIzaSyFakeSecretKey12345", row[0])
            self.assertIn("[REDACTED]", row[0])


if __name__ == "__main__":
    unittest.main()
