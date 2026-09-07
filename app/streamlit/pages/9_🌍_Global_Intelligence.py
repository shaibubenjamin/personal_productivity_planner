"""PEOS - Page 10: Global Intelligence (spec Section 27, Page 10)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import inject_css, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Global Intelligence", page_icon="🌍", layout="wide")
inject_css()
init_db()

page_header("🌍", "Global Intelligence")

conn = get_connection()
try:
    items = conn.execute(
        "SELECT * FROM intelligence_items ORDER BY item_date DESC LIMIT 50"
    ).fetchall()
finally:
    conn.close()

if not items:
    st.info(
        "No intelligence items stored yet — same gap as Reviews: the daily "
        "routine's findings are delivered as part of the brief message, not "
        "yet written back to this database."
    )
else:
    for i in items:
        with st.container(border=True):
            st.markdown(f"**{i['title']}**")
            st.caption(f"{i['topic'] or ''} · relevance {i['relevance']}")
