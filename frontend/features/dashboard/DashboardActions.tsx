import { Target } from "lucide-react";
import DashboardActionCard from "@/features/dashboard/DashboardActionCard";

/**
 * The dashboard's single primary action, directly below DashboardHero.
 *
 * This used to be a two-card "Goals + Habits" row with equal visual
 * weight (see git history) - the sidebar architecture redesign
 * supersedes that: Goals is now explicitly the center's one job, and
 * every supporting capability (Habits, Memory, and future modules) moved
 * to the sidebar (see components/layout/navConfig.ts), reachable from
 * every page rather than competing for space on this one. Keeping this
 * as its own component (rather than inlining a button in DashboardHero)
 * is what lets DashboardActionCard's `href`/`onAction` shape stay
 * reusable if a second genuinely goal-related action ever belongs here.
 */
export default function DashboardActions({ onCreateGoal }: { onCreateGoal: () => void }) {
  return (
    <div className="mx-auto w-full max-w-md">
      <DashboardActionCard
        icon={Target}
        title="Create Goal"
        description="Turn an objective into an AI-powered execution plan."
        actionLabel="Create Goal"
        onAction={onCreateGoal}
      />
    </div>
  );
}
