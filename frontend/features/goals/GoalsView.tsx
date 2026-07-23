"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import CreateGoalModal from "@/features/dashboard/CreateGoalModal";
import DashboardActions from "@/features/dashboard/DashboardActions";
import EmptyGoalsState from "@/features/dashboard/EmptyGoalsState";
import GoalCard from "@/features/dashboard/GoalCard";
import GoalShowcaseSection from "@/features/dashboard/GoalShowcaseSection";
import { motion } from "@/design-system/motion";
import { listGoals } from "@/services/goals";
import type { Goal } from "@/types/goal";

/**
 * The sidebar's "Goals" destination (/goals - see components/layout/
 * navConfig.ts) - this is where goal creation actually happens: the
 * Create Goal action, the Goal Showcase's example journeys, and the real
 * "Your Goals" list. Everything here is exactly what used to live at "/"
 * before the sidebar architecture split Home and Goals apart - moved,
 * not redesigned (see features/dashboard/ for the still-shared
 * components: DashboardActions, GoalShowcaseSection, GoalCard,
 * EmptyGoalsState, CreateGoalModal - none of them changed, only who
 * imports them did).
 *
 * The one real difference from the old dashboard: no personalized
 * greeting/headline at the top. That's Home's job now
 * (features/home/HomeView.tsx) - repeating "Good afternoon, Krishna"
 * here would just duplicate it one click later. A plain page heading
 * takes its place instead.
 */
export default function GoalsView() {
  const router = useRouter();
  const [goals, setGoals] = useState<Goal[] | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalInitialTitle, setModalInitialTitle] = useState("");

  useEffect(() => {
    listGoals()
      .then(setGoals)
      .catch(() => setGoals([]));
  }, []);

  function openCreateModal(initialTitle = "") {
    setModalInitialTitle(initialTitle);
    setModalOpen(true);
  }

  function handleCreated(goal: Goal) {
    setModalOpen(false);
    router.push(`/workspace/${goal.workspace_id}`);
  }

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-24 px-8 py-20 sm:gap-32 sm:py-28">
      <div className="flex flex-col gap-12 sm:gap-16">
        <div className="animate-fade-in-up flex flex-col items-center gap-2 text-center">
          <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">Goals</p>
          <h1 className="text-foreground text-3xl font-semibold tracking-tight sm:text-4xl">
            Create and manage your goals
          </h1>
        </div>

        <DashboardActions onCreateGoal={() => openCreateModal()} />

        <GoalShowcaseSection onSelectExample={(title) => openCreateModal(title)} />
      </div>

      <div
        className="animate-fade-in-up flex flex-col gap-8"
        style={{ animationDelay: motion.heroSectionDelay() }}
      >
        <div className="flex flex-col items-center gap-1.5 text-center">
          <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            Life Command Center
          </p>
          <h2 className="text-foreground text-3xl font-semibold tracking-tight">Your Goals</h2>
        </div>

        {goals === null && (
          <p className="text-muted-foreground text-center text-sm">Loading your goals…</p>
        )}

        {goals !== null && goals.length === 0 && (
          <EmptyGoalsState onCreateGoal={() => openCreateModal()} />
        )}

        {goals !== null && goals.length > 0 && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {goals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        )}
      </div>

      <CreateGoalModal
        open={modalOpen}
        initialTitle={modalInitialTitle}
        onClose={() => setModalOpen(false)}
        onCreated={handleCreated}
      />
    </div>
  );
}
