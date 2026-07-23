import { apiFetch } from "@/lib/api";
import type { ReplanEvent, ReplanProposal } from "@/types/replan";
import type { PlanTasksResponse } from "@/types/task";

/**
 * Adaptive Planning Engine client - mirrors app/api/v1/replan.py's three
 * routes. proposeReplan/acceptReplan are deliberately two separate calls
 * (see that file's docstring): propose only reads and returns a preview;
 * nothing is saved until the caller re-sends the exact same proposal to
 * acceptReplan, which is what lets the UI show a review step in between.
 */

export function proposeReplan(planId: string): Promise<ReplanProposal> {
  return apiFetch<ReplanProposal>(`/planner/plans/${planId}/replan`, { method: "POST" });
}

export function acceptReplan(planId: string, proposal: ReplanProposal): Promise<PlanTasksResponse> {
  return apiFetch<PlanTasksResponse>(`/planner/plans/${planId}/replan/accept`, {
    method: "POST",
    body: JSON.stringify(proposal),
  });
}

export function getReplanHistory(planId: string): Promise<ReplanEvent[]> {
  return apiFetch<ReplanEvent[]>(`/planner/plans/${planId}/replan/history`);
}
