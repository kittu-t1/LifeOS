"""
Adaptive Planning Service - the Adaptive Planning Engine's brain.

    PlannerService
        |
        v
    AdaptivePlanningService

Deliberately its own module, not folded into planner_service.py or
task_service.py, for the same reason the Execution Engine phase split
Planner/Execution/Progress: this service has one job - given a Plan's
current tasks, propose an updated schedule - and never generates task
content (planner_service's job) and never itself marks a task done
(task_service's job). It only ever *moves* existing PlanTask rows
(week_number/day_number), never replaces them, which is what lets a
replan preserve every task's id, title, and completed_at untouched.

Two-step, review-before-write flow, per the sprint spec ("do NOT
automatically overwrite the current plan - the user should review
first"):
  - propose_replan: pure computation, touches the database only to read.
    Returns a ReplanProposal describing what *would* change and why.
    Nothing is persisted.
  - apply_replan: takes a proposal the caller has already shown the user
    and the user accepted, writes the new week_number/day_number onto
    the real PlanTask rows, and logs the acceptance as a PlanReplanEvent
    (see app/models/plan_replan_event.py) - a lightweight history/audit
    trail, deliberately not full Plan versioning (each Plan row is still
    updated in place, same as regenerate), but the extension point for
    it if that's ever needed later.

No calendar integration here (out of scope - see docs/mvp_scope.md), but
"overdue" needs *some* notion of dates. This resolves that with the
smallest thing that works: Plan.created_at (which already exists) is
treated as "day 1 of week 1," and every week's date range is just
arithmetic from there (see week_window). No new date fields, no
external sync, no notifications - just enough to answer "is this task
late" using data the Plan already has.

Because propose_replan recomputes everything from the plan's *current*
state every time it's called, it also transparently handles the sprint's
other triggers without any special-casing: a changed Goal.deadline
changes what deadline_at_risk evaluates against on the very next call,
and "finished early" (no overdue tasks) is just the no-op path - see
the empty-`overdue` branch below.

Recurring Task System compatibility: propose_replan optionally takes the
user's active Habits and shrinks each week's redistribution budget by
their approximate time cost for that week (see
habit_service.weekly_load_minutes) - so a replanned week doesn't assume
time already claimed by a recurring commitment is free for goal tasks.
This module never reads or writes HabitOccurrence rows at all, which is
what actually guarantees "never delete/duplicate recurring tasks" - task
reassignment here only ever touches PlanTask ids, so a habit occurrence
is structurally impossible to reach from this code path, not just
avoided by convention.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.habit import Habit
from app.models.plan import Plan
from app.models.plan_replan_event import PlanReplanEvent
from app.models.plan_task import PlanTask, PlanTaskStatus
from app.services import habit_service, task_service

WEEK_LENGTH_DAYS = 7
# Fallback redistribution budget (task count, not minutes) used only when
# a plan has zero estimated_minutes data at all - i.e. every task came
# from a pre-planner_v2 generation. Real plans always have minute
# estimates (planner_v2's prompt requires them), so this is a legacy
# safety net, not the common path.
FALLBACK_TASKS_PER_WEEK = 3


@dataclass(frozen=True)
class TaskAssignment:
    """One task's placement - either proposed (inside a ReplanProposal,
    not yet saved) or the exact thing the accept endpoint is asked to
    apply. The same shape serves both directions on purpose: the
    frontend echoes a proposal's `task_assignments` straight back to
    /replan/accept rather than the server trying to remember a pending
    proposal server-side between the two calls (see app/api/v1/replan.py)."""

    task_id: uuid.UUID
    week_number: int
    day_number: int | None


@dataclass(frozen=True)
class TaskReschedule:
    """One task whose week actually changed - what the review UI lists
    under "Changes". Tasks whose placement didn't move don't appear here
    even though they're still present in task_assignments."""

    task_id: uuid.UUID
    title: str
    estimated_minutes: int | None
    previous_week: int
    new_week: int


@dataclass(frozen=True)
class ReplanProposal:
    plan_id: uuid.UUID
    reason: str
    changes: list[TaskReschedule]
    remaining_effort_minutes: int
    new_completion_estimate: date | None
    deadline_at_risk: bool
    task_assignments: list[TaskAssignment]


