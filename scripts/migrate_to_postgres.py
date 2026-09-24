"""One-time migration: apply data/schemas/schema.sql to a Postgres/Supabase
database, then copy every row currently in the local SQLite file over.

Run this yourself, locally, once DATABASE_URL is set in your .env - it is
never invoked automatically by the app (see engine/common/db.py). Safe to
re-run: schema application is skipped if the `domains` table already
exists, and each table copy uses INSERT ... ON CONFLICT DO NOTHING, so
re-running after a partial failure won't duplicate rows.

Usage: python -m scripts.migrate_to_postgres
"""

import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from sqlalchemy import create_engine, text  # noqa: E402

from engine.common.db import DB_PATH, POSTGRES_CA_CERT_PATH, POSTGRES_SCHEMA_PATH  # noqa: E402
from engine.common.db import _database_url  # noqa: E402


def get_sqlite_connection(db_path: Path) -> sqlite3.Connection:
    """Always a raw SQLite connection, ignoring DATABASE_URL - unlike
    engine.common.db.get_connection(), which is DATABASE_URL-aware and
    would otherwise hand back a second Postgres connection here, since
    this script runs with DATABASE_URL already set in the environment."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Parent-before-child order (matches data/schemas/schema.sql table order) -
# required so foreign keys resolve correctly on first insert.
TABLE_ORDER = [
    "app_auth", "domains", "objectives", "goals", "goal_dependencies", "daily_habits",
    "platform_feedback", "goal_logs", "goal_risks", "projects", "tasks",
    "captures", "decision_log", "commitments", "calendar_events", "emails",
    "documents", "learning_items", "learning_item_logs", "reviews",
    "intelligence_items", "claude_outputs", "actions", "audit_log",
]

# SQLite has no real boolean type - these columns come back from sqlite3 as
# plain int (0/1), but Postgres's actual BOOLEAN columns reject int outright
# (no implicit cast). Convert on the way across.
BOOLEAN_COLUMNS = {
    "domains": {"active"},
    "daily_habits": {"completed"},
    "emails": {"action_required", "processed"},
    "claude_outputs": {"reviewed"},
    "actions": {"approval_required"},
    "audit_log": {"approval_required", "approval_given"},
}


def main() -> None:
    database_url = _database_url()
    if not database_url:
        print("DATABASE_URL is not set in your environment/.env - nothing to do.")
        sys.exit(1)

    if not DB_PATH.exists():
        print(f"No local SQLite database found at {DB_PATH} - nothing to copy.")
        sys.exit(1)

    connect_args = {}
    if POSTGRES_CA_CERT_PATH.exists():
        connect_args = {"sslmode": "verify-full", "sslrootcert": str(POSTGRES_CA_CERT_PATH)}
    pg_engine = create_engine(database_url, connect_args=connect_args)

    with pg_engine.begin() as pg_conn:
        existing = pg_conn.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'domains'"
            )
        ).fetchone()
        if existing is None:
            print("Applying schema.sql to Postgres...")
            schema_sql = POSTGRES_SCHEMA_PATH.read_text(encoding="utf-8")
            # Strip full-line comments before splitting on ";" - a statement
            # left with only a comment (no actual SQL) is sent to Postgres
            # as an empty query otherwise, which psycopg2 rejects outright.
            lines = [
                line for line in schema_sql.splitlines()
                if not line.strip().startswith("--")
            ]
            cleaned_sql = "\n".join(lines)
            for statement in cleaned_sql.split(";"):
                statement = statement.strip()
                if statement:
                    pg_conn.execute(text(statement))
            print("Schema applied.")
        else:
            print("Schema already present on Postgres - skipping schema creation.")

    sqlite_conn = get_sqlite_connection(DB_PATH)
    try:
        total_rows = 0
        with pg_engine.begin() as pg_conn:
            for table in TABLE_ORDER:
                rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
                if not rows:
                    continue
                columns = rows[0].keys()
                col_list = ", ".join(columns)
                placeholders = ", ".join(f":{c}" for c in columns)
                insert_sql = text(
                    f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                    f"ON CONFLICT DO NOTHING"
                )
                bool_cols = BOOLEAN_COLUMNS.get(table, set())
                for row in rows:
                    row_dict = dict(row)
                    for col in bool_cols:
                        if row_dict.get(col) is not None:
                            row_dict[col] = bool(row_dict[col])
                    pg_conn.execute(insert_sql, row_dict)
                print(f"  {table}: copied {len(rows)} row(s)")
                total_rows += len(rows)
        print(f"Done. Copied {total_rows} total row(s) from {DB_PATH} to Postgres.")
    finally:
        sqlite_conn.close()


if __name__ == "__main__":
    main()
