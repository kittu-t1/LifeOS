"""
Execution Engine tests (PlanTask completion + progress). Uses the same
FakeLLMProvider pattern as test_planner.py to generate a real Plan (and
its PlanTask rows) to exercise against, without calling OpenAI.
"""

import json

import pytest

from app.main import app
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
                ],
            },
        ],
        "timeline": ["Weeks 1-2: Foundation"],
    }
)

ADJUSTED_PLAN_JSON = json.dumps(
    {
        "mission": "Ship a smaller MVP first.",
        "estimated_duration": "60 days",
        "milestones": [
            {"title": "Foundation", "description": "Backend only.", "duration": "1 week"},
        ],
        "weekly_plan": [
            {
                "week": 1,
                "focus": "Setup",
                "tasks": [
                    {
                        "title": "Scaffold backend only",
                        "description": "Skip the frontend for now.",
                        "estimated_minutes": 90,
                    },
                ],
            },
        ],
        "timeline": ["Week 1: Foundation"],
    }
)


class FakeLLMProvider(LLMProvider):
    def __init__(self, responses: list):
        self._responses = list(responses)
        self.call_count = 0

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
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


def _create_goal_with_plan(client, override_llm, responses=None) -> tuple[str, str]:
    """Returns (goal_id, plan_id) for a freshly generated plan."""
    goal_id = client.post("/api/v1/goals", json={"title": "Build LifeOS MVP"}).json()["id"]
    override_llm(FakeLLMProvider(responses or [VALID_PLAN_JSON]))
    plan = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "90 days", "availability": "10 hours/week", "constraints": []},
    ).json()
    return goal_id, plan["id"]


def test_generate_plan_creates_plan_tasks(client, override_llm):
    _goal_id, plan_id = _create_goal_with_plan(client, override_llm)

    response = client.get(f"/api/v1/plans/{plan_id}/tasks")
    assert response.status_code == 200
    body = response.json()

    assert [w["week_number"] for w in body["weeks"]] == [1, 2]
    week1_titles = [t["title"] for t in body["weeks"][0]["tasks"]]
    assert week1_titles == ["Scaffold backend", "Scaffold frontend"]
    assert body["weeks"][0]["tasks"][0]["estimated_minutes"] == 90
    assert all(t["status"] == "pending" for w in body["weeks"] for t in w["tasks"])
    assert all(t["completed_at"] is None for w in body["weeks"] for t in w["tasks"])


def test_get_tasks_plan_not_found(client):
    response = client.get("/api/v1/plans/00000000-0000-0000-0000-000000000000/tasks")
    assert response.status_code == 404


def test_complete_task_sets_status_and_completed_at(client, override_llm):
    _goal_id, plan_id = _create_goal_with_plan(client, override_llm)
    task_id = client.get(f"/api/v1/plans/{plan_id}/tasks").json()["weeks"][0]["tasks"][0]["id"]

    response = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "completed"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["completed_at"] is not None


def test_reopen_task_clears_completed_at(client, override_llm):
    _goal_id, plan_id = _create_goal_with_plan(client, override_llm)
    task_id = client.get(f"/api/v1/plans/{plan_id}/tasks").json()["weeks"][0]["tasks"][0]["id"]
    client.patch(f"/api/v1/tasks/{task_id}", json={"status": "completed"})

    response = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "pending"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["completed_at"] is None


def test_update_task_not_found(client):
    response = client.patch(
        "/api/v1/tasks/00000000-0000-0000-0000-000000000000", json={"status": "completed"}
    )
    assert response.status_code == 404


def test_update_task_rejects_invalid_status(client, override_llm):
    _goal_id, plan_id = _create_goal_with_plan(client, override_llm)
    task_id = client.get(f"/api/v1/plans/{plan_id}/tasks").json()["weeks"][0]["tasks"][0]["id"]

    response = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "archived"})
    assert response.status_code == 422


def test_progress_reflects_completed_tasks(client, override_llm):
    _goal_id, plan_id = _create_goal_with_plan(client, override_llm)

    zero = client.get(f"/api/v1/plans/{plan_id}/progress").json()
    assert zero == {"completed": 0, "total": 3, "remaining": 3, "percentage": 0}

    tasks = client.get(f"/api/v1/plans/{plan_id}/tasks").json()
    all_task_ids = [t["id"] for w in tasks["weeks"] for t in w["tasks"]]
    client.patch(f"/api/v1/tasks/{all_task_ids[0]}", json={"status": "completed"})

    one_done = client.get(f"/api/v1/plans/{plan_id}/progress").json()
    assert one_done == {"completed": 1, "total": 3, "remaining": 2, "percentage": 33}


def test_progress_zero_tasks_does_not_divide_by_zero(client, db_session):
    # A goal with no plan at all isn't reachable via /plans/{id}/progress
    # (404s first), but a plan with an empty weekly_plan is a real edge
    # case worth covering directly at the service level.
    from app.models.goal import Goal
    from app.models.plan import Plan
    from app.models.user import User
    from app.services import progress_service

    user = User(email="progress-edge@lifeos.local", name="Edge Case")
    db_session.add(user)
    db_session.flush()
    goal = Goal(user_id=user.id, title="Empty plan goal")
    db_session.add(goal)
    db_session.flush()
    plan = Plan(
        goal_id=goal.id,
        mission="Nothing generated yet.",
        estimated_duration="unknown",
        timeline=[],
        weekly_plan=[],
    )
    db_session.add(plan)
    db_session.commit()

    summary = progress_service.calculate_progress(db_session, plan_id=plan.id)
    assert summary.total == 0
    assert summary.percentage == 0


def test_regenerate_replaces_tasks_wholesale(client, override_llm):
    goal_id, plan_id = _create_goal_with_plan(client, override_llm)
    before = client.get(f"/api/v1/plans/{plan_id}/tasks").json()
    before_ids = {t["id"] for w in before["weeks"] for t in w["tasks"]}
    assert len(before_ids) == 3

    override_llm(FakeLLMProvider([ADJUSTED_PLAN_JSON]))
    client.post(
        f"/api/v1/planner/plans/{plan_id}/regenerate", json={"adjustment": "make it smaller"}
    )

    after = client.get(f"/api/v1/plans/{plan_id}/tasks").json()
    after_ids = {t["id"] for w in after["weeks"] for t in w["tasks"]}
    assert len(after_ids) == 1
    assert before_ids.isdisjoint(after_ids)
    assert after["weeks"][0]["tasks"][0]["title"] == "Scaffold backend only"
