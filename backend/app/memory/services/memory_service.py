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

Still no embeddings, no vector search, no LLM calls anywhere in this
module - `get_relevant_memories` is deterministic, ranked by three plain
signals (category priority, recency, confidence - see
`_CATEGORY_PRIORITY` below), not "all memories" like the original V1.
That's the "Relevant Memory Selection" sprint's whole point: the seam a
future semantic-search implementation eventually replaces is still this
same method (same signature plus a `limit`), just with a smarter sort
inside instead of an embedding lookup.
"""

from __future__ import annotations

import uuid

from app.memory.models.memory import Memory, MemoryCategory
from app.memory.repositories.memory_repository import MemoryRepository
from app.memory.schemas.memory import MemoryCreate, MemoryUpdate

# Lower number = surfaced first. Mirrors the sprint spec's stated
# priority order (preferences, planning-related notes, active
# learning/notes, work patterns) mapped onto this app's actual five
# categories - HABIT_INSIGHT isn't called out in the spec's examples, so
# it ranks last rather than being excluded outright: a habit streak is
# still occasionally useful planning context, just less consistently
# than an explicit stated preference.
_CATEGORY_PRIORITY: dict[MemoryCategory, int] = {
    MemoryCategory.PREFERENCE: 0,
    MemoryCategory.PLANNING_CONTEXT: 1,
    MemoryCategory.LEARNED_PATTERN: 2,
    MemoryCategory.NOTE: 3,
    MemoryCategory.HABIT_INSIGHT: 4,
}

# Caps how many memories ever reach a prompt, regardless of how many a
# user has accumulated - an unbounded dump defeats the point of ranking
# at all (a 50-memory prompt is no more "relevant" than an unranked
# one) and inflates token cost for no benefit. 8 is a judgment call, not
# a measured number - generous enough that a handful of real preferences
# and notes all fit, small enough to stay skimmable in a prompt.
DEFAULT_RELEVANT_MEMORY_LIMIT = 8


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
        self,
        *,
        user_id: uuid.UUID,
        category: MemoryCategory | None = None,
        limit: int = DEFAULT_RELEVANT_MEMORY_LIMIT,
    ) -> list[Memory]:
        """Called by consumers that want planner-style context (see
        app/services/planner_service.py's `_build_memory_context`).

        Ranks by (category priority, most-recently-updated first, highest
        confidence first) and returns at most `limit` - see module
        docstring for why this is still deterministic sorting, not
        semantic search. A memory with `confidence=None` sorts as if it
        were 0.0 (least confident), not as "unknown/skip" - there's no
        row in this app that can currently produce a null confidence
        (the schema defaults it to 1.0), but the sort has to resolve to
        *something* for whichever future SYSTEM-sourced writer leaves it
        unset."""
        memories = self.list_memories(user_id=user_id, category=category)
        ranked = sorted(
            memories,
            key=lambda m: (
                _CATEGORY_PRIORITY.get(m.category, len(_CATEGORY_PRIORITY)),
                -m.updated_at.timestamp(),
                -(m.confidence or 0.0),
            ),
        )
        return ranked[:limit]
