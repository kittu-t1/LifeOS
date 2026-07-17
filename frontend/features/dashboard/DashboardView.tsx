"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Plus } from "lucide-react";
import Button from "@/components/ui/Button";
import { motion } from "@/design-system/motion";
import { typography } from "@/design-system/typography";
import CreateGoalModal from "@/features/dashboard/CreateGoalModal";
import EmptyGoalsState from "@/features/dashboard/EmptyGoalsState";
import GoalCard from "@/features/dashboard/GoalCard";
import { listGoals } from "@/services/goals";
import type { Goal } from "@/types/goal";

function timeOfDayGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardView() {
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
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-24 px-8 py-28 sm:py-36">
      {/* Hero - typography carries the page, so the copy stays down to two
          short lines (see docs/vision.md's "goal -> workspace -> execution
          -> outcome" arc) rather than a sentence-length subtitle. No name
          in the headline on purpose: the confidence comes from the
          statement, not the personalization. */}
      <div className="animate-fade-in-up flex flex-col items-start gap-8">
        <h1
          className={`text-foreground max-w-2xl text-[${typography.displayXL.fontSize}] leading-[${typography.displayXL.lineHeight}] font-semibold tracking-tight sm:text-[${typography.displayXL.responsive.fontSize}] sm:leading-[${typography.displayXL.responsive.lineHeight}]`}
        >
          {timeOfDayGreeting()}.
          <br />
          <span className="text-foreground-secondary">What will you build today?</span>
        </h1>
        <p className="text-muted-foreground max-w-sm text-base leading-relaxed">
          LifeOS turns every goal into an intelligent workspace.
        </p>
        <Button onClick={() => openCreateModal()} className="group">
          <Plus size={16} />
          Create Goal
          <ArrowRight
            size={15}
            className={`${motion.transition.lift} group-hover:translate-x-0.5`}
          />
        </Button>
      </div>

      <div
        className="animate-fade-in-up flex flex-col gap-4"
        style={{ animationDelay: motion.heroSectionDelay() }}
      >
        {goals === null && <p className="text-muted-foreground text-sm">Loading your goals…</p>}

        {goals !== null && goals.length === 0 && (
          <EmptyGoalsState onSelectExample={(title) => openCreateModal(title)} />
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
