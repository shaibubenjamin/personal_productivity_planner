"""PEOS entry point / router.

Pure navigation setup - actual page content lives in views/. Domain-specific
content is NOT one tab per domain (Career, French, Finance, ... were
near-duplicate pages and cluttered the sidebar); instead every domain links
into the single views/domain_detail.py from its card on the dashboard.
"""

import sys
from datetime import date
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.auth import render_logout_button, require_login  # noqa: E402
from app.components.style import inject_css, render_sidebar_brand  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="Productivity Tracker", page_icon=":material/dashboard:", layout="wide")

# Must run before require_login(): the login gate itself reads/writes the
# app_auth table, so the schema needs to exist first.
init_db()

if require_login():
    inject_css()
    render_sidebar_brand()

    conn = get_connection()
    try:
        new_opportunities = conn.execute(
            "SELECT COUNT(*) AS n FROM intelligence_items WHERE category = 'opportunity' AND status = 'new'"
        ).fetchone()["n"]
        overdue_deliverables = conn.execute(
            "SELECT COUNT(*) AS n FROM tasks WHERE status != 'done' AND deadline IS NOT NULL AND deadline < :today",
            {"today": date.today().isoformat()},
        ).fetchone()["n"]
    finally:
        conn.close()

    # Plain text, no icon parameter - owner feedback 2026-09-13: icon
    # shortcodes were showing up as literal text in places, and it should
    # "feel written by a human."
    if overdue_deliverables:
        st.sidebar.error(f"{overdue_deliverables} overdue deliverable{'s' if overdue_deliverables != 1 else ''}")

    if new_opportunities:
        st.sidebar.warning(f"{new_opportunities} new opportunit{'y' if new_opportunities == 1 else 'ies'}")

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
    render_logout_button()
    pg.run()
