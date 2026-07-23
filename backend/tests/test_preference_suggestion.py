"""
Planner preference-suggestion tests.

Covers the whole "detect, suggest, let the user decide" flow this sprint
added on top of the Memory Personalization work:
  - Unit tests for the pure detector (app/planner/preference_detection.py)
    - what it does and doesn't match, independent of the DB or an LLM.
  - Integration tests for generate/regenerate: does a preference-shaped
    constraint/adjustment actually surface as PlanRead.suggested_memory,
    does an already-saved identical memory suppress it, and does
    ordinary non-preference text correctly suggest nothing.
  - Confirms nothing is EVER written to the memories table just from
    calling generate/regenerate - detection is suggest-only. The "Accept"
    half of the flow is exercised as a plain call to the existing
    POST /api/v1/memories endpoint (already covered by test_memory.py's
    CRUD tests), proving the suggestion is forward-compatible with that
    endpoint's schema without any change to it.
"""

from __future__ import annotations

import json

import pytest

from app.main import app
from app.memory.models.memory import Memory
from app.planner.llm.base import LLMProvider
from app.planner.llm.factory import get_llm_provider
from app.planner.preference_detection import detect_preference_statement

VALID_PLAN_JSON = json.dumps(
    {
        "mission": "Ship a working LifeOS MVP that proves the core loop.",
        "estimated_duration": "90 days",
        "milestones": [
            {"title": "Foundation", "description": "Backend + DB in place.", "duration": "2 weeks"}
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
                    }
                ],
            }
        ],
        "timeline": ["Weeks 1-2: Foundation"],
    }
)


class FakeLLMProvider(LLMProvider):
    def __init__(self, responses: list):
        self._responses = list(responses)

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        return self._responses.pop(0)


@pytest.fixture()
def override_llm():
    def _set(fake: LLMProvider) -> None:
        app.dependency_overrides[get_llm_provider] = lambda: fake

    yield _set
    app.dependency_overrides.pop(get_llm_provider, None)


# --- Unit tests: the pure detector ---------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "I only study after work.",
        "I always work out in the mornings.",
        "I never schedule anything on Sundays.",
        "I usually finish backend tasks faster than expected.",
        "I prefer short, focused sessions.",
        "I like to batch similar tasks together.",
        "I need to keep weekends completely free.",
        "I want to avoid working late at night.",
        "I work best in 90-minute blocks.",
    ],
)
def test_detect_preference_statement_matches_common_phrasings(text):
    assert detect_preference_statement(text) == text


def test_detect_preference_statement_returns_none_for_ordinary_text():
    assert detect_preference_statement("Make it more realistic") is None
    assert detect_preference_statement("Add more buffer time") is None
    assert detect_preference_statement("") is None
    assert detect_preference_statement(None) is None


def test_detect_preference_statement_ignores_mid_sentence_occurrences():
    # "I only" appears, but not as the start of a standalone sentence -
    # this is a subordinate clause explaining a constraint, not a clean,
    # quotable preference statement on its own.
    text = "Add more buffer time since I only have evenings free"
    assert detect_preference_statement(text) is None


def test_detect_preference_statement_finds_the_first_matching_sentence_across_multiple_texts():
    result = detect_preference_statement(
        "Keep it under budget.", "I only study after work. Also cut the last milestone."
    )
    assert result == "I only study after work."


# --- Integration: generate/regenerate surface a suggestion ---------------


def _create_goal(client, title="Learn guitar") -> str:
    return client.post("/api/v1/goals", json={"title": title}).json()["id"]


def test_generate_plan_surfaces_a_preference_suggestion(client, db_session, override_llm):
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    goal_id = _create_goal(client)

    response = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={
            "timeline": "90 days",
            "availability": "5 hours/week",
            "constraints": ["I only study after work."],
        },
    )

    assert response.status_code == 201
    suggestion = response.json()["suggested_memory"]
    assert suggestion is not None
    assert suggestion["value"] == "I only study after work."
    assert suggestion["category"] == "preference"
    assert suggestion["key"]

    # Suggest-only: generate_plan must never write a Memory row itself.
    assert db_session.query(Memory).count() == 0


def test_regenerate_plan_surfaces_a_preference_suggestion(client, override_llm):
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    goal_id = _create_goal(client)
    plan_id = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "90 days", "availability": "5 hours/week", "constraints": []},
    ).json()["id"]

    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    response = client.post(
        f"/api/v1/planner/plans/{plan_id}/regenerate",
        json={"adjustment": "I prefer shorter sessions in the evening."},
    )

    assert response.status_code == 200
    suggestion = response.json()["suggested_memory"]
    assert suggestion is not None
    assert suggestion["value"] == "I prefer shorter sessions in the evening."


def test_generate_plan_suggests_nothing_for_ordinary_constraints(client, override_llm):
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    goal_id = _create_goal(client)

    response = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={
            "timeline": "90 days",
            "availability": "5 hours/week",
            "constraints": ["Keep it under 5 hours a week", "No weekend work"],
        },
    )

    assert response.status_code == 201
    assert response.json()["suggested_memory"] is None


def test_generate_plan_suppresses_suggestion_when_memory_already_exists(client, override_llm):
    client.post(
        "/api/v1/memories",
        json={
            "category": "preference",
            "key": "planner_detected_preference",
            "value": "I only study after work.",
        },
    )

    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    goal_id = _create_goal(client)

    response = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={
            "timeline": "90 days",
            "availability": "5 hours/week",
            "constraints": ["I only study after work."],
        },
    )

    assert response.status_code == 201
    # Already have this exact memory - nothing new worth asking about.
    assert response.json()["suggested_memory"] is None


def test_accepted_suggestion_round_trips_through_the_existing_memory_api(client, override_llm):
    """Proves SuggestedMemory's shape is forward-compatible with the
    existing memory-create endpoint without any change to it - this is
    what the frontend's "Accept" button does under the hood."""
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    goal_id = _create_goal(client)
    response = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={
            "timeline": "90 days",
            "availability": "5 hours/week",
            "constraints": ["I only study after work."],
        },
    )
    suggestion = response.json()["suggested_memory"]

    accept_response = client.post("/api/v1/memories", json=suggestion)

    assert accept_response.status_code == 201
    saved = accept_response.json()
    assert saved["value"] == "I only study after work."
    assert saved["category"] == "preference"
    assert saved["source"] == "manual"  # default when the caller omits it, same as any manual entry
