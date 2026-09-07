from engine.balance.balance import BalanceStatus, DomainAttention, assess_life_balance


def test_healthy_domain():
    domains = [DomainAttention("career", minimum_attention_pct=50, actual_attention_pct=55, days_since_meaningful_activity=1)]
    result = assess_life_balance(domains)
    assert result["career"] == BalanceStatus.HEALTHY


def test_under_investment_by_low_attention():
    domains = [DomainAttention("financial", minimum_attention_pct=10, actual_attention_pct=2, days_since_meaningful_activity=1)]
    result = assess_life_balance(domains)
    assert result["financial"] == BalanceStatus.UNDER_INVESTMENT


def test_under_investment_by_neglect_days():
    domains = [DomainAttention("french", minimum_attention_pct=10, actual_attention_pct=10, days_since_meaningful_activity=30)]
    result = assess_life_balance(domains)
    assert result["french"] == BalanceStatus.UNDER_INVESTMENT


def test_mandatory_spec_scenario_career_dominance_flags_neglect():
    """Spec Section 53 'BALANCE TEST': career at 80% while other strategically
    important domains receive almost no attention must be detected."""
    domains = [
        DomainAttention("career", minimum_attention_pct=50, actual_attention_pct=80, days_since_meaningful_activity=0),
        DomainAttention("financial", minimum_attention_pct=10, actual_attention_pct=1, days_since_meaningful_activity=20),
        DomainAttention("french", minimum_attention_pct=10, actual_attention_pct=1, days_since_meaningful_activity=25),
        DomainAttention("relationships", minimum_attention_pct=10, actual_attention_pct=8, days_since_meaningful_activity=5),
    ]
    result = assess_life_balance(domains)

    assert result["career"] == BalanceStatus.OVER_INVESTMENT
    assert result["financial"] == BalanceStatus.UNDER_INVESTMENT
    assert result["french"] == BalanceStatus.UNDER_INVESTMENT


def test_over_investment_not_flagged_when_no_other_domain_is_neglected():
    """A domain exceeding its own threshold isn't a problem on its own if
    nothing else is being neglected — balance doesn't mean equality (spec
    Principle 2)."""
    domains = [
        DomainAttention("career", minimum_attention_pct=50, actual_attention_pct=80, days_since_meaningful_activity=0),
        DomainAttention("financial", minimum_attention_pct=10, actual_attention_pct=15, days_since_meaningful_activity=1),
    ]
    result = assess_life_balance(domains)
    assert result["career"] == BalanceStatus.HEALTHY
