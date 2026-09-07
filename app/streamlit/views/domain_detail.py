"""Domain drill-down - one page for all 8 domains, reached by clicking a
card's "View" link on the Executive Dashboard or Life Balance page, rather
than each domain having its own near-duplicate page file (owner feedback,
2026-09-07: numerous near-identical tabs was cluttered UX).
"""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.goal_card import render_goal_card  # noqa: E402
from app.components.style import domain_icon, icon_md, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()

domain_id = st.query_params.get("domain")

conn = get_connection()
try:
    domains = {d["id"]: d for d in conn.execute("SELECT * FROM domains").fetchall()}
finally:
    conn.close()

if not domain_id or domain_id not in domains:
    # Structural guard, not just st.stop() - st.stop() only halts execution
    # inside Streamlit's own script runner; outside it (e.g. a bare `python
    # domain_detail.py` smoke test) it's a no-op, and code after it would
    # still run and crash on domains[None]. Real bug caught this way once.
    st.warning("No domain selected - go back to the Executive Dashboard and click into a domain from there.")
    st.page_link("views/dashboard.py", label="Back to Executive Dashboard", icon=":material/arrow_back:")
else:
    d = domains[domain_id]
    icon = domain_icon(domain_id)
    st.page_link("views/dashboard.py", label="Executive Dashboard", icon=":material/arrow_back:")
    page_header(icon, d["name"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Strategic weight", f"{d['strategic_weight']:.0f}%" if d["strategic_weight"] is not None else "-")
    c2.metric("Min. attention", f"{d['minimum_attention_pct']:.0f}%" if d["minimum_attention_pct"] is not None else "-")

    conn = get_connection()
    try:
        goals = conn.execute(
            "SELECT g.*, d.name AS domain_name, d.id AS domain_id FROM goals g "
            "JOIN domains d ON g.domain_id = d.id WHERE g.domain_id = :id "
            "ORDER BY strategic_importance DESC NULLS LAST",
            {"id": domain_id},
        ).fetchall()
    finally:
        conn.close()

    c3.metric("Goals", len(goals))
    st.divider()

    if not goals:
        st.info("No goals yet for this domain. Add one from the Goals page.")
        st.page_link("views/goals.py", label="Go to Goals", icon=":material/flag:")
    else:
        for g in goals:
            render_goal_card(g, show_domain=False)
