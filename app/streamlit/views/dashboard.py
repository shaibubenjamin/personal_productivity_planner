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
from engine.common.dates import to_date  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402
from engine.goals.schedule_status import ScheduleStatus, assess_schedule  # noqa: E402

init_db()
page_header("dashboard", "Executive Dashboard", "Productivity Tracker — V1, Phase 1/4")

# At-a-glance: aggregate on-course/behind counts across every goal, computed
# from the same engine that drives each goal's own badge - an executive
# dashboard should lead with this, not raw table-row counts.
conn = get_connection()
try:
    goals = conn.execute("SELECT id FROM goals").fetchall()
    tasks_by_goal: dict[str, list] = {}
    for t in conn.execute("SELECT goal_id, status, deadline FROM tasks").fetchall():
        tasks_by_goal.setdefault(t["goal_id"], []).append(t)
finally:
    conn.close()

status_counts = {s: 0 for s in ScheduleStatus}
for g in goals:
    status, _ = assess_schedule(tasks_by_goal.get(g["id"], []))
    status_counts[status] += 1

m1, m2, m3, m4 = st.columns(4)
m1.metric(":material/flag: Goals tracked", len(goals))
m2.metric(":material/check_circle: On course", status_counts[ScheduleStatus.ON_COURSE])
m3.metric(":material/schedule: Falling behind", status_counts[ScheduleStatus.BEHIND])
open_ended = status_counts[ScheduleStatus.NO_DEADLINES] + status_counts[ScheduleStatus.NO_TASKS]
m4.metric(":material/event_busy: Open-ended", open_ended)

st.divider()

render_quick_capture()
render_capture_inbox()

with st.container(border=True):
    render_daily_habit("french_ai_tutor", "Spoke to my French AI tutor today")

st.markdown(f"### {icon_md('today')} Today")
st.caption("Every overdue or due-today deliverable, across every goal, in one place.")

conn = get_connection()
try:
    due_items = conn.execute(
        """
        SELECT t.title, t.deadline, g.name AS goal_name, d.id AS domain_id, d.name AS domain_name
        FROM tasks t
        JOIN goals g ON t.goal_id = g.id
        JOIN domains d ON t.domain_id = d.id
        WHERE t.status != 'done' AND t.deadline IS NOT NULL AND t.deadline <= :today
        ORDER BY t.deadline
        """,
        {"today": date.today().isoformat()},
    ).fetchall()
finally:
    conn.close()

if not due_items:
    st.success("Nothing overdue or due today - clear.")
else:
    today_date = date.today()
    for item in due_items:
        overdue = to_date(item["deadline"]) < today_date
        icon = domain_icon(item["domain_id"])
        tag = "OVERDUE" if overdue else "DUE TODAY"
        text_color, bg_color = ("#B91C1C", "#FEF2F2") if overdue else ("#B45309", "#FFFBEB")
        st.markdown(
            f'<div style="border-left: 4px solid {text_color}; background:{bg_color}; '
            f'border-radius: 0.5rem; padding: 0.7rem 1rem; margin-bottom: 0.5rem; '
            f'display:flex; align-items:center; justify-content:space-between;">'
            f'<div>{icon_md(icon)} <b>{item["title"]}</b>'
            f'<div style="color:#64748B; font-size:0.85rem;">{item["goal_name"]} · {item["domain_name"]}</div></div>'
            f'<span style="color:{text_color}; font-weight:700; font-size:0.78rem; '
            f'white-space:nowrap; margin-left:1rem;">{tag}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

st.divider()

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT * FROM domains WHERE active = TRUE ORDER BY strategic_weight DESC NULLS LAST, name"
    ).fetchall()
finally:
    conn.close()

if not goals:
    st.info(
        "No goals entered yet. This dashboard fills in as config/goals.yaml is "
        "populated and the priority/balance engines have real data to score."
    )

st.markdown(f"### {icon_md('dashboard_customize')} Life Domains")
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
