"""PEOS - Page 3: Goals (spec Section 27, Page 3).

Status/progress editing and a log-note history live here so there's always
one place to see where a goal actually stands, not just what it was
supposed to be (owner request, 2026-09-07).
"""

import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import domain_icon, inject_css, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Goals", page_icon="🎯", layout="wide")
inject_css()
init_db()

page_header("🎯", "Goals")

STATUS_OPTIONS = ["not_started", "in_progress", "at_risk", "done", "abandoned"]
STATUS_LABEL = {
    "not_started": "Not started",
    "in_progress": "In progress",
    "at_risk": "At risk",
    "done": "Done",
    "abandoned": "Abandoned",
}

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT id, name FROM domains WHERE active = 1 ORDER BY name"
    ).fetchall()
finally:
    conn.close()

domain_options = {d["name"]: d["id"] for d in domains}

with st.expander("＋ Add a goal", expanded=False):
    with st.form("add_goal"):
        name = st.text_input("Goal name")
        domain_name = st.selectbox("Domain", list(domain_options.keys()) or ["(no domains configured)"])
        why = st.text_area("Why it matters")
        strategic_importance = st.slider("Strategic importance", 0, 10, 5)
        deadline = st.date_input("Target date", value=None)
        submitted = st.form_submit_button("Add goal", type="primary")

        if submitted:
            if not name or not domain_options:
                st.error("Goal name and at least one configured domain are required.")
            else:
                conn = get_connection()
                try:
                    conn.execute(
                        """
                        INSERT INTO goals (id, domain_id, name, why_it_matters,
                                           strategic_importance, deadline, status, progress, confidence)
                        VALUES (:id, :domain_id, :name, :why, :importance, :deadline, 'not_started', 0, 'LOW')
                        """,
                        {
                            "id": f"goal-{uuid.uuid4().hex[:8]}",
                            "domain_id": domain_options[domain_name],
                            "name": name,
                            "why": why,
                            "importance": strategic_importance,
                            "deadline": deadline.isoformat() if deadline else None,
                        },
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.success(f"Added goal: {name}")
                st.rerun()

st.divider()

conn = get_connection()
try:
    goals = conn.execute(
        """
        SELECT g.*, d.name AS domain_name, d.id AS domain_id
        FROM goals g JOIN domains d ON g.domain_id = d.id
        ORDER BY
            CASE g.status WHEN 'at_risk' THEN 0 WHEN 'in_progress' THEN 1
                          WHEN 'not_started' THEN 2 WHEN 'done' THEN 3 ELSE 4 END,
            g.strategic_importance DESC NULLS LAST
        """
    ).fetchall()
finally:
    conn.close()

if not goals:
    st.info("No goals yet — add one above.")

for g in goals:
    icon = domain_icon(g["domain_id"])
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**{icon} {g['name']}**  \n:gray[{g['domain_name']}]")
        done = c2.checkbox("Done", value=(g["status"] == "done"), key=f"done_{g['id']}")

        if g["why_it_matters"]:
            st.caption(g["why_it_matters"])

        col_status, col_progress = st.columns([1, 2])
        with col_status:
            current_status = "done" if done else g["status"]
            new_status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0,
                format_func=lambda s: STATUS_LABEL[s],
                key=f"status_{g['id']}",
                disabled=done,
            )
        with col_progress:
            new_progress = st.slider(
                "Progress %",
                0, 100,
                value=100 if done else min(max(int(g["progress"] or 0), 0), 100),
                key=f"progress_{g['id']}",
                disabled=done,
            )

        final_status = "done" if done else new_status
        final_progress = 100 if done else new_progress

        if final_status != g["status"] or final_progress != (g["progress"] or 0):
            conn = get_connection()
            try:
                conn.execute(
                    "UPDATE goals SET status = :status, progress = :progress, "
                    "updated_at = :now WHERE id = :id",
                    {
                        "status": final_status,
                        "progress": final_progress,
                        "now": datetime.now(timezone.utc).isoformat(),
                        "id": g["id"],
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()

        with st.form(f"log_form_{g['id']}", clear_on_submit=True):
            note = st.text_input("Log an update — what did you actually do?", key=f"note_input_{g['id']}")
            log_submitted = st.form_submit_button("Add log entry")
            if log_submitted and note.strip():
                conn = get_connection()
                try:
                    conn.execute(
                        """
                        INSERT INTO goal_logs (goal_id, note, status_at_time, progress_at_time)
                        VALUES (:goal_id, :note, :status, :progress)
                        """,
                        {
                            "goal_id": g["id"],
                            "note": note.strip(),
                            "status": final_status,
                            "progress": final_progress,
                        },
                    )
                    conn.execute(
                        "UPDATE goals SET last_reviewed = :now WHERE id = :id",
                        {"now": datetime.now(timezone.utc).date().isoformat(), "id": g["id"]},
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.rerun()

        conn = get_connection()
        try:
            logs = conn.execute(
                "SELECT * FROM goal_logs WHERE goal_id = :id ORDER BY created_at DESC LIMIT 20",
                {"id": g["id"]},
            ).fetchall()
        finally:
            conn.close()

        if logs:
            with st.expander(f"History ({len(logs)})"):
                for log in logs:
                    st.markdown(f"**{log['created_at']}** — {log['note']}")
