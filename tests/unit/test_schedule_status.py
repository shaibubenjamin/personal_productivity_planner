from datetime import date

from engine.goals.schedule_status import ScheduleStatus, assess_schedule


class FakeTask(dict):
    """Lets tests use dict literals while goal_card.py uses sqlite3.Row
    (both support t["field"] access, which is all assess_schedule needs)."""


def test_no_tasks():
    assert assess_schedule([]) == (ScheduleStatus.NO_TASKS, [])


def test_no_deadlines_set():
    tasks = [FakeTask(status="not_started", deadline=None)]
    status, overdue = assess_schedule(tasks)
    assert status == ScheduleStatus.NO_DEADLINES
    assert overdue == []


def test_on_course_when_deadline_in_future():
    tasks = [FakeTask(status="not_started", deadline="2099-01-01")]
    status, overdue = assess_schedule(tasks, today=date(2026, 1, 1))
    assert status == ScheduleStatus.ON_COURSE


def test_on_course_when_overdue_but_done():
    tasks = [FakeTask(status="done", deadline="2020-01-01")]
    status, overdue = assess_schedule(tasks, today=date(2026, 1, 1))
    assert status == ScheduleStatus.ON_COURSE


def test_behind_when_deadline_passed_and_not_done():
    tasks = [
        FakeTask(status="not_started", deadline="2020-01-01"),
        FakeTask(status="done", deadline="2099-01-01"),
    ]
    status, overdue = assess_schedule(tasks, today=date(2026, 1, 1))
    assert status == ScheduleStatus.BEHIND
    assert len(overdue) == 1
