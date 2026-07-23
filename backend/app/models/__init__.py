"""
ORM models.

Import every model here so Alembic's autogenerate and Base.metadata.create_all
can discover them from a single place - `Memory` is the one exception to
"lives in app/models/": it's defined in app/memory/models/memory.py (the
Memory Engine's own Clean-Architecture module, kept independent from the
rest of the app - see app/memory/__init__.py), but is still re-exported
here so this stays the single registry every model can be discovered
from, per this file's own rule.
"""

from app.memory.models.memory import Memory, MemoryCategory, MemorySource
from app.models.goal import Goal, GoalStatus
from app.models.habit import (
    Habit,
    HabitOccurrence,
    HabitOccurrenceStatus,
    HabitStatus,
    RecurrenceType,
)
from app.models.plan import Milestone, Plan
from app.models.plan_replan_event import PlanReplanEvent
from app.models.plan_task import PlanTask, PlanTaskStatus
from app.models.planner_run import PlannerRun, PlannerRunStatus
from app.models.user import User
from app.models.workspace import Workspace

__all__ = [
    "Goal",
    "GoalStatus",
    "Habit",
    "HabitOccurrence",
    "HabitOccurrenceStatus",
    "HabitStatus",
    "Memory",
    "MemoryCategory",
    "MemorySource",
    "Milestone",
    "Plan",
    "PlanReplanEvent",
    "PlanTask",
    "PlanTaskStatus",
    "PlannerRun",
    "PlannerRunStatus",
    "RecurrenceType",
    "User",
    "Workspace",
]
