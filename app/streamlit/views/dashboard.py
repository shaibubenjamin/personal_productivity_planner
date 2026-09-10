"""PEOS - Executive Dashboard (spec Section 27, Page 1).

Each domain card links straight into that domain's to-do/status view
(Domain page) instead of every domain needing its own sidebar tab.
"""

import sys
from datetime import date
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.daily_habit import render_daily_habit  # noqa: E402
from app.components.domain_card import render_domain_card  # noqa: E402
from app.components.quick_capture import render_capture_inbox, render_quick_capture  # noqa: E402
from app.components.style import domain_icon, icon_md, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()
page_header("dashboard", "Executive Dashboard", "Productivity Tracker — V1, Phase 1/4")

render_quick_capture()
render_capture_inbox()

with st.container(border=True):
    render_daily_habit("french_ai_tutor", "Spoke to my French AI tutor today")

st.subheader("Today")
st.caption("Every overdue or due-today deliverable, across every goal, in one place.")

conn = get_connection()
try:
    due_items = conn.execute(
        """
        SELECT t.title, t.deadline, g.name AS goal_name, d.id AS domain_id, d.name AS domain_name
        FROM tasks t
        JOIN goals g ON t.goal_id = g.id
        JOIN domains d ON t.domain_id = d.id
        WHERE t.status != 'done' AND t.deadline IS NOT NULL AND t.deadline <= date('now')
        ORDER BY t.deadline
        """
    ).fetchall()
finally:
    conn.close()

if not due_items:
    st.success("Nothing overdue or due today - clear.")
else:
    today_str = date.today().isoformat()
    for item in due_items:
        overdue = item["deadline"] < today_str
        icon = domain_icon(item["domain_id"])
        tag = "OVERDUE" if overdue else "DUE TODAY"
        color = "#B91C1C" if overdue else "#B45309"
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"{icon_md(icon)} **{item['title']}**  \n:gray[{item['goal_name']} · {item['domain_name']}]")
            c2.markdown(f'<span style="color:{color}; font-weight:600;">{tag}</span>', unsafe_allow_html=True)

st.divider()

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
