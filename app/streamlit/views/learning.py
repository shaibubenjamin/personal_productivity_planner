"""PEOS - Learning (spec Section 27, Page 5).

Every course/book is a real goal with its own dated task, not a
standalone item floating with no timeline (owner request, 2026-09-14:
"books to read are not standalone... every single action should align
with a goal... goal subdivided into task with timeline"). Grouped by
domain here, same as everywhere else in the app - rendered via the same
goal-card component used on the Goals/Domain pages, so ticking, logging,
adjusting deadlines, and deleting all just work identically.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.goal_card import render_goal_card  # noqa: E402
from app.components.google_links import calendar_quick_add_url  # noqa: E402
from app.components.style import icon_md, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402
from engine.goals.schedule_status import ScheduleStatus, assess_schedule  # noqa: E402

init_db()

page_header(
    "school",
    "Learning",
    "Every capability course and book is its own goal with a deadline, grouped by "
    "the life domain it actually serves - nothing here floats independent of a goal.",
)

conn = get_connection()
try:
    goals = conn.execute(
        "SELECT g.*, d.name AS domain_name, d.id AS domain_id FROM goals g "
        "JOIN domains d ON g.domain_id = d.id WHERE g.id LIKE 'goal-learning-%' "
        "ORDER BY d.name, g.deadline"
    ).fetchall()
    tasks_by_goal: dict[str, list] = {}
    for t in conn.execute("SELECT goal_id, status, deadline FROM tasks").fetchall():
        tasks_by_goal.setdefault(t["goal_id"], []).append(t)
finally:
    conn.close()

if not goals:
    st.info("No learning goals yet - add courses/books to config/learning_items.yaml and reseed.")
else:
    on_course = sum(
        1 for g in goals if assess_schedule(tasks_by_goal.get(g["id"], []))[0] == ScheduleStatus.ON_COURSE
    )
    done = sum(1 for g in goals if g["status"] == "done")
    m1, m2, m3 = st.columns(3)
    m1.metric(f"{icon_md('school')} Total learning goals", len(goals))
    m2.metric(f"{icon_md('check_circle')} On course", on_course)
    m3.metric(f"{icon_md('task_alt')} Done", done)
    st.divider()

    by_domain: dict[str, list] = {}
    for g in goals:
        by_domain.setdefault(g["domain_name"], []).append(g)

    for domain_name, domain_goals in by_domain.items():
        domain_done = sum(1 for g in domain_goals if g["status"] == "done")
        st.markdown(f"### {domain_name} ({domain_done}/{len(domain_goals)} done)")
        for g in domain_goals:
            render_goal_card(g, show_domain=False)
            with st.popover("Block a focus-review slot on my calendar", icon=":material/event:"):
                tomorrow_9am = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
                    hour=9, minute=0, second=0, microsecond=0
                )
                url = calendar_quick_add_url(
                    title=f"Focus review: {g['name']}",
                    start=tomorrow_9am,
                    end=tomorrow_9am + timedelta(hours=1),
                    details=f"PEOS learning focus block for: {g['name']}",
                )
                st.link_button("Open Google Calendar (prefilled)", url)
                st.caption("Opens Calendar with the event prefilled — confirm there to actually add it.")
        st.divider()
