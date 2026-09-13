"""Date-value normalization across backends.

SQLite has no native DATE type - it stores/returns DATE columns as plain
TEXT strings, so `date.fromisoformat(row["deadline"])` always worked.
Postgres has a real DATE type, and psycopg2 returns it as an actual
`datetime.date` object already - calling `date.fromisoformat()` on that
raises TypeError (it requires a str). Every call site that reads a
DATE/TEXT deadline column needs to go through this instead of
`date.fromisoformat()` directly, so it works against either backend.
"""

from datetime import date


def to_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
