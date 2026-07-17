import { apiFetch } from "@/lib/api";
import type { CreateGoalInput, Goal } from "@/types/goal";

export function listGoals(): Promise<Goal[]> {
  return apiFetch<Goal[]>("/goals");
}

export function getGoal(goalId: string): Promise<Goal> {
  return apiFetch<Goal>(`/goals/${goalId}`);
}

export function createGoal(input: CreateGoalInput): Promise<Goal> {
  return apiFetch<Goal>("/goals", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
