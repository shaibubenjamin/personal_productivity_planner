"""PEOS - Executive Dashboard (spec Section 27, Page 1).

Each domain card links straight into that domain's to-do/status view
(Domain page) instead of every domain needing its own sidebar tab.
"""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.domain_card import render_domain_card  # noqa: E402
from app.components.style import page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()
page_header("dashboard", "Executive Dashboard", "Personal Executive Operating System — V1, Phase 1/4")

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT * FROM domains WHERE active = 1 ORDER BY strategic_weight DESC NULLS LAST, name"
    ).fetchall()
    goal_count = conn.execute("SELECT COUNT(*) AS n FROM goals").fetchone()["n"]
finally:
    conn.close()

col1, col2, col3 = st.columns(3)
col1.metric("Active domains", len(domains))
col2.metric("Goals tracked", goal_count)
col3.metric("Automation category", "A · read-only")

st.divider()

if goal_count == 0:
    st.info(
        "No goals entered yet. This dashboard fills in as config/goals.yaml is "
        "populated and the priority/balance engines have real data to score."
    )

st.subheader("Life Domains")
st.caption("Click into any domain to see its goals, to-dos, and log history.")

if not domains:
    st.warning("No domains configured — check config/life_domains.yaml.")
else:
    cols = st.columns(2)
    for i, d in enumerate(domains):
        with cols[i % 2]:
            render_domain_card(d)

st.divider()
st.caption(
    "Balance flags (OVER/UNDER/HEALTHY per domain) need real calendar-hours "
    "attention data, which isn't wired up here yet — see the Life Balance "
    "page for the engine's output on illustrative placeholder data."
)
