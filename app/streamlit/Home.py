"""PEOS entry point / router.

Pure navigation setup - actual page content lives in views/. Domain-specific
content is NOT one tab per domain (Career, French, Finance, ... were
near-duplicate pages and cluttered the sidebar); instead every domain links
into the single views/domain_detail.py from its card on the dashboard.
"""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.auth import require_login  # noqa: E402
from app.components.style import inject_css  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="Productivity Tracker", page_icon=":material/dashboard:", layout="wide")

if require_login():
    inject_css()
    init_db()

    conn = get_connection()
    try:
        new_opportunities = conn.execute(
            "SELECT COUNT(*) AS n FROM intelligence_items WHERE category = 'opportunity' AND status = 'new'"
        ).fetchone()["n"]
        overdue_deliverables = conn.execute(
            "SELECT COUNT(*) AS n FROM tasks WHERE status != 'done' AND deadline IS NOT NULL AND deadline < date('now')"
        ).fetchone()["n"]
    finally:
        conn.close()

    if overdue_deliverables:
        st.sidebar.markdown(
            f'<div style="background:#FEE2E2; color:#B91C1C; padding:0.5rem 0.75rem; '
            f'border-radius:0.5rem; font-weight:600; margin-bottom:0.5rem;">'
            f":material/schedule: {overdue_deliverables} overdue deliverable"
            f"{'s' if overdue_deliverables != 1 else ''}</div>",
            unsafe_allow_html=True,
        )

    if new_opportunities:
        st.sidebar.markdown(
            f'<div style="background:#FEF3C7; color:#B45309; padding:0.5rem 0.75rem; '
            f'border-radius:0.5rem; font-weight:600; margin-bottom:0.5rem;">'
            f":material/notifications_active: {new_opportunities} new opportunit"
            f"{'y' if new_opportunities == 1 else 'ies'}</div>",
            unsafe_allow_html=True,
        )

    pages = {
        "Overview": [
            st.Page("views/dashboard.py", title="Executive Dashboard", icon=":material/dashboard:", default=True),
            st.Page("views/goals.py", title="Goals", icon=":material/flag:"),
            st.Page("views/life_balance.py", title="Life Balance", icon=":material/balance:"),
            st.Page("views/reviews.py", title="Reviews", icon=":material/fact_check:"),
            st.Page("views/domain_detail.py", title="Domain", icon=":material/category:", visibility="hidden"),
        ],
        "System": [
            st.Page("views/learning.py", title="Learning", icon=":material/school:"),
            st.Page("views/global_intelligence.py", title="Global Intelligence", icon=":material/public:"),
            st.Page("views/digital_housekeeping.py", title="Digital Housekeeping", icon=":material/cleaning_services:"),
        ],
    }

    pg = st.navigation(pages)
    pg.run()
