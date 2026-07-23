"""
Execution Engine routes - PlanTask completion tracking and progress.

Deliberately its own router/file, not folded into planner.py, mirroring
the service-layer split (planner_service generates; task_service and
progress_service track/calculate) - see those modules' docstrings for
why. Two resource roots, matching the sprint's URL shapes:
  - `/plans/{plan_id}/tasks` and `/plans/{plan_id}/progress` - reading a
    plan's execution state.
  - `/tasks/{task_id}` - updating one task's status.

No prefix on the router itself (both roots are set per-route) so this
file can own paths that don't share a common parent, the same reasoning
`/planner/goals/...` vs `/planner/plans/...` already established for
planner.py's two resource roots.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.task import PlanTaskRead, PlanTasksResponse, ProgressRead, UpdateTaskStatusRequest
from app.services import planner_service, progress_service, task_service

router = APIRouter(tags=["execution"])


def _get_owned_plan(db: Session, *, user: User, plan_id: uuid.UUID):
    # Reuses planner_service's ownership query rather than duplicating an
    # identical join here - that function is plain data-access
    # infrastructure ("find a Plan this user owns"), not planning logic,
    # so sharing it doesn't blur the Planner/Execution split.
    plan = planner_service.get_owned_plan(db, user_id=user.id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.get("/plans/{plan_id}/tasks", response_model=PlanTasksResponse)
def get_plan_tasks(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanTasksResponse:
    _get_owned_plan(db, user=current_user, plan_id=plan_id)
    tasks = task_service.get_tasks_for_plan(db, plan_id=plan_id)
    return task_service.build_tasks_response(tasks)


@router.get("/plans/{plan_id}/progress", response_model=ProgressRead)
def get_plan_progress(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProgressRead:
    _get_owned_plan(db, user=current_user, plan_id=plan_id)
    summary = progress_service.calculate_progress(db, plan_id=plan_id)
    return ProgressRead(
        completed=summary.completed,
        total=summary.total,
        remaining=summary.remaining,
        percentage=summary.percentage,
    )


@router.patch("/tasks/{task_id}", response_model=PlanTaskRead)
def update_task_status(
    task_id: uuid.UUID,
    payload: UpdateTaskStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanTaskRead:
    task = task_service.get_owned_task(db, user_id=current_user.id, task_id=task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    updated = task_service.set_task_status(db, task=task, status=payload.status)
    return PlanTaskRead.model_validate(updated)
