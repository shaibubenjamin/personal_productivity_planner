"""PEOS - Global Intelligence (spec Section 27, Page 10).

Split into Global Politics / Global Opportunities / Other (owner request,
2026-09-08). The daily 4 AM cloud routine already gathers this via WebSearch
(see the PEOS 4 AM Executive Brief routine), but it can't write back to this
local database yet (same cloud-sandbox-has-no-DB-access gap noted elsewhere
in docs/decision_log.md) - so for now, items land here either by you adding
them from what the brief surfaced, or once the Drive-folder bridge (also
being set up) is read into this DB. Ticking/logging/acting on an item works
fully today regardless of how it got here.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.google_links import calendar_quick_add_url, gmail_compose_url  # noqa: E402
from app.components.style import icon_md, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()

page_header("public", "Global Intelligence")

CATEGORY_META = {
    "politics": ("Global Politics", "gavel"),
    "opportunity": ("Global Opportunities", "rocket_launch"),
    "other": ("Other Beneficial Items", "lightbulb"),
}
STATUS_LABEL = {"new": "New", "reviewed": "Reviewed", "actioned": "Actioned"}


def _render_item(item) -> None:
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        item_icon = CATEGORY_META.get(item["category"], (None, "lightbulb"))[1]
        c1.markdown(f"**{icon_md(item_icon)} {item['title']}**")
        if item["url"]:
            c1.caption(item["url"])
        c1.caption(f"{item['topic'] or ''} · relevance {item['relevance'] if item['relevance'] is not None else '—'}")

        reviewed = c2.checkbox(
            "Reviewed", value=(item["status"] in ("reviewed", "actioned")), key=f"intel_reviewed_{item['id']}"
        )
        new_status = "reviewed" if reviewed and item["status"] == "new" else item["status"]

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            with st.popover("Set reminder", icon=":material/event:"):
                tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
                    hour=9, minute=0, second=0, microsecond=0
                )
                url = calendar_quick_add_url(
                    title=f"Follow up: {item['title']}", start=tomorrow, end=tomorrow + timedelta(minutes=30),
                    details=item["url"] or "",
                )
                st.link_button("Open Google Calendar (prefilled)", url)
        with col_b:
            with st.popover("Draft email", icon=":material/mail:"):
                url = gmail_compose_url(subject=f"Re: {item['title']}", body=item["url"] or "")
                st.link_button("Open Gmail (prefilled)", url)
        with col_c:
            with st.popover("Log a note", icon=":material/edit_note:"):
                note = st.text_input("Note / action taken", key=f"intel_note_{item['id']}")
                if st.button("Save", key=f"intel_note_save_{item['id']}") and note.strip():
                    conn = get_connection()
                    try:
                        conn.execute(
                            "UPDATE intelligence_items SET action_taken = :note, status = 'actioned' WHERE id = :id",
                            {"note": note.strip(), "id": item["id"]},
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    st.rerun()

        if item["action_taken"]:
            st.caption(f"Action taken: {item['action_taken']}")

        if new_status != item["status"]:
            conn = get_connection()
            try:
                conn.execute(
                    "UPDATE intelligence_items SET status = :status WHERE id = :id",
                    {"status": new_status, "id": item["id"]},
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()


conn = get_connection()
try:
    items = conn.execute(
        "SELECT * FROM intelligence_items ORDER BY item_date DESC, created_at DESC"
    ).fetchall()
finally:
    conn.close()

by_category: dict[str, list] = {c: [] for c in CATEGORY_META}
for i in items:
    by_category.setdefault(i["category"], []).append(i)

new_count = sum(1 for i in items if i["status"] == "new")
reviewed_count = sum(1 for i in items if i["status"] == "reviewed")
actioned_count = sum(1 for i in items if i["status"] == "actioned")
m1, m2, m3, m4 = st.columns(4)
m1.metric(":material/inbox: Total items", len(items))
m2.metric(":material/fiber_new: New", new_count)
m3.metric(":material/visibility: Reviewed", reviewed_count)
m4.metric(":material/task_alt: Actioned", actioned_count)
st.divider()

for category, (label, icon) in CATEGORY_META.items():
    entries = by_category.get(category, [])
    st.markdown(f"### {icon_md(icon)} {label} ({len(entries)})")
    if not entries:
        st.caption("Nothing here yet.")
    for entry in entries:
        _render_item(entry)
    st.write("")

st.divider()
with st.expander("Add an item", icon=":material/add:"):
    with st.form("add_intel_item", clear_on_submit=True):
        title = st.text_input("Title")
        url = st.text_input("URL (optional)")
        category = st.selectbox("Category", list(CATEGORY_META.keys()), format_func=lambda c: CATEGORY_META[c][0])
        topic = st.text_input("Topic (optional, e.g. climate finance)")
        if st.form_submit_button("Add", type="primary") and title.strip():
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO intelligence_items (id, source, title, url, category, topic, item_date) "
                    "VALUES (:id, 'manual', :title, :url, :category, :topic, :date)",
                    {
                        "id": f"intel-{uuid.uuid4().hex[:8]}",
                        "title": title.strip(),
                        "url": url.strip() or None,
                        "category": category,
                        "topic": topic.strip() or None,
                        "date": datetime.now(timezone.utc).date().isoformat(),
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()
