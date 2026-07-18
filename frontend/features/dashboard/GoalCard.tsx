import Link from "next/link";
import { ArrowUpRight, Calendar } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import ProgressRing from "@/components/ui/ProgressRing";
import { formatDate } from "@/lib/format";
import { statusMeta } from "@/lib/goal-status";
import type { Goal } from "@/types/goal";

export default function GoalCard({ goal }: { goal: Goal }) {
  const status = statusMeta[goal.status];

  return (
    <Card hoverable className="flex flex-col gap-5">
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h3 className="text-foreground text-base font-semibold">{goal.title}</h3>
          <Badge tone={status.tone}>{status.label}</Badge>
        </div>
        {/* Apple Fitness-style ring rather than a linear bar - progress
            at a glance, matching the "Goal Journey" visual language. */}
        <ProgressRing value={goal.progress} size={52} strokeWidth={4} />
      </div>

      <div className="flex items-center justify-between pt-1">
        <span className="text-muted-foreground flex items-center gap-1.5 text-xs">
          <Calendar size={13} />
          {formatDate(goal.created_at)}
        </span>
        <Link
          href={`/workspace/${goal.workspace_id}`}
          className="text-accent hover:text-accent-hover flex items-center gap-1 text-sm font-medium"
        >
          Open Workspace
          <ArrowUpRight size={15} />
        </Link>
      </div>
    </Card>
  );
}
