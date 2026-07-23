"use client";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import ImprovePlanModal from "@/features/planner/ImprovePlanModal";
import PlanProgress from "@/features/planner/PlanProgress";
import ReplanModal from "@/features/planner/ReplanModal";
import TaskChecklist from "@/features/planner/TaskChecklist";
import TodaysFocus from "@/features/planner/TodaysFocus";
import type { Plan } from "@/types/planner";
import type { ReplanProposal } from "@/types/replan";
import type { PlanTask, Progress, WeekTasksGroup } from "@/types/task";

interface PlanResultViewProps {
  plan: Plan;
  goalTitle: string;
  taskWeeks: WeekTasksGroup[] | null;
  progress: Progress | null;
  onToggleTask: (task: PlanTask) => void;
  improveModalOpen: boolean;
  onOpenImprove: () => void;
  onCloseImprove: () => void;
  onSubmitImprove: (adjustment: string) => void;
  improving: boolean;
  improveError: string | null;
  onReplan: () => void;
  replanning: boolean;
  replanProposal: ReplanProposal | null;
  replanModalOpen: boolean;
  onAcceptReplan: () => void;
  onDiscardReplan: () => void;
  acceptingReplan: boolean;
  replanError: string | null;
}

/**
 * The Planner tab's "wow moment" screen - what the user actually came
 * for (see the AI Planner MVP spec's Plan Result View section: Mission,
 * Timeline, Milestones, Weekly Plan, in that order). Deliberately plain
 * reading order rather than a dashboard-style grid of widgets - one idea
 * per Card, top to bottom, matching this codebase's existing "minimal
 * cognitive load" pattern (see OverviewSection.tsx).
 */
export default function PlanResultView({
  plan,
  goalTitle,
  taskWeeks,
  progress,
  onToggleTask,
  improveModalOpen,
  onOpenImprove,
  onCloseImprove,
  onSubmitImprove,
  improving,
  improveError,
  onReplan,
  replanning,
  replanProposal,
  replanModalOpen,
  onAcceptReplan,
  onDiscardReplan,
  acceptingReplan,
  replanError,
}: PlanResultViewProps) {
  const weekFocus = Object.fromEntries(plan.weekly_plan.map((week) => [week.week, week.focus]));

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-8">
      {progress && <PlanProgress progress={progress} />}

      {taskWeeks && <TodaysFocus goalTitle={goalTitle} weeks={taskWeeks} onToggle={onToggleTask} />}

      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-muted-foreground mb-1.5 text-xs font-medium tracking-wide uppercase">
              Mission
            </h2>
            <p className="text-foreground text-base leading-relaxed">{plan.mission}</p>
          </div>
          <Badge tone="accent">{plan.estimated_duration}</Badge>
        </div>
      </Card>

      <Card>
        <h2 className="text-muted-foreground mb-3 text-xs font-medium tracking-wide uppercase">
          Timeline
        </h2>
        <ol className="flex flex-col gap-2.5">
          {plan.timeline.map((entry, i) => (
            <li key={i} className="flex items-start gap-2.5 text-sm">
              <span className="text-accent mt-0.5 shrink-0 text-xs font-semibold">{i + 1}</span>
              <span className="text-foreground">{entry}</span>
            </li>
          ))}
        </ol>
      </Card>

      <Card>
        <h2 className="text-muted-foreground mb-4 text-xs font-medium tracking-wide uppercase">
          Milestones
        </h2>
        <div className="flex flex-col gap-5">
          {plan.milestones.map((milestone) => (
            <div key={milestone.id} className="border-accent/30 border-l-2 pl-4">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-foreground text-sm font-semibold">{milestone.title}</h3>
                {milestone.duration && <Badge tone="neutral">{milestone.duration}</Badge>}
              </div>
              {milestone.description && (
                <p className="text-muted-foreground mt-1 text-sm leading-relaxed">
                  {milestone.description}
                </p>
              )}
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <h2 className="text-muted-foreground mb-4 text-xs font-medium tracking-wide uppercase">
          Weekly Plan
        </h2>
        {taskWeeks ? (
          <TaskChecklist weeks={taskWeeks} weekFocus={weekFocus} onToggle={onToggleTask} />
        ) : (
          <p className="text-muted-foreground text-sm">Loading tasks…</p>
        )}
      </Card>

      <div className="flex flex-col items-center gap-2 pt-1">
        <div className="flex justify-center gap-3">
          <Button variant="secondary" onClick={onOpenImprove}>
            Improve Plan
          </Button>
          <Button variant="secondary" onClick={onReplan} disabled={replanning}>
            {replanning ? "Checking schedule…" : "Replan"}
          </Button>
        </div>
        {replanError && !replanModalOpen && <p className="text-danger text-sm">{replanError}</p>}
      </div>

      <ImprovePlanModal
        open={improveModalOpen}
        onClose={onCloseImprove}
        onSubmit={onSubmitImprove}
        submitting={improving}
        error={improveError}
      />

      <ReplanModal
        open={replanModalOpen}
        proposal={replanProposal}
        onDiscard={onDiscardReplan}
        onAccept={onAcceptReplan}
        accepting={acceptingReplan}
        error={replanError}
      />
    </div>
  );
}
