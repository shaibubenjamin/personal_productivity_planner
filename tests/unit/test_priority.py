import pytest

from engine.priority.scoring import PriorityFactors, compute_priority_score, load_weights


def test_weights_sum_to_one():
    weights = load_weights()
    assert abs(sum(weights.values()) - 1.0) < 1e-6


def test_max_factors_yield_max_score():
    weights = load_weights()
    factors = PriorityFactors(10, 10, 10, 10, 10, 10)
    assert compute_priority_score(factors, weights) == 100.0


def test_min_factors_yield_zero_score():
    weights = load_weights()
    factors = PriorityFactors(0, 0, 0, 0, 0, 0)
    assert compute_priority_score(factors, weights) == 0.0


def test_known_weighted_case():
    weights = {
        "strategic_importance": 0.30,
        "urgency": 0.20,
        "strategic_value": 0.15,
        "risk_of_neglect": 0.15,
        "deadline_pressure": 0.10,
        "dependency_criticality": 0.10,
    }
    # All factors at 5/10 (half) should give exactly half the max score, 50.0,
    # regardless of the weight split, since weights sum to 1.
    factors = PriorityFactors(5, 5, 5, 5, 5, 5)
    assert compute_priority_score(factors, weights) == 50.0


def test_out_of_range_factor_rejected():
    with pytest.raises(ValueError):
        PriorityFactors(11, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        PriorityFactors(0, -1, 0, 0, 0, 0)
