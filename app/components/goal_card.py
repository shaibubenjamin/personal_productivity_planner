"""Shared goal rendering: status/progress editing, log notes, and a to-do
checklist per goal. Used by both the flat All Goals view and the per-domain
drill-down view so the tick/note/status experience is identical everywhere
(owner request, 2026-09-07: "this applies to every area of life").
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import streamlit as st

from app.components.style import domain_icon, icon_md
from engine.common.db import get_connection
from engine.goals.schedule_status import ScheduleStatus, assess_schedule

SCHEDULE_BADGE = {
    ScheduleStatus.ON_COURSE: ("On course", "#15803D", "#DCFCE7"),
    ScheduleStatus.BEHIND: ("Falling behind", "#B91C1C", "#FEE2E2"),
    ScheduleStatus.NO_DEADLINES: ("No deadlines set", "#B45309", "#FEF3C7"),
    ScheduleStatus.NO_TASKS: ("No deliverables yet", "#64748B", "#F1F5F9"),
}

STATUS_OPTIONS = ["not_started", "in_progress", "at_risk", "done", "abandoned"]
STATUS_LABEL = {
    "not_started": "Not started",
    "in_progress": "In progress",
    "at_risk": "At risk",
    "done": "Done",
    "abandoned": "Abandoned",
}


def render_goal_card(g, show_domain: bool = True) -> None:
    icon = domain_icon(g["domain_id"])
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        label = f"### {icon_md(icon)} {g['name']}" if not show_domain else f"### {icon_md(icon)} {g['name']}"
        c1.markdown(label)
        if show_domain:
            c1.caption(g["domain_name"])
        done = c2.checkbox("Done", value=(g["status"] == "done"), key=f"done_{g['id']}")

        if g["why_it_matters"]:
            st.caption(g["why_it_matters"])
        if g["deadline"]:
            st.caption(f"Target date: {g['deadline']}")

        tasks = _load_tasks(g["id"])
        has_tasks = len(tasks) > 0

        schedule_status, _overdue = assess_schedule(tasks)
        label_text, text_color, bg_color = SCHEDULE_BADGE[schedule_status]
        st.markdown(
            f'<span style="color:{text_color}; background:{bg_color}; padding:0.15rem 0.6rem; '
            f'border-radius:999px; font-size:0.78rem; font-weight:600;">{label_text}</span>',
            unsafe_allow_html=True,
        )

        col_status, col_progress = st.columns([1, 2])
        with col_status:
            current_status = "done" if done else g["status"]
            new_status = st.selectbox(
                "Status", STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(current_status) if current_status in STATUS_OPTIONS else 0,
                format_func=lambda s: STATUS_LABEL[s],
                key=f"status_{g['id']}", disabled=done,
            )
        with col_progress:
            if has_tasks:
                computed = round(100 * sum(1 for t in tasks if t["status"] == "done") / len(tasks))
                st.progress(computed / 100, text=f"{computed}% - computed from {len(tasks)} to-do(s)")
                new_progress = computed
            else:
                new_progress = st.slider(
                    "Progress %", 0, 100,
                    value=100 if done else min(max(int(g["progress"] or 0), 0), 100),
                    key=f"progress_{g['id']}", disabled=done,
                )

        final_status = "done" if done else new_status
        final_progress = 100 if done else new_progress

        if final_status != g["status"] or final_progress != (g["progress"] or 0):
            conn = get_connection()
            try:
                conn.execute(
                    "UPDATE goals SET status = :status, progress = :progress, updated_at = :now WHERE id = :id",
                    {
                        "status": final_status, "progress": final_progress,
                        "now": datetime.now(timezone.utc).isoformat(), "id": g["id"],
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()

        _render_todos(g["id"], tasks)

        with st.form(f"log_form_{g['id']}", clear_on_submit=True):
            note = st.text_input("Log an update - what did you actually do?", key=f"note_input_{g['id']}")
            log_submitted = st.form_submit_button("Add log entry")
            if log_submitted and note.strip():
                conn = get_connection()
                try:
                    conn.execute(
                        "INSERT INTO goal_logs (goal_id, note, status_at_time, progress_at_time) "
                        "VALUES (:goal_id, :note, :status, :progress)",
                        {"goal_id": g["id"], "note": note.strip(), "status": final_status, "progress": final_progress},
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
                    st.markdown(f"**{log['created_at']}** - {log['note']}")


def _load_tasks(goal_id: str):
    conn = get_connection()
    try:
        return conn.execute(
            "SELECT * FROM tasks WHERE goal_id = :id ORDER BY created_at", {"id": goal_id}
        ).fetchall()
    finally:
        conn.close()


def _render_todos(goal_id: str, tasks) -> None:
    schedule_status, overdue = assess_schedule(tasks)
    if schedule_status == ScheduleStatus.BEHIND:
        names = ", ".join(t["title"] for t in overdue[:3])
        more = f" (+{len(overdue) - 3} more)" if len(overdue) > 3 else ""
        st.warning(f"Falling behind - {len(overdue)} overdue: {names}{more}", icon=":material/schedule:")
    elif schedule_status == ScheduleStatus.NO_DEADLINES:
        st.warning(
            "None of these deliverables have a deadline yet - set one below so this "
            "doesn't stay open-ended.",
            icon=":material/event_busy:",
        )

    ordered = sorted(tasks, key=lambda t: (t["deadline"] or "9999-99-99", t["created_at"]))
    with st.expander(f"Deliverables ({sum(1 for t in tasks if t['status'] == 'done')}/{len(tasks)})", expanded=len(tasks) > 0):
        today = date.today()
        for t in ordered:
            tc1, tc2 = st.columns([5, 3])
            label = t["title"]
            if t["deadline"]:
                overdue_flag = t["status"] != "done" and date.fromisoformat(t["deadline"]) < today
                label += f"  ({'⚠ ' if overdue_flag else ''}due {t['deadline']})"
            checked = tc1.checkbox(label, value=(t["status"] == "done"), key=f"task_done_{t['id']}")
            new_note = tc2.text_input(
                "note", value=t["notes"] or "", key=f"task_note_{t['id']}",
                placeholder="note...", label_visibility="collapsed",
            )

            new_status = "done" if checked else ("in_progress" if t["status"] == "in_progress" else "not_started")
            if new_status != t["status"] or new_note != (t["notes"] or ""):
                conn = get_connection()
                try:
                    conn.execute(
                        "UPDATE tasks SET status = :status, notes = :notes, "
                        "completed_at = CASE WHEN :status = 'done' THEN datetime('now') ELSE NULL END, "
                        "updated_at = datetime('now') WHERE id = :id",
                        {"status": new_status, "notes": new_note, "id": t["id"]},
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.rerun()

            if not t["deadline"] and t["status"] != "done":
                dc1, dc2 = st.columns([4, 1])
                picked = dc1.date_input(
                    "Set a deadline - currently open-ended",
                    value=date.today() + timedelta(days=7),
                    key=f"task_set_deadline_{t['id']}",
                )
                if dc2.button("Set", key=f"task_set_deadline_btn_{t['id']}"):
                    conn = get_connection()
                    try:
                        conn.execute(
                            "UPDATE tasks SET deadline = :deadline, updated_at = datetime('now') WHERE id = :id",
                            {"deadline": picked.isoformat(), "id": t["id"]},
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    st.rerun()

        with st.form(f"add_task_form_{goal_id}", clear_on_submit=True):
            new_title = st.text_input("Add a deliverable", key=f"new_task_{goal_id}", placeholder="e.g. Finish chapter 3 of PMP prep")
            new_deadline = st.date_input(
                "Deadline (required - nothing stays open-ended)",
                value=date.today() + timedelta(days=7),
                key=f"new_task_deadline_{goal_id}",
            )
            if st.form_submit_button("Add deliverable") and new_title.strip():
                conn = get_connection()
                try:
                    domain_id = conn.execute(
                        "SELECT domain_id FROM goals WHERE id = :id", {"id": goal_id}
                    ).fetchone()["domain_id"]
                    conn.execute(
                        "INSERT INTO tasks (id, goal_id, domain_id, title, deadline, status) "
                        "VALUES (:id, :goal_id, :domain_id, :title, :deadline, 'not_started')",
                        {
                            "id": f"task-{uuid.uuid4().hex[:8]}", "goal_id": goal_id,
                            "domain_id": domain_id, "title": new_title.strip(),
                            "deadline": new_deadline.isoformat(),
                        },
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.rerun()
