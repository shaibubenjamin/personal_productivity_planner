"""PEOS - Page 2: Life Balance (spec Section 27, Page 2 / Section 6 engine)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.style import domain_icon, inject_css, page_header, status_pill  # noqa: E402
from engine.balance.balance import BalanceStatus, DomainAttention, assess_life_balance  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Life Balance", page_icon="⚖️", layout="wide")
inject_css()
init_db()

page_header(
    "⚖️",
    "Life Balance",
    "OVER / UNDER / HEALTHY per domain — no composite \"life score\" by design.",
)

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT * FROM domains WHERE active = 1 ORDER BY name"
    ).fetchall()
finally:
    conn.close()

domains_missing_config = [d for d in domains if d["minimum_attention_pct"] is None]
if domains_missing_config:
    st.warning(
        f"{len(domains_missing_config)} domain(s) have no minimum_attention_pct set in "
        "config/life_domains.yaml — balance can't be assessed for those yet."
    )

st.info(
    "Real calendar-hours attention tracking isn't wired up yet, so the figures "
    "below are illustrative placeholders (0% actual attention, 0 days since "
    "activity) to show how the engine's output will render once real data flows in."
)

configured = [d for d in domains if d["minimum_attention_pct"] is not None]
if configured:
    attentions = [
        DomainAttention(
            domain_id=d["id"],
            minimum_attention_pct=d["minimum_attention_pct"],
            actual_attention_pct=0,
            days_since_meaningful_activity=0,
        )
        for d in configured
    ]
    results = assess_life_balance(attentions)

    id_to_name = {d["id"]: d["name"] for d in domains}
    cols = st.columns(2)
    for i, (domain_id, status) in enumerate(results.items()):
        with cols[i % 2]:
            with st.container(border=True):
                icon = domain_icon(domain_id)
                c1, c2 = st.columns([3, 2])
                c1.markdown(f"### {icon} {id_to_name[domain_id]}")
                c2.markdown(status_pill(status.value.replace("_", " "), status.value), unsafe_allow_html=True)
