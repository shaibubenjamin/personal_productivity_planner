import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import inject_css, page_header  # noqa: E402

st.set_page_config(page_title="PEOS - Relationships & Marriage", page_icon="💞", layout="wide")
inject_css()
page_header("💞", "Relationships / Marriage")
st.info(
    "Relationship/marriage engine ships in V2 (spec Section 27, Page 8). "
    "Qualitative by design — never reduced to a numeric score (spec Domain 5/7)."
)
