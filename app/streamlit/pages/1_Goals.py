"""PEOS - Page 3: Goals (spec Section 27, Page 3)."""

import sys
import uuid
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Goals", layout="wide")
init_db()

st.title("Goals")

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT id, name FROM domains WHERE active = 1 ORDER BY name"
    ).fetchall()
finally:
    conn.close()

domain_options = {d["name"]: d["id"] for d in domains}

with st.expander("Add a goal", expanded=False):
    with st.form("add_goal"):
        name = st.text_input("Goal name")
        domain_name = st.selectbox("Domain", list(domain_options.keys()) or ["(no domains configured)"])
        why = st.text_area("Why it matters")
        strategic_importance = st.slider("Strategic importance", 0, 10, 5)
        deadline = st.date_input("Target date", value=None)
        submitted = st.form_submit_button("Add goal")

        if submitted:
            if not name or not domain_options:
                st.error("Goal name and at least one configured domain are required.")
            else:
                conn = get_connection()
                try:
                    conn.execute(
                        """
                        INSERT INTO goals (id, domain_id, name, why_it_matters,
                                           strategic_importance, deadline, status, progress, confidence)
                        VALUES (:id, :domain_id, :name, :why, :importance, :deadline, 'not_started', 0, 'LOW')
                        """,
                        {
                            "id": f"goal-{uuid.uuid4().hex[:8]}",
                            "domain_id": domain_options[domain_name],
                            "name": name,
                            "why": why,
                            "importance": strategic_importance,
                            "deadline": deadline.isoformat() if deadline else None,
                        },
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.success(f"Added goal: {name}")
                st.rerun()

st.divider()

conn = get_connection()
try:
    goals = conn.execute(
        """
        SELECT g.*, d.name AS domain_name
        FROM goals g JOIN domains d ON g.domain_id = d.id
        ORDER BY g.strategic_importance DESC NULLS LAST, g.created_at DESC
        """
    ).fetchall()
finally:
    conn.close()

if not goals:
    st.info("No goals yet — add one above.")
else:
    for g in goals:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{g['name']}**  \n_{g['domain_name']}_")
            c2.markdown(f"Status: `{g['status']}`")
            if g["why_it_matters"]:
                st.caption(g["why_it_matters"])
            st.progress(min(max(int(g["progress"] or 0), 0), 100) / 100)
