"""
Habit service - CRUD + occurrence generation/completion for the
Recurring Task system (see app/models/habit.py, app/services/recurrence.py).

Habits are user-scoped, not Goal-scoped - "workout every morning" is a
fixed life commitment independent of which Goal is currently being
planned. That's exactly why the Planner and Adaptive Planning Engine
both treat active habits as context to plan *around* rather than content
either one generates or reschedules - see this module's
summarize_for_planner (consumed by planner_service's prompt building)
and weekly_load_minutes (consumed by adaptive_planning_service's
capacity calculation).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.habit import (
    Habit,
    HabitOccurrence,
    HabitOccurrenceStatus,
    HabitStatus,
    RecurrenceType,
)
from app.schemas.habit import HabitCreate, HabitUpdate
from app.services import recurrence

# How far ahead occurrences are kept generated - the spec's own example
# ("the next 30 days"). sync_occurrences tops this window up on every
# call rather than generating a fixed batch once, so a habit created
# today still has occurrences 30 days out next month too, as long as
# something calls sync_occurrences again (every read path here does).
OCCURRENCE_WINDOW_DAYS = 30


def create_habit(db: Session, *, user_id: uuid.UUID, data: HabitCreate) -> Habit:
    habit = Habit(
        user_id=user_id,
        title=data.title,
        description=data.description,
        recurrence_type=data.recurrence_type,
        recurrence_config=data.recurrence_config,
        estimated_minutes=data.estimated_minutes,
        start_date=data.start_date,
        end_date=data.end_date,
        status=HabitStatus.ACTIVE,
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    sync_occurrences(db, habit=habit)
    return habit


def list_habits(db: Session, *, user_id: uuid.UUID) -> list[Habit]:
    return db.query(Habit).filter(Habit.user_id == user_id).order_by(Habit.created_at.desc()).all()


def list_active_habits(db: Session, *, user_id: uuid.UUID) -> list[Habit]:
    """Used by the Planner/Adaptive Planning integrations - only ACTIVE
    habits are "fixed commitments" to plan around; a paused habit isn't
    currently happening, so it shouldn't constrain anything."""
    return (
        db.query(Habit)
        .filter(Habit.user_id == user_id, Habit.status == HabitStatus.ACTIVE)
        .order_by(Habit.created_at)
        .all()
    )


def get_owned_habit(db: Session, *, user_id: uuid.UUID, habit_id: uuid.UUID) -> Habit | None:
    return db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()


def update_habit(db: Session, *, habit: Habit, data: HabitUpdate) -> Habit:
    recurrence_changed = False
    if data.title is not None:
        habit.title = data.title
    if data.description is not None:
        habit.description = data.description
    if data.recurrence_type is not None and data.recurrence_type != habit.recurrence_type:
        habit.recurrence_type = data.recurrence_type
        recurrence_changed = True
    if data.recurrence_config is not None:
        habit.recurrence_config = data.recurrence_config
        recurrence_changed = True
    if data.estimated_minutes is not None:
        habit.estimated_minutes = data.estimated_minutes
    if data.start_date is not None and data.start_date != habit.start_date:
        habit.start_date = data.start_date
        recurrence_changed = True
    if data.end_date is not None and data.end_date != habit.end_date:
        habit.end_date = data.end_date
        recurrence_changed = True
    db.commit()
    db.refresh(habit)

    if recurrence_changed:
        # The schedule itself changed - top up the occurrence window
        # under the new rule rather than leaving stale future PENDING
        # occurrences generated under the old one lying around.
        _clear_future_pending_occurrences(db, habit=habit)
    sync_occurrences(db, habit=habit)
    return habit


def pause_habit(db: Session, *, habit: Habit) -> Habit:
    habit.status = HabitStatus.PAUSED
    db.commit()
    db.refresh(habit)
    return habit


def resume_habit(db: Session, *, habit: Habit) -> Habit:
    habit.status = HabitStatus.ACTIVE
    db.commit()
    db.refresh(habit)
    sync_occurrences(db, habit=habit)
    return habit


def sync_occurrences(db: Session, *, habit: Habit) -> None:
    """Idempotently tops up HabitOccurrence rows for the next
    OCCURRENCE_WINDOW_DAYS days. Safe to call on every read (not just
    create/resume) since it only ever inserts dates that don't already
    have a row - the actual "never duplicate occurrences" guarantee is
    the unique (habit_id, occurrence_date) constraint on the table
    itself (see app/models/habit.py); this is the write path that
    respects it. No-ops entirely for a paused habit."""
    if habit.status != HabitStatus.ACTIVE:
        return

    today = datetime.now(timezone.utc).date()
    window_end = today + timedelta(days=OCCURRENCE_WINDOW_DAYS)
    wanted_dates = set(
        recurrence.generate_occurrence_dates(habit, range_start=today, range_end=window_end)
    )
    if not wanted_dates:
        return

    existing_dates = {
        row.occurrence_date
        for row in db.query(HabitOccurrence.occurrence_date)
        .filter(
            HabitOccurrence.habit_id == habit.id,
            HabitOccurrence.occurrence_date.in_(wanted_dates),
        )
        .all()
    }
    missing_dates = wanted_dates - existing_dates
    for occurrence_date in missing_dates:
        db.add(HabitOccurrence(habit_id=habit.id, occurrence_date=occurrence_date))
    if missing_dates:
        db.commit()


