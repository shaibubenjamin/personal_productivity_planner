"""PEOS - Life Balance (spec Section 27, Page 2 / Section 6 engine)."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.domain_card import render_domain_card  # noqa: E402
from app.components.style import page_header, status_pill  # noqa: E402
from engine.balance.balance import BalanceStatus, DomainAttention, assess_life_balance  # noqa: E402
from engine.common.db import get_connection, init_db  # noqa: E402

init_db()

page_header(
    "balance",
    "Life Balance",
    "OVER / UNDER / HEALTHY per domain — no composite \"life score\" by design.",
)

conn = get_connection()
try:
    domains = conn.execute(
        "SELECT * FROM domains WHERE active = TRUE ORDER BY name"
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

    by_id = {d["id"]: d for d in configured}
    cols = st.columns(2)
    for i, (domain_id, status) in enumerate(results.items()):
        badge = status_pill(status.value.replace("_", " "), status.value)
        with cols[i % 2]:
            render_domain_card(by_id[domain_id], badge_html=badge)
