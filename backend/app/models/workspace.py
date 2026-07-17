"""
Workspace model.

The dedicated environment created automatically for every Goal (see
docs/vision.md - "Primary Object"). Deliberately thin today: Mission and
Progress are views onto the parent Goal's own fields (title/description,
progress), not separate columns here, to avoid duplicating state. Tasks,
Planner output, Knowledge, Timeline, and Chat history will attach to a
Workspace as their own models once those features are implemented -
today only the container itself exists.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.goal import Goal


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), unique=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # TODO(workspace-metadata): fields planned but not yet implemented -
    # see docs/product_principles.md and docs/roadmap.md. Adding these is
    # a deliberate future change, not an oversight; do not add columns
    # for them without a matching Alembic migration.
    #   - last_activity: datetime | None - updated whenever anything in
    #                                        the workspace changes; backs
    #                                        the real ActivityTimeline
    #                                        (see frontend
    #                                        features/workspace/ActivityTimeline.tsx)
    #   - theme: str | None               - per-workspace visual theme
    #                                        override, if ever needed
    #   - icon: str | None                - user-chosen icon shown on
    #                                        Goal Cards / workspace nav
    #   - color: str | None               - accent color override for
    #                                        this workspace
    #   - archived: bool                  - soft-hide completed/abandoned
    #                                        workspaces from the Dashboard
    #                                        without deleting them

    goal: Mapped[Goal] = relationship(back_populates="workspace")