def _clear_future_pending_occurrences(db: Session, *, habit: Habit) -> None:
    """Only called right before a recurrence-rule edit re-syncs. Removes
    not-yet-happened, still-PENDING occurrences so a changed schedule
    doesn't leave orphaned dates from the old rule sitting alongside new
    ones. Past and completed occurrences are never touched - editing a
    habit's schedule going forward shouldn't erase its history."""
    today = datetime.now(timezone.utc).date()
    db.query(HabitOccurrence).filter(
        HabitOccurrence.habit_id == habit.id,
        HabitOccurrence.occurrence_date >= today,
        HabitOccurrence.status == HabitOccurrenceStatus.PENDING,
    ).delete(synchronize_session=False)
    db.commit()


def list_occurrences(
    db: Session, *, habit_id: uuid.UUID, from_date: date, to_date: date
) -> list[HabitOccurrence]:
    return (
        db.query(HabitOccurrence)
        .filter(
            HabitOccurrence.habit_id == habit_id,
            HabitOccurrence.occurrence_date >= from_date,
            HabitOccurrence.occurrence_date <= to_date,
        )
        .order_by(HabitOccurrence.occurrence_date)
        .all()
    )


def get_owned_occurrence(
    db: Session, *, user_id: uuid.UUID, occurrence_id: uuid.UUID
) -> HabitOccurrence | None:
    return (
        db.query(HabitOccurrence)
        .join(Habit, HabitOccurrence.habit_id == Habit.id)
        .filter(HabitOccurrence.id == occurrence_id, Habit.user_id == user_id)
        .first()
    )


def set_occurrence_status(
    db: Session, *, occurrence: HabitOccurrence, status: HabitOccurrenceStatus
) -> HabitOccurrence:
    occurrence.status = status
    occurrence.completed_at = (
        datetime.now(timezone.utc) if status == HabitOccurrenceStatus.COMPLETED else None
    )
    db.commit()
    db.refresh(occurrence)
    return occurrence


# --- Planner / Adaptive Planning integration -----------------------------


def summarize_for_planner(habits: list[Habit]) -> list[str]:
    """Turns active habits into short human-readable lines for the
    Planner prompt (see app/planner/prompts.py's existing-commitments
    section) - e.g. "Workout - every day (~45 min)". Kept here, not in
    prompts.py, since it's about describing a Habit, not about prompt
    construction."""
    return [
        f"{habit.title} - {_describe_recurrence(habit)}"
        + (f" (~{habit.estimated_minutes} min)" if habit.estimated_minutes else "")
        for habit in habits
    ]


def weekly_load_minutes(habits: list[Habit], *, week_start: date) -> int:
    """Approximate total minutes active habits consume during the 7-day
    window starting at week_start - used by the Adaptive Planning Engine
    to shrink its redistribution budget (see
    adaptive_planning_service.propose_replan) so a replanned week doesn't
    assume all of it is free time when recurring commitments already
    claim part of it. Deliberately approximate (counts occurrences per
    week, not real time-of-day conflicts) since LifeOS has no
    time-of-day scheduling yet - see that module's docstring."""
    week_end = week_start + timedelta(days=6)
    total = 0
    for habit in habits:
        if habit.estimated_minutes is None:
            continue
        occurrence_dates = recurrence.generate_occurrence_dates(
            habit, range_start=week_start, range_end=week_end
        )
        total += len(occurrence_dates) * habit.estimated_minutes
    return total


def _describe_recurrence(habit: Habit) -> str:
    if habit.recurrence_type == RecurrenceType.DAILY:
        return "every day"
    if habit.recurrence_type == RecurrenceType.WEEKDAYS:
        return "every weekday"
    if habit.recurrence_type == RecurrenceType.WEEKLY:
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        days = sorted(d for d in habit.recurrence_config.get("days_of_week", []) if 0 <= d <= 6)
        return "every " + ", ".join(names[d] for d in days) if days else "weekly"
    if habit.recurrence_type == RecurrenceType.MONTHLY:
        day = habit.recurrence_config.get("day_of_month", habit.start_date.day)
        return f"monthly on day {day}"
    if habit.recurrence_type == RecurrenceType.CUSTOM_INTERVAL:
        interval = habit.recurrence_config.get("interval_days", 1)
        return f"every {interval} day(s)"
    return "recurring"
