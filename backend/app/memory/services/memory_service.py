"""
Memory service - the Memory Engine's business logic layer, and the only
thing other modules (Planner, Habits, a future Calendar/Execution
Assistant) should ever import from the Memory Engine.

Deliberately independent from Planner/Habits/every other feature (see
the sprint's Design Principles: "Keep Memory independent from Planner
and Habits... do not tightly couple memory logic to any single
feature"): this module never imports anything from app.services,
app.planner, or the Habit/Plan/Goal models. The dependency only ever
points one way - a consumer (e.g. planner_service.py) imports
MemoryService, never the reverse - which is what actually keeps Memory
reusable as a platform service instead of becoming Planner-flavored.

V1 is intentionally deterministic - no embeddings, no ranking, no LLM
calls anywhere in this module. `get_relevant_memories` exists as the one
seam a future semantic-search implementation replaces: same signature
(user_id, optional category), smarter selection inside. Today "relevant"
simply means "all of this user's memories, optionally narrowed by
category" - see the Future Compatibility section of the sprint spec for
what that method is deliberately leaving room for (importance scoring,
vector similarity, context ranking) without committing to any of it now.
"""

from __future__ import annotations

import uuid

from app.memory.models.memory import Memory, MemoryCategory
from app.memory.repositories.memory_repository import MemoryRepository
from app.memory.schemas.memory import MemoryCreate, MemoryUpdate


class MemoryService:
    def __init__(self, repository: MemoryRepository) -> None:
        self._repository = repository

    def create_memory(self, *, user_id: uuid.UUID, data: MemoryCreate) -> Memory:
        memory = Memory(
            user_id=user_id,
            category=data.category,
            key=data.key,
            value=data.value,
            source=data.source,
            confidence=data.confidence,
        )
        return self._repository.add(memory)

    def list_memories(
        self, *, user_id: uuid.UUID, category: MemoryCategory | None = None
    ) -> list[Memory]:
        return self._repository.list(user_id=user_id, category=category)

    def get_owned_memory(self, *, user_id: uuid.UUID, memory_id: uuid.UUID) -> Memory | None:
        return self._repository.get(memory_id=memory_id, user_id=user_id)

    def update_memory(self, *, memory: Memory, data: MemoryUpdate) -> Memory:
        if data.category is not None:
            memory.category = data.category
        if data.key is not None:
            memory.key = data.key
        if data.value is not None:
            memory.value = data.value
        return self._repository.save(memory)

    def delete_memory(self, *, memory: Memory) -> None:
        self._repository.delete(memory)

    def get_relevant_memories(
        self, *, user_id: uuid.UUID, category: MemoryCategory | None = None
    ) -> list[Memory]:
        """Called by consumers that want planner-style context (see
        app/services/planner_service.py) - see module docstring for why
        "relevant" is just "all/category-filtered" in V1, not a ranked
        subset."""
        return self.list_memories(user_id=user_id, category=category)
