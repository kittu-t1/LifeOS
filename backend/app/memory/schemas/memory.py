"""Request/response schemas for the Memory Engine."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.memory.models.memory import MemoryCategory, MemorySource


class MemoryCreate(BaseModel):
    category: MemoryCategory
    key: str = Field(min_length=1, max_length=255)
    value: str = Field(min_length=1)
    # Not user-settable in the UI today (every memory written through the
    # API is a human stating something) - accepted here, not derived
    # server-side, so a future automatic-extraction caller can pass
    # source=SYSTEM/confidence<1.0 through this exact same schema instead
    # of needing a second endpoint.
    source: MemorySource = MemorySource.MANUAL
    confidence: float | None = Field(default=1.0, ge=0.0, le=1.0)


class MemoryUpdate(BaseModel):
    """All fields optional - only what's provided gets changed (see
    memory_service.update_memory). `source`/`confidence` are excluded
    here on purpose: editing a memory's *content* shouldn't silently
    change who/what claimed it or how confident that claim was."""

    category: MemoryCategory | None = None
    key: str | None = Field(default=None, min_length=1, max_length=255)
    value: str | None = Field(default=None, min_length=1)


class MemoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: MemoryCategory
    key: str
    value: str
    source: MemorySource
    confidence: float | None
    created_at: datetime
    updated_at: datetime
