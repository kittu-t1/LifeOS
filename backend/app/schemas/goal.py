"""Request/response schemas for Goals."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.goal import GoalStatus


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    # Not yet collected by the Create Goal form - added to the model/API
    # now (Planner Productization phase) so nothing blocks a future form
    # field from just working. Optional, so existing callers are unaffected.
    deadline: datetime | None = None


class GoalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    deadline: datetime | None
    status: GoalStatus
    progress: int
    created_at: datetime
    updated_at: datetime
    workspace_id: uuid.UUID
