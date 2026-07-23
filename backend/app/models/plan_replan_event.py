"""
PlanReplanEvent model.

One row per *accepted* replan (see app/services/adaptive_planning_service.py
and app/api/v1/replan.py) - the lightweight "History" the Adaptive
Planning Engine sprint asked for, without building full Plan versioning
(each Plan row is still updated in place, same as regenerate - see
app/models/plan.py). This exists purely as an audit trail: what changed,
why, and when a replan was accepted. It's also the explicit extension
point for real versioning later if that's ever needed - `summary`
already captures everything a future "restore this version" feature
would need, without committing to that shape now.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.plan import Plan


class PlanReplanEvent(Base):
    __tablename__ = "plan_replan_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"), index=True
    )

    reason: Mapped[str] = mapped_column(Text)
    # {"changes": [{task_id, title, estimated_minutes, previous_week,
    #   new_week}], "remaining_effort_minutes": int,
    #   "new_completion_estimate": "YYYY-MM-DD" | None,
    #   "deadline_at_risk": bool} - mirrors
    # adaptive_planning_service.ReplanProposal.
    summary: Mapped[dict[str, Any]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )

    plan: Mapped[Plan] = relationship(back_populates="replan_events")
