"""PEOS - Page 9: Reviews (spec Section 27, Page 9)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import inject_css, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Reviews", page_icon="📝", layout="wide")
inject_css()
init_db()

page_header("📝", "Reviews")

conn = get_connection()
try:
    reviews = conn.execute(
        "SELECT * FROM reviews ORDER BY review_date DESC LIMIT 50"
    ).fetchall()
finally:
    conn.close()

if not reviews:
    st.info(
        "No reviews stored yet. The daily 4 AM routine runs in claude.ai's cloud "
        "environment and delivers the brief as a message/push notification — it "
        "doesn't have access to this local database, so nothing is persisted "
        "here yet. Wiring that up is a follow-up (needs the hosted Postgres)."
    )
else:
    for r in reviews:
        with st.container(border=True):
            st.markdown(f"**{r['review_type'].title()} review — {r['review_date']}**")
            if r["summary"]:
                st.write(r["summary"])
