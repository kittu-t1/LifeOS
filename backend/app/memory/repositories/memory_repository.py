"""
Memory repository - the Memory Engine's persistence boundary.

Every other service/module in this codebase talks to the database
directly through plain functions (`db.query(Model)...` inline in
`*_service.py` - see habit_service.py, task_service.py). The Memory
Engine sprint explicitly asked for the Repository pattern instead, so
this module is a deliberate exception: `MemoryService` depends on the
abstract `MemoryRepository` interface below, never on SQLAlchemy
directly. That's the actual Clean-Architecture payoff - the concrete
`SqlAlchemyMemoryRepository` is swappable (e.g. for a future
vector-store-backed implementation once semantic search lands) without
MemoryService's business logic changing at all.

Kept intentionally small - four operations, matching exactly what the
CRUD + list/filter API needs today. Not a generic repository base class
other modules must adopt; this is scoped to Memory.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.memory.models.memory import Memory, MemoryCategory


class MemoryRepository(ABC):
    @abstractmethod
    def add(self, memory: Memory) -> Memory: ...

    @abstractmethod
    def get(self, *, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory | None: ...

    @abstractmethod
    def list(
        self, *, user_id: uuid.UUID, category: MemoryCategory | None = None
    ) -> list[Memory]: ...

    @abstractmethod
    def save(self, memory: Memory) -> Memory:
        """Persists changes to an already-tracked Memory (an update, as
        opposed to `add`'s insert)."""
        ...

    @abstractmethod
    def delete(self, memory: Memory) -> None: ...


class SqlAlchemyMemoryRepository(MemoryRepository):
    """The only implementation today - a thin wrapper around the same
    SQLAlchemy Session every other service in this app already uses.
    Nothing exotic: this class exists so MemoryService's *signature*
    doesn't mention SQLAlchemy, not because the underlying storage is
    doing anything unusual yet."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, memory: Memory) -> Memory:
        self._db.add(memory)
        self._db.commit()
        self._db.refresh(memory)
        return memory

    def get(self, *, memory_id: uuid.UUID, user_id: uuid.UUID) -> Memory | None:
        return (
            self._db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()
        )

    def list(self, *, user_id: uuid.UUID, category: MemoryCategory | None = None) -> list[Memory]:
        query = self._db.query(Memory).filter(Memory.user_id == user_id)
        if category is not None:
            query = query.filter(Memory.category == category)
        return query.order_by(Memory.updated_at.desc()).all()

    def save(self, memory: Memory) -> Memory:
        self._db.commit()
        self._db.refresh(memory)
        return memory

    def delete(self, memory: Memory) -> None:
        self._db.delete(memory)
        self._db.commit()
