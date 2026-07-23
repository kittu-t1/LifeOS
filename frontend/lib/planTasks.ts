import type { PlanTask, PlanTaskStatus, Progress, WeekTasksGroup } from "@/types/task";

/**
 * Pure helper for optimistically flipping one task's status inside the
 * grouped-by-week shape GET /plans/{id}/tasks returns, without a refetch.
 */
export function updateTaskInWeeks(
  weeks: WeekTasksGroup[],
  taskId: string,
  status: PlanTaskStatus,
): WeekTasksGroup[] {
  return weeks.map((week) => ({
    ...week,
    tasks: week.tasks.map((task) =>
      task.id === taskId
        ? {
            ...task,
            status,
            completed_at: status === "completed" ? new Date().toISOString() : null,
          }
        : task,
    ),
  }));
}

export function flattenTasks(weeks: WeekTasksGroup[]): PlanTask[] {
  return weeks.flatMap((week) => week.tasks);
}

/**
 * Mirrors backend/app/services/progress_service.py's arithmetic exactly
 * (count/percentage, 0 when there are no tasks) so the number on screen
 * updates the instant a checkbox is clicked, without waiting on a round
 * trip to GET /plans/{id}/progress. This is a client-side mirror of the
 * same "live-computed, never stored" philosophy, not a competing source
 * of truth - the backend endpoint (services/tasks.ts:getPlanProgress)
 * still exists for anything that needs progress without first loading
 * every task.
 */
export function computeProgress(weeks: WeekTasksGroup[]): Progress {
  const tasks = flattenTasks(weeks);
  const total = tasks.length;
  const completed = tasks.filter((task) => task.status === "completed").length;
  const percentage = total ? Math.round((completed / total) * 100) : 0;
  return { completed, total, remaining: total - completed, percentage };
}
