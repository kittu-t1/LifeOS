"""
Recurring Task System tests.

Three layers:
  - Pure recurrence engine tests (no DB) - each pattern type, pause,
    start/end-date clipping.
  - Direct habit_service tests (via db_session) - occurrence sync
    idempotency, pause/resume, editing a recurrence rule, completion,
    the planner-context helpers.
  - API tests (via `client`) - CRUD, pause/resume, occurrences,
    ownership.
  - Integration tests confirming the Planner prompt and Adaptive
    Planning capacity actually account for active habits.
"""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.main import app
from app.models.goal import Goal
from app.models.habit import (
    Habit,
    HabitOccurrence,
    HabitOccurrenceStatus,
    HabitStatus,
    RecurrenceType,
)
from app.models.plan import Plan
from app.models.plan_task import PlanTask, PlanTaskStatus
from app.models.user import User
from app.planner.llm.base import LLMProvider
from app.planner.llm.factory import get_llm_provider
from app.planner.prompts import build_regenerate_user_prompt, build_user_prompt
from app.services import adaptive_planning_service, habit_service, recurrence


def _habit(
    *,
    recurrence_type: RecurrenceType,
    start_date: date,
    recurrence_config: dict | None = None,
    end_date: date | None = None,
    status: HabitStatus = HabitStatus.ACTIVE,
    estimated_minutes: int | None = None,
) -> Habit:
    return Habit(
        title="Test Habit",
        recurrence_type=recurrence_type,
        recurrence_config=recurrence_config or {},
        start_date=start_date,
        end_date=end_date,
        status=status,
        estimated_minutes=estimated_minutes,
    )


# --- Recurrence engine (pure, no DB) --------------------------------------


def test_daily_generates_every_day():
    habit = _habit(recurrence_type=RecurrenceType.DAILY, start_date=date(2026, 1, 1))
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 1, 5)
    )
    assert dates == [date(2026, 1, d) for d in range(1, 6)]


def test_weekdays_skips_weekend():
    # 2026-01-01 is a Thursday; 01-03/01-04 are Sat/Sun.
    habit = _habit(recurrence_type=RecurrenceType.WEEKDAYS, start_date=date(2026, 1, 1))
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 1, 7)
    )
    assert dates == [
        date(2026, 1, 1),
        date(2026, 1, 2),
        date(2026, 1, 5),
        date(2026, 1, 6),
        date(2026, 1, 7),
    ]


def test_weekly_matches_configured_days():
    # Mon=0, Wed=2 -> 2026-01-05 (Mon) and 2026-01-07 (Wed).
    habit = _habit(
        recurrence_type=RecurrenceType.WEEKLY,
        start_date=date(2026, 1, 1),
        recurrence_config={"days_of_week": [0, 2]},
    )
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 1, 8)
    )
    assert dates == [date(2026, 1, 5), date(2026, 1, 7)]


def test_monthly_matches_day_of_month():
    habit = _habit(
        recurrence_type=RecurrenceType.MONTHLY,
        start_date=date(2026, 1, 15),
        recurrence_config={"day_of_month": 15},
    )
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 3, 31)
    )
    assert dates == [date(2026, 1, 15), date(2026, 2, 15), date(2026, 3, 15)]


def test_custom_interval_every_n_days():
    habit = _habit(
        recurrence_type=RecurrenceType.CUSTOM_INTERVAL,
        start_date=date(2026, 1, 1),
        recurrence_config={"interval_days": 3},
    )
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 1, 10)
    )
    assert dates == [date(2026, 1, 1), date(2026, 1, 4), date(2026, 1, 7), date(2026, 1, 10)]


def test_paused_habit_generates_nothing():
    habit = _habit(
        recurrence_type=RecurrenceType.DAILY, start_date=date(2026, 1, 1), status=HabitStatus.PAUSED
    )
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 1, 5)
    )
    assert dates == []


def test_end_date_clips_generation():
    habit = _habit(
        recurrence_type=RecurrenceType.DAILY, start_date=date(2026, 1, 1), end_date=date(2026, 1, 3)
    )
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 1, 10)
    )
    assert dates == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]


