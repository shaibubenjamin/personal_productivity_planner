"""All Goals - flat cross-domain view (spec Section 27, Page 3).

For a single domain's goals, use the Domain page instead (linked from each
card on the Executive Dashboard) - this page is the "everything, prioritized"
view across domains.
"""

import sys
import uuid
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.goal_card import render_goal_card  # noqa: E402
from app.components.style import page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()
page_header("flag", "Goals")

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT id, name FROM domains WHERE active = TRUE ORDER BY name"
    ).fetchall()
finally:
    conn.close()

domain_options = {d["name"]: d["id"] for d in domains}

with st.expander("Add a goal", expanded=False, icon=":material/add:"):
    with st.form("add_goal"):
        name = st.text_input("Goal name")
        domain_name = st.selectbox("Domain", list(domain_options.keys()) or ["(no domains configured)"])
        why = st.text_area("Why it matters")
        strategic_importance = st.slider("Strategic importance", 0, 10, 5)
        deadline = st.date_input("Target date", value=None)
        submitted = st.form_submit_button("Add goal", type="primary")

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
        SELECT g.*, d.name AS domain_name, d.id AS domain_id
        FROM goals g JOIN domains d ON g.domain_id = d.id
        ORDER BY
            CASE g.status WHEN 'at_risk' THEN 0 WHEN 'in_progress' THEN 1
                          WHEN 'not_started' THEN 2 WHEN 'done' THEN 3 ELSE 4 END,
            g.strategic_importance DESC NULLS LAST
        """
    ).fetchall()
finally:
    conn.close()

if not goals:
    st.info("No goals yet - add one above.")

for g in goals:
    render_goal_card(g, show_domain=True)
