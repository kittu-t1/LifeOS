"""
Habit + HabitOccurrence models - the Recurring Task system.

A Habit is a recurrence *rule* (title, cadence, optional start/end date,
active/paused). HabitOccurrence is one concrete, completable instance of
that rule on a specific calendar date - the same "definition vs
instance" split already established for Plan -> PlanTask (see
app/models/plan_task.py), applied here because it solves the identical
problem: "mark today's occurrence done" needs a real row with its own id
and status, while the recurrence rule itself (how often, until when)
shouldn't be duplicated per-occurrence.

Habits are user-scoped, not Goal-scoped - "workout every morning" is a
fixed life commitment that exists independent of any single Goal's plan
(see app/services/planner_service.py and
app/services/adaptive_planning_service.py for how the Planner and
Adaptive Planning Engine both treat active habits as context to plan
around, never as content either one generates, deletes, or duplicates).

Deliberately isolated from planner/plan_task models (no foreign keys in
either direction) - per the sprint spec's own instruction to keep
recurrence logic reusable later by Calendar Sync, Notifications, streak
tracking, and habit analytics without those features having to touch
Plan/PlanTask at all.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class RecurrenceType(str, enum.Enum):
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_INTERVAL = "custom_interval"


class HabitStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"


class HabitOccurrenceStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class Habit(Base):
    __tablename__ = "habits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    recurrence_type: Mapped[RecurrenceType] = mapped_column(
        Enum(RecurrenceType, name="habit_recurrence_type", native_enum=False)
    )
    # Shape depends on recurrence_type - see app/services/recurrence.py:
    #   DAILY / WEEKDAYS: {} (nothing to configure)
    #   WEEKLY:           {"days_of_week": [0, 2, 4]}  (0=Monday..6=Sunday)
    #   MONTHLY:          {"day_of_month": 15}
    #   CUSTOM_INTERVAL:  {"interval_days": 3}
    recurrence_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Optional - lets the Planner/Adaptive Planning Engine account for
    # this habit's time cost (see app/services/habit_service.py's
    # weekly_load_minutes) without forcing every habit to have one.
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[HabitStatus] = mapped_column(
        Enum(HabitStatus, name="habit_status", native_enum=False), default=HabitStatus.ACTIVE
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="habits")
    occurrences: Mapped[list[HabitOccurrence]] = relationship(
        back_populates="habit",
        cascade="all, delete-orphan",
        order_by="HabitOccurrence.occurrence_date",
    )


class HabitOccurrence(Base):
    __tablename__ = "habit_occurrences"
    __table_args__ = (
        # The actual "never duplicate occurrences" guarantee (see
        # app/services/habit_service.py:sync_occurrences) - enforced at
        # the database level, not just by application code being
        # careful.
        UniqueConstraint("habit_id", "occurrence_date", name="uq_habit_occurrence_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    habit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"), index=True
    )

    occurrence_date: Mapped[date] = mapped_column(Date)
    status: Mapped[HabitOccurrenceStatus] = mapped_column(
        Enum(HabitOccurrenceStatus, name="habit_occurrence_status", native_enum=False),
        default=HabitOccurrenceStatus.PENDING,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    habit: Mapped[Habit] = relationship(back_populates="occurrences")
