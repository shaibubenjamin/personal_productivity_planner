"""PEOS - Page 2: Life Balance (spec Section 27, Page 2 / Section 6 engine)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from engine.balance.balance import BalanceStatus, DomainAttention, assess_life_balance  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

st.set_page_config(page_title="PEOS - Life Balance", layout="wide")
init_db()

st.title("Life Balance")
st.caption(
    "OVER_INVESTMENT / UNDER_INVESTMENT / HEALTHY per domain (spec Section 6). "
    "No composite 'life score' is produced by design (Section 54)."
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
        "config/life_domains.yaml — balance can't be assessed for those until it's confirmed."
    )

st.info(
    "Real calendar-hours attention tracking isn't wired up yet, so the figures below "
    "are illustrative placeholders (0% actual attention, 0 days since activity) to show "
    "how the balance engine's output will render once real data flows in."
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

    badge = {
        BalanceStatus.OVER_INVESTMENT: "🟠 OVER-INVESTMENT",
        BalanceStatus.UNDER_INVESTMENT: "🔴 UNDER-INVESTMENT",
        BalanceStatus.HEALTHY: "🟢 HEALTHY",
    }

    id_to_name = {d["id"]: d["name"] for d in domains}
    for domain_id, status in results.items():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{id_to_name[domain_id]}**")
            c2.markdown(badge[status])
