"""
Task service - the Execution Engine's tracking layer.

Owns exactly one responsibility: reading PlanTask rows and changing
their status. It never generates tasks (that's planner_service's job -
see PlanTask creation in generate_plan/regenerate_plan) and never
calculates progress from them (that's progress_service's job). Keeping
these three modules separate is a deliberate architecture rule for this
phase: Planner generates, Execution tracks, Progress calculates.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.models.plan import Plan
from app.models.plan_task import PlanTask, PlanTaskStatus
from app.schemas.task import PlanTaskRead, PlanTasksResponse, WeekTasksGroup


def get_tasks_for_plan(db: Session, *, plan_id: uuid.UUID) -> list[PlanTask]:
    """Ordered the same way the plan's checklist should read: week first,
    then each week's own display_order."""
    return (
        db.query(PlanTask)
        .filter(PlanTask.plan_id == plan_id)
        .order_by(PlanTask.week_number, PlanTask.display_order)
        .all()
    )


def get_owned_task(db: Session, *, user_id: uuid.UUID, task_id: uuid.UUID) -> PlanTask | None:
    """Fetches a PlanTask by its own id, scoped to the requesting user via
    a join through its Plan to its Goal - same not-fetched-then-checked
    idiom as goal_service.get_goal/planner_service.get_owned_plan."""
    return (
        db.query(PlanTask)
        .join(Plan, PlanTask.plan_id == Plan.id)
        .join(Goal, Plan.goal_id == Goal.id)
        .filter(PlanTask.id == task_id, Goal.user_id == user_id)
        .first()
    )


def set_task_status(db: Session, *, task: PlanTask, status: PlanTaskStatus) -> PlanTask:
    """The only place completed_at gets written - kept in lockstep with
    status here so nothing can set one without the other (e.g. a task
    marked pending again always has completed_at cleared, not stale)."""
    task.status = status
    task.completed_at = datetime.now(timezone.utc) if status == PlanTaskStatus.COMPLETED else None
    db.commit()
    db.refresh(task)
    return task


def build_tasks_response(tasks: list[PlanTask]) -> PlanTasksResponse:
    """Groups an already week-ordered task list (see get_tasks_for_plan)
    into the API's {weeks: [{week_number, tasks}]} shape. Shared by every
    endpoint that returns a plan's task checklist (see
    app/api/v1/execution.py and app/api/v1/replan.py) so the grouping
    logic itself only lives in one place - the Adaptive Planning Engine
    sprint's "no duplicated scheduling logic" rule applies here too, even
    though this particular bit predates that sprint."""
    weeks: list[WeekTasksGroup] = []
    for task in tasks:
        if not weeks or weeks[-1].week_number != task.week_number:
            weeks.append(WeekTasksGroup(week_number=task.week_number, tasks=[]))
        weeks[-1].tasks.append(PlanTaskRead.model_validate(task))
    return PlanTasksResponse(weeks=weeks)
