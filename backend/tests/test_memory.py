"""
Memory Engine tests.

Four layers:
  - Direct service/repository tests (via db_session) - CRUD, ownership
    scoping, category filtering, and the deterministic relevance ranking
    (category priority / recency / confidence - see MemoryService.
    get_relevant_memories), exercised through MemoryService the same way
    any other consumer of the Memory Engine would use it.
  - API tests (via client) - the CRUD + category-filter HTTP contract.
  - Prompt-formatting tests - confirms planner_service._format_memory_context
    turns ranked memories into the grouped, readable "User Context" block
    (never raw JSON), independent of any real LLM call.
  - Planner integration tests - confirms generate_plan/regenerate_plan
    actually inject that "User Context" block into the LLM prompt (see
    planner_service._build_memory_context), while replan's own memory
    lookup (app/api/v1/replan.py) stays log-only, since
    adaptive_planning_service.propose_replan never calls an LLM at all -
    there's no prompt there to inject into.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

import pytest

from app.main import app
from app.memory.models.memory import Memory, MemoryCategory, MemorySource
from app.memory.repositories.memory_repository import SqlAlchemyMemoryRepository
from app.memory.schemas.memory import MemoryCreate, MemoryUpdate
from app.memory.services.memory_service import DEFAULT_RELEVANT_MEMORY_LIMIT, MemoryService
from app.models.user import User
from app.planner.llm.base import LLMProvider
from app.planner.llm.factory import get_llm_provider
from app.services.planner_service import _format_memory_context

VALID_PLAN_JSON = json.dumps(
    {
        "mission": "Ship a working LifeOS MVP that proves the core loop.",
        "estimated_duration": "90 days",
        "milestones": [
            {"title": "Foundation", "description": "Backend + DB in place.", "duration": "2 weeks"},
        ],
        "weekly_plan": [
            {
                "week": 1,
                "focus": "Setup",
                "tasks": [
                    {
                        "title": "Scaffold backend",
                        "description": "FastAPI project skeleton.",
                        "estimated_minutes": 90,
                    },
                ],
            },
        ],
        "timeline": ["Weeks 1-2: Foundation"],
    }
)


def _make_user(db_session) -> User:
    user = User(email=f"memory-{uuid.uuid4().hex[:8]}@lifeos.local", name="Memory Tester")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# --- Direct service/repository tests --------------------------------------


def test_create_memory_persists_expected_fields(db_session):
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))

    memory = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(
            category=MemoryCategory.PREFERENCE,
            key="preferred_working_hours",
            value="6am-9am, focused deep work only",
        ),
    )

    assert memory.id is not None
    assert memory.category == MemoryCategory.PREFERENCE
    assert memory.key == "preferred_working_hours"
    assert memory.source == MemorySource.MANUAL
    assert memory.confidence == 1.0
    assert memory.created_at is not None


def test_list_memories_filters_by_category(db_session):
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.PREFERENCE, key="a", value="morning person"),
    )
    service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.NOTE, key="b", value="AWS cert prep"),
    )

    all_memories = service.list_memories(user_id=user.id)
    prefs_only = service.list_memories(user_id=user.id, category=MemoryCategory.PREFERENCE)

    assert len(all_memories) == 2
    assert len(prefs_only) == 1
    assert prefs_only[0].key == "a"


def test_list_memories_scoped_to_owner(db_session):
    user_a = _make_user(db_session)
    user_b = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    service.create_memory(
        user_id=user_a.id,
        data=MemoryCreate(category=MemoryCategory.NOTE, key="a", value="user a's note"),
    )

    assert len(service.list_memories(user_id=user_a.id)) == 1
    assert len(service.list_memories(user_id=user_b.id)) == 0


def test_get_owned_memory_returns_none_for_other_user(db_session):
    user_a = _make_user(db_session)
    user_b = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    memory = service.create_memory(
        user_id=user_a.id,
        data=MemoryCreate(category=MemoryCategory.NOTE, key="a", value="private to user a"),
    )

    assert service.get_owned_memory(user_id=user_a.id, memory_id=memory.id) is not None
    assert service.get_owned_memory(user_id=user_b.id, memory_id=memory.id) is None


def test_update_memory_only_changes_provided_fields(db_session):
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    memory = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(
            category=MemoryCategory.LEARNED_PATTERN,
            key="friday_postpone",
            value="Frequently postpones Friday work",
        ),
    )
    original_source = memory.source
    original_confidence = memory.confidence

    updated = service.update_memory(
        memory=memory, data=MemoryUpdate(value="Frequently postpones Friday afternoon work")
    )

    assert updated.value == "Frequently postpones Friday afternoon work"
    assert updated.key == "friday_postpone"  # untouched
    assert updated.category == MemoryCategory.LEARNED_PATTERN  # untouched
    assert updated.source == original_source  # update schema can't change this
    assert updated.confidence == original_confidence


def test_delete_memory_removes_it(db_session):
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    memory = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.NOTE, key="a", value="temporary"),
    )

    service.delete_memory(memory=memory)

    assert service.get_owned_memory(user_id=user.id, memory_id=memory.id) is None


def test_get_relevant_memories_is_deterministic_across_calls(db_session):
    """No randomness, no embeddings (see memory_service.py's module
    docstring) - calling get_relevant_memories twice with no changes in
    between must return the exact same order both times."""
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.PREFERENCE, key="a", value="x"),
    )
    service.create_memory(
        user_id=user.id, data=MemoryCreate(category=MemoryCategory.NOTE, key="b", value="y")
    )

    first = [m.id for m in service.get_relevant_memories(user_id=user.id)]
    second = [m.id for m in service.get_relevant_memories(user_id=user.id)]
    assert first == second


def test_get_relevant_memories_ranks_by_category_priority(db_session):
    """Preferences > planning context > patterns > notes > habit
    insights (see MemoryService._CATEGORY_PRIORITY) - created here in
    the opposite order, so a passing assertion actually proves the sort
    is doing something, not just preserving insertion order."""
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    habit_insight = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.HABIT_INSIGHT, key="h", value="21-day streak"),
    )
    note = service.create_memory(
        user_id=user.id, data=MemoryCreate(category=MemoryCategory.NOTE, key="n", value="a note")
    )
    pattern = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(
            category=MemoryCategory.LEARNED_PATTERN, key="p", value="postpones Fridays"
        ),
    )
    planning_context = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(
            category=MemoryCategory.PLANNING_CONTEXT, key="pc", value="prefers short sprints"
        ),
    )
    preference = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.PREFERENCE, key="pref", value="evenings"),
    )

    ranked = service.get_relevant_memories(user_id=user.id)

    assert [m.id for m in ranked] == [
        preference.id,
        planning_context.id,
        pattern.id,
        note.id,
        habit_insight.id,
    ]


def test_get_relevant_memories_breaks_ties_by_recency(db_session):
    """Same category (so priority can't decide) - the more recently
    updated memory should sort first."""
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    older = service.create_memory(
        user_id=user.id, data=MemoryCreate(category=MemoryCategory.NOTE, key="a", value="older")
    )
    newer = service.create_memory(
        user_id=user.id, data=MemoryCreate(category=MemoryCategory.NOTE, key="b", value="newer")
    )
    older.updated_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    newer.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    db_session.add_all([older, newer])
    db_session.commit()

    ranked = service.get_relevant_memories(user_id=user.id)

    assert [m.id for m in ranked] == [newer.id, older.id]


def test_get_relevant_memories_breaks_recency_ties_by_confidence(db_session):
    """Same category, same updated_at - the higher-confidence memory
    should sort first."""
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    less_confident = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.NOTE, key="a", value="guess", confidence=0.3),
    )
    more_confident = service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.NOTE, key="b", value="certain", confidence=0.9),
    )
    same_timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    less_confident.updated_at = same_timestamp
    more_confident.updated_at = same_timestamp
    db_session.add_all([less_confident, more_confident])
    db_session.commit()

    ranked = service.get_relevant_memories(user_id=user.id)

    assert [m.id for m in ranked] == [more_confident.id, less_confident.id]


def test_get_relevant_memories_respects_limit(db_session):
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    for i in range(DEFAULT_RELEVANT_MEMORY_LIMIT + 4):
        service.create_memory(
            user_id=user.id,
            data=MemoryCreate(category=MemoryCategory.NOTE, key=f"n{i}", value=f"note {i}"),
        )

    assert len(service.get_relevant_memories(user_id=user.id)) == DEFAULT_RELEVANT_MEMORY_LIMIT
    assert len(service.get_relevant_memories(user_id=user.id, limit=3)) == 3


# --- API tests --------------------------------------------------------


def test_create_and_list_memory_via_api(client):
    response = client.post(
        "/api/v1/memories",
        json={
            "category": "preference",
            "key": "session_length",
            "value": "Prefers 45-minute focused sessions",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "preference"
    assert body["source"] == "manual"
    assert body["confidence"] == 1.0

    listed = client.get("/api/v1/memories").json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]


def test_list_memories_category_filter_via_api(client):
    client.post(
        "/api/v1/memories",
        json={"category": "preference", "key": "a", "value": "morning person"},
    )
    client.post(
        "/api/v1/memories",
        json={"category": "note", "key": "b", "value": "Preparing for AWS certification."},
    )

    all_memories = client.get("/api/v1/memories").json()
    notes_only = client.get("/api/v1/memories", params={"category": "note"}).json()

    assert len(all_memories) == 2
    assert len(notes_only) == 1
    assert notes_only[0]["category"] == "note"


def test_get_memory_not_found(client):
    response = client.get(f"/api/v1/memories/{uuid.uuid4()}")
    assert response.status_code == 404


def test_update_memory_via_api(client):
    created = client.post(
        "/api/v1/memories",
        json={"category": "note", "key": "focus", "value": "Focus on backend this month."},
    ).json()

    updated = client.patch(
        f"/api/v1/memories/{created['id']}",
        json={"value": "Focus on backend and infra this month."},
    )
    assert updated.status_code == 200
    assert updated.json()["value"] == "Focus on backend and infra this month."


def test_update_memory_not_found(client):
    response = client.patch(f"/api/v1/memories/{uuid.uuid4()}", json={"value": "x"})
    assert response.status_code == 404


def test_delete_memory_via_api(client):
    created = client.post(
        "/api/v1/memories",
        json={"category": "habit_insight", "key": "streak", "value": "Longest streak: 21 days"},
    ).json()

    response = client.delete(f"/api/v1/memories/{created['id']}")
    assert response.status_code == 204

    assert client.get(f"/api/v1/memories/{created['id']}").status_code == 404


def test_create_memory_rejects_invalid_category(client):
    response = client.post(
        "/api/v1/memories",
        json={"category": "not_a_real_category", "key": "a", "value": "b"},
    )
    assert response.status_code == 422


# --- Prompt-formatting tests -------------------------------------------


def _memory(category: MemoryCategory, value: str) -> Memory:
    """Builds an unpersisted Memory for _format_memory_context tests -
    that function only ever reads category/value, so nothing else needs
    a real user_id/db row."""
    return Memory(category=category, key="k", value=value)


def test_format_memory_context_returns_none_for_empty_list():
    assert _format_memory_context([]) is None


def test_format_memory_context_groups_by_category_with_readable_headings():
    memories = [
        _memory(MemoryCategory.PREFERENCE, "Prefers evening work sessions"),
        _memory(MemoryCategory.PREFERENCE, "Likes 60-minute focus blocks"),
        _memory(MemoryCategory.LEARNED_PATTERN, "Usually finishes backend tasks early"),
        _memory(MemoryCategory.NOTE, "Preparing for interviews"),
    ]

    formatted = _format_memory_context(memories)

    assert formatted is not None
    # Grouped under a readable heading, not the raw enum value.
    assert "Preferences" in formatted
    assert "Patterns" in formatted
    assert "Notes" in formatted
    # Preferences heading comes first (matches MemoryService's ranking
    # priority order), and both preference memories land under it.
    assert formatted.index("Preferences") < formatted.index("Patterns")
    assert formatted.index("Patterns") < formatted.index("Notes")
    assert "- Prefers evening work sessions" in formatted
    assert "- Likes 60-minute focus blocks" in formatted
    assert "- Usually finishes backend tasks early" in formatted
    assert "- Preparing for interviews" in formatted
    # Never a raw JSON dump - the whole point of this formatting step.
    assert "{" not in formatted and "}" not in formatted


# --- Planner integration -------------------------------------------------


class _RecordingFakeLLMProvider(LLMProvider):
    """Records every user_prompt it's called with, so tests can assert on
    exactly what the model would have seen."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.received_prompts: list[str] = []

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.received_prompts.append(user_prompt)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture()
def override_llm():
    def _set(fake: LLMProvider) -> None:
        app.dependency_overrides[get_llm_provider] = lambda: fake

    yield _set
    app.dependency_overrides.pop(get_llm_provider, None)


def test_generate_plan_injects_memory_context_into_prompt(client, override_llm, caplog):
    memory_value = "Prepping for AWS certification interviews"
    client.post(
        "/api/v1/memories",
        json={"category": "note", "key": "marker", "value": memory_value},
    )

    fake = _RecordingFakeLLMProvider([VALID_PLAN_JSON])
    override_llm(fake)
    goal_id = client.post("/api/v1/goals", json={"title": "Learn guitar"}).json()["id"]

    with caplog.at_level(logging.INFO):
        response = client.post(
            f"/api/v1/planner/goals/{goal_id}/generate",
            json={"timeline": "90 days", "availability": "5 hours/week", "constraints": []},
        )

    assert response.status_code == 201
    body = response.json()
    # The memory's content must actually reach the prompt now...
    prompt = fake.received_prompts[0]
    assert memory_value in prompt
    # ...inside a structured "User Context" section, not appended raw.
    assert "User Context" in prompt
    assert "Notes" in prompt
    # ...and the response tells the frontend a memory was actually used,
    # so a "Personalized using N memories" indicator doesn't have to
    # guess from log output (see PlanRead.memories_used).
    assert body["memories_used"] == 1
    assert any(
        "injecting" in record.message and "user context" in record.message
        for record in caplog.records
    )


def test_regenerate_plan_injects_memory_context_into_prompt(client, override_llm):
    override_llm(_RecordingFakeLLMProvider([VALID_PLAN_JSON]))
    goal_id = client.post("/api/v1/goals", json={"title": "Ship a feature"}).json()["id"]
    plan_id = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "30 days", "availability": "5 hours/week", "constraints": []},
    ).json()["id"]

    memory_value = "Prefers 60-minute focus blocks"
    client.post(
        "/api/v1/memories",
        json={"category": "preference", "key": "session_length", "value": memory_value},
    )

    fake = _RecordingFakeLLMProvider([VALID_PLAN_JSON])
    override_llm(fake)
    response = client.post(
        f"/api/v1/planner/plans/{plan_id}/regenerate",
        json={"adjustment": "add more buffer time"},
    )

    assert response.status_code == 200
    body = response.json()
    prompt = fake.received_prompts[0]
    assert memory_value in prompt
    assert "User Context" in prompt
    assert "Preferences" in prompt
    assert body["memories_used"] == 1


def test_replan_logs_memories_without_a_prompt_to_inject_into(client, override_llm, caplog):
    """replan/propose is a deterministic scheduler with no LLM call at
    all (see adaptive_planning_service.propose_replan) - memory is still
    fetched and logged for observability, but there's no prompt for it to
    join, unlike generate/regenerate above."""
    client.post(
        "/api/v1/memories",
        json={"category": "planning_context", "key": "style", "value": "prefers short sprints"},
    )
    override_llm(_RecordingFakeLLMProvider([VALID_PLAN_JSON]))
    goal_id = client.post("/api/v1/goals", json={"title": "Ship a feature"}).json()["id"]
    plan_id = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "30 days", "availability": "5 hours/week", "constraints": []},
    ).json()["id"]

    with caplog.at_level(logging.INFO):
        response = client.post(f"/api/v1/planner/plans/{plan_id}/replan")

    assert response.status_code == 200
    assert any("memories available" in record.message for record in caplog.records)
