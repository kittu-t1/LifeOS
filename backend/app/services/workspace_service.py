"""Workspace service - read-only today, since Workspaces are only ever
created as a side effect of goal_service.create_goal()."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.models.workspace import Workspace


def get_workspace(db: Session, *, user_id: uuid.UUID, workspace_id: uuid.UUID) -> Workspace | None:
    return (
        db.query(Workspace)
        .join(Goal, Goal.id == Workspace.goal_id)
        .filter(Workspace.id == workspace_id, Goal.user_id == user_id)
        .first()
    )
