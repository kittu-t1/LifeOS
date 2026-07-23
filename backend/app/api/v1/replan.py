"""
Adaptive Planning Engine routes.

Nested under `/planner/plans/{plan_id}/replan...`, matching the existing
convention for operating on a Plan that already exists (see
app/api/v1/planner.py's docstring) rather than the sprint spec's literal
`POST /planner/replan` with an id in the body - same reasoning already
applied to `/planner/plans/{plan_id}/regenerate`.

Two calls, matching adaptive_planning_service's propose/apply split:
  - POST .../replan computes and returns a proposal. Nothing is saved.
  - POST .../replan/accept takes that same proposal straight back
    (the client re-sends what it was just given) and actually applies
    it. The server never caches a "pending proposal" between the two
    calls - there's nothing to expire or clean up, and it means
    accept is just "trust what I already showed the user," which is
    exactly the review-before-write flow the spec asked for.

GET .../replan/history lists past accepted replans (see
app/models/plan_replan_event.py) - the "History" the spec asked for.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.memory.repositories.memory_repository import SqlAlchemyMemoryRepository
from app.memory.services.memory_service import MemoryService
from app.models.user import User
from app.schemas.replan import (
    ReplanAcceptRequest,
    ReplanEventRead,
    ReplanProposalRead,
    TaskAssignmentSchema,
    TaskRescheduleRead,
)
from app.schemas.task import PlanTasksResponse
from app.services import adaptive_planning_service, habit_service, planner_service, task_service
from app.services.adaptive_planning_service import ReplanProposal, TaskAssignment, TaskReschedule

router = APIRouter(prefix="/planner", tags=["replan"])
logger = logging.getLogger(__name__)


def _get_owned_plan(db: Session, *, user: User, plan_id: uuid.UUID):
    plan = planner_service.get_owned_plan(db, user_id=user.id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


@router.post("/plans/{plan_id}/replan", response_model=ReplanProposalRead)
def propose_replan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReplanProposalRead:
    plan = _get_owned_plan(db, user=current_user, plan_id=plan_id)
    tasks = task_service.get_tasks_for_plan(db, plan_id=plan.id)
    active_habits = habit_service.list_active_habits(db, user_id=current_user.id)

    # Memory Engine integration point (see app/memory/) - same "log, don't
    # inject" scope as planner_service._log_relevant_memories: replanning
    # doesn't change its scheduling behavior based on memories yet, this
    # just surfaces what a future version would have available.
    memory_service = MemoryService(SqlAlchemyMemoryRepository(db))
    relevant_memories = memory_service.get_relevant_memories(user_id=current_user.id)
    logger.info(
        "planner.replan: %d memories available as context (not yet used in scheduling): %s",
        len(relevant_memories),
        [f"{m.category.value}:{m.key}" for m in relevant_memories],
    )

    proposal = adaptive_planning_service.propose_replan(plan, tasks, active_habits=active_habits)
    return ReplanProposalRead(
        plan_id=proposal.plan_id,
        reason=proposal.reason,
        changes=[
            TaskRescheduleRead(
                task_id=c.task_id,
                title=c.title,
                estimated_minutes=c.estimated_minutes,
                previous_week=c.previous_week,
                new_week=c.new_week,
            )
            for c in proposal.changes
        ],
        remaining_effort_minutes=proposal.remaining_effort_minutes,
        new_completion_estimate=proposal.new_completion_estimate,
        deadline_at_risk=proposal.deadline_at_risk,
        task_assignments=[
            TaskAssignmentSchema(
                task_id=a.task_id, week_number=a.week_number, day_number=a.day_number
            )
            for a in proposal.task_assignments
        ],
    )


@router.post("/plans/{plan_id}/replan/accept", response_model=PlanTasksResponse)
def accept_replan(
    plan_id: uuid.UUID,
    payload: ReplanAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanTasksResponse:
    plan = _get_owned_plan(db, user=current_user, plan_id=plan_id)

    proposal = ReplanProposal(
        plan_id=plan.id,
        reason=payload.reason,
        changes=[
            TaskReschedule(
                task_id=c.task_id,
                title=c.title,
                estimated_minutes=c.estimated_minutes,
                previous_week=c.previous_week,
                new_week=c.new_week,
            )
            for c in payload.changes
        ],
        remaining_effort_minutes=payload.remaining_effort_minutes,
        new_completion_estimate=payload.new_completion_estimate,
        deadline_at_risk=payload.deadline_at_risk,
        task_assignments=[
            TaskAssignment(task_id=a.task_id, week_number=a.week_number, day_number=a.day_number)
            for a in payload.task_assignments
        ],
    )
    # Returns the updated task list directly (same shape as GET
    # .../plans/{id}/tasks) so the frontend can refresh its checklist
    # from this one response instead of needing a second round trip.
    # GET .../replan/history is the separate call for anyone who
    # actually wants the audit log.
    updated_tasks = adaptive_planning_service.apply_replan(db, plan=plan, proposal=proposal)
    return task_service.build_tasks_response(updated_tasks)


@router.get("/plans/{plan_id}/replan/history", response_model=list[ReplanEventRead])
def get_replan_history(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ReplanEventRead]:
    plan = _get_owned_plan(db, user=current_user, plan_id=plan_id)
    return [
        ReplanEventRead.model_validate(event)
        for event in adaptive_planning_service.get_replan_history(db, plan_id=plan.id)
    ]
