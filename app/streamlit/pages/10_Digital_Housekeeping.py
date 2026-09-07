"""PEOS - Page 11: Digital Housekeeping (spec Section 27, Page 11)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Digital Housekeeping", layout="wide")
init_db()

st.title("Digital Housekeeping")

conn = get_connection()
try:
    emails = conn.execute(
        "SELECT COUNT(*) AS n FROM emails WHERE processed = 0"
    ).fetchone()["n"]
    docs = conn.execute(
        "SELECT COUNT(*) AS n FROM documents WHERE status = 'duplicate_candidate'"
    ).fetchone()["n"]
finally:
    conn.close()

tab1, tab2 = st.tabs(["Gmail", "Drive"])

with tab1:
    st.metric("Unprocessed emails in review queue", emails)
    if emails == 0:
        st.info(
            "Nothing here yet — the daily routine classifies email as part of the "
            "brief but doesn't write results back to this database yet (Category B "
            "archiving/labeling isn't enabled until the 14-day trust-graduation "
            "window per config/automation_policy.yaml)."
        )

with tab2:
    st.metric("Duplicate-candidate files", docs)
    if docs == 0:
        st.info("No Drive housekeeping data persisted yet - same gap as above.")
