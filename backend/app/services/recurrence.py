"""
Recurrence engine - pure date math for turning a Habit's recurrence rule
into a concrete list of occurrence dates over a range.

No DB session, no FastAPI, no knowledge of Plan/PlanTask - deliberately
isolated (per the Recurring Task System spec) so it can be reused later
by Calendar Sync, Notifications, streak tracking, or habit analytics
without any of them having to touch habit persistence or planner logic.
Every function here is a pure function of its arguments.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.models.habit import Habit, HabitStatus, RecurrenceType


def generate_occurrence_dates(habit: Habit, *, range_start: date, range_end: date) -> list[date]:
    """All dates in [range_start, range_end] (inclusive) that `habit`
    recurs on, clipped to the habit's own start_date/end_date. Returns []
    for a paused habit - callers that want "what this would look like if
    active" should check status themselves before calling, since silently
    ignoring pause here would make it too easy to accidentally generate
    occurrences for something the user explicitly turned off."""
    if habit.status != HabitStatus.ACTIVE:
        return []

    window_start = max(range_start, habit.start_date)
    window_end = range_end if habit.end_date is None else min(range_end, habit.end_date)
    if window_start > window_end:
        return []

    if habit.recurrence_type == RecurrenceType.DAILY:
        return _every_day(window_start, window_end)

    if habit.recurrence_type == RecurrenceType.WEEKDAYS:
        return [d for d in _every_day(window_start, window_end) if d.weekday() < 5]

    if habit.recurrence_type == RecurrenceType.WEEKLY:
        days_of_week = set(habit.recurrence_config.get("days_of_week", []))
        return [d for d in _every_day(window_start, window_end) if d.weekday() in days_of_week]

    if habit.recurrence_type == RecurrenceType.MONTHLY:
        # Falls back to the habit's own start-date day-of-month if none
        # was explicitly configured ("repeat on the day it started").
        # Months shorter than day_of_month (e.g. day 31 in February)
        # simply have no occurrence that month - a deliberate, simple
        # rule rather than "roll over to the last day of the month".
        day_of_month = habit.recurrence_config.get("day_of_month", habit.start_date.day)
        return [d for d in _every_day(window_start, window_end) if d.day == day_of_month]

    if habit.recurrence_type == RecurrenceType.CUSTOM_INTERVAL:
        interval_days = max(1, habit.recurrence_config.get("interval_days", 1))
        return [
            d
            for d in _every_day(window_start, window_end)
            if (d - habit.start_date).days % interval_days == 0
        ]

    raise ValueError(f"Unknown recurrence_type: {habit.recurrence_type!r}")


def _every_day(start: date, end: date) -> list[date]:
    return [start + timedelta(days=i) for i in range((end - start).days + 1)]
