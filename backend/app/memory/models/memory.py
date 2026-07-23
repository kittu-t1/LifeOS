"""
Memory model - the Memory Engine's single persistence unit.

One row is one fact/preference/observation about a user, deliberately
generic (category + key + value) rather than a separate table per
category (a `PreferredWorkingHours` table, a `HabitInsight` table, ...).
That genericity is what makes this a reusable *platform* service other
modules (Planner, Habits, a future Calendar/Execution Assistant) can all
read and write through one API, instead of every feature growing its own
bespoke "remember this" column somewhere.

Deliberately its own table, not a JSON blob on User (see the sprint
spec's explicit instruction) - a user has many independent memories with
their own lifecycle (created, updated, deleted, individually filterable
by category), which a single JSON column can't index, query, or evolve
cleanly.

V1 is intentionally deterministic (see module docstring in
app/memory/services/memory_service.py): `source`/`confidence` exist now
so the schema doesn't need a migration when automatic extraction or AI
summarization (see docs/agents.md's Memory Agent scope) starts writing
rows with source=SYSTEM and confidence < 1.0 - today, every memory is
source=MANUAL with confidence=1.0, written by a human through the CRUD
API, not inferred.

No embedding/vector column here on purpose - semantic search is an
explicit "Future Compatibility" item, not a V1 requirement. Adding it
later is a straightforward additive migration; the category/key/value
shape isn't disturbed by it.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class MemoryCategory(str, enum.Enum):
    PREFERENCE = "preference"
    PLANNING_CONTEXT = "planning_context"
    HABIT_INSIGHT = "habit_insight"
    LEARNED_PATTERN = "learned_pattern"
    NOTE = "note"


class MemorySource(str, enum.Enum):
    # Written directly by the user through the Memory CRUD API/UI - the
    # only source that exists in V1.
    MANUAL = "manual"
    # Reserved for future automatic extraction/inference (see docs/
    # agents.md's Memory Agent) - not produced by anything yet.
    SYSTEM = "system"


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )

    category: Mapped[MemoryCategory] = mapped_column(
        Enum(MemoryCategory, name="memory_category", native_enum=False), index=True
    )
    # Short, machine-ish identifier for what this memory is about (e.g.
    # "preferred_working_hours", "aws_certification_focus") - lets a
    # future caller ask "do we already have a memory about X" without
    # parsing `value`. Not unique/enforced - a user can have multiple
    # memories sharing a key (e.g. several "note" entries) and nothing
    # here assumes otherwise.
    key: Mapped[str] = mapped_column(String(255))
    # The actual remembered content - free text so it can hold anything
    # from "6am-9am" to a full paragraph note, per the spec's "User
    # Notes" category.
    value: Mapped[str] = mapped_column(Text)

    source: Mapped[MemorySource] = mapped_column(
        Enum(MemorySource, name="memory_source", native_enum=False), default=MemorySource.MANUAL
    )
    # 0.0-1.0, nullable. Always 1.0 for MANUAL memories in V1 (a human
    # stated it, so it's not "uncertain") - meaningful once SYSTEM-
    # sourced memories exist and need to express how sure the extraction
    # was.
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True, default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="memories")
