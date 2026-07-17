"""
ORM models.

Import every model here so Alembic's autogenerate and Base.metadata.create_all
can discover them from a single place.
"""

from app.models.goal import Goal, GoalStatus
from app.models.user import User
from app.models.workspace import Workspace

__all__ = ["Goal", "GoalStatus", "User", "Workspace"]
