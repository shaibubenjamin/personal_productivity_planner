"""Priority engine — spec Section 5.

Base formula only (the weighted sum). Modifiers listed in config/priorities.yaml
(current_progress, goal_gap, life_domain_imbalance, opportunity_value,
consequence_of_delay, available_time, energy_requirement, existing_commitments)
have no concrete formula defined in the spec yet and are intentionally not
implemented here — applying invented math for them would be fabricating a
spec that doesn't exist. Revisit once each modifier's intended effect is
defined.
"""

from dataclasses import dataclass

from engine.common.config import load_yaml

FACTOR_NAMES = (
    "strategic_importance",
    "urgency",
    "strategic_value",
    "risk_of_neglect",
    "deadline_pressure",
    "dependency_criticality",
)


@dataclass(frozen=True)
class PriorityFactors:
    """Each factor is on a 0-10 scale."""

    strategic_importance: float
    urgency: float
    strategic_value: float
    risk_of_neglect: float
    deadline_pressure: float
    dependency_criticality: float

    def __post_init__(self) -> None:
        for name in FACTOR_NAMES:
            value = getattr(self, name)
            if not 0 <= value <= 10:
                raise ValueError(f"{name} must be within 0-10, got {value}")


def load_weights() -> dict[str, float]:
    config = load_yaml("priorities.yaml")
    weights = config["weights"]
    total = sum(weights[name] for name in FACTOR_NAMES)
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"priorities.yaml weights must sum to 1.0, got {total}")
    return weights


def compute_priority_score(factors: PriorityFactors, weights: dict[str, float]) -> float:
    """Returns a score on a 0-100 scale."""
    normalized = sum(
        weights[name] * (getattr(factors, name) / 10.0) for name in FACTOR_NAMES
    )
    return round(normalized * 100, 2)
