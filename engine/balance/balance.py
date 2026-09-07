"""Life-balance engine — spec Section 6.

No composite "life score" is produced (spec Section 54 forbids fake
precision). Each domain gets one of three flags for a given window.
"""

from dataclasses import dataclass
from enum import Enum


class BalanceStatus(Enum):
    OVER_INVESTMENT = "OVER_INVESTMENT"
    UNDER_INVESTMENT = "UNDER_INVESTMENT"
    HEALTHY = "HEALTHY"


@dataclass(frozen=True)
class DomainAttention:
    domain_id: str
    minimum_attention_pct: float  # from config/life_domains.yaml
    actual_attention_pct: float  # observed share of tracked time in the window
    days_since_meaningful_activity: int


def assess_domain(
    domain: DomainAttention,
    neglect_days_threshold: int = 14,
    over_investment_ratio: float = 1.5,
) -> BalanceStatus:
    """Single-domain assessment against its own minimum threshold."""
    if (
        domain.actual_attention_pct < domain.minimum_attention_pct
        or domain.days_since_meaningful_activity > neglect_days_threshold
    ):
        return BalanceStatus.UNDER_INVESTMENT

    if domain.actual_attention_pct > domain.minimum_attention_pct * over_investment_ratio:
        return BalanceStatus.OVER_INVESTMENT

    return BalanceStatus.HEALTHY


def assess_life_balance(
    domains: list[DomainAttention],
    neglect_days_threshold: int = 14,
    over_investment_ratio: float = 1.5,
) -> dict[str, BalanceStatus]:
    """Cross-domain assessment.

    A domain is only flagged OVER_INVESTMENT if it exceeds its own threshold
    *and* at least one other domain is concurrently under its minimum — this
    matches the spec's own example (career at 80% while other domains get
    almost nothing) rather than penalizing a domain for doing well in
    isolation.
    """
    per_domain = {
        d.domain_id: assess_domain(d, neglect_days_threshold, over_investment_ratio)
        for d in domains
    }

    any_under_investment = any(
        status == BalanceStatus.UNDER_INVESTMENT for status in per_domain.values()
    )
    if not any_under_investment:
        for domain_id, status in per_domain.items():
            if status == BalanceStatus.OVER_INVESTMENT:
                per_domain[domain_id] = BalanceStatus.HEALTHY

    return per_domain