def week_window(plan_start: datetime, week_number: int) -> tuple[datetime, datetime]:
    """The [start, end) instant range week `week_number` covers, anchored
    to `plan_start` ("day 1 of week 1"). Both inputs/outputs are naive
    datetimes treated as UTC - see _naive_utc for why."""
    start = plan_start + timedelta(days=(week_number - 1) * WEEK_LENGTH_DAYS)
    return start, start + timedelta(days=WEEK_LENGTH_DAYS)


def task_due_at(plan_start: datetime, task: PlanTask) -> datetime:
    """A task is due at the end of its assigned day if day_number is set
    (forward-compatible - the planner doesn't produce day_number yet, see
    app/models/plan_task.py), otherwise at the end of its whole week."""
    week_start, week_end = week_window(plan_start, task.week_number)
    if task.day_number is not None:
        return week_start + timedelta(days=task.day_number)
    return week_end


def current_week_number(plan_start: datetime, now: datetime) -> int:
    if now <= plan_start:
        return 1
    return (now - plan_start).days // WEEK_LENGTH_DAYS + 1


def propose_replan(
    plan: Plan,
    tasks: list[PlanTask],
    *,
    now: datetime | None = None,
    active_habits: list[Habit] | None = None,
) -> ReplanProposal:
    """Computes (but does not save) an updated schedule. `tasks` should be
    every PlanTask belonging to `plan` (completed and pending) - pass
    task_service.get_tasks_for_plan's result. `active_habits` (see
    habit_service.list_active_habits) is optional context that shrinks
    each week's redistribution budget by recurring commitments already
    claiming part of it - omitting it just means habit load isn't
    factored in, not an error."""
    now = _naive_utc(now or datetime.now(timezone.utc))
    active_habits = active_habits or []
    plan_start = _naive_utc(plan.created_at)

    incomplete = sorted(
        (t for t in tasks if t.status == PlanTaskStatus.PENDING),
        key=lambda t: (t.week_number, t.display_order),
    )
    remaining_effort_minutes = sum(t.estimated_minutes or 0 for t in incomplete)
    overdue = [t for t in incomplete if task_due_at(plan_start, t) < now]

    if not overdue:
        assignments = [
            TaskAssignment(task_id=t.id, week_number=t.week_number, day_number=t.day_number)
            for t in incomplete
        ]
        max_week = max((t.week_number for t in tasks), default=1)
        return ReplanProposal(
            plan_id=plan.id,
            reason="No overdue tasks — this plan is on track.",
            changes=[],
            remaining_effort_minutes=remaining_effort_minutes,
            new_completion_estimate=week_window(plan_start, max_week)[1].date(),
            deadline_at_risk=_is_at_risk(plan, plan_start, max_week),
            task_assignments=assignments,
        )

    weekly_budget_minutes = _average_weekly_minutes(tasks)
    base_capacity = (
        weekly_budget_minutes if weekly_budget_minutes is not None else FALLBACK_TASKS_PER_WEEK
    )

    def _capacity_for_week(week_number: int) -> float:
        """base_capacity, minus whatever active habits already claim
        during that specific week - see habit_service.weekly_load_minutes.
        Only meaningful in minutes mode; the legacy task-count fallback
        has no time unit to subtract habit minutes from. Floors at 30
        minutes so a week is never made literally unschedulable even if
        habit load alone would exceed the budget."""
        if weekly_budget_minutes is None or not active_habits:
            return base_capacity
        week_start = week_window(plan_start, week_number)[0].date()
        habit_load = habit_service.weekly_load_minutes(active_habits, week_start=week_start)
        return max(30, base_capacity - habit_load)

    start_week = max(current_week_number(plan_start, now), incomplete[0].week_number)

    assignments = []
    changes: list[TaskReschedule] = []
    week_cursor = start_week
    load_used = 0
    capacity = _capacity_for_week(week_cursor)

    for task in incomplete:
        cost = (task.estimated_minutes or 0) if weekly_budget_minutes is not None else 1
        if load_used > 0 and load_used + cost > capacity:
            week_cursor += 1
            load_used = 0
            capacity = _capacity_for_week(week_cursor)

        new_week = week_cursor
        # A shifted task's specific day is no longer meaningful once its
        # week changes; a task that stayed in its original week keeps
        # whatever day it had.
        new_day = task.day_number if new_week == task.week_number else None

        assignments.append(
            TaskAssignment(task_id=task.id, week_number=new_week, day_number=new_day)
        )
        if new_week != task.week_number:
            changes.append(
                TaskReschedule(
                    task_id=task.id,
                    title=task.title,
                    estimated_minutes=task.estimated_minutes,
                    previous_week=task.week_number,
                    new_week=new_week,
                )
            )
        load_used += cost

    max_week = max((a.week_number for a in assignments), default=start_week)
    reason = f"{len(overdue)} overdue task{'s' if len(overdue) != 1 else ''} detected"

    return ReplanProposal(
        plan_id=plan.id,
        reason=reason,
        changes=changes,
        remaining_effort_minutes=remaining_effort_minutes,
        new_completion_estimate=week_window(plan_start, max_week)[1].date(),
        deadline_at_risk=_is_at_risk(plan, plan_start, max_week),
        task_assignments=assignments,
    )


