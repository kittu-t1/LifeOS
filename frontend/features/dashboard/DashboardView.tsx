"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "@/design-system/motion";
import CreateGoalModal from "@/features/dashboard/CreateGoalModal";
import DashboardActions from "@/features/dashboard/DashboardActions";
import DashboardHero from "@/features/dashboard/DashboardHero";
import EmptyGoalsState from "@/features/dashboard/EmptyGoalsState";
import GoalCard from "@/features/dashboard/GoalCard";
import GoalShowcaseSection from "@/features/dashboard/GoalShowcaseSection";
import { listGoals } from "@/services/goals";
import type { Goal } from "@/types/goal";

/**
 * The dashboard as a home screen, not a landing page: a personalized
 * greeting (DashboardHero), a single "Create Goal" action
 * (DashboardActions), the Goal Showcase's example journeys, then the
 * real, functional goal list ("Your Goals"). See docs/vision.md for the
 * underlying goal -> workspace -> execution -> outcome arc this page is
 * telling.
 *
 * Per the sidebar architecture redesign, this page's job narrowed on
 * purpose: Goals is the center's only concern now. Habits and Memory
 * used to have their own dashboard entry points (a "Goals + Habits"
 * two-card row) - both moved to the sidebar (see
 * components/layout/navConfig.ts and components/layout/MainLayout.tsx),
 * reachable from every page instead of competing for space on this one.
 * The center should always answer "what am I trying to accomplish" -
 * the sidebar answers "what tools help me accomplish it."
 *
 * DashboardHero replaces the old marketing-style Hero (a fixed headline
 * + orbit illustration + single "Create Your First Goal" CTA - see git
 * history for HeroSection.tsx/OrbitIllustration.tsx, removed once
 * nothing referenced them).
 *
 * One section intentionally isn't repeated here - it used to be a
 * compact inline teaser, and duplicated /explore
 * (features/explore/ExploreView.tsx) with no real benefit once the
 * "Explore LifeOS" tile (inside GoalShowcaseSection) reliably takes
 * people to the full version: the step-by-step "How LifeOS works"
 * walkthrough (removed; was HowItWorksSection.tsx). One copy of this
 * content, reached through one link, beats two copies that can drift
 * apart.
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
      {/* Hero, Actions, and Goal Showcase share a tighter gap than the
          rest of the page's rhythm - all three are one continuous
          "here's what LifeOS is and how to start" opening statement, not
          separate ideas that need the bigger gap-24/32 rhythm used below
          between Goal Showcase and the live "Your Goals" section. */}
      <div className="flex flex-col gap-12 sm:gap-16">
        <DashboardHero />

        <DashboardActions onCreateGoal={() => openCreateModal()} />

        <GoalShowcaseSection onSelectExample={(title) => openCreateModal(title)} />
      </div>

      <div
        className="animate-fade-in-up flex flex-col gap-8"
        style={{ animationDelay: motion.heroSectionDelay() }}
      >
        <div className="flex flex-col items-center gap-1.5 text-center">
          {/* Names this section for what it actually is - the live,
              functional part of the page below the storytelling sections
              above it (see the "Dashboard Experience" framing: LifeOS as
              a "Life Command Center," not a bare goal list). The
              time-based greeting already lives in DashboardHero above,
              so this heading doesn't repeat it. */}
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
