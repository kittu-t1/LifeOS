"""Request/response schemas for the Execution Engine (PlanTask + progress)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.plan_task import PlanTaskStatus


class PlanTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    milestone_id: uuid.UUID | None
    week_number: int
    day_number: int | None
    title: str
    description: str | None
    estimated_minutes: int | None
    display_order: int
    status: PlanTaskStatus
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WeekTasksGroup(BaseModel):
    week_number: int
    tasks: list[PlanTaskRead]


class PlanTasksResponse(BaseModel):
    weeks: list[WeekTasksGroup]


class UpdateTaskStatusRequest(BaseModel):
    """Pydantic's enum validation is the whole guard here - anything
    other than "pending"/"completed" (see PlanTaskStatus) is rejected
    with a 422 before this ever reaches task_service, matching the
    "status should initially support pending/completed" constraint."""

    status: PlanTaskStatus


class ProgressRead(BaseModel):
    completed: int
    total: int
    remaining: int
    percentage: int
