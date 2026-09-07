from engine.reviews.weekly_progress import ProgressCategory, classify_goal


def test_done_is_completed_regardless_of_recent_log():
    assert classify_goal("done", False) == ProgressCategory.COMPLETED
    assert classify_goal("done", True) == ProgressCategory.COMPLETED


def test_at_risk_is_struggling():
    assert classify_goal("at_risk", True) == ProgressCategory.STRUGGLING


def test_not_started_is_remaining():
    assert classify_goal("not_started", False) == ProgressCategory.REMAINING


def test_in_progress_with_recent_log_is_on_track():
    assert classify_goal("in_progress", True) == ProgressCategory.ON_TRACK


def test_in_progress_gone_quiet_is_struggling():
    """A goal marked in_progress but with no log entry this week has gone
    quiet - that's the neglect signal, not a numeric miss."""
    assert classify_goal("in_progress", False) == ProgressCategory.STRUGGLING


def test_abandoned_stays_abandoned():
    assert classify_goal("abandoned", True) == ProgressCategory.ABANDONED
