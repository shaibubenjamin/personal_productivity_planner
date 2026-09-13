"""GTD-style quick capture: write it down now, triage later. The capture
form only ever writes a *suggestion* (engine/capture/triage.py); nothing is
filed under a real goal/domain until the owner confirms it in the inbox
below, per the confidence model (never present an inference as fact).
"""

import uuid
from datetime import date, datetime, timedelta, timezone

import streamlit as st

from app.components.style import icon_md
from engine.capture.triage import suggest_triage
from engine.common.db import get_connection


def render_quick_capture() -> None:
    with st.form("quick_capture", clear_on_submit=True):
        text = st.text_input(
            "Quick capture - write it down now, sort it later",
            placeholder="e.g. book a swim lesson, call the accountant about tax, ask about the CSEA fellowship deadline",
        )
        if st.form_submit_button("Capture", type="primary") and text.strip():
            conn = get_connection()
            try:
                goals = conn.execute("SELECT id, domain_id, name FROM goals").fetchall()
                domain_id, goal_id = suggest_triage(text.strip(), goals)
                conn.execute(
                    "INSERT INTO captures (id, raw_text, suggested_domain_id, suggested_goal_id, "
                    "domain_id, goal_id, status) "
                    "VALUES (:id, :text, :sd, :sg, :sd, :sg, 'new')",
                    {
                        "id": f"capture-{uuid.uuid4().hex[:8]}",
                        "text": text.strip(),
                        "sd": domain_id,
                        "sg": goal_id,
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()


def render_capture_inbox() -> None:
    conn = get_connection()
    try:
        pending = conn.execute(
            "SELECT * FROM captures WHERE status = 'new' ORDER BY created_at DESC"
        ).fetchall()
        domains = conn.execute("SELECT id, name FROM domains WHERE active = TRUE ORDER BY name").fetchall()
        goals = conn.execute("SELECT id, domain_id, name FROM goals").fetchall()
    finally:
        conn.close()

    if not pending:
        return

    domain_name_by_id = {d["id"]: d["name"] for d in domains}
    domain_id_by_name = {d["name"]: d["id"] for d in domains}

    with st.expander(f"Inbox to triage ({len(pending)})", expanded=True, icon=":material/inbox:"):
        for c in pending:
            with st.container(border=True):
                st.markdown(f"**{icon_md('edit_note')} {c['raw_text']}**")

                current_domain_id = c["domain_id"] or ""
                domain_names = list(domain_name_by_id.values())
                default_index = (
                    domain_names.index(domain_name_by_id[current_domain_id])
                    if current_domain_id in domain_name_by_id
                    else 0
                )
                chosen_domain_name = st.selectbox(
                    "Domain", domain_names, index=default_index, key=f"capture_domain_{c['id']}",
                )
                chosen_domain_id = domain_id_by_name[chosen_domain_name]

                domain_goals = [g for g in goals if g["domain_id"] == chosen_domain_id]
                goal_options = {g["name"]: g["id"] for g in domain_goals}
                goal_names = list(goal_options.keys()) or ["(no goals in this domain yet)"]
                goal_default = 0
                if c["goal_id"]:
                    matching = [g["name"] for g in domain_goals if g["id"] == c["goal_id"]]
                    if matching:
                        goal_default = goal_names.index(matching[0])
                chosen_goal_name = st.selectbox(
                    "Goal", goal_names, index=goal_default, key=f"capture_goal_{c['id']}",
                )
                chosen_goal_id = goal_options.get(chosen_goal_name)

                c1, c2, c3 = st.columns(3)
                deadline = c1.date_input(
                    "Deadline (if saving as a deliverable)",
                    value=date.today() + timedelta(days=7),
                    key=f"capture_deadline_{c['id']}",
                )

                if c2.button("Save as deliverable", key=f"capture_task_{c['id']}", disabled=not chosen_goal_id):
                    conn = get_connection()
                    try:
                        task_id = f"task-{uuid.uuid4().hex[:8]}"
                        conn.execute(
                            "INSERT INTO tasks (id, goal_id, domain_id, title, deadline, status) "
                            "VALUES (:id, :goal_id, :domain_id, :title, :deadline, 'not_started')",
                            {
                                "id": task_id, "goal_id": chosen_goal_id, "domain_id": chosen_domain_id,
                                "title": c["raw_text"], "deadline": deadline.isoformat(),
                            },
                        )
                        conn.execute(
                            "UPDATE captures SET status = 'triaged', domain_id = :d, goal_id = :g, "
                            "resulting_task_id = :t, triaged_at = :now WHERE id = :id",
                            {
                                "d": chosen_domain_id, "g": chosen_goal_id, "t": task_id,
                                "now": datetime.now(timezone.utc).isoformat(), "id": c["id"],
                            },
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    st.rerun()

                if c3.button("Save as note", key=f"capture_note_{c['id']}", disabled=not chosen_goal_id):
                    conn = get_connection()
                    try:
                        conn.execute(
                            "INSERT INTO goal_logs (goal_id, note) VALUES (:goal_id, :note)",
                            {"goal_id": chosen_goal_id, "note": c["raw_text"]},
                        )
                        conn.execute(
                            "UPDATE captures SET status = 'triaged', domain_id = :d, goal_id = :g, "
                            "triaged_at = :now WHERE id = :id",
                            {
                                "d": chosen_domain_id, "g": chosen_goal_id,
                                "now": datetime.now(timezone.utc).isoformat(), "id": c["id"],
                            },
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    st.rerun()

                if st.button("Discard", key=f"capture_discard_{c['id']}"):
                    conn = get_connection()
                    try:
                        conn.execute(
                            "UPDATE captures SET status = 'discarded', triaged_at = :now WHERE id = :id",
                            {"now": datetime.now(timezone.utc).isoformat(), "id": c["id"]},
                        )
                        conn.commit()
                    finally:
                        conn.close()
                    st.rerun()
