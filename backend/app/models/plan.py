"""
Plan and Milestone models.

A Plan is a Goal's one AI-generated execution roadmap (mission, estimated
duration, timeline, weekly plan) - see app/planner/ for the logic that
produces one and app/services/planner_service.py for how it gets
persisted. As of the Planner Productization phase this is a strict
one-to-one with Goal (goal_id is unique): "regenerating" a plan
(app/services/planner_service.regenerate_plan) updates this same row in
place - new mission/milestones/weekly_plan/timeline, bumped updated_at -
rather than creating a second Plan for the goal. History of every
attempt (including failed ones) still exists, just at the PlannerRun
level (app/models/planner_run.py) instead of via duplicate Plan rows -
that split reads more naturally: Plan is "the current roadmap," PlannerRun
is "the audit log of every attempt to produce one."

Milestone is a Plan's ordered list of major steps, stored as its own
table (not JSON) because the UI needs to render, count, and potentially
link tasks to individual milestones later - the same reasoning JSON
columns on Plan (timeline, weekly_plan) don't need to meet, since nothing
addresses "week 3" or "timeline entry 2" individually today. Regenerating
replaces a Plan's milestones wholesale (old ones deleted via cascade, new
ones inserted) rather than diffing/updating individual rows - the AI
output is treated as a full new draft each time, not a patch.

As of the Execution Engine phase, weekly_plan's `tasks` are ALSO
promoted into their own table - see app/models/plan_task.py. weekly_plan
(JSON) is kept as-is for its `focus` text per week (still genuinely
read-only planner content) and as a lightweight historical record, but
PlanTask is the source of truth for anything execution needs: status,
completion, progress. The two are linked only by week_number, not a
foreign key - see planner_service._build_tasks.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.goal import Goal
    from app.models.plan_replan_event import PlanReplanEvent
    from app.models.plan_task import PlanTask


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), unique=True, index=True
    )

    mission: Mapped[str] = mapped_column(Text)
    estimated_duration: Mapped[str] = mapped_column(String(100))

    # Free-form structured data straight from the validated LLM output
    # (see app/schemas/planner.py:PlannerLLMOutput). `timeline` still has
    # no reason to be its own table (nothing addresses "timeline entry 2"
    # individually). `weekly_plan.tasks` is now duplicated into PlanTask
    # rows on save (see planner_service._build_tasks) - this JSON copy is
    # historical/display-only past that point, not the execution source
    # of truth.
    #   timeline: list[str]
    #   weekly_plan: list[{"week": int, "focus": str, "tasks": list[TaskItem]}]
    #     where TaskItem = {"title": str, "description": str, "estimated_minutes": int | None}
    timeline: Mapped[list[Any]] = mapped_column(JSON)
    weekly_plan: Mapped[list[Any]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    # Bumped on every regenerate (see planner_service.regenerate_plan) -
    # the signal for "this roadmap changed since you last looked," now
    # that regenerating updates this row instead of creating a new one.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    goal: Mapped[Goal] = relationship(back_populates="plan")
    milestones: Mapped[list[Milestone]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="Milestone.order",
    )
    tasks: Mapped[list[PlanTask]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanTask.display_order",
    )
    # Audit trail of accepted replans (see
    # app/services/adaptive_planning_service.py) - unlike milestones/tasks,
    # never wholesale-replaced or deleted on regenerate; it's history, not
    # current state.
    replan_events: Mapped[list[PlanReplanEvent]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanReplanEvent.created_at.desc()",
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 0-based position within the plan's milestone list - `order` (not
    # `position`) to match the DB design doc; SQLAlchemy quotes it
    # automatically since it's a SQL reserved word.
    order: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    plan: Mapped[Plan] = relationship(back_populates="milestones")
