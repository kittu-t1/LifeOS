import Link from "next/link";
import { ArrowUpRight, Calendar } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import ProgressBar from "@/components/ui/ProgressBar";
import { formatDate } from "@/lib/format";
import { statusMeta } from "@/lib/goal-status";
import type { Goal } from "@/types/goal";

export default function GoalCard({ goal }: { goal: Goal }) {
  const status = statusMeta[goal.status];

  return (
    <Card hoverable className="flex flex-col gap-4">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-foreground text-base font-semibold">{goal.title}</h3>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="text-muted-foreground flex items-center justify-between text-xs">
          <span>Progress</span>
          <span>{goal.progress}%</span>
        </div>
        <ProgressBar value={goal.progress} />
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
