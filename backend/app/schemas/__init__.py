# Pydantic request/response schemas live here.

from app.schemas.goal import GoalCreate, GoalRead
from app.schemas.workspace import WorkspaceRead

__all__ = ["GoalCreate", "GoalRead", "WorkspaceRead"]