def test_start_date_clips_generation():
    habit = _habit(recurrence_type=RecurrenceType.DAILY, start_date=date(2026, 1, 5))
    dates = recurrence.generate_occurrence_dates(
        habit, range_start=date(2026, 1, 1), range_end=date(2026, 1, 7)
    )
    assert dates == [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7)]


# --- habit_service (direct, via db_session) -------------------------------


def _make_user(db_session) -> User:
    user = User(email=f"habits-{uuid.uuid4().hex[:8]}@lifeos.local", name="Habit Tester")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_create_habit_generates_occurrence_window(db_session):
    user = _make_user(db_session)
    from app.schemas.habit import HabitCreate

    today = datetime.now(timezone.utc).date()
    habit = habit_service.create_habit(
        db_session,
        user_id=user.id,
        data=HabitCreate(title="Workout", recurrence_type=RecurrenceType.DAILY, start_date=today),
    )

    occurrences = habit_service.list_occurrences(
        db_session, habit_id=habit.id, from_date=today, to_date=today + timedelta(days=60)
    )
    # 31 days: today plus the next 30 (OCCURRENCE_WINDOW_DAYS).
    assert len(occurrences) == 31
    assert all(o.status == HabitOccurrenceStatus.PENDING for o in occurrences)


def test_sync_occurrences_is_idempotent(db_session):
    user = _make_user(db_session)
    from app.schemas.habit import HabitCreate

    today = datetime.now(timezone.utc).date()
    habit = habit_service.create_habit(
        db_session,
        user_id=user.id,
        data=HabitCreate(title="Read", recurrence_type=RecurrenceType.DAILY, start_date=today),
    )

    habit_service.sync_occurrences(db_session, habit=habit)
    habit_service.sync_occurrences(db_session, habit=habit)

    count = db_session.query(HabitOccurrence).filter(HabitOccurrence.habit_id == habit.id).count()
    assert count == 31


def test_pause_stops_generation_resume_restarts_it(db_session):
    user = _make_user(db_session)
    from app.schemas.habit import HabitCreate

    today = datetime.now(timezone.utc).date()
    habit = habit_service.create_habit(
        db_session,
        user_id=user.id,
        data=HabitCreate(title="Meditate", recurrence_type=RecurrenceType.DAILY, start_date=today),
    )
    habit_service.pause_habit(db_session, habit=habit)

    # Delete all occurrences to prove sync truly no-ops while paused,
    # not just "happens to already have rows".
    db_session.query(HabitOccurrence).filter(HabitOccurrence.habit_id == habit.id).delete()
    db_session.commit()

    habit_service.sync_occurrences(db_session, habit=habit)
    count = db_session.query(HabitOccurrence).filter(HabitOccurrence.habit_id == habit.id).count()
    assert count == 0

    habit_service.resume_habit(db_session, habit=habit)
    count = db_session.query(HabitOccurrence).filter(HabitOccurrence.habit_id == habit.id).count()
    assert count == 31


def test_update_recurrence_clears_future_pending_but_not_completed(db_session):
    user = _make_user(db_session)
    from app.schemas.habit import HabitCreate, HabitUpdate

    today = datetime.now(timezone.utc).date()
    habit = habit_service.create_habit(
        db_session,
        user_id=user.id,
        data=HabitCreate(title="Journal", recurrence_type=RecurrenceType.DAILY, start_date=today),
    )
    # Complete today's occurrence before changing the schedule.
    today_occurrence = (
        db_session.query(HabitOccurrence)
        .filter(HabitOccurrence.habit_id == habit.id, HabitOccurrence.occurrence_date == today)
        .one()
    )
    habit_service.set_occurrence_status(
        db_session, occurrence=today_occurrence, status=HabitOccurrenceStatus.COMPLETED
    )

    habit_service.update_habit(
        db_session, habit=habit, data=HabitUpdate(recurrence_type=RecurrenceType.WEEKDAYS)
    )

    db_session.refresh(today_occurrence)
    # Completed occurrence survives even if today isn't a weekday match.
    assert today_occurrence.status == HabitOccurrenceStatus.COMPLETED

    remaining = habit_service.list_occurrences(
        db_session, habit_id=habit.id, from_date=today, to_date=today + timedelta(days=30)
    )
    assert all(d.weekday() < 5 for d in (o.occurrence_date for o in remaining) if d != today)


