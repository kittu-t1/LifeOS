"""
Habit routes - CRUD, pause/resume, and occurrence management for the
Recurring Task system.

Habits are user-scoped (see app/models/habit.py), so unlike goals/plans
there's no goal_id/plan_id in these paths at all - every route resolves
ownership straight from the current user. `sync_occurrences` is called
on every read that returns occurrences, not just on create/resume, so
the "next 30 days" window is always topped up whenever the UI actually
looks at it rather than depending on a background job existing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.habit import (
    HabitCreate,
    HabitOccurrenceRead,
    HabitRead,
    HabitUpdate,
    UpdateOccurrenceStatusRequest,
)
from app.services import habit_service

router = APIRouter(prefix="/habits", tags=["habits"])

OCCURRENCE_LIST_WINDOW_DAYS = 30


def _get_owned_habit(db: Session, *, user: User, habit_id: uuid.UUID):
    habit = habit_service.get_owned_habit(db, user_id=user.id, habit_id=habit_id)
    if habit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    return habit


@router.post("", response_model=HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(
    payload: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HabitRead:
    habit = habit_service.create_habit(db, user_id=current_user.id, data=payload)
    return HabitRead.model_validate(habit)


@router.get("", response_model=list[HabitRead])
def list_habits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HabitRead]:
    return [
        HabitRead.model_validate(h) for h in habit_service.list_habits(db, user_id=current_user.id)
    ]


@router.get("/{habit_id}", response_model=HabitRead)
def get_habit(
    habit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HabitRead:
    habit = _get_owned_habit(db, user=current_user, habit_id=habit_id)
    return HabitRead.model_validate(habit)


@router.patch("/{habit_id}", response_model=HabitRead)
def update_habit(
    habit_id: uuid.UUID,
    payload: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HabitRead:
    habit = _get_owned_habit(db, user=current_user, habit_id=habit_id)
    updated = habit_service.update_habit(db, habit=habit, data=payload)
    return HabitRead.model_validate(updated)


@router.post("/{habit_id}/pause", response_model=HabitRead)
def pause_habit(
    habit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HabitRead:
    habit = _get_owned_habit(db, user=current_user, habit_id=habit_id)
    return HabitRead.model_validate(habit_service.pause_habit(db, habit=habit))


@router.post("/{habit_id}/resume", response_model=HabitRead)
def resume_habit(
    habit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HabitRead:
    habit = _get_owned_habit(db, user=current_user, habit_id=habit_id)
    return HabitRead.model_validate(habit_service.resume_habit(db, habit=habit))


@router.get("/{habit_id}/occurrences", response_model=list[HabitOccurrenceRead])
def list_occurrences(
    habit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[HabitOccurrenceRead]:
    """Upcoming (and recent past) occurrences for one habit - a fixed
    +/- window around today rather than accepting arbitrary date range
    query params, since "view upcoming occurrences" (the spec's own
    wording) doesn't call for open-ended historical browsing yet."""
    habit = _get_owned_habit(db, user=current_user, habit_id=habit_id)
    habit_service.sync_occurrences(db, habit=habit)

    today = datetime.now(timezone.utc).date()
    occurrences = habit_service.list_occurrences(
        db,
        habit_id=habit.id,
        from_date=today - timedelta(days=7),
        to_date=today + timedelta(days=OCCURRENCE_LIST_WINDOW_DAYS),
    )
    return [HabitOccurrenceRead.model_validate(o) for o in occurrences]


@router.patch("/occurrences/{occurrence_id}", response_model=HabitOccurrenceRead)
def update_occurrence_status(
    occurrence_id: uuid.UUID,
    payload: UpdateOccurrenceStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HabitOccurrenceRead:
    occurrence = habit_service.get_owned_occurrence(
        db, user_id=current_user.id, occurrence_id=occurrence_id
    )
    if occurrence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Occurrence not found")
    updated = habit_service.set_occurrence_status(db, occurrence=occurrence, status=payload.status)
    return HabitOccurrenceRead.model_validate(updated)
