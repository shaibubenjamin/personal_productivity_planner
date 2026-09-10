from datetime import date, timedelta

from engine.habits.streak import compute_streak


def test_no_history_is_zero():
    assert compute_streak(set()) == 0


def test_single_day_done_today():
    today = date(2026, 9, 10)
    assert compute_streak({today}, today=today) == 1


def test_three_day_streak_ending_today():
    today = date(2026, 9, 10)
    dates = {today, today - timedelta(days=1), today - timedelta(days=2)}
    assert compute_streak(dates, today=today) == 3


def test_gap_breaks_streak():
    today = date(2026, 9, 10)
    dates = {today, today - timedelta(days=2)}  # yesterday missing
    assert compute_streak(dates, today=today) == 1


def test_today_not_done_yet_still_counts_yesterday_streak():
    """Today isn't marked done yet (owner just hasn't gotten to it) -
    the streak up to yesterday should still show, not reset to 0
    prematurely."""
    today = date(2026, 9, 10)
    dates = {today - timedelta(days=1), today - timedelta(days=2)}
    assert compute_streak(dates, today=today) == 2


def test_missed_yesterday_and_today_is_zero():
    today = date(2026, 9, 10)
    dates = {today - timedelta(days=3)}
    assert compute_streak(dates, today=today) == 0
