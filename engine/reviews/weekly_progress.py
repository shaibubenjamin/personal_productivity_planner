"""Weekly progress classification - "what's going fine, what's left, what's
struggling" (owner's own framing, 2026-09-07).

Deliberately evidence-based rather than a fabricated velocity/benchmark
number: a goal is "struggling" because it went quiet (no log entry this
week) or was explicitly marked at_risk, not because it missed some invented
percent-per-week target no one ever set (spec Section 54 - no fake precision).
"""

from enum import Enum


class ProgressCategory(Enum):
    COMPLETED = "COMPLETED"
    ON_TRACK = "ON_TRACK"
    STRUGGLING = "STRUGGLING"
    REMAINING = "REMAINING"
    ABANDONED = "ABANDONED"


def classify_goal(status: str, has_recent_log: bool) -> ProgressCategory:
    """`has_recent_log`: whether a goal_logs entry exists within the review window."""
    if status == "done":
        return ProgressCategory.COMPLETED
    if status == "abandoned":
        return ProgressCategory.ABANDONED
    if status == "at_risk":
        return ProgressCategory.STRUGGLING
    if status == "not_started":
        return ProgressCategory.REMAINING
    if status == "in_progress":
        return ProgressCategory.ON_TRACK if has_recent_log else ProgressCategory.STRUGGLING
    return ProgressCategory.REMAINING
