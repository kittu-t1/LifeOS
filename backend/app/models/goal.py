"""
Goal model.

The primary object in LifeOS (see docs/vision.md). Every Goal belongs to
one User and owns exactly one Workspace, created automatically when the
Goal is created (see app/services/goal_service.py).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace


class GoalStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # TODO(goal-fields): fields planned but not yet implemented - see
    # docs/product_principles.md and docs/roadmap.md. Adding these is a
    # deliberate future change, not an oversight; do not add columns for
    # them without a matching Alembic migration.
    #   - category: str | None       - lets users/goal cards group by type
    #                                   (career, health, finance, etc.)
    #   - priority: enum | None      - low/medium/high, informs Planner
    #                                   sequencing across multiple goals
    #   - deadline: datetime | None  - target completion date, feeds
    #                                   Timeline and Adaptive Planning
    #   - visibility: enum           - private/shared, relevant once
    #                                   multi-user Workspaces exist (see
    #                                   docs/roadmap.md Post-MVP)
    # (`description` above already covers the "description" field once
    # planned here - no action needed for it.)

    # Plain manual field for now - nothing computes this automatically yet.
    # Once Tasks/Planner are real (see docs/roadmap.md), progress should be
    # derived from task completion instead of stored directly.
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus, name="goal_status", native_enum=False), default=GoalStatus.NOT_STARTED
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="goals")
    workspace: Mapped[Workspace] = relationship(
        back_populates="goal", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def workspace_id(self) -> uuid.UUID:
        """Convenience accessor so API responses can include workspace_id
        without the client having to make a second request to discover it."""
        return self.workspace.id
