"""Request/response schemas for the Recurring Task system (Habits)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.habit import HabitOccurrenceStatus, HabitStatus, RecurrenceType


class HabitCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    recurrence_type: RecurrenceType
    # Validated loosely (see app/services/recurrence.py for the shape
    # each recurrence_type actually reads) rather than a strict per-type
    # schema - a WEEKLY habit with a missing/empty days_of_week just
    # produces zero occurrences rather than a 422, which is forgiving
    # enough for a first pass and easy to tighten later if it causes
    # real confusion.
    recurrence_config: dict[str, Any] = Field(default_factory=dict)
    estimated_minutes: int | None = Field(default=None, ge=1)
    start_date: date
    end_date: date | None = None


class HabitUpdate(BaseModel):
    """All fields optional - only what's provided gets changed (see
    habit_service.update_habit). Pause/resume are separate endpoints,
    not part of this schema, since they're a distinct, simpler action
    that shouldn't require resending the whole habit."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    recurrence_type: RecurrenceType | None = None
    recurrence_config: dict[str, Any] | None = None
    estimated_minutes: int | None = Field(default=None, ge=1)
    start_date: date | None = None
    end_date: date | None = None


class HabitRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    recurrence_type: RecurrenceType
    recurrence_config: dict[str, Any]
    estimated_minutes: int | None
    start_date: date
    end_date: date | None
    status: HabitStatus
    created_at: datetime
    updated_at: datetime


class HabitOccurrenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    habit_id: uuid.UUID
    occurrence_date: date
    status: HabitOccurrenceStatus
    completed_at: datetime | None
    created_at: datetime


class UpdateOccurrenceStatusRequest(BaseModel):
    status: HabitOccurrenceStatus
