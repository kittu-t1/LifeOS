import { API_BASE_URL } from "@/lib/api";
import type { GeneratePlanInput, Plan, RegeneratePlanInput } from "@/types/planner";

/**
 * Thrown with the backend's actual `detail` message (see
 * app/api/v1/planner.py's HTTPException calls - "took too long", "AI
 * planner is temporarily unavailable", "unexpected response") rather
 * than a generic "request failed" string, since the whole point of the
 * Planner MVP's error handling is that the user sees an understandable
 * message, not raw response text. Doesn't reuse lib/api.ts's apiFetch
 * for that reason - apiFetch's error message wraps the whole response
 * body rather than surfacing just `detail`.
 */
export class PlannerApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "PlannerApiError";
    this.status = status;
  }
}

async function extractDetail(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // Response wasn't JSON (or had no body) - fall through to the generic message.
  }
  return `Something went wrong (status ${res.status}). Please try again.`;
}

export async function generatePlan(goalId: string, input: GeneratePlanInput): Promise<Plan> {
  const res = await fetch(`${API_BASE_URL}/api/v1/planner/goals/${goalId}/generate`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    throw new PlannerApiError(await extractDetail(res), res.status);
  }
  return res.json() as Promise<Plan>;
}

/**
 * Returns a goal's Plan, or `null` if one hasn't been generated yet - a
 * 404 here is expected/normal state (a fresh Planner tab), not an error,
 * so it doesn't throw. Goal has at most one Plan (see
 * backend/app/models/plan.py), so there's no "which one" ambiguity.
 */
export async function getLatestPlan(goalId: string): Promise<Plan | null> {
  const res = await fetch(`${API_BASE_URL}/api/v1/planner/goals/${goalId}`, {
    cache: "no-store",
  });

  if (res.status === 404) return null;
  if (!res.ok) {
    throw new PlannerApiError(await extractDetail(res), res.status);
  }
  return res.json() as Promise<Plan>;
}

/**
 * Regenerates an existing Plan in place using an adjustment note (e.g.
 * "make it more realistic") - the backend pulls the original goal and
 * current plan itself, so this never needs the original timeline/
 * availability/constraints the way the old same-inputs regenerate did.
 */
export async function regeneratePlan(planId: string, input: RegeneratePlanInput): Promise<Plan> {
  const res = await fetch(`${API_BASE_URL}/api/v1/planner/plans/${planId}/regenerate`, {
    method: "POST",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    throw new PlannerApiError(await extractDetail(res), res.status);
  }
  return res.json() as Promise<Plan>;
}
