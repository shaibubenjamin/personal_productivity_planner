import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import inject_css, page_header  # noqa: E402

st.set_page_config(page_title="PEOS - Career", page_icon="💼", layout="wide")
inject_css()
page_header("💼", "Career")
st.info(
    "Career capability engine ships in V2 (spec Section 27, Page 4). "
    "See the Learning page for the real capability plan captured so far."
)
