"""PEOS - Page 1: Executive Dashboard (spec Section 27, Page 1)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Executive Dashboard", layout="wide")

init_db()

st.title("Executive Dashboard")
st.caption("Personal Executive Operating System — V1, Phase 1/4")

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT * FROM domains WHERE active = 1 ORDER BY strategic_weight DESC NULLS LAST, name"
    ).fetchall()
    goal_count = conn.execute("SELECT COUNT(*) AS n FROM goals").fetchone()["n"]
finally:
    conn.close()

col1, col2, col3 = st.columns(3)
col1.metric("Active domains", len(domains))
col2.metric("Goals tracked", goal_count)
col3.metric("Automation category", "A (read-only)")

st.divider()

if goal_count == 0:
    st.info(
        "No goals entered yet. This dashboard will fill in as domains/goals.yaml "
        "is populated and the priority/balance engines have real data to score. "
        "Use the Goals page to add your first goal."
    )

st.subheader("Life Domains")

if not domains:
    st.warning("No domains configured — check config/life_domains.yaml.")
else:
    for d in domains:
        weight = d["strategic_weight"]
        min_attn = d["minimum_attention_pct"]
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{d['name']}**")
            c2.metric("Strategic weight", f"{weight:.0f}%" if weight is not None else "not set")
            c3.metric("Min. attention", f"{min_attn:.0f}%" if min_attn is not None else "not set")

st.divider()
st.caption(
    "Balance flags (OVER/UNDER/HEALTHY per domain) require real calendar-hours "
    "attention data, which isn't wired into this dashboard yet — see "
    "engine/balance/balance.py, which is implemented and tested, just not "
    "connected to a live data source here."
)
