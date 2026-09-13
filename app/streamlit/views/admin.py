"""Admin panel - structure management (domains/goals/tasks) and database
housekeeping (size, reset), per owner request 2026-09-13.

Not a separate access tier - this is a single-user app, already gated by
the same login as everything else. "Subtask" is represented as another
task under the same goal (the schema is flat, no parent/child task
hierarchy) - noted in the Tasks tab so expectations match reality.
"""

import sys
import uuid
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import page_header  # noqa: E402
from data.seeds.seed_from_config import (  # noqa: E402
    seed_domains, seed_goals, seed_learning_items, seed_tasks,
)
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()
page_header("admin_panel_settings", "Admin")

tab_domains, tab_goals, tab_tasks, tab_database = st.tabs(
    ["Domains", "Goals", "Tasks", "Database"]
)

# Tables never touched by config seeding - safe to wipe for a "reset to
# config" that leaves domains/goals/tasks/learning_items intact.
# app_auth is deliberately excluded - clearing it would lock the owner out.
RUNTIME_TABLES = [
    "goal_dependencies", "daily_habits", "platform_feedback", "goal_logs",
    "goal_risks", "captures", "decision_log", "commitments",
    "calendar_events", "emails", "documents", "learning_item_logs",
    "reviews", "intelligence_items", "claude_outputs", "actions",
    "audit_log", "objectives", "projects",
]

