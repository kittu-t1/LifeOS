import HabitsView from "@/features/habits/HabitsView";

/**
 * Habits are user-scoped, not Goal-scoped (see backend/app/models/habit.py),
 * so this route lives at the top level rather than nested under
 * /workspace/[workspaceId] like Planner/Tasks/etc.
 */
export default function HabitsPage() {
  return <HabitsView />;
}
