"""PEOS - Page 5: Learning (spec Section 27, Page 5)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Learning", layout="wide")
init_db()

st.title("Learning")
st.caption(
    "Full learning-management engine (knowledge/skill/application/evidence/"
    "outcome/visibility per spec Section 18) ships in V2. This page shows the "
    "raw capability plan captured so far."
)

conn = get_connection()
try:
    courses = conn.execute(
        "SELECT * FROM learning_items WHERE item_type = 'course' ORDER BY priority_rank"
    ).fetchall()
    books = conn.execute(
        "SELECT * FROM learning_items WHERE item_type = 'book' ORDER BY capability"
    ).fetchall()
finally:
    conn.close()

st.subheader(f"Career capability priorities ({len(courses)})")
for c in courses:
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**{c['priority_rank']}. {c['capability']}**")
        c2.markdown(f"`{c['priority_label']}`")
        st.caption(c["course"])
        st.progress(min(max(int(c["progress"] or 0), 0), 100) / 100)

st.divider()
st.subheader(f"Planned book purchases ({len(books)})")
cols = st.columns(3)
for i, b in enumerate(books):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"**{b['course']}**")
            st.caption(b["capability"])
