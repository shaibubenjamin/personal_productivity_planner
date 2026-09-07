"""PEOS - Page 9: Reviews (spec Section 27, Page 9).

The "cloud routine" reviews (daily/weekly brief) can't persist here yet (see
docs/decision_log.md), but weekly progress against goal logs is entirely
local data - computed for real, not a placeholder.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import domain_icon, inject_css, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402
from engine.reviews.weekly_progress import ProgressCategory, classify_goal  # noqa: E402

st.set_page_config(page_title="PEOS - Reviews", page_icon="📝", layout="wide")
inject_css()
init_db()

page_header("📝", "Reviews")

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
    ProgressCategory.ON_TRACK: ("✅ Going Fine", "#15803D"),
    ProgressCategory.STRUGGLING: ("⚠️ Struggling", "#B91C1C"),
    ProgressCategory.REMAINING: ("⏳ Left To Start", "#B45309"),
    ProgressCategory.COMPLETED: ("🎉 Completed", "#4F46E5"),
    ProgressCategory.ABANDONED: ("🗑️ Abandoned", "#64748B"),
}

cols = st.columns(len(SECTION_META))
for col, (category, (label, color)) in zip(cols, SECTION_META.items()):
    col.markdown(f'<span style="color:{color}; font-weight:600;">{label}</span>', unsafe_allow_html=True)
    col.metric("", len(buckets[category]))

st.divider()

for category, (label, color) in SECTION_META.items():
    items = buckets[category]
    if not items:
        continue
    st.markdown(f'### <span style="color:{color};">{label}</span>', unsafe_allow_html=True)
    for g in items:
        icon = domain_icon(g["domain_id"])
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{icon} {g['name']}**  \n:gray[{g['domain_name']}]")
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
