import { apiFetch } from "@/lib/api";
import type { PlanTaskStatus, PlanTasksResponse, Progress } from "@/types/task";

/**
 * Execution Engine client - reading a plan's PlanTask checklist/progress
 * and flipping one task's status. Mirrors app/api/v1/execution.py's three
 * routes 1:1. Uses the shared apiFetch (unlike services/planner.ts) since
 * these endpoints don't need PlannerApiError's "surface the AI failure
 * message" behavior - a task-update failure is just a generic network/
 * server error.
 */

export function getPlanTasks(planId: string): Promise<PlanTasksResponse> {
  return apiFetch<PlanTasksResponse>(`/plans/${planId}/tasks`);
}

export function getPlanProgress(planId: string): Promise<Progress> {
  return apiFetch<Progress>(`/plans/${planId}/progress`);
}

export function updateTaskStatus(taskId: string, status: PlanTaskStatus) {
  return apiFetch(`/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
