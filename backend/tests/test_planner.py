"""
Planner tests use a FakeLLMProvider (via FastAPI dependency override, the
same mechanism conftest.py uses for get_db) instead of calling OpenAI -
fast, deterministic, and doesn't require an API key to run the suite.
"""

import json
import uuid

import pytest

from app.main import app
from app.models.plan import Plan
from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.planner.llm.base import LLMProvider, LLMRequestError, LLMTimeoutError
from app.planner.llm.factory import get_llm_provider
from app.planner.prompts import PLANNER_V5_SYSTEM_PROMPT

VALID_PLAN_JSON = json.dumps(
    {
        "mission": "Ship a working LifeOS MVP that proves the core loop.",
        "estimated_duration": "90 days",
        "milestones": [
            {
                "title": "Foundation",
                "description": "Backend + DB in place.",
                "duration": "2 weeks",
            },
            {
                "title": "Core loop",
                "description": "Goal -> Plan -> Execution works.",
                "duration": "6 weeks",
            },
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
                    {
                        "title": "Scaffold frontend",
                        "description": "Next.js project skeleton.",
                        "estimated_minutes": 60,
                    },
                ],
            },
            {
                "week": 2,
                "focus": "Data model",
                "tasks": [
                    {
                        "title": "Design schema",
                        "description": "Sketch tables and relationships.",
                        "estimated_minutes": 45,
                    },
                    {
                        "title": "Write migrations",
                        "description": "Alembic revision for the schema.",
                        "estimated_minutes": 30,
                    },
                ],
            },
        ],
        "timeline": ["Weeks 1-2: Foundation", "Weeks 3-8: Core loop"],
    }
)

ADJUSTED_PLAN_JSON = json.dumps(
    {
        "mission": "Ship a realistic, lower-stress LifeOS MVP over a longer runway.",
        "estimated_duration": "120 days",
        "milestones": [
            {
                "title": "Foundation",
                "description": "Backend + DB in place, no rush.",
                "duration": "3 weeks",
            },
        ],
        "weekly_plan": [
            {
                "week": 1,
                "focus": "Setup",
                "tasks": [
                    {
                        "title": "Scaffold backend",
                        "description": "FastAPI project skeleton, take it slow.",
                        "estimated_minutes": 90,
                    },
                ],
            },
        ],
        "timeline": ["Weeks 1-3: Foundation"],
    }
)


