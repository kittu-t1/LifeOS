"""
Goal service.

Owns the one rule that matters most in this phase: creating a Goal always,
atomically, creates its Workspace. No route handler or other code path
should create a Goal without going through this function - that's what
keeps "every Goal owns exactly one Workspace" true everywhere, not just
in the happy path.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.models.workspace import Workspace
from app.schemas.goal import GoalCreate


def create_goal(db: Session, *, user_id: uuid.UUID, data: GoalCreate) -> Goal:
    goal = Goal(user_id=user_id, title=data.title, description=data.description)
    db.add(goal)
    db.flush()  # assigns goal.id without committing yet

    workspace = Workspace(goal_id=goal.id)
    db.add(workspace)

    db.commit()
    db.refresh(goal)
    return goal


def list_goals(db: Session, *, user_id: uuid.UUID) -> list[Goal]:
    return db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.created_at.desc()).all()


def get_goal(db: Session, *, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal | None:
    return db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
