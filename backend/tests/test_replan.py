"""
Adaptive Planning Engine tests.

Two layers, matching adaptive_planning_service's own split:
  - Direct service-level tests (build Plan/PlanTask rows via db_session,
    call propose_replan/apply_replan directly) - the fastest way to cover
    the actual scheduling logic (overdue detection, redistribution,
    budget spillover, deadline risk) without going through the API or an
    LLM at all, since propose_replan/apply_replan never touch either.
  - API-level tests (via `client`, using the same self-contained
    FakeLLMProvider pattern as test_execution.py) - covering the HTTP
    contract: propose doesn't persist, accept does and logs history,
    ownership 404s.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.main import app
from app.models.goal import Goal
from app.models.plan import Plan
from app.models.plan_task import PlanTask, PlanTaskStatus
from app.models.user import User
from app.planner.llm.base import LLMProvider
from app.planner.llm.factory import get_llm_provider
from app.services import adaptive_planning_service

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
                        "estimated_minutes": 90,
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


class FakeLLMProvider(LLMProvider):
    def __init__(self, responses: list):
        self._responses = list(responses)

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
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


def _make_plan(db_session, *, created_at, deadline=None) -> Plan:
    user = User(email=f"replan-{uuid.uuid4().hex[:8]}@lifeos.local", name="Replan Tester")
    db_session.add(user)
    db_session.flush()
    goal = Goal(user_id=user.id, title="Learn to juggle", deadline=deadline)
    db_session.add(goal)
    db_session.flush()
    plan = Plan(
        goal_id=goal.id,
        mission="Learn to juggle three balls.",
        estimated_duration="4 weeks",
        timeline=["Week 1-4: Practice"],
        weekly_plan=[],
    )
    plan.created_at = created_at
    db_session.add(plan)
    db_session.flush()
    return plan


def _add_task(db_session, plan, *, week, minutes, order, status=PlanTaskStatus.PENDING):
    task = PlanTask(
        plan_id=plan.id,
        week_number=week,
        title=f"Task w{week}#{order}",
        estimated_minutes=minutes,
        display_order=order,
        status=status,
    )
    db_session.add(task)
    db_session.flush()
    return task


# --- Direct service-level tests ---------------------------------------


def test_propose_no_overdue_is_a_noop(db_session):
    plan = _make_plan(db_session, created_at=datetime.now(timezone.utc))
    t1 = _add_task(db_session, plan, week=1, minutes=60, order=0)
    db_session.commit()

    proposal = adaptive_planning_service.propose_replan(plan, [t1])

    assert proposal.changes == []
    assert "No overdue tasks" in proposal.reason
    assert proposal.task_assignments == [
        adaptive_planning_service.TaskAssignment(task_id=t1.id, week_number=1, day_number=None)
    ]


def test_propose_redistributes_overdue_tasks_into_current_week(db_session):
    # Plan started 10 days ago -> week 1 (days 0-6) is long over, we're
    # into week 2 (day 10 // 7 + 1 = 2).
    plan = _make_plan(db_session, created_at=datetime.now(timezone.utc) - timedelta(days=10))
    t1 = _add_task(db_session, plan, week=1, minutes=60, order=0)
    t2 = _add_task(db_session, plan, week=1, minutes=60, order=1)
    db_session.commit()

    proposal = adaptive_planning_service.propose_replan(plan, [t1, t2])

    assert "2 overdue tasks detected" in proposal.reason
    assert {c.task_id for c in proposal.changes} == {t1.id, t2.id}
    assert all(c.previous_week == 1 and c.new_week == 2 for c in proposal.changes)
    assert proposal.remaining_effort_minutes == 120


def test_propose_spills_over_into_a_new_week_when_over_budget(db_session):
    # Two overdue weeks (1 and 2), each originally totaling 180 minutes -
    # that average (180) becomes the per-week budget. 20 elapsed days ->
    # current week = 20 // 7 + 1 = 3.
    plan = _make_plan(db_session, created_at=datetime.now(timezone.utc) - timedelta(days=20))
    t1 = _add_task(db_session, plan, week=1, minutes=90, order=0)
    t2 = _add_task(db_session, plan, week=1, minutes=90, order=1)
    t3 = _add_task(db_session, plan, week=2, minutes=90, order=2)
    t4 = _add_task(db_session, plan, week=2, minutes=90, order=3)
    db_session.commit()

    proposal = adaptive_planning_service.propose_replan(plan, [t1, t2, t3, t4])

    by_id = {a.task_id: a for a in proposal.task_assignments}
    # First two (budget 90+90=180, exactly at capacity) fit in week 3;
    # the next two overflow into week 4.
    assert by_id[t1.id].week_number == 3
    assert by_id[t2.id].week_number == 3
    assert by_id[t3.id].week_number == 4
    assert by_id[t4.id].week_number == 4
    assert proposal.remaining_effort_minutes == 360


def test_propose_flags_deadline_at_risk(db_session):
    now = datetime.now(timezone.utc)
    near_deadline = now + timedelta(days=3)  # long before the pushed-out estimate
    plan = _make_plan(db_session, created_at=now - timedelta(days=10), deadline=near_deadline)
    t1 = _add_task(db_session, plan, week=1, minutes=60, order=0)
    db_session.commit()

    proposal = adaptive_planning_service.propose_replan(plan, [t1])

    assert proposal.deadline_at_risk is True


def test_propose_no_risk_when_deadline_is_comfortable(db_session):
    now = datetime.now(timezone.utc)
    plan = _make_plan(db_session, created_at=now, deadline=now + timedelta(days=365))
    t1 = _add_task(db_session, plan, week=1, minutes=60, order=0)
    db_session.commit()

    proposal = adaptive_planning_service.propose_replan(plan, [t1])

    assert proposal.deadline_at_risk is False


def test_apply_replan_persists_new_weeks_and_logs_history(db_session):
    plan = _make_plan(db_session, created_at=datetime.now(timezone.utc) - timedelta(days=10))
    t1 = _add_task(db_session, plan, week=1, minutes=60, order=0)
    db_session.commit()
    db_session.refresh(plan)

    proposal = adaptive_planning_service.propose_replan(plan, [t1])
    adaptive_planning_service.apply_replan(db_session, plan=plan, proposal=proposal)

    db_session.refresh(t1)
    assert t1.week_number == 2

    history = adaptive_planning_service.get_replan_history(db_session, plan_id=plan.id)
    assert len(history) == 1
    assert "overdue" in history[0].reason
    assert history[0].summary["remaining_effort_minutes"] == 60


def test_apply_replan_skips_a_task_completed_since_the_proposal(db_session):
    plan = _make_plan(db_session, created_at=datetime.now(timezone.utc) - timedelta(days=10))
    t1 = _add_task(db_session, plan, week=1, minutes=60, order=0)
    db_session.commit()
    db_session.refresh(plan)

    proposal = adaptive_planning_service.propose_replan(plan, [t1])
    # Simulate the task being completed in the gap between propose and
    # accept - apply_replan should leave it alone rather than reopening
    # its schedule.
    t1.status = PlanTaskStatus.COMPLETED
    db_session.commit()
    db_session.refresh(plan)

    adaptive_planning_service.apply_replan(db_session, plan=plan, proposal=proposal)

    db_session.refresh(t1)
    assert t1.week_number == 1
    assert t1.status == PlanTaskStatus.COMPLETED


# --- API-level tests -----------------------------------------------------


def _generate_plan_via_api(client, override_llm) -> tuple[str, str]:
    goal_id = client.post("/api/v1/goals", json={"title": "Build LifeOS MVP"}).json()["id"]
    override_llm(FakeLLMProvider([VALID_PLAN_JSON]))
    plan = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "90 days", "availability": "10 hours/week", "constraints": []},
    ).json()
    return goal_id, plan["id"]


def _backdate_plan(db_session, plan_id: str, days: int) -> None:
    plan = db_session.query(Plan).filter(Plan.id == uuid.UUID(plan_id)).first()
    plan.created_at = datetime.now(timezone.utc) - timedelta(days=days)
    db_session.commit()


def test_replan_propose_does_not_persist_changes(client, db_session, override_llm):
    _goal_id, plan_id = _generate_plan_via_api(client, override_llm)
    _backdate_plan(db_session, plan_id, days=10)

    before = client.get(f"/api/v1/plans/{plan_id}/tasks").json()
    before_weeks = {t["id"]: t["week_number"] for w in before["weeks"] for t in w["tasks"]}

    response = client.post(f"/api/v1/planner/plans/{plan_id}/replan")
    assert response.status_code == 200
    proposal = response.json()
    assert len(proposal["changes"]) > 0

    after = client.get(f"/api/v1/plans/{plan_id}/tasks").json()
    after_weeks = {t["id"]: t["week_number"] for w in after["weeks"] for t in w["tasks"]}
    assert before_weeks == after_weeks  # nothing persisted yet


def test_replan_accept_applies_and_returns_updated_tasks(client, db_session, override_llm):
    _goal_id, plan_id = _generate_plan_via_api(client, override_llm)
    _backdate_plan(db_session, plan_id, days=10)

    proposal = client.post(f"/api/v1/planner/plans/{plan_id}/replan").json()
    changed_ids = {c["task_id"] for c in proposal["changes"]}
    assert changed_ids  # sanity check the fixture actually produced overdue changes

    response = client.post(f"/api/v1/planner/plans/{plan_id}/replan/accept", json=proposal)
    assert response.status_code == 200
    updated = response.json()
    updated_weeks = {t["id"]: t["week_number"] for w in updated["weeks"] for t in w["tasks"]}

    # The accept response's task list matches what's actually persisted...
    persisted = client.get(f"/api/v1/plans/{plan_id}/tasks").json()
    persisted_weeks = {t["id"]: t["week_number"] for w in persisted["weeks"] for t in w["tasks"]}
    assert updated_weeks == persisted_weeks

    # ...and every task the proposal said would move no longer sits in
    # its original (now-overdue) week 1.
    assert all(persisted_weeks[task_id] != 1 for task_id in changed_ids)


def test_replan_history_lists_accepted_event(client, db_session, override_llm):
    _goal_id, plan_id = _generate_plan_via_api(client, override_llm)
    _backdate_plan(db_session, plan_id, days=10)

    proposal = client.post(f"/api/v1/planner/plans/{plan_id}/replan").json()
    client.post(f"/api/v1/planner/plans/{plan_id}/replan/accept", json=proposal)

    history = client.get(f"/api/v1/planner/plans/{plan_id}/replan/history").json()
    assert len(history) == 1
    assert history[0]["reason"] == proposal["reason"]


def test_replan_propose_plan_not_found(client):
    response = client.post("/api/v1/planner/plans/00000000-0000-0000-0000-000000000000/replan")
    assert response.status_code == 404


def test_replan_accept_plan_not_found(client):
    response = client.post(
        "/api/v1/planner/plans/00000000-0000-0000-0000-000000000000/replan/accept",
        json={
            "reason": "test",
            "changes": [],
            "remaining_effort_minutes": 0,
            "new_completion_estimate": None,
            "deadline_at_risk": False,
            "task_assignments": [],
        },
    )
    assert response.status_code == 404
