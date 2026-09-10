"""PEOS - Reviews (spec Section 27, Page 9).

The cloud routine reviews (daily/weekly brief) can't persist here yet (see
docs/decision_log.md), but weekly progress against goal logs is entirely
local data - computed for real, not a placeholder.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import domain_icon, icon_md, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402
from engine.reviews.weekly_progress import ProgressCategory, classify_goal  # noqa: E402

init_db()

page_header("fact_check", "Reviews")

st.subheader("This Week's Progress")
st.caption(
    "Evidence-based, not a fabricated benchmark: a goal is \"struggling\" because "
    "it went quiet (no log entry in the last 7 days) or was explicitly marked "
    "at risk — not because it missed some percent-per-week target no one set."
)

window_start = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

conn = get_connection()
try:
    goals = conn.execute(
        "SELECT g.*, d.name AS domain_name, d.id AS domain_id FROM goals g "
        "JOIN domains d ON g.domain_id = d.id"
    ).fetchall()
    recent_log_goal_ids = {
        row["goal_id"]
        for row in conn.execute(
            "SELECT DISTINCT goal_id FROM goal_logs WHERE created_at >= :start",
            {"start": window_start},
        ).fetchall()
    }
finally:
    conn.close()

buckets: dict[ProgressCategory, list] = {c: [] for c in ProgressCategory}
for g in goals:
    category = classify_goal(g["status"], g["id"] in recent_log_goal_ids)
    buckets[category].append(g)

SECTION_META = {
    ProgressCategory.ON_TRACK: ("Going Fine", "check_circle", "#15803D"),
    ProgressCategory.STRUGGLING: ("Struggling", "warning", "#B91C1C"),
    ProgressCategory.REMAINING: ("Left To Start", "hourglass_empty", "#B45309"),
    ProgressCategory.COMPLETED: ("Completed", "celebration", "#4F46E5"),
    ProgressCategory.ABANDONED: ("Abandoned", "delete", "#64748B"),
}

cols = st.columns(len(SECTION_META))
for col, (category, (label, icon, color)) in zip(cols, SECTION_META.items()):
    col.markdown(f'<span style="color:{color}; font-weight:600;">{icon_md(icon)} {label}</span>', unsafe_allow_html=True)
    col.metric("", len(buckets[category]))

st.divider()

for category, (label, icon, color) in SECTION_META.items():
    items = buckets[category]
    if not items:
        continue
    st.markdown(f'### <span style="color:{color};">{icon_md(icon)} {label}</span>', unsafe_allow_html=True)
    for g in items:
        d_icon = domain_icon(g["domain_id"])
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{icon_md(d_icon)} {g['name']}**  \n:gray[{g['domain_name']}]")
            c2.markdown(f"{int(g['progress'] or 0)}%")
    st.write("")

st.divider()
st.subheader("Daily / Weekly / Monthly / Quarterly briefs")

conn = get_connection()
try:
    reviews = conn.execute(
        "SELECT * FROM reviews ORDER BY review_date DESC LIMIT 50"
    ).fetchall()
finally:
    conn.close()

if not reviews:
    st.info(
        "No cloud-routine reviews stored here yet. The daily 4 AM brief and "
        "weekly review email run in claude.ai's cloud sandbox and deliver "
        "their output as a message/email — they don't have access to this "
        "local database, so nothing from them shows up here. The weekly "
        "progress view above is fully local and doesn't have that gap."
    )
else:
    for r in reviews:
        with st.container(border=True):
            st.markdown(f"**{r['review_type'].title()} review — {r['review_date']}**")
            if r["summary"]:
                st.write(r["summary"])

st.divider()
st.subheader("Decision Log")
st.caption(
    "Why a goal was prioritised, deferred, stopped, started, or changed - "
    "your own strategic reasoning (spec Section 35), so future reviews can "
    "see the reasoning, not just the outcome."
)

conn = get_connection()
try:
    all_goals = conn.execute("SELECT id, name FROM goals ORDER BY name").fetchall()
    decisions = conn.execute("SELECT * FROM decision_log ORDER BY created_at DESC").fetchall()
finally:
    conn.close()

DECISION_TYPES = ["prioritised", "deferred", "stopped", "started", "changed", "other"]
goal_options = {g["name"]: g["id"] for g in all_goals}

with st.expander("Log a decision", icon=":material/add:"):
    with st.form("add_decision", clear_on_submit=True):
        decision_type = st.selectbox("Type", DECISION_TYPES)
        goal_name = st.selectbox("Related goal (optional)", ["(none)"] + list(goal_options.keys()))
        description = st.text_input("What was decided")
        rationale = st.text_area("Why")
        if st.form_submit_button("Log decision", type="primary") and description.strip():
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO decision_log (id, decision_type, goal_id, description, rationale) "
                    "VALUES (:id, :type, :goal_id, :desc, :rationale)",
                    {
                        "id": f"decision-{uuid.uuid4().hex[:8]}",
                        "type": decision_type,
                        "goal_id": goal_options.get(goal_name),
                        "desc": description.strip(),
                        "rationale": rationale.strip() or None,
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()

if not decisions:
    st.info("No decisions logged yet.")
else:
    goal_name_by_id = {g["id"]: g["name"] for g in all_goals}
    for dec in decisions:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{dec['description']}**")
            c2.markdown(f":gray[{dec['decision_type']}]")
            if dec["goal_id"] and dec["goal_id"] in goal_name_by_id:
                st.caption(f"Goal: {goal_name_by_id[dec['goal_id']]}")
            if dec["rationale"]:
                st.write(dec["rationale"])
            st.caption(dec["created_at"])
