"""
PlannerRun model.

One row per attempted AI plan generation - success or failure. Exists
purely for evaluation/observability (see the AI Planner MVP spec's
"Testing > AI evaluation" section): which prompt version and model
produced which plan, and why a generation failed when it did. Not
exposed as its own API surface yet - just written to on every
planner_service.generate_plan call and readable directly from the DB
for now.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.goal import Goal


class PlannerRunStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class PlannerRun(Base):
    __tablename__ = "planner_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), index=True
    )
    # Only set when status is SUCCESS - a failed run never produced a Plan.
    # SET NULL (not CASCADE) so deleting a Plan doesn't also delete the
    # historical record that it was once generated.
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"), nullable=True
    )

    prompt_version: Mapped[str] = mapped_column(String(50))
    model_used: Mapped[str] = mapped_column(String(100))
    status: Mapped[PlannerRunStatus] = mapped_column(
        Enum(PlannerRunStatus, name="planner_run_status", native_enum=False)
    )
    # Set when status is FAILED - the exception message surfaced back to
    # the caller (see app/planner/llm/base.py exception types), kept here
    # so failure patterns are visible without digging through server logs.
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # See the matching comment on Plan.created_at (app/models/plan.py) -
    # same microsecond-precision reasoning applies to ordering runs.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    goal: Mapped[Goal] = relationship(back_populates="planner_runs")
