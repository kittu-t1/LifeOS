"""
Memory Engine tests.

Three layers:
  - Direct service/repository tests (via db_session) - CRUD, ownership
    scoping, category filtering, exercised through MemoryService the
    same way any other consumer of the Memory Engine would use it.
  - API tests (via client) - the CRUD + category-filter HTTP contract.
  - Planner integration tests - confirms generate_plan/regenerate_plan/
    replan retrieve and log memories (see planner_service.
    _log_relevant_memories and app/api/v1/replan.py) WITHOUT altering
    the actual prompt sent to the LLM - the sprint's explicit "log or
    display... do not alter LLM prompts yet" scope.
"""

from __future__ import annotations

import json
import logging
import uuid

import pytest

from app.main import app
from app.memory.models.memory import MemoryCategory, MemorySource
from app.memory.repositories.memory_repository import SqlAlchemyMemoryRepository
from app.memory.schemas.memory import MemoryCreate, MemoryUpdate
from app.memory.services.memory_service import MemoryService
from app.models.user import User
from app.planner.llm.base import LLMProvider
from app.planner.llm.factory import get_llm_provider

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


def test_get_relevant_memories_is_deterministic_full_list(db_session):
    """V1 has no ranking/embeddings (see memory_service.py's module
    docstring) - get_relevant_memories is just list_memories today."""
    user = _make_user(db_session)
    service = MemoryService(SqlAlchemyMemoryRepository(db_session))
    service.create_memory(
        user_id=user.id,
        data=MemoryCreate(category=MemoryCategory.PREFERENCE, key="a", value="x"),
    )
    service.create_memory(
        user_id=user.id, data=MemoryCreate(category=MemoryCategory.NOTE, key="b", value="y")
    )

    assert service.get_relevant_memories(user_id=user.id) == service.list_memories(user_id=user.id)


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


# --- Planner integration (log-only, prompts unchanged) ---------------------


class _RecordingFakeLLMProvider(LLMProvider):
    """Records every user_prompt it's called with - the only way to prove
    generate_plan/regenerate_plan did NOT thread memory content into the
    prompt, per the sprint's explicit "do not alter LLM prompts yet"."""

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


def test_generate_plan_logs_memories_without_altering_prompt(client, override_llm, caplog):
    memory_value = "UNIQUE_MEMORY_MARKER_should_not_leak_into_prompt"
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
    # The prompt itself must never contain the memory's content.
    assert memory_value not in fake.received_prompts[0]
    # But the log should show the Memory Engine was consulted.
    assert any("memories available" in record.message for record in caplog.records)


def test_replan_logs_memories(client, override_llm, caplog):
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