class FakeLLMProvider(LLMProvider):
    """Returns each item in `responses` in order, one per call. A response
    that is an Exception instance is raised instead of returned - lets a
    single fake express "fail then succeed" or "fail forever" sequences."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.call_count = 0

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        if not self._responses:
            raise AssertionError("FakeLLMProvider called more times than it has responses for")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture()
def override_llm():
    """Yields a setter: override_llm(fake) swaps in a fake provider for
    the duration of the test, and the override is cleared afterward
    regardless of pass/fail."""

    def _set(fake: LLMProvider) -> None:
        app.dependency_overrides[get_llm_provider] = lambda: fake

    yield _set
    app.dependency_overrides.pop(get_llm_provider, None)


def _create_goal(client) -> str:
    response = client.post("/api/v1/goals", json={"title": "Build LifeOS MVP"})
    assert response.status_code == 201
    return response.json()["id"]


def _generate(client, goal_id: str):
    return client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "90 days", "availability": "10 hours/week", "constraints": []},
    )


def test_generate_plan_success(client, db_session, override_llm):
    goal_id = _create_goal(client)
    fake = FakeLLMProvider([VALID_PLAN_JSON])
    override_llm(fake)

    response = _generate(client, goal_id)

    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] == goal_id
    assert body["mission"].startswith("Ship a working")
    assert len(body["milestones"]) == 2
    assert body["milestones"][0]["order"] == 0
    assert body["milestones"][1]["order"] == 1
    assert len(body["weekly_plan"]) == 2
    assert body["timeline"] == ["Weeks 1-2: Foundation", "Weeks 3-8: Core loop"]
    # No memories exist for this user - 0, not None, since generate_plan
    # always runs the memory lookup (see PlanRead.memories_used).
    assert body["memories_used"] == 0
    assert fake.call_count == 1

    # Persisted, not just returned.
    goal_uuid = uuid.UUID(goal_id)
    assert db_session.query(Plan).filter(Plan.goal_id == goal_uuid).count() == 1
    run = db_session.query(PlannerRun).filter(PlannerRun.goal_id == goal_uuid).one()
    assert run.status == PlannerRunStatus.SUCCESS
    assert run.prompt_version == "planner_v5"


def test_generate_plan_twice_rejects_second_call(client, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([VALID_PLAN_JSON, VALID_PLAN_JSON]))

    first = _generate(client, goal_id)
    assert first.status_code == 201

    second = _generate(client, goal_id)
    assert second.status_code == 409

    # Still exactly one plan for the goal - the rejected second call
    # shouldn't have touched anything.
    response = client.get(f"/api/v1/planner/goals/{goal_id}")
    assert response.status_code == 200
    assert response.json()["id"] == first.json()["id"]


def test_get_latest_plan_404_before_any_generation(client):
    goal_id = _create_goal(client)
    response = client.get(f"/api/v1/planner/goals/{goal_id}")
    assert response.status_code == 404


def test_generate_plan_goal_not_found(client, override_llm):
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    response = _generate(client, "00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_generate_plan_recovers_after_one_invalid_response(client, override_llm):
    goal_id = _create_goal(client)
    fake = FakeLLMProvider(["not json at all", VALID_PLAN_JSON])
    override_llm(fake)

    response = _generate(client, goal_id)

    assert response.status_code == 201
    assert fake.call_count == 2


def test_generate_plan_fails_after_two_invalid_responses(client, db_session, override_llm):
    goal_id = _create_goal(client)
    fake = FakeLLMProvider(["not json", "still not json"])
    override_llm(fake)

    response = _generate(client, goal_id)

    assert response.status_code == 502
    assert fake.call_count == 2
    goal_uuid = uuid.UUID(goal_id)
    run = db_session.query(PlannerRun).filter(PlannerRun.goal_id == goal_uuid).one()
    assert run.status == PlannerRunStatus.FAILED
    assert run.error_message is not None
    assert db_session.query(Plan).filter(Plan.goal_id == goal_uuid).count() == 0


def test_generate_plan_llm_timeout(client, db_session, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([LLMTimeoutError("timed out")]))

    response = _generate(client, goal_id)

    assert response.status_code == 504
    run = db_session.query(PlannerRun).filter(PlannerRun.goal_id == uuid.UUID(goal_id)).one()
    assert run.status == PlannerRunStatus.FAILED


def test_generate_plan_llm_request_error(client, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([LLMRequestError("no api key")]))

    response = _generate(client, goal_id)

    assert response.status_code == 502


def test_generate_plan_rejects_empty_timeline(client, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))

    response = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "", "availability": "10 hours/week", "constraints": []},
    )
    assert response.status_code == 422


def test_get_plan_by_id(client, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    plan_id = _generate(client, goal_id).json()["id"]

    response = client.get(f"/api/v1/planner/plans/{plan_id}")
    assert response.status_code == 200
    assert response.json()["id"] == plan_id
    # memories_used is only set by generate/regenerate's own response
    # (see api/v1/planner.py) - a plain re-fetch doesn't run memory
    # lookup again, so it stays null rather than a stale/misleading 0.
    assert response.json()["memories_used"] is None


def test_get_plan_by_id_not_found(client):
    response = client.get("/api/v1/planner/plans/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_regenerate_plan_updates_in_place(client, db_session, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    original = _generate(client, goal_id).json()

    override_llm(FakeLLMProvider([ADJUSTED_PLAN_JSON]))
    response = client.post(
        f"/api/v1/planner/plans/{original['id']}/regenerate",
        json={"adjustment": "Make it more realistic"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == original["id"]  # same Plan row, not a new one
    assert body["mission"] != original["mission"]
    assert body["estimated_duration"] == "120 days"
    assert len(body["milestones"]) == 1

    # Still exactly one plan for this goal.
    goal_uuid = uuid.UUID(goal_id)
    assert db_session.query(Plan).filter(Plan.goal_id == goal_uuid).count() == 1

    runs = (
        db_session.query(PlannerRun)
        .filter(PlannerRun.goal_id == goal_uuid)
        .order_by(PlannerRun.created_at)
        .all()
    )
    assert [r.prompt_version for r in runs] == ["planner_v5", "planner_v5_regenerate"]


def test_regenerate_plan_failure_leaves_plan_untouched(client, db_session, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    original = _generate(client, goal_id).json()

    override_llm(FakeLLMProvider([LLMTimeoutError("timed out")]))
    response = client.post(
        f"/api/v1/planner/plans/{original['id']}/regenerate",
        json={"adjustment": "Make it more realistic"},
    )

    assert response.status_code == 504

    # The original plan is still there, unchanged.
    current = client.get(f"/api/v1/planner/goals/{goal_id}").json()
    assert current["mission"] == original["mission"]
    assert current["id"] == original["id"]

    run = (
        db_session.query(PlannerRun)
        .filter(PlannerRun.prompt_version == "planner_v5_regenerate")
        .one()
    )
    assert run.status == PlannerRunStatus.FAILED


def test_regenerate_plan_not_found(client, override_llm):
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    response = client.post(
        "/api/v1/planner/plans/00000000-0000-0000-0000-000000000000/regenerate",
        json={"adjustment": "Make it more realistic"},
    )
    assert response.status_code == 404


def test_regenerate_plan_rejects_empty_adjustment(client, override_llm):
    goal_id = _create_goal(client)
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    original = _generate(client, goal_id).json()

    response = client.post(
        f"/api/v1/planner/plans/{original['id']}/regenerate",
        json={"adjustment": ""},
    )
    assert response.status_code == 422


def test_v5_system_prompt_generalizes_memory_reasoning_beyond_its_own_examples():
    """Locks in the intent behind the v4->v5 bump: the model should reason
    over whatever User Context it's given, not just the two illustrative
    cases (time-of-day preference, disliked workload) named in the prompt
    itself - this can't be proven by a FakeLLMProvider-based test (that
    would require judging real model reasoning), but the instruction
    telling it to generalize should always be present in the text we
    actually send. See app/planner/prompts.py's PLANNER_V5_SYSTEM_PROMPT
    for the full rule."""
    assert "not an exhaustive list" in PLANNER_V5_SYSTEM_PROMPT
    assert "whatever User Context is actually provided" in PLANNER_V5_SYSTEM_PROMPT
    # The two illustrative examples from the sprint spec are present as
    # *examples*, not hardcoded branches - proven by the fact that this
    # is plain text inside a prompt string, not a code path keyed on
    # these phrases anywhere in planner_service.py.
    assert "prefers evenings" in PLANNER_V5_SYSTEM_PROMPT
    assert "dislikes weekend work" in PLANNER_V5_SYSTEM_PROMPT