def apply_replan(db: Session, *, plan: Plan, proposal: ReplanProposal) -> list[PlanTask]:
    """Persists a proposal the caller already showed the user and the
    user accepted. Moves existing PlanTask rows (week_number/day_number
    only) rather than planner_service's wholesale-replace pattern -
    replanning reschedules, it doesn't regenerate, so ids/titles/
    completed_at must all survive untouched. Stale assignments (a task
    that was completed or deleted between propose and accept) are
    skipped rather than failing the whole batch."""
    by_id = {task.id: task for task in plan.tasks}
    for assignment in proposal.task_assignments:
        task = by_id.get(assignment.task_id)
        if task is None or task.status == PlanTaskStatus.COMPLETED:
            continue
        task.week_number = assignment.week_number
        task.day_number = assignment.day_number

    db.add(
        PlanReplanEvent(
            plan_id=plan.id,
            reason=proposal.reason,
            summary={
                "changes": [
                    {
                        "task_id": str(change.task_id),
                        "title": change.title,
                        "estimated_minutes": change.estimated_minutes,
                        "previous_week": change.previous_week,
                        "new_week": change.new_week,
                    }
                    for change in proposal.changes
                ],
                "remaining_effort_minutes": proposal.remaining_effort_minutes,
                "new_completion_estimate": (
                    proposal.new_completion_estimate.isoformat()
                    if proposal.new_completion_estimate
                    else None
                ),
                "deadline_at_risk": proposal.deadline_at_risk,
            },
        )
    )
    db.commit()
    return task_service.get_tasks_for_plan(db, plan_id=plan.id)


def get_replan_history(db: Session, *, plan_id: uuid.UUID) -> list[PlanReplanEvent]:
    return (
        db.query(PlanReplanEvent)
        .filter(PlanReplanEvent.plan_id == plan_id)
        .order_by(PlanReplanEvent.created_at.desc())
        .all()
    )


def _average_weekly_minutes(tasks: list[PlanTask]) -> int | None:
    """The redistribution budget: the average total estimated_minutes
    across the plan's original weeks, so a replanned week doesn't get
    more crammed than a "normal" week of this specific plan already was
    (spec: "avoid putting 12 hours into one day"). None only if the plan
    has no minute estimates at all, which falls back to
    FALLBACK_TASKS_PER_WEEK instead."""
    if not tasks or all(t.estimated_minutes is None for t in tasks):
        return None
    totals: dict[int, int] = {}
    for task in tasks:
        totals[task.week_number] = totals.get(task.week_number, 0) + (task.estimated_minutes or 0)
    if not totals:
        return None
    return max(1, round(sum(totals.values()) / len(totals)))


def _is_at_risk(plan: Plan, plan_start: datetime, max_week: int) -> bool:
    if plan.goal.deadline is None:
        return False
    deadline = _naive_utc(plan.goal.deadline)
    _, estimate_end = week_window(plan_start, max_week)
    return estimate_end > deadline


def _naive_utc(value: datetime) -> datetime:
    """Normalizes to a naive UTC datetime regardless of whether the value
    came back timezone-aware (Postgres, in real usage) or naive (SQLite,
    in tests - see tests/conftest.py) - SQLAlchemy's SQLite dialect
    doesn't round-trip tzinfo, so comparing/subtracting a mix of aware
    and naive datetimes would otherwise raise. Every datetime this module
    touches is funneled through here first."""
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value
