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

from app.components.style import inject_css  # noqa: E402

st.set_page_config(page_title="PEOS", page_icon=":material/dashboard:", layout="wide")
inject_css()

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