def test_set_occurrence_status_sets_and_clears_completed_at(db_session):
    user = _make_user(db_session)
    from app.schemas.habit import HabitCreate

    today = datetime.now(timezone.utc).date()
    habit = habit_service.create_habit(
        db_session,
        user_id=user.id,
        data=HabitCreate(title="Stretch", recurrence_type=RecurrenceType.DAILY, start_date=today),
    )
    occurrence = habit_service.list_occurrences(
        db_session, habit_id=habit.id, from_date=today, to_date=today
    )[0]

    completed = habit_service.set_occurrence_status(
        db_session, occurrence=occurrence, status=HabitOccurrenceStatus.COMPLETED
    )
    assert completed.completed_at is not None

    reopened = habit_service.set_occurrence_status(
        db_session, occurrence=completed, status=HabitOccurrenceStatus.PENDING
    )
    assert reopened.completed_at is None


def test_summarize_for_planner_describes_cadence():
    habit = _habit(
        recurrence_type=RecurrenceType.WEEKLY,
        start_date=date(2026, 1, 1),
        recurrence_config={"days_of_week": [0, 2, 4]},
        estimated_minutes=45,
    )
    habit.title = "Workout"
    [summary] = habit_service.summarize_for_planner([habit])
    assert summary == "Workout - every Mon, Wed, Fri (~45 min)"


def test_weekly_load_minutes_sums_occurrences_in_range():
    habit = _habit(
        recurrence_type=RecurrenceType.DAILY, start_date=date(2026, 1, 1), estimated_minutes=30
    )
    load = habit_service.weekly_load_minutes([habit], week_start=date(2026, 1, 5))
    assert load == 30 * 7


# --- API ------------------------------------------------------------------


