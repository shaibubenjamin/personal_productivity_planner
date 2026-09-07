import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import inject_css, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - French", page_icon="🇫🇷", layout="wide")
inject_css()
init_db()

page_header("🇫🇷", "French", "Full French coach engine ships in V2 — real goal/milestones below.")

conn = get_connection()
try:
    goal = conn.execute("SELECT * FROM goals WHERE domain_id = 'french'").fetchone()
finally:
    conn.close()

if goal:
    with st.container(border=True):
        st.markdown(f"**{goal['name']}**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Baseline", goal["baseline"] or "—")
        c2.metric("Target", goal["target"] or "—")
        c3.metric("Target date", goal["deadline"] or "—")
        if goal["description"]:
            st.caption(goal["description"])
        if goal["next_action"]:
            st.markdown(f"**Milestones / next action:** {goal['next_action']}")
else:
    st.info("No French goal in the database yet — check config/goals.yaml.")
