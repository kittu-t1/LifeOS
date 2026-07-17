"""Goal routes - thin handlers only. All logic lives in goal_service."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalRead
from app.services import goal_service

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    """Creates a Goal. A Workspace is created automatically alongside it -
    see goal_service.create_goal."""
    goal = goal_service.create_goal(db, user_id=current_user.id, data=payload)
    return GoalRead.model_validate(goal)


@router.get("", response_model=list[GoalRead])
def list_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[GoalRead]:
    goals = goal_service.list_goals(db, user_id=current_user.id)
    return [GoalRead.model_validate(g) for g in goals]


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GoalRead:
    goal = goal_service.get_goal(db, user_id=current_user.id, goal_id=goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return GoalRead.model_validate(goal)
