"use client";

import { CheckCircle2, Circle, Flag, Sparkles } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import ProgressBar from "@/components/ui/ProgressBar";
import ActivityTimeline from "@/features/workspace/ActivityTimeline";
import { useWorkspace } from "@/features/workspace/WorkspaceContext";
import { formatDate } from "@/lib/format";
import { statusMeta } from "@/lib/goal-status";

// Curated, not generated - these two "done" entries are things we
// genuinely know happened (the goal and its workspace really were just
// created); the "coming soon" entries flag features that will start
// writing real entries here once they exist. This is deliberately
// distinct from ActivityTimeline below, which will hold the real,
// chronological event log and is honestly empty until that exists.
const RECENT_ACTIVITY = [
  { label: "Goal Created", done: true },
  { label: "Workspace Created", done: true },
  { label: "Planner Coming Soon", done: false },
  { label: "Knowledge Engine Coming Soon", done: false },
];

/**
 * Overview is the goal's main dashboard - it deliberately folds Mission
 * and Progress into itself rather than giving them their own top-level
 * nav tabs (see WorkspaceShell's TABS list). Both are just views onto
 * the parent Goal's own data (title/description, status, progress,
 * timestamps), not independent entities with their own lifecycle, so a
 * dedicated tab for either would be navigation for navigation's sake and
 * would fragment a single "how is this goal doing" picture across
 * clicks. See docs/architecture.md for the same rationale documented at
 * the architecture level.
 */
export default function OverviewSection() {
  const { workspace, loading } = useWorkspace();

  if (loading || !workspace) return null;

  const { goal } = workspace;
  const status = statusMeta[goal.status];

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 px-6 py-8">
      <Card>
        <h2 className="text-muted-foreground mb-1 text-xs font-medium tracking-wide uppercase">
          Mission
        </h2>
        <p className="text-foreground text-sm">{goal.description?.trim() || goal.title}</p>
      </Card>

      <Card>
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
              Progress
            </h2>
            <Badge tone={status.tone}>{status.label}</Badge>
          </div>
          <span className="text-foreground text-sm font-medium">{goal.progress}%</span>
        </div>
        <ProgressBar value={goal.progress} />
        <div className="text-muted-foreground mt-3 flex items-center gap-4 text-xs">
          <span>Created {formatDate(goal.created_at)}</span>
          <span>Last updated {formatDate(goal.updated_at)}</span>
        </div>
      </Card>

      <Card>
        <h2 className="text-muted-foreground mb-3 text-xs font-medium tracking-wide uppercase">
          Recent Activity
        </h2>
        <ul className="flex flex-col gap-2.5">
          {RECENT_ACTIVITY.map((entry) => (
            <li key={entry.label} className="flex items-center gap-2 text-sm">
              {entry.done ? (
                <CheckCircle2 size={14} className="text-success shrink-0" />
              ) : (
                <Circle size={14} className="text-muted-foreground shrink-0" />
              )}
              <span className={entry.done ? "text-foreground" : "text-muted-foreground"}>
                {entry.label}
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <div className="mb-1 flex items-center gap-2">
          <Flag size={14} className="text-muted-foreground" />
          <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            Upcoming Milestones
          </h2>
        </div>
        <p className="text-muted-foreground text-sm">
          Milestones will appear here once the Planner breaks this goal down into a plan.
        </p>
      </Card>

      <Card>
        <div className="mb-1 flex items-center gap-2">
          <Sparkles size={14} className="text-muted-foreground" />
          <h2 className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            AI Suggestions
          </h2>
        </div>
        <p className="text-muted-foreground text-sm">
          LifeOS will surface suggestions here once the Planner and Memory engines are live.
        </p>
      </Card>

      <ActivityTimeline />
    </div>
  );
}