def test_create_and_list_habit(client):
    response = client.post(
        "/api/v1/habits",
        json={
            "title": "Drink water",
            "recurrence_type": "daily",
            "start_date": "2026-01-01",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Drink water"
    assert body["status"] == "active"

    listed = client.get("/api/v1/habits").json()
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]


def test_get_habit_not_found(client):
    response = client.get("/api/v1/habits/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_pause_and_resume_habit(client):
    created = client.post(
        "/api/v1/habits",
        json={"title": "Walk", "recurrence_type": "daily", "start_date": "2026-01-01"},
    ).json()

    paused = client.post(f"/api/v1/habits/{created['id']}/pause").json()
    assert paused["status"] == "paused"

    resumed = client.post(f"/api/v1/habits/{created['id']}/resume").json()
    assert resumed["status"] == "active"


def test_list_occurrences_returns_upcoming_window(client):
    today = datetime.now(timezone.utc).date().isoformat()
    created = client.post(
        "/api/v1/habits",
        json={"title": "Read", "recurrence_type": "daily", "start_date": today},
    ).json()

    occurrences = client.get(f"/api/v1/habits/{created['id']}/occurrences").json()
    assert len(occurrences) == 31
    assert occurrences[0]["occurrence_date"] == today
    assert all(o["status"] == "pending" for o in occurrences)


def test_complete_todays_occurrence(client):
    today = datetime.now(timezone.utc).date().isoformat()
    created = client.post(
        "/api/v1/habits",
        json={"title": "Stretch", "recurrence_type": "daily", "start_date": today},
    ).json()
    occurrences = client.get(f"/api/v1/habits/{created['id']}/occurrences").json()
    today_occurrence = next(o for o in occurrences if o["occurrence_date"] == today)

    response = client.patch(
        f"/api/v1/habits/occurrences/{today_occurrence['id']}", json={"status": "completed"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["completed_at"] is not None


def test_update_occurrence_status_not_found(client):
    response = client.patch(
        "/api/v1/habits/occurrences/00000000-0000-0000-0000-000000000000",
        json={"status": "completed"},
    )
    assert response.status_code == 404


def test_update_habit_title(client):
    created = client.post(
        "/api/v1/habits",
        json={"title": "Old name", "recurrence_type": "daily", "start_date": "2026-01-01"},
    ).json()
    updated = client.patch(f"/api/v1/habits/{created['id']}", json={"title": "New name"}).json()
    assert updated["title"] == "New name"


# --- Planner / Adaptive Planning integration ------------------------------


def test_prompt_includes_existing_commitments():
    prompt = build_user_prompt(
        goal_title="Learn guitar",
        goal_description=None,
        timeline="60 days",
        availability="5 hours/week",
        constraints=[],
        existing_commitments=["Workout - every day (~45 min)"],
    )
    assert "Existing recurring commitments" in prompt
    assert "Workout - every day (~45 min)" in prompt


def test_prompt_omits_commitments_section_when_none():
    prompt = build_user_prompt(
        goal_title="Learn guitar",
        goal_description=None,
        timeline="60 days",
        availability="5 hours/week",
        constraints=[],
        existing_commitments=[],
    )
    assert "Existing recurring commitments" not in prompt


def test_regenerate_prompt_includes_existing_commitments():
    prompt = build_regenerate_user_prompt(
        goal_title="Learn guitar",
        goal_description=None,
        previous_plan={"mission": "x", "milestones": [], "weekly_plan": [], "timeline": []},
        adjustment="make it shorter",
        existing_commitments=["Workout - every day"],
    )
    assert "Existing recurring commitments" in prompt
    assert "Workout - every day" in prompt


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


class _RecordingFakeLLMProvider(LLMProvider):
    """Same fake-provider pattern as test_execution.py/test_replan.py, but
    also records the exact user_prompt it was called with - the only way
    to verify generate_plan actually threaded habit context into the
    prompt without mocking internals."""

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


def test_generate_plan_passes_active_habit_to_llm_prompt(client, override_llm):
    goal_id = client.post("/api/v1/goals", json={"title": "Build LifeOS MVP"}).json()["id"]
    client.post(
        "/api/v1/habits",
        json={
            "title": "Morning workout",
            "recurrence_type": "daily",
            "start_date": "2026-01-01",
            "estimated_minutes": 45,
        },
    )

    fake = _RecordingFakeLLMProvider([VALID_PLAN_JSON])
    override_llm(fake)
    response = client.post(
        f"/api/v1/planner/goals/{goal_id}/generate",
        json={"timeline": "90 days", "availability": "10 hours/week", "constraints": []},
    )
    assert response.status_code == 201
    assert "Morning workout" in fake.received_prompts[0]
    assert "Existing recurring commitments" in fake.received_prompts[0]


def test_propose_replan_shrinks_capacity_for_weeks_with_habit_load(db_session):
    user = User(email=f"replan-habit-{uuid.uuid4().hex[:8]}@lifeos.local", name="Tester")
    db_session.add(user)
    db_session.flush()
    goal = Goal(user_id=user.id, title="Get fit")
    db_session.add(goal)
    db_session.flush()

    plan_start = datetime.now(timezone.utc) - timedelta(days=10)
    plan = Plan(
        goal_id=goal.id,
        mission="Get fit",
        estimated_duration="4 weeks",
        timeline=[],
        weekly_plan=[],
    )
    plan.created_at = plan_start
    db_session.add(plan)
    db_session.flush()

    # Two overdue week-1 tasks, 90 min each (180 total, so budget=180).
    tasks = [
        PlanTask(
            plan_id=plan.id,
            week_number=1,
            title=f"Task {i}",
            estimated_minutes=90,
            display_order=i,
            status=PlanTaskStatus.PENDING,
        )
        for i in range(2)
    ]
    db_session.add_all(tasks)
    db_session.commit()

    # A heavy daily habit (100 min/day) that alone exceeds the 180/week
    # budget within days.
    heavy_habit = _habit(
        recurrence_type=RecurrenceType.DAILY,
        start_date=plan_start.date(),
        estimated_minutes=100,
    )

    without_habits = adaptive_planning_service.propose_replan(plan, tasks)
    with_habits = adaptive_planning_service.propose_replan(plan, tasks, active_habits=[heavy_habit])

    assignments_without = {a.task_id: a.week_number for a in without_habits.task_assignments}
    assignments_with = {a.task_id: a.week_number for a in with_habits.task_assignments}

    # Without habit load, both 90-minute tasks fit in the same week
    # (90+90=180, exactly at capacity). With a heavy habit eating most of
    # the week's capacity, they should spread across more weeks instead.
    assert len(set(assignments_without.values())) == 1
    assert len(set(assignments_with.values())) == 2
