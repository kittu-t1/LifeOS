import type { GoalStatus } from "@/types/goal";

type Tone = "neutral" | "accent" | "success";

/**
 * Shared status -> label/tone mapping - used by GoalCard, WorkspaceShell,
 * and OverviewSection so the three places a Goal's status is displayed
 * can't drift out of sync with each other.
 */
export const statusMeta: Record<GoalStatus, { label: string; tone: Tone }> = {
  not_started: { label: "Not started", tone: "neutral" },
  in_progress: { label: "In progress", tone: "accent" },
  completed: { label: "Completed", tone: "success" },
};
