"""Daily "did I do X today" trackers - simpler than the goal/task model,
one row per (habit, date). Owner request 2026-09-08: a visible reminder for
whether the French AI tutor session happened today. Streak added 2026-09-10.
"""

from datetime import date

import streamlit as st

from engine.common.db import get_connection
from engine.habits.streak import compute_streak


def render_daily_habit(habit_key: str, label: str) -> None:
    today = date.today().isoformat()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT completed FROM daily_habits WHERE habit_key = :k AND date = :d",
            {"k": habit_key, "d": today},
        ).fetchone()
        completed_dates = {
            date.fromisoformat(r["date"])
            for r in conn.execute(
                "SELECT date FROM daily_habits WHERE habit_key = :k AND completed = :completed",
                {"k": habit_key, "completed": True},
            ).fetchall()
        }
    finally:
        conn.close()

    done_today = bool(row["completed"]) if row else False
    streak = compute_streak(completed_dates)

    c1, c2 = st.columns([4, 1])
    streak_text = f" · {streak}-day streak" if streak > 0 else ""
    if done_today:
        c1.markdown(f"✅ **{label}** — done today{streak_text}")
    else:
        c1.markdown(f"⏳ **{label}** — not yet today{streak_text}")

    checked = c2.checkbox("Done", value=done_today, key=f"habit_{habit_key}_{today}", label_visibility="collapsed")

    if checked != done_today:
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO daily_habits (id, habit_key, habit_label, date, completed) "
                "VALUES (:id, :key, :label, :date, :completed) "
                "ON CONFLICT(habit_key, date) DO UPDATE SET completed = excluded.completed",
                {
                    "id": f"{habit_key}-{today}",
                    "key": habit_key,
                    "label": label,
                    "date": today,
                    "completed": checked,
                },
            )
            conn.commit()
        finally:
            conn.close()
        st.rerun()
