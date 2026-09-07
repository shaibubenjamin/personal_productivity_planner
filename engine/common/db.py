"""SQLite storage layer - interim until Supabase/Neon Postgres is wired up
(see docs/decision_log.md). Swapping the backend later means replacing this
module's connection/execute helpers; callers should not construct SQL
elsewhere without going through here.
"""

import sqlite3
from pathlib import Path

from engine.common.config import REPO_ROOT

DB_PATH = REPO_ROOT / "data" / "local" / "peos.db"
SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "schema_sqlite.sql"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH) -> None:
    """Create all tables if they don't already exist. Safe to call repeatedly."""
    conn = get_connection(db_path)
    try:
        existing = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='domains'"
        ).fetchone()
        if existing is None:
            with schema_path.open("r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()
    finally:
        conn.close()
