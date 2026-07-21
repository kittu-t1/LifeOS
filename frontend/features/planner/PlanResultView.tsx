"use client";

import { CheckCircle2 } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { radius } from "@/design-system/radius";
import ImprovePlanModal from "@/features/planner/ImprovePlanModal";
import type { Plan } from "@/types/planner";

interface PlanResultViewProps {
  plan: Plan;
  improveModalOpen: boolean;
  onOpenImprove: () => void;
  onCloseImprove: () => void;
  onSubmitImprove: (adjustment: string) => void;
  improving: boolean;
  improveError: string | null;
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
  improveModalOpen,
  onOpenImprove,
  onCloseImprove,
  onSubmitImprove,
  improving,
  improveError,
}: PlanResultViewProps) {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-8">
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
        <div className="flex flex-col gap-3">
          {plan.weekly_plan.map((week) => (
            <div
              key={week.week}
              className={`bg-surface-hover ${radius.xl.class} border-border border p-4`}
            >
              <div className="mb-2 flex items-baseline gap-2">
                <span className="text-accent text-xs font-semibold tracking-wide uppercase">
                  Week {week.week}
                </span>
                <span className="text-foreground text-sm font-medium">{week.focus}</span>
              </div>
              <ul className="flex flex-col gap-1.5">
                {week.tasks.map((task, i) => (
                  <li key={i} className="text-muted-foreground flex items-start gap-2 text-sm">
                    <CheckCircle2 size={14} className="text-muted-foreground/50 mt-0.5 shrink-0" />
                    <span>{task}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </Card>

      <div className="flex justify-center pt-1">
        <Button variant="secondary" onClick={onOpenImprove}>
          Improve Plan
        </Button>
      </div>

      <ImprovePlanModal
        open={improveModalOpen}
        onClose={onCloseImprove}
        onSubmit={onSubmitImprove}
        submitting={improving}
        error={improveError}
      />
    </div>
  );
}
