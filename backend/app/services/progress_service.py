"""
Progress service - the Execution Engine's calculation layer.

Deliberately the smallest of the three (Planner generates, Execution
tracks, Progress calculates): it reads PlanTask rows and does arithmetic,
nothing else. Progress is intentionally NOT stored anywhere (no
Plan.progress column, no cached counters) - it's always computed live
from PlanTask.status, so it can never drift out of sync with the tasks
that actually determine it. The cost (one COUNT query per read) is
trivial at this scale and worth paying for that guarantee.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models.plan_task import PlanTask, PlanTaskStatus


@dataclass(frozen=True)
class ProgressSummary:
    completed: int
    total: int
    remaining: int
    percentage: int  # 0-100, rounded; 0 when total is 0 (nothing to divide by)


def calculate_progress(db: Session, *, plan_id: uuid.UUID) -> ProgressSummary:
    total, completed = (
        db.query(
            func.count(PlanTask.id),
            func.coalesce(
                func.sum(case((PlanTask.status == PlanTaskStatus.COMPLETED, 1), else_=0)), 0
            ),
        )
        .filter(PlanTask.plan_id == plan_id)
        .one()
    )

    percentage = round((completed / total) * 100) if total else 0
    return ProgressSummary(
        completed=completed, total=total, remaining=total - completed, percentage=percentage
    )
