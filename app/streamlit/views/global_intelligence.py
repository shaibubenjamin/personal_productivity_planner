"""PEOS - Global Opportunities.

A structured drop box for anything found online worth acting on -
conferences, fellowships, jobs, calls for proposals - paste a link, a
short description, and an end date (deadline/event date), then act on
it: add a calendar reminder (Google Calendar's own notification settings
handle the actual email/push reminder - this app has no scheduler of its
own), draft an email, or log a note once you've reviewed it.

Owner request 2026-09-15: simplified from three categories (politics/
opportunities/other) down to just opportunities - this is the one that
gets used, and it's a structured capture tool now, not a triage inbox.
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
from engine.common.dates import to_date  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()

page_header(
    "rocket_launch", "Global Opportunities",
    "Drop anything worth acting on here - a conference, fellowship, job, or call "
    "for proposals - with a link, a short description, and an end date.",
)

STATUS_LABEL = {"new": "New", "reviewed": "Reviewed", "actioned": "Actioned"}


def _render_item(item) -> None:
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**{icon_md('rocket_launch')} {item['title']}**")
        if item["url"]:
            c1.caption(item["url"])
        if item["topic"]:
            c1.write(item["topic"])
        end_date = to_date(item["item_date"])
        if end_date:
            overdue = end_date < datetime.now(timezone.utc).date()
            c1.caption(f"{'⚠ Ended' if overdue else 'Ends'}: {end_date.isoformat()}")

        reviewed = c2.checkbox(
            "Reviewed", value=(item["status"] in ("reviewed", "actioned")), key=f"intel_reviewed_{item['id']}"
        )
        new_status = "reviewed" if reviewed and item["status"] == "new" else item["status"]

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            with st.popover("Set reminder", icon=":material/event:"):
                st.caption(
                    "Adds a Calendar event on the end date (or tomorrow, if no end "
                    "date was set) - Calendar's own notification settings handle the "
                    "actual email/push reminder."
                )
                default_dt = (
                    datetime.combine(end_date, datetime.min.time()).replace(hour=9, tzinfo=timezone.utc)
                    if end_date else
                    (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
                )
                url = calendar_quick_add_url(
                    title=f"Deadline: {item['title']}", start=default_dt, end=default_dt + timedelta(minutes=30),
                    details=f"{item['topic'] or ''}\n{item['url'] or ''}".strip(),
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
        "SELECT * FROM intelligence_items ORDER BY "
        "CASE WHEN item_date IS NULL THEN 1 ELSE 0 END, item_date, created_at DESC"
    ).fetchall()
finally:
    conn.close()

new_count = sum(1 for i in items if i["status"] == "new")
reviewed_count = sum(1 for i in items if i["status"] == "reviewed")
actioned_count = sum(1 for i in items if i["status"] == "actioned")
m1, m2, m3, m4 = st.columns(4)
m1.metric(":material/inbox: Total items", len(items))
m2.metric(":material/fiber_new: New", new_count)
m3.metric(":material/visibility: Reviewed", reviewed_count)
m4.metric(":material/task_alt: Actioned", actioned_count)
st.divider()

if not items:
    st.info("Nothing dropped in yet - add one below.")
for item in items:
    _render_item(item)

st.divider()
with st.expander("Add an opportunity", icon=":material/add:", expanded=not items):
    with st.form("add_intel_item", clear_on_submit=True):
        title = st.text_input("Title", placeholder="e.g. CSEA Africa Data Future Fellowship")
        url = st.text_input("Link")
        description = st.text_area("Short description", placeholder="What is it, and why does it matter?")
        end_date = st.date_input("End date (deadline or event date)", value=None)
        if st.form_submit_button("Add", type="primary") and title.strip():
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO intelligence_items (id, source, title, url, category, topic, item_date) "
                    "VALUES (:id, 'manual', :title, :url, 'opportunity', :topic, :date)",
                    {
                        "id": f"intel-{uuid.uuid4().hex[:8]}",
                        "title": title.strip(),
                        "url": url.strip() or None,
                        "topic": description.strip() or None,
                        "date": end_date.isoformat() if end_date else None,
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()
