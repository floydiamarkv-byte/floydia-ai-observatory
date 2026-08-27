"""
Tests unitarios para la base de datos y snapshots.
"""

from src.core.db import init_db, save_raw_snapshot, get_db_connection


def test_database_snapshots():
    init_db()
    test_payload = '{"status": "ok", "models": 42}'
    hash_1 = save_raw_snapshot("TestCollector", "https://api.test/models", test_payload)
    assert len(hash_1) == 64

    # Intentar guardar el mismo snapshot (debe deduplicar por SHA256)
    hash_2 = save_raw_snapshot("TestCollector", "https://api.test/models", test_payload)
    assert hash_1 == hash_2

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM snapshots_raw WHERE sha256_hash = ?", (hash_1,))
        count = cursor.fetchone()[0]
        assert count == 1

    print("✅ test_database_snapshots PASSED")


if __name__ == "__main__":
    test_database_snapshots()
