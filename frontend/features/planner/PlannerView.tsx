"use client";

import { useEffect, useState } from "react";
import GoalInputCard from "@/features/planner/GoalInputCard";
import PlanResultView from "@/features/planner/PlanResultView";
import { useWorkspace } from "@/features/workspace/WorkspaceContext";
import { computeProgress, updateTaskInWeeks } from "@/lib/planTasks";
import { createMemory } from "@/services/memory";
import { generatePlan, getLatestPlan, PlannerApiError, regeneratePlan } from "@/services/planner";
import { acceptReplan, proposeReplan } from "@/services/replan";
import { getPlanTasks, updateTaskStatus } from "@/services/tasks";
import type { GeneratePlanInput, Plan, SuggestedMemory } from "@/types/planner";
import type { ReplanProposal } from "@/types/replan";
import type { PlanTask, WeekTasksGroup } from "@/types/task";

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
  const [taskWeeks, setTaskWeeks] = useState<WeekTasksGroup[] | null>(null);
  const [replanProposal, setReplanProposal] = useState<ReplanProposal | null>(null);
  const [replanModalOpen, setReplanModalOpen] = useState(false);
  const [replanning, setReplanning] = useState(false);
  const [acceptingReplan, setAcceptingReplan] = useState(false);
  const [replanError, setReplanError] = useState<string | null>(null);
  const [memorySuggestion, setMemorySuggestion] = useState<SuggestedMemory | null>(null);
  const [savingMemorySuggestion, setSavingMemorySuggestion] = useState(false);
  const [memorySuggestionError, setMemorySuggestionError] = useState<string | null>(null);

  const goalId = workspace?.goal.id;

  // Loads (or reloads) a plan's PlanTask checklist. Called explicitly
  // after every event that produces a plan with tasks - initial load,
  // generate, regenerate - rather than a useEffect keyed on plan.id,
  // since regenerate updates the same Plan row in place (id doesn't
  // change) and still needs a refetch: it wholesale-replaces tasks (see
  // planner_service.regenerate_plan), so a completed checkbox from
  // before a regenerate won't survive one.
  async function loadTasks(planId: string) {
    try {
      const response = await getPlanTasks(planId);
      setTaskWeeks(response.weeks);
    } catch {
      // A failed task fetch shouldn't block the rest of the plan from
      // rendering - PlanResultView just shows "Loading tasks..." and
      // Today's Focus/Progress stay hidden until it succeeds.
    }
  }

  useEffect(() => {
    if (!goalId) return;
    let cancelled = false;

    getLatestPlan(goalId)
      .then((existing) => {
        if (cancelled) return;
        setPlan(existing);
        setPhase(existing ? "result" : "form");
        if (existing) void loadTasks(existing.id);
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
      setMemorySuggestion(generated.suggested_memory ?? null);
      setMemorySuggestionError(null);
      void loadTasks(generated.id);
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
      setMemorySuggestion(updated.suggested_memory ?? null);
      setMemorySuggestionError(null);
      void loadTasks(updated.id);
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

  // Optimistic toggle: updates the on-screen checklist (and thus
  // Progress/Today's Focus, both derived from taskWeeks) immediately,
  // then persists it - rolling back only if the request actually fails,
  // so a slow network never makes the checkbox feel laggy.
  async function handleToggleTask(task: PlanTask) {
    if (!taskWeeks) return;
    const nextStatus = task.status === "completed" ? "pending" : "completed";
    const previous = taskWeeks;
    setTaskWeeks(updateTaskInWeeks(taskWeeks, task.id, nextStatus));
    try {
      await updateTaskStatus(task.id, nextStatus);
    } catch {
      setTaskWeeks(previous);
    }
  }

  // Replan is check-then-review, not click-and-forget (see
  // services/replan.ts): this only ever fetches a proposal - nothing is
  // saved until handleAcceptReplan explicitly echoes it back to
  // /replan/accept, so a user can always discard what they see in
  // ReplanModal without the plan having changed underneath them.
  async function handleReplan() {
    if (!plan) return;
    setReplanning(true);
    setReplanError(null);
    try {
      const proposal = await proposeReplan(plan.id);
      setReplanProposal(proposal);
      setReplanModalOpen(true);
    } catch {
      setReplanError("Couldn't check your schedule. Is the backend running?");
    } finally {
      setReplanning(false);
    }
  }

  async function handleAcceptReplan() {
    if (!plan || !replanProposal) return;
    setAcceptingReplan(true);
    setReplanError(null);
    try {
      const response = await acceptReplan(plan.id, replanProposal);
      setTaskWeeks(response.weeks);
      setReplanModalOpen(false);
      setReplanProposal(null);
    } catch {
      setReplanError("Couldn't save the new schedule. Please try again.");
    } finally {
      setAcceptingReplan(false);
    }
  }

  function handleDiscardReplan() {
    setReplanModalOpen(false);
    setReplanProposal(null);
    setReplanError(null);
  }

  // "Create a Memory using the existing Memory API" per the spec -
  // SuggestedMemory (types/planner.ts) is shaped identically to
  // MemoryCreateInput on purpose, so this is a direct pass-through, not
  // a new endpoint or a reshaped payload.
  async function handleAcceptMemorySuggestion() {
    if (!memorySuggestion) return;
    setSavingMemorySuggestion(true);
    setMemorySuggestionError(null);
    try {
      await createMemory(memorySuggestion);
      setMemorySuggestion(null);
    } catch {
      setMemorySuggestionError("Couldn't save that. Please try again.");
    } finally {
      setSavingMemorySuggestion(false);
    }
  }

  // Decline is "do nothing" per the spec - no API call, just dismiss.
  function handleDeclineMemorySuggestion() {
    setMemorySuggestion(null);
    setMemorySuggestionError(null);
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
        goalTitle={workspace.goal.title}
        taskWeeks={taskWeeks}
        progress={taskWeeks ? computeProgress(taskWeeks) : null}
        onToggleTask={handleToggleTask}
        improveModalOpen={improveModalOpen}
        onOpenImprove={() => {
          setImproveError(null);
          setImproveModalOpen(true);
        }}
        onCloseImprove={() => setImproveModalOpen(false)}
        onSubmitImprove={handleImprove}
        improving={improving}
        improveError={improveError}
        onReplan={handleReplan}
        replanning={replanning}
        replanProposal={replanProposal}
        replanModalOpen={replanModalOpen}
        onAcceptReplan={handleAcceptReplan}
        onDiscardReplan={handleDiscardReplan}
        acceptingReplan={acceptingReplan}
        replanError={replanError}
        memorySuggestion={memorySuggestion}
        onAcceptMemorySuggestion={handleAcceptMemorySuggestion}
        onDeclineMemorySuggestion={handleDeclineMemorySuggestion}
        savingMemorySuggestion={savingMemorySuggestion}
        memorySuggestionError={memorySuggestionError}
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
