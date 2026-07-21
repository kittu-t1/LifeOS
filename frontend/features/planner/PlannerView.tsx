"use client";

import { useEffect, useState } from "react";
import GoalInputCard from "@/features/planner/GoalInputCard";
import PlanResultView from "@/features/planner/PlanResultView";
import { useWorkspace } from "@/features/workspace/WorkspaceContext";
import { generatePlan, getLatestPlan, PlannerApiError, regeneratePlan } from "@/services/planner";
import type { GeneratePlanInput, Plan } from "@/types/planner";

type Phase = "checking" | "form" | "result";

/**
 * The Planner tab's top-level orchestrator (see the AI Planner spec's
 * User Flow: enter goal context -> Generate Plan -> view result -> later,
 * Improve Plan). The goal itself doesn't need to be entered here -
 * useWorkspace already has it, since this tab only exists inside a
 * Goal's Workspace - so the state this component owns is "do we have a
 * plan yet" plus the request lifecycles around generating and improving
 * one.
 *
 * On mount it checks for an existing Plan (GET /planner/goals/{id})
 * before showing the input form, so revisiting the tab after a plan was
 * already generated shows the plan again instead of an empty form every
 * time. Improving a plan (see handleImprove) never needs to know what
 * the original timeline/availability/constraints were - the backend
 * pulls the goal and current plan itself (see
 * app/services/planner_service.regenerate_plan) - so unlike a naive
 * "resubmit the same inputs" regenerate, this works identically whether
 * the plan on screen came from this session or a previous one.
 */
export default function PlannerView() {
  const { workspace, loading: workspaceLoading, error: workspaceError } = useWorkspace();
  const [phase, setPhase] = useState<Phase>("checking");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [improveModalOpen, setImproveModalOpen] = useState(false);
  const [improving, setImproving] = useState(false);
  const [improveError, setImproveError] = useState<string | null>(null);

  const goalId = workspace?.goal.id;

  useEffect(() => {
    if (!goalId) return;
    let cancelled = false;

    getLatestPlan(goalId)
      .then((existing) => {
        if (cancelled) return;
        setPlan(existing);
        setPhase(existing ? "result" : "form");
      })
      .catch(() => {
        // No existing plan is the common, expected case (getLatestPlan
        // already treats 404 as `null`, not an error) - reaching here
        // means the check itself failed (backend unreachable, etc).
        // Fail open into the form rather than blocking the tab entirely;
        // Generate will surface a clear error if the backend really is
        // down.
        if (!cancelled) setPhase("form");
      });

    return () => {
      cancelled = true;
    };
  }, [goalId]);

  async function handleGenerate(input: GeneratePlanInput) {
    if (!goalId) return;
    setSubmitting(true);
    setError(null);
    try {
      const generated = await generatePlan(goalId, input);
      setPlan(generated);
      setPhase("result");
    } catch (err) {
      setError(
        err instanceof PlannerApiError
          ? err.message
          : "Couldn't reach LifeOS. Is the backend running?",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleImprove(adjustment: string) {
    if (!plan) return;
    setImproving(true);
    setImproveError(null);
    try {
      const updated = await regeneratePlan(plan.id, { adjustment });
      setPlan(updated);
      setImproveModalOpen(false);
    } catch (err) {
      setImproveError(
        err instanceof PlannerApiError
          ? err.message
          : "Couldn't reach LifeOS. Is the backend running?",
      );
    } finally {
      setImproving(false);
    }
  }

  if (workspaceLoading || phase === "checking") {
    return (
      <div className="text-muted-foreground px-6 py-24 text-center text-sm">Loading planner…</div>
    );
  }

  if (workspaceError || !workspace) {
    return (
      <div className="text-danger px-6 py-24 text-center text-sm">
        Couldn&apos;t load this goal. Is the backend running?
      </div>
    );
  }

  if (phase === "result" && plan) {
    return (
      <PlanResultView
        plan={plan}
        improveModalOpen={improveModalOpen}
        onOpenImprove={() => {
          setImproveError(null);
          setImproveModalOpen(true);
        }}
        onCloseImprove={() => setImproveModalOpen(false)}
        onSubmitImprove={handleImprove}
        improving={improving}
        improveError={improveError}
      />
    );
  }

  return (
    <div className="px-6 py-8">
      <GoalInputCard
        goalTitle={workspace.goal.title}
        onGenerate={handleGenerate}
        submitting={submitting}
        error={error}
      />
    </div>
  );
}
