"""Consecutive-day streak for a daily habit. A missed day breaks it - no
partial credit, no invented grace period, since that would misrepresent
what actually happened (spec Section 54: no fake precision)."""

from datetime import date, timedelta


def compute_streak(completed_dates: set[date], today: date | None = None) -> int:
    """`completed_dates`: the set of dates the habit was marked done.
    Counts backward from today (or yesterday, if today isn't done yet -
    an in-progress day shouldn't break a streak that's still alive)."""
    today = today or date.today()

    if today in completed_dates:
        cursor = today
    elif (today - timedelta(days=1)) in completed_dates:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in completed_dates:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
