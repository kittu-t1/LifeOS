import { ArrowRight, Compass } from "lucide-react";
import Link from "next/link";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";
import OrbitIllustration from "@/features/dashboard/OrbitIllustration";

// Single-demo-user placeholder (see backend/app/core/deps.py -
// DEMO_USER_EMAIL resolves to a hardcoded User(name="Krishna") until real
// auth/login exists). Same convention DashboardHero.tsx used before this
// page took over the greeting.
const USER_NAME = "Krishna";

function timeOfDayGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

/**
 * The sidebar's "Home" destination (/ - see components/layout/
 * navConfig.ts) - deliberately just a welcome message and a couple of
 * lines about LifeOS, nothing else. This used to be where the full Goals
 * dashboard lived (Create Goal action, Goal Showcase, the goal list);
 * that content now lives at /goals (see features/goals/GoalsView.tsx),
 * reached via the sidebar's own "Goals" item. Splitting the two apart is
 * what lets Home answer "what is this app" while Goals answers "what am
 * I trying to accomplish" - the sidebar architecture's whole point (see
 * MainLayout.tsx's docstring).
 *
 * OrbitIllustration (features/dashboard/OrbitIllustration.tsx) moves
 * here from the old marketing Hero it originally shipped with - reused
 * as-is rather than duplicated, since nothing about the illustration
 * itself needed to change, just where it's shown.
 *
 * The "Explore LifeOS" tile (routes to /explore - see
 * features/explore/ExploreView.tsx) moved here too, from
 * GoalShowcaseSection.tsx on the Goals page. Home is where people get
 * oriented on what LifeOS actually is, so "see how the whole loop
 * works" belongs with the welcome message, not on the page whose job is
 * narrowly "create a goal."
 */
export default function HomeView() {
  return (
    <div className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-8 px-8 py-20 text-center">
      <div className="animate-fade-in-up flex flex-col items-center gap-4">
        <p className="text-muted-foreground text-base">
          {timeOfDayGreeting()}, {USER_NAME} 👋
        </p>
        <h1 className="text-foreground text-4xl font-semibold tracking-tight sm:text-5xl">
          Welcome to LifeOS
        </h1>
        <p className="text-muted-foreground max-w-md text-lg leading-relaxed">
          LifeOS is your personal execution operating system - it turns your goals into AI-planned
          workspaces and helps you build the habits that carry them through.
        </p>
      </div>

      <OrbitIllustration />

      <Link
        href="/explore"
        className={`border-border bg-surface group relative flex items-center gap-4 overflow-hidden ${radius["2xl"].class} border px-6 py-4 ${shadows.floating} ${motion.transition.cardHover} hover:bg-surface-hover hover:${motion.transform.hoverLift} hover:border-black/[0.12] hover:${shadows.floatingHover}`}
      >
        <div
          className={`bg-accent/10 flex h-11 w-11 shrink-0 items-center justify-center ${radius.full.class}`}
        >
          <Compass size={19} className="text-accent" strokeWidth={1.75} />
        </div>
        <div className="flex flex-col gap-0.5 text-left">
          <span className="text-foreground text-base font-bold">Explore LifeOS</span>
          <span className="text-muted-foreground text-xs">
            See how the whole loop works, from goal to achievement.
          </span>
        </div>
        <ArrowRight
          size={16}
          className="text-muted-foreground/50 group-hover:text-accent shrink-0 transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:translate-x-0.5"
        />
      </Link>
    </div>
  );
}
