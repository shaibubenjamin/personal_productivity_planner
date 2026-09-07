import tempfile
from pathlib import Path

from engine.common.db import SCHEMA_PATH, get_connection, init_db


def test_init_db_creates_tables_and_is_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        init_db(db_path, SCHEMA_PATH)
        init_db(db_path, SCHEMA_PATH)  # must not raise on second call

        conn = get_connection(db_path)
        try:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        finally:
            conn.close()

        assert {"domains", "goals", "actions", "audit_log"} <= tables


def test_domain_insert_and_read_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        init_db(db_path, SCHEMA_PATH)
        conn = get_connection(db_path)
        try:
            conn.execute(
                "INSERT INTO domains (id, name, strategic_weight, minimum_attention_pct) "
                "VALUES ('career', 'Career', 50, 50)"
            )
            conn.commit()
            row = conn.execute("SELECT * FROM domains WHERE id = 'career'").fetchone()
        finally:
            conn.close()

        assert row["name"] == "Career"
        assert row["minimum_attention_pct"] == 50
