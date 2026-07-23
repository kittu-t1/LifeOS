"""
Planner routes - thin handlers only, same pattern as goals.py/workspaces.py.

Two resource shapes:
  - `/planner/goals/{goal_id}/...` - creating a Plan (POST generate) and
    checking whether one exists yet (GET), scoped by the goal it belongs
    to. Nested under goal_id rather than accepting a free-text goal in
    the body, per the note in app/schemas/planner.py: this app already
    requires a Goal to exist before the Planner tab is reachable.
  - `/planner/plans/{plan_id}/...` - operating on a Plan that already
    exists (GET a specific plan, POST regenerate). These don't need a
    goal_id at all; get_owned_plan resolves ownership via a join.

Provider/output/persistence failures are translated into specific,
honest HTTP statuses by _map_planner_error rather than a blanket 500 -
see the spec's Error Handling section (LLM failures, invalid JSON,
timeout, DB save failures should all reach the user as understandable
messages, not a stack trace).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.planner.llm.base import LLMProviderError, LLMTimeoutError
from app.planner.llm.factory import get_llm_provider
from app.planner.parser import PlannerOutputError
from app.schemas.planner import PlannerGenerateRequest, PlanRead, RegeneratePlanRequest
from app.services import goal_service, planner_service
from app.services.planner_service import PlanAlreadyExistsError, PlanPersistenceError

router = APIRouter(prefix="/planner", tags=["planner"])


def _get_owned_goal(db: Session, *, user: User, goal_id: uuid.UUID):
    goal = goal_service.get_goal(db, user_id=user.id, goal_id=goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


def _get_owned_plan(db: Session, *, user: User, plan_id: uuid.UUID):
    plan = planner_service.get_owned_plan(db, user_id=user.id, plan_id=plan_id)
    if plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")
    return plan


def _map_planner_error(exc: Exception) -> HTTPException:
    """Shared exception -> HTTPException mapping for generate_plan and
    regenerate_plan, both of which can fail the same three ways (LLM
    provider trouble, an unparseable/invalid model response, or a DB
    write failure) despite doing different work otherwise."""
    if isinstance(exc, LLMTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The AI planner took too long to respond. Please try again.",
        )
    if isinstance(exc, PlanPersistenceError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Couldn't save your plan. Please try again.",
        )
    if isinstance(exc, PlannerOutputError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI planner returned an unexpected response. Please try again.",
        )
    # Remaining LLMProviderError subclasses (auth, rate limit, network, etc.)
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="The AI planner is temporarily unavailable. Please try again in a moment.",
    )


@router.post(
    "/goals/{goal_id}/generate", response_model=PlanRead, status_code=status.HTTP_201_CREATED
)
def generate_plan(
    goal_id: uuid.UUID,
    payload: PlannerGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm_provider=Depends(get_llm_provider),
) -> PlanRead:
    goal = _get_owned_goal(db, user=current_user, goal_id=goal_id)

    try:
        result = planner_service.generate_plan(
            db, goal=goal, data=payload, llm_provider=llm_provider
        )
    except PlanAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (LLMProviderError, PlannerOutputError, PlanPersistenceError) as exc:
        raise _map_planner_error(exc) from exc

    return PlanRead.model_validate(result.plan).model_copy(
        update={
            "memories_used": result.memories_used,
            "suggested_memory": result.suggested_memory,
        }
    )


@router.get("/goals/{goal_id}", response_model=PlanRead)
def get_plan_for_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanRead:
    goal = _get_owned_goal(db, user=current_user, goal_id=goal_id)
    plan = planner_service.get_plan_for_goal(db, goal_id=goal.id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No plan generated for this goal yet"
        )
    return PlanRead.model_validate(plan)


@router.get("/plans/{plan_id}", response_model=PlanRead)
def get_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanRead:
    plan = _get_owned_plan(db, user=current_user, plan_id=plan_id)
    return PlanRead.model_validate(plan)


@router.post("/plans/{plan_id}/regenerate", response_model=PlanRead)
def regenerate_plan(
    plan_id: uuid.UUID,
    payload: RegeneratePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm_provider=Depends(get_llm_provider),
) -> PlanRead:
    plan = _get_owned_plan(db, user=current_user, plan_id=plan_id)

    try:
        result = planner_service.regenerate_plan(
            db, plan=plan, adjustment=payload.adjustment, llm_provider=llm_provider
        )
    except (LLMProviderError, PlannerOutputError, PlanPersistenceError) as exc:
        raise _map_planner_error(exc) from exc

    return PlanRead.model_validate(result.plan).model_copy(
        update={
            "memories_used": result.memories_used,
            "suggested_memory": result.suggested_memory,
        }
    )
