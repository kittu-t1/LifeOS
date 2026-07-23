import { apiFetch } from "@/lib/api";
import type {
  Habit,
  HabitCreateInput,
  HabitOccurrence,
  HabitOccurrenceStatus,
  HabitUpdateInput,
} from "@/types/habit";

/**
 * Recurring Task System client - mirrors app/api/v1/habits.py's routes
 * 1:1. Habits are user-scoped (no goal/plan/workspace id in any of these
 * paths - see that file's docstring), unlike every other service in this
 * folder.
 */

export function createHabit(data: HabitCreateInput): Promise<Habit> {
  return apiFetch<Habit>("/habits", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function listHabits(): Promise<Habit[]> {
  return apiFetch<Habit[]>("/habits");
}

export function getHabit(habitId: string): Promise<Habit> {
  return apiFetch<Habit>(`/habits/${habitId}`);
}

export function updateHabit(habitId: string, data: HabitUpdateInput): Promise<Habit> {
  return apiFetch<Habit>(`/habits/${habitId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function pauseHabit(habitId: string): Promise<Habit> {
  return apiFetch<Habit>(`/habits/${habitId}/pause`, { method: "POST" });
}

export function resumeHabit(habitId: string): Promise<Habit> {
  return apiFetch<Habit>(`/habits/${habitId}/resume`, { method: "POST" });
}

/** Upcoming (and last 7 days of) occurrences for one habit - a fixed
 * window, not an arbitrary date range (see the backend route's docstring). */
export function listOccurrences(habitId: string): Promise<HabitOccurrence[]> {
  return apiFetch<HabitOccurrence[]>(`/habits/${habitId}/occurrences`);
}

export function updateOccurrenceStatus(
  occurrenceId: string,
  status: HabitOccurrenceStatus,
): Promise<HabitOccurrence> {
  return apiFetch<HabitOccurrence>(`/habits/occurrences/${occurrenceId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
