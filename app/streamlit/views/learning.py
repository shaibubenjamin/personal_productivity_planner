"""PEOS - Learning (spec Section 27, Page 5).

Tick items done, add new ones, log notes, and block a calendar focus-review
slot per item (owner request, 2026-09-08). Calendar blocking uses a Google
Calendar "quick add" link (no OAuth needed) rather than a fake button - see
app/components/google_links.py for why.
"""

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.google_links import calendar_quick_add_url  # noqa: E402
from app.components.style import icon_md, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()

page_header(
    "school",
    "Learning",
    "Full learning-management engine (knowledge/skill/application/evidence/outcome/"
    "visibility per spec Section 18) ships in V2 — this is the real capability plan, trackable now.",
)

PRIORITY_COLOR = {"Critical": "#B91C1C", "Very High": "#B45309"}


def _render_item(item) -> None:
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        title = item["course"] if item["item_type"] == "book" else item["capability"]
        item_icon = "menu_book" if item["item_type"] == "book" else "school"
        c1.markdown(f"**{icon_md(item_icon)} {title}**")
        if item["item_type"] == "course":
            c1.caption(item["course"])
        else:
            c1.caption(item["capability"])
        done = c2.checkbox("Done", value=(item["status"] == "done"), key=f"litem_done_{item['id']}")

        if item["priority_label"]:
            color = PRIORITY_COLOR.get(item["priority_label"], "#334155")
            st.markdown(
                f'<span style="color:{color}; font-weight:600;">{item["priority_label"]}</span>',
                unsafe_allow_html=True,
            )

        new_status = "done" if done else ("in_progress" if item["status"] != "not_started" else "not_started")
        if new_status != item["status"]:
            now = datetime.now(timezone.utc).isoformat()
            conn = get_connection()
            try:
                conn.execute(
                    "UPDATE learning_items SET status = :status, "
                    "completed_at = CASE WHEN :status = 'done' THEN :now ELSE NULL END, "
                    "updated_at = :now WHERE id = :id",
                    {"status": new_status, "now": now, "id": item["id"]},
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()

        col_a, col_b = st.columns(2)
        with col_a:
            with st.popover("Block focus review", icon=":material/event:"):
                tomorrow_9am = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
                    hour=9, minute=0, second=0, microsecond=0
                )
                url = calendar_quick_add_url(
                    title=f"Focus review: {title}",
                    start=tomorrow_9am,
                    end=tomorrow_9am + timedelta(hours=1),
                    details=f"PEOS learning focus block for: {title}",
                )
                st.link_button("Open Google Calendar (prefilled)", url)
                st.caption("Opens Calendar with the event prefilled — confirm there to actually add it.")

        with col_b:
            with st.popover("Log a note", icon=":material/edit_note:"):
                note = st.text_input("What did you do / learn?", key=f"litem_note_{item['id']}")
                if st.button("Save", key=f"litem_note_save_{item['id']}") and note.strip():
                    conn = get_connection()
                    try:
                        conn.execute(
                            "INSERT INTO learning_item_logs (learning_item_id, note) VALUES (:id, :note)",
                            {"id": item["id"], "note": note.strip()},
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    st.rerun()

        conn = get_connection()
        try:
            logs = conn.execute(
                "SELECT * FROM learning_item_logs WHERE learning_item_id = :id ORDER BY created_at DESC",
                {"id": item["id"]},
            ).fetchall()
        finally:
            conn.close()
        if logs:
            with st.expander(f"History ({len(logs)})"):
                for log in logs:
                    st.markdown(f"**{log['created_at']}** - {log['note']}")


conn = get_connection()
try:
    courses = conn.execute(
        "SELECT * FROM learning_items WHERE item_type = 'course' ORDER BY priority_rank"
    ).fetchall()
    books = conn.execute(
        "SELECT * FROM learning_items WHERE item_type = 'book' ORDER BY capability"
    ).fetchall()
finally:
    conn.close()

st.markdown(f"### {icon_md('work')} Career capability priorities ({sum(1 for c in courses if c['status'] == 'done')}/{len(courses)} done)")
for c in courses:
    _render_item(c)

st.divider()
st.markdown(f"### {icon_md('menu_book')} Planned book purchases ({sum(1 for b in books if b['status'] == 'done')}/{len(books)} done)")
for b in books:
    _render_item(b)

st.divider()
with st.expander("Add a learning item", icon=":material/add:"):
    conn = get_connection()
    try:
        domains = conn.execute("SELECT id, name FROM domains WHERE active = TRUE ORDER BY name").fetchall()
    finally:
        conn.close()
    domain_options = {d["name"]: d["id"] for d in domains}

    with st.form("add_learning_item", clear_on_submit=True):
        item_type = st.radio("Type", ["course", "book"], horizontal=True)
        capability = st.text_input("Capability")
        course = st.text_input("Course / book title")
        domain_name = st.selectbox("Domain", list(domain_options.keys()))
        if st.form_submit_button("Add", type="primary") and capability.strip():
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO learning_items (id, domain_id, capability, course, item_type, status) "
                    "VALUES (:id, :domain_id, :capability, :course, :item_type, 'not_started')",
                    {
                        "id": f"{item_type}-{uuid.uuid4().hex[:8]}",
                        "domain_id": domain_options[domain_name],
                        "capability": capability.strip(),
                        "course": course.strip(),
                        "item_type": item_type,
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()
