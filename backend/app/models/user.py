"""
User model.

Minimal today - no password/auth fields wired up to anything yet. A
single demo user is used everywhere (see app/core/deps.py) until real
authentication (JWT signup/login) is implemented in a later phase (see
docs/roadmap.md). `hashed_password` exists now, nullable, so that phase
doesn't require another migration to add it.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:
    from app.models.goal import Goal


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goals: Mapped[list[Goal]] = relationship(back_populates="owner", cascade="all, delete-orphan")
