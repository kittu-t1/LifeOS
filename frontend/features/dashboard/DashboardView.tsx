"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "@/design-system/motion";
import CreateGoalModal from "@/features/dashboard/CreateGoalModal";
import EmptyGoalsState from "@/features/dashboard/EmptyGoalsState";
import GoalCard from "@/features/dashboard/GoalCard";
import GoalShowcaseSection from "@/features/dashboard/GoalShowcaseSection";
import HeroSection from "@/features/dashboard/HeroSection";
import { listGoals } from "@/services/goals";
import type { Goal } from "@/types/goal";

function timeOfDayGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

/**
 * The homepage as a storytelling landing experience (Hero -> Goal
 * Showcase), ending in the real, functional dashboard - the actual
 * Create Goal flow and goal list. Every section above "Your Goals" is
 * presentation that explains the product; "Your Goals" is where the
 * product actually runs. See docs/vision.md for the underlying goal ->
 * workspace -> execution -> outcome arc this page is telling.
 *
 * Two sections intentionally aren't repeated here - both used to be
 * compact inline teasers, and both duplicated /explore
 * (features/explore/ExploreView.tsx) with no real benefit once the
 * "Explore LifeOS" tile reliably takes people to the full version:
 *   - the step-by-step "How LifeOS works" walkthrough (removed; was
 *     HowItWorksSection.tsx)
 *   - "The intelligence behind LifeOS" capability list (removed; was
 *     AIIntelligenceSection.tsx) - three of its four capabilities
 *     (roadmap generation, personal reflection, and progress tracking)
 *     restated what the AI Planning/Daily Execution/Reflection steps on
 *     /explore already say; the one genuinely new idea, smart
 *     reminders, was folded into the Daily Execution step's brief
 *     (see workflowSteps.ts) instead of keeping a whole section alive
 *     for it.
 * One copy of this content, reached through one link, beats two copies
 * that can drift apart.
 */
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
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-24 px-8 py-20 sm:gap-32 sm:py-28">
      <HeroSection onCreateGoal={() => openCreateModal()} />

      <GoalShowcaseSection onSelectExample={(title) => openCreateModal(title)} />

      <div
        className="animate-fade-in-up flex flex-col gap-8"
        style={{ animationDelay: motion.heroSectionDelay() }}
      >
        <div className="flex flex-col items-center gap-1.5 text-center">
          {/* Names this section for what it actually is - the live,
              functional part of the page below the storytelling sections
              above it (see the "Dashboard Experience" framing: LifeOS as
              a "Life Command Center," not a bare goal list). */}
          <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            Life Command Center
          </p>
          {goals !== null && goals.length > 0 && (
            <p className="text-muted-foreground text-sm">{timeOfDayGreeting()}, welcome back.</p>
          )}
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
