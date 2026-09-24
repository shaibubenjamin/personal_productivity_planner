"""Storage layer. SQLite by default (data/local/peos.db) - or Postgres
(Supabase) when a DATABASE_URL environment variable is set. Callers only
ever use get_connection()/init_db(); this module is the one place that
knows two backends exist, so nothing else in the app needs to change
depending on which one is active. See scripts/migrate_to_postgres.py for
the one-time schema-apply + data-copy step that switches a local install
over to Postgres - init_db() deliberately does NOT auto-apply DDL to a
hosted database on every page load, only to the local SQLite file.
"""

import os
import sqlite3
from pathlib import Path
from typing import Any

from engine.common.config import REPO_ROOT

DB_PATH = REPO_ROOT / "data" / "local" / "peos.db"
SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "schema_sqlite.sql"
POSTGRES_SCHEMA_PATH = REPO_ROOT / "data" / "schemas" / "schema.sql"
POSTGRES_CA_CERT_PATH = REPO_ROOT / "data" / "certs" / "supabase-ca.crt"

_pg_engine = None  # lazily created, reused across get_connection() calls


def _database_url() -> str | None:
    """Forces the psycopg2 dialect explicitly, rather than leaving it to
    SQLAlchemy's own driver auto-detection for a bare `postgresql://` URL.
    Real bug, hit on Streamlit Cloud: a newer SQLAlchemy release there
    resolved the driverless scheme to the psycopg (v3) dialect instead of
    psycopg2 - which isn't installed (only psycopg2-binary is, in
    requirements.txt) - raising ModuleNotFoundError at connect time. This
    behaved differently there than in local testing purely because of
    which SQLAlchemy version each environment happened to have installed,
    not because of anything about the URL itself - forcing the dialect
    removes that version-dependent ambiguity for good.
    """
    url = os.environ.get("DATABASE_URL")
    if url and url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def _postgres_engine():
    global _pg_engine
    if _pg_engine is None:
        from sqlalchemy import create_engine

        connect_args = {}
        if POSTGRES_CA_CERT_PATH.exists():
            connect_args = {"sslmode": "verify-full", "sslrootcert": str(POSTGRES_CA_CERT_PATH)}
        _pg_engine = create_engine(_database_url(), pool_pre_ping=True, connect_args=connect_args)
    return _pg_engine


class _PostgresRows:
    """Mimics the .fetchone()/.fetchall() surface of a sqlite3 cursor, over
    a list of already-materialized dict rows (bracket access: row["col"])."""

    def __init__(self, rows: list[dict]):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class _PostgresConnection:
    """Wraps a SQLAlchemy Connection so call sites can keep using the exact
    same conn.execute(sql, params).fetchone()/.fetchall() / row["col"]
    pattern they already use against sqlite3.Connection - callers never
    need to know which backend is active."""

    def __init__(self, sa_connection):
        self._conn = sa_connection

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> _PostgresRows:
        from sqlalchemy import text

        result = self._conn.execute(text(sql), params or {})
        if result.returns_rows:
            return _PostgresRows([dict(r._mapping) for r in result.fetchall()])
        return _PostgresRows([])

    def executescript(self, script: str) -> None:
        # Strip full-line comments first - a fragment left with only a
        # comment after splitting on ";" is an empty query to psycopg2.
        lines = [line for line in script.splitlines() if not line.strip().startswith("--")]
        for statement in "\n".join(lines).split(";"):
            statement = statement.strip()
            if statement:
                self.execute(statement)

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def get_connection(db_path: Path = DB_PATH):
    if _database_url():
        return _PostgresConnection(_postgres_engine().connect())

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path = DB_PATH, schema_path: Path = SCHEMA_PATH) -> None:
    """Create all tables if they don't already exist. Safe to call repeatedly.

    Only touches the local SQLite file - when DATABASE_URL is set, schema
    application is a deliberate one-time step (scripts/migrate_to_postgres.py),
    not something that runs silently against a shared hosted database on
    every app start.
    """
    if _database_url():
        return

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