with tab_domains:
    st.caption("Domains split the whole 100% of your attention across every area of life.")
    conn = get_connection()
    try:
        domains = conn.execute(
            "SELECT * FROM domains ORDER BY strategic_weight DESC NULLS LAST, name"
        ).fetchall()
    finally:
        conn.close()

    for d in domains:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(f"**{d['name']}**  \n:gray[{d['id']}]")
            c2.metric("Weight", f"{d['strategic_weight']:.2f}%" if d["strategic_weight"] is not None else "—")
            c3.metric("Active", "Yes" if d["active"] else "No")
    total_weight = sum(float(d["strategic_weight"] or 0) for d in domains)
    if abs(total_weight - 100) > 0.1:
        st.warning(f"Domain weights sum to {total_weight:.2f}%, not 100% - worth reviewing config/life_domains.yaml.")

    with st.expander("Add a domain", icon=":material/add:"):
        st.caption(
            "This only adds the row here - to keep it permanently, also add it to "
            "config/life_domains.yaml (otherwise a future reseed won't know about it, "
            "though it won't delete it either)."
        )
        with st.form("add_domain", clear_on_submit=True):
            new_id = st.text_input("Domain id (lowercase, no spaces)", placeholder="e.g. health")
            new_name = st.text_input("Display name", placeholder="e.g. Health")
            new_weight = st.number_input("Weight %", min_value=0.0, max_value=100.0, value=10.0, step=0.1)
            if st.form_submit_button("Add domain", type="primary") and new_id.strip() and new_name.strip():
                conn = get_connection()
                try:
                    conn.execute(
                        "INSERT INTO domains (id, name, strategic_weight, minimum_attention_pct, active) "
                        "VALUES (:id, :name, :weight, :weight, TRUE)",
                        {"id": new_id.strip().lower().replace(" ", "_"), "name": new_name.strip(), "weight": new_weight},
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.success(f"Added domain: {new_name}")
                st.rerun()

with tab_goals:
    st.caption("Same as the Goals page's own form - included here too for a single admin entry point.")
    conn = get_connection()
    try:
        domains = conn.execute("SELECT id, name FROM domains WHERE active = TRUE ORDER BY name").fetchall()
    finally:
        conn.close()
    domain_options = {d["name"]: d["id"] for d in domains}

    with st.form("admin_add_goal", clear_on_submit=True):
        name = st.text_input("Goal name")
        domain_name = st.selectbox("Domain", list(domain_options.keys()) or ["(no domains configured)"])
        why = st.text_area("Why it matters")
        strategic_importance = st.slider("Strategic importance", 0, 10, 5)
        deadline = st.date_input("Target date", value=None)
        if st.form_submit_button("Add goal", type="primary") and name.strip() and domain_options:
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO goals (id, domain_id, name, why_it_matters, "
                    "strategic_importance, deadline, status, progress, confidence) "
                    "VALUES (:id, :domain_id, :name, :why, :importance, :deadline, 'not_started', 0, 'LOW')",
                    {
                        "id": f"goal-{uuid.uuid4().hex[:8]}",
                        "domain_id": domain_options[domain_name],
                        "name": name.strip(),
                        "why": why.strip() or None,
                        "importance": strategic_importance,
                        "deadline": deadline.isoformat() if deadline else None,
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.success(f"Added goal: {name}")
            st.rerun()

with tab_tasks:
    st.caption(
        "A task here is a deliverable under a goal. There's no separate 'subtask' "
        "level in the data model - add another task under the same goal instead."
    )
    conn = get_connection()
    try:
        goals = conn.execute(
            "SELECT g.id, g.name, d.name AS domain_name FROM goals g "
            "JOIN domains d ON g.domain_id = d.id ORDER BY d.name, g.name"
        ).fetchall()
    finally:
        conn.close()
    goal_options = {f"{g['domain_name']} · {g['name']}": (g["id"], g["domain_name"]) for g in goals}

    with st.form("admin_add_task", clear_on_submit=True):
        goal_label = st.selectbox("Goal", list(goal_options.keys()) or ["(no goals yet)"])
        title = st.text_input("Deliverable title")
        deadline = st.date_input("Deadline (required)")
        if st.form_submit_button("Add task", type="primary") and title.strip() and goal_options:
            goal_id, domain_name_for_goal = goal_options[goal_label]
            conn = get_connection()
            try:
                domain_id = conn.execute(
                    "SELECT domain_id FROM goals WHERE id = :id", {"id": goal_id}
                ).fetchone()["domain_id"]
                conn.execute(
                    "INSERT INTO tasks (id, goal_id, domain_id, title, deadline, status) "
                    "VALUES (:id, :goal_id, :domain_id, :title, :deadline, 'not_started')",
                    {
                        "id": f"task-{uuid.uuid4().hex[:8]}",
                        "goal_id": goal_id,
                        "domain_id": domain_id,
                        "title": title.strip(),
                        "deadline": deadline.isoformat(),
                    },
                )
                conn.commit()
            finally:
                conn.close()
            st.success(f"Added task: {title}")
            st.rerun()

with tab_database:
    st.subheader("Row counts")
    conn = get_connection()
    try:
        all_tables = [
            "domains", "goals", "tasks", "learning_items", "app_auth",
        ] + RUNTIME_TABLES
        counts = {}
        for t in all_tables:
            counts[t] = conn.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchone()["n"]
    finally:
        conn.close()

    total_rows = sum(counts.values())
    c1, c2 = st.columns(2)
    c1.metric("Total rows across all tables", total_rows)
    c2.caption(
        "Supabase's free tier caps the whole database around 500 MB - row count "
        "alone won't hit that for this kind of data, but worth knowing the ceiling exists."
    )

    with st.expander("Row counts by table"):
        for t, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            st.caption(f"{t}: {n}")

    st.divider()
    st.subheader("Reset to config")
    st.caption(
        "Wipes runtime data only - habit history, log notes, quick captures, "
        "decision log, platform feedback, and everything else NOT defined in "
        "config/*.yaml. Domains, goals, tasks, and learning items are then "
        "re-applied fresh from config, so your goal/task structure survives. "
        "Your login is never touched. This cannot be undone."
    )
    confirm_text = st.text_input('Type "RESET" to enable the button below')
    if st.button("Reset to config", type="primary", disabled=(confirm_text != "RESET")):
        conn = get_connection()
        try:
            for t in RUNTIME_TABLES:
                conn.execute(f"DELETE FROM {t}")
            conn.commit()
            seed_domains(conn)
            seed_goals(conn)
            seed_learning_items(conn)
            seed_tasks(conn)
        finally:
            conn.close()
        st.success("Reset complete - runtime data cleared, structure re-applied from config.")
        st.rerun()
