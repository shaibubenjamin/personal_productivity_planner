"""Are we on course? Answers this per goal from its to-dos' deadlines
(owner request, 2026-09-09: "nothing is left open-ended, and on the
strength of that would we say we are on course"). Evidence-based like the
weekly-progress classifier - a goal is BEHIND because a dated to-do is
actually overdue, not from an invented velocity target.
"""

from datetime import date
from enum import Enum

from engine.common.dates import to_date


class ScheduleStatus(Enum):
    ON_COURSE = "ON_COURSE"
    BEHIND = "BEHIND"
    NO_DEADLINES = "NO_DEADLINES"
    NO_TASKS = "NO_TASKS"


def assess_schedule(tasks, today: date | None = None) -> tuple[ScheduleStatus, list]:
    """`tasks`: sequence of objects with `status` and `deadline` (ISO date
    string or None/empty). Returns (status, overdue_tasks)."""
    today = today or date.today()
    if not tasks:
        return ScheduleStatus.NO_TASKS, []

    dated = [t for t in tasks if t["deadline"]]
    if not dated:
        return ScheduleStatus.NO_DEADLINES, []

    overdue = [t for t in dated if t["status"] != "done" and to_date(t["deadline"]) < today]
    if overdue:
        return ScheduleStatus.BEHIND, overdue
    return ScheduleStatus.ON_COURSE, []
