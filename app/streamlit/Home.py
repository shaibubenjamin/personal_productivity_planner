"""PEOS - Page 1: Executive Dashboard (spec Section 27, Page 1)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import domain_icon, inject_css, page_header  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Executive Dashboard", page_icon="🧭", layout="wide")
inject_css()
init_db()

page_header("🧭", "Executive Dashboard", "Personal Executive Operating System — V1, Phase 1/4")

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
col3.metric("Automation category", "A · read-only")

st.divider()

if goal_count == 0:
    st.info(
        "No goals entered yet. This dashboard fills in as config/goals.yaml is "
        "populated and the priority/balance engines have real data to score. "
        "Use the Goals page to add one."
    )

st.subheader("Life Domains")

if not domains:
    st.warning("No domains configured — check config/life_domains.yaml.")
else:
    cols = st.columns(2)
    for i, d in enumerate(domains):
        weight = d["strategic_weight"]
        min_attn = d["minimum_attention_pct"]
        with cols[i % 2]:
            with st.container(border=True):
                icon = domain_icon(d["id"])
                st.markdown(f"### {icon} {d['name']}")
                c1, c2 = st.columns(2)
                c1.metric("Strategic weight", f"{weight:.0f}%" if weight is not None else "—")
                c2.metric("Min. attention", f"{min_attn:.0f}%" if min_attn is not None else "—")

st.divider()
st.caption(
    "Balance flags (OVER/UNDER/HEALTHY per domain) need real calendar-hours "
    "attention data, which isn't wired up here yet — see the Life Balance "
    "page for the engine's output on illustrative placeholder data."
)
