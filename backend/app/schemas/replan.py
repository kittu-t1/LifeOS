"""Request/response schemas for the Adaptive Planning Engine (replan)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class TaskAssignmentSchema(BaseModel):
    """One task's week/day placement - the same shape flows out of
    POST .../replan (inside a proposal) and back into
    POST .../replan/accept (echoed by the client), since the server
    never stores a pending proposal between the two calls - see
    app/api/v1/replan.py."""

    task_id: uuid.UUID
    week_number: int
    day_number: int | None = None


class TaskRescheduleRead(BaseModel):
    task_id: uuid.UUID
    title: str
    estimated_minutes: int | None
    previous_week: int
    new_week: int


class ReplanProposalRead(BaseModel):
    """Response for POST /planner/plans/{plan_id}/replan - a preview only,
    nothing in the database has changed yet."""

    plan_id: uuid.UUID
    reason: str
    changes: list[TaskRescheduleRead]
    remaining_effort_minutes: int
    new_completion_estimate: date | None
    deadline_at_risk: bool
    task_assignments: list[TaskAssignmentSchema]


class ReplanAcceptRequest(BaseModel):
    """The client sends back exactly what POST .../replan just proposed -
    `reason`/`changes`/etc. so the accepted event can be logged verbatim,
    and `task_assignments` so the server knows what to actually write."""

    reason: str
    changes: list[TaskRescheduleRead]
    remaining_effort_minutes: int
    new_completion_estimate: date | None
    deadline_at_risk: bool
    task_assignments: list[TaskAssignmentSchema]


class ReplanEventRead(BaseModel):
    """One row of replan history (GET /planner/plans/{plan_id}/replan/history)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    reason: str
    summary: dict
    created_at: datetime
