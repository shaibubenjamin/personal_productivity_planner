"""PEOS - Digital Housekeeping (spec Section 27, Page 11).

Also tracks what Claude has sent you (daily brief, weekly review email, ad
hoc routine runs) and whether you've reviewed it / what you did about it
(owner request, 2026-09-08) - separate from the Gmail/Drive housekeeping
queues below, which are about YOUR inbox/Drive, not PEOS's own output.
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import icon_md, page_header  # noqa: E402
from engine.common.db import DB_PATH, get_connection, init_db  # noqa: E402

init_db()

page_header("cleaning_services", "Digital Housekeeping")

tab1, tab2, tab3, tab4 = st.tabs(["Claude Outputs", "Gmail", "Drive", "System"])

with tab1:
    st.caption(
        "Every brief/email/routine run PEOS has sent you, and whether you've "
        "reviewed it and acted on it. Logged manually for now - the cloud "
        "routines don't write here directly yet (same persistence gap as "
        "Global Intelligence and Reviews)."
    )
    conn = get_connection()
    try:
        outputs = conn.execute(
            "SELECT * FROM claude_outputs ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    if not outputs:
        st.info("Nothing logged yet - add the weekly review email or daily brief below once you've read it.")

    OUTPUT_TYPE_ICON = {
        "daily_brief": "wb_sunny", "weekly_review_email": "mail",
        "routine_run": "smart_toy", "other": "info",
    }
    for o in outputs:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{icon_md(OUTPUT_TYPE_ICON.get(o['output_type'], 'info'))} {o['subject'] or o['output_type']}**")
            c1.caption(f"{o['output_type']} · sent {o['sent_at'] or o['created_at']}")
            reviewed = c2.checkbox("Reviewed", value=bool(o["reviewed"]), key=f"output_reviewed_{o['id']}")
            if o["summary"]:
                st.caption(o["summary"])

            action = st.text_input(
                "Action taken", value=o["action_taken"] or "", key=f"output_action_{o['id']}",
                placeholder="e.g. Updated the French goal deadline after reading this",
            )

            if reviewed != bool(o["reviewed"]) or action != (o["action_taken"] or ""):
                conn = get_connection()
                try:
                    conn.execute(
                        "UPDATE claude_outputs SET reviewed = :reviewed, action_taken = :action WHERE id = :id",
                        {"reviewed": reviewed, "action": action, "id": o["id"]},
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.rerun()

    with st.expander("Log a Claude output", icon=":material/add:"):
        with st.form("add_claude_output", clear_on_submit=True):
            output_type = st.selectbox(
                "Type", ["daily_brief", "weekly_review_email", "routine_run", "other"]
            )
            subject = st.text_input("Subject / title")
            summary = st.text_area("Summary (optional)")
            if st.form_submit_button("Log", type="primary") and subject.strip():
                conn = get_connection()
                try:
                    conn.execute(
                        "INSERT INTO claude_outputs (id, output_type, subject, summary, sent_at) "
                        "VALUES (:id, :type, :subject, :summary, :now)",
                        {
                            "id": f"output-{uuid.uuid4().hex[:8]}",
                            "type": output_type,
                            "subject": subject.strip(),
                            "summary": summary.strip() or None,
                            "now": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    conn.commit()
                finally:
                    conn.close()
                st.rerun()

with tab2:
    conn = get_connection()
    try:
        emails = conn.execute("SELECT COUNT(*) AS n FROM emails WHERE processed = FALSE").fetchone()["n"]
    finally:
        conn.close()
    st.metric(f"{icon_md('mail')} Unprocessed emails in review queue", emails)
    if emails == 0:
        st.info(
            "Nothing here yet — the daily routine classifies email as part of "
            "the brief but doesn't write results back to this database yet "
            "(Category B archiving/labeling stays off until the 14-day "
            "trust-graduation window per config/automation_policy.yaml)."
        )

with tab3:
    conn = get_connection()
    try:
        docs = conn.execute("SELECT COUNT(*) AS n FROM documents WHERE status = 'duplicate_candidate'").fetchone()["n"]
    finally:
        conn.close()
    st.metric(f"{icon_md('content_copy')} Duplicate-candidate files", docs)
    if docs == 0:
        st.info(
            "No Drive housekeeping data persisted yet. A PEOS/ folder with "
            "subfolders (Reviews, Global Intelligence, Learning, Logs) is "
            "being set up in your Drive as the shared bridge between the "
            "cloud routines and this app - see the chat for details."
        )

with tab4:
    st.markdown(f"### {icon_md('database')} Storage")
    if os.environ.get("DATABASE_URL"):
        st.success("Connected to hosted Postgres (Supabase) - the same database whether run locally or deployed.")
        st.caption(
            "No ephemeral-storage risk: unlike a local SQLite file, this database persists "
            "across redeploys/restarts and is reachable from anywhere, not just this machine."
        )
    else:
        db_size_mb = DB_PATH.stat().st_size / (1024 * 1024) if DB_PATH.exists() else 0
        WARNING_THRESHOLD_MB = 200  # sanity-check threshold, not a real SQLite limit - see caption below
        st.metric(f"{icon_md('database')} Local database size", f"{db_size_mb:.2f} MB")
        if db_size_mb > WARNING_THRESHOLD_MB:
            st.warning(
                f"Database has grown past {WARNING_THRESHOLD_MB} MB - unusual for this kind of "
                "habit/goal-tracking data. Worth checking for unbounded log growth rather than "
                "treating it as a real capacity limit (see caption below)."
            )
        else:
            st.success(f"Well under the {WARNING_THRESHOLD_MB} MB sanity-check threshold.")
        st.caption(
            "SQLite itself has no meaningful ceiling for this use case (technical limit "
            "is ~281 TB) - the real constraint is disk space on whatever machine runs it. "
            "One real risk: if this app is deployed to Streamlit Community Cloud as-is, its "
            "containers are ephemeral - a local SQLite file can be wiped on redeploy/restart. "
            "Set DATABASE_URL (see docs/decision_log.md) to remove that risk entirely."
        )

    st.divider()
    st.markdown(f"### {icon_md('feedback')} Platform feedback")
    st.caption(
        "Log anything about the platform itself - not life/goal content - that "
        "should improve (confusing layout, a missing action, something that felt "
        "slow or unclear)."
    )

    conn = get_connection()
    try:
        feedback_items = conn.execute(
            "SELECT * FROM platform_feedback ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    with st.form("add_feedback", clear_on_submit=True):
        note = st.text_area("What should improve?")
        if st.form_submit_button("Log feedback", type="primary") and note.strip():
            conn = get_connection()
            try:
                conn.execute(
                    "INSERT INTO platform_feedback (id, note) VALUES (:id, :note)",
                    {"id": f"feedback-{uuid.uuid4().hex[:8]}", "note": note.strip()},
                )
                conn.commit()
            finally:
                conn.close()
            st.rerun()

    if feedback_items:
        for f in feedback_items:
            with st.container(border=True):
                st.markdown(f"{icon_md('feedback')} {f['note']}")
                st.caption(f"{f['status']} · {f['created_at']}")
    else:
        st.info("No feedback logged yet.")
