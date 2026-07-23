"""
PlanTask model - the LifeOS Execution Engine's core entity.

Until now, a Plan's weekly actions only existed as read-only strings
inside Plan.weekly_plan (JSON). PlanTask promotes each of those actions
into its own row with an id and a status, which is what makes "did the
user actually do this" a question the app can answer - everything listed
in the Execution Engine sprint (progress tracking, Today's Focus, and
eventually calendar scheduling/reminders/adaptive planning) depends on
that being true.

Deliberately minimal: status is only pending/completed for now - no
priority, recurrence, subtasks, labels, dependencies, or attachments.
Those are real future features, not omissions; adding them later needs a
migration either way, so there's no cost to leaving them out until
they're actually driven by a real requirement.

Ownership rule (see app/services/planner_service.py's regenerate_plan):
every PlanTask belongs to exactly one Plan and is wholesale replaced
whenever that Plan regenerates - same "AI output is a full new draft,
not a patch" reasoning Milestone already follows. milestone_id is
nullable and NOT populated yet (see app/services/planner_service.py's
_build_tasks) - the planner's weekly_plan and milestones are still
generated as separate, unlinked lists; forcing a fuzzy match between
them isn't something this phase asked for.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.plan import Plan


class PlanTaskStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"


class PlanTask(Base):
    __tablename__ = "plan_tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )
    # Nullable and unpopulated for now - see module docstring.
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("milestones.id", ondelete="SET NULL"), nullable=True
    )

    week_number: Mapped[int] = mapped_column(Integer)
    # Day-level assignment isn't produced by the planner yet (see
    # app/planner/prompts.py) - Today's Focus falls back to "remaining
    # tasks in the current week" until this is populated (see
    # app/services/task_service.py).
    day_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # 0-based position across the whole plan (not just within a week) -
    # same `order`-by-index convention as Milestone.order, named
    # `display_order` per this phase's field list.
    display_order: Mapped[int] = mapped_column(Integer)

    status: Mapped[PlanTaskStatus] = mapped_column(
        Enum(PlanTaskStatus, name="plan_task_status", native_enum=False),
        default=PlanTaskStatus.PENDING,
    )
    # Set/cleared together with `status` (see task_service.set_task_status)
    # - never touched by the planner, only by execution.
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    plan: Mapped[Plan] = relationship(back_populates="tasks")
