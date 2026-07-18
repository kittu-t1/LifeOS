import { Compass } from "lucide-react";
import Button from "@/components/ui/Button";
import { colors } from "@/design-system/colors";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";

/**
 * The actual functional entry point, at the bottom of the storytelling
 * homepage - deliberately minimal. The workflow explanation lives on
 * /explore (features/explore/ExploreView.tsx, reached via the Hero's
 * "Explore LifeOS" link) and the example goals live in
 * GoalShowcaseSection higher up the page, so this doesn't repeat
 * either; it's just "here's the button" for anyone who scrolled all the
 * way down instead of using the Hero's CTA.
 */
export default function EmptyGoalsState({ onCreateGoal }: { onCreateGoal: () => void }) {
  return (
    <div className="flex flex-col items-center gap-5 py-6 text-center">
      <div className="relative flex h-14 w-14 items-center justify-center">
        <div
          aria-hidden
          className={`${motion.animation.softPulse} absolute inset-0 rounded-full blur-xl`}
          style={{ background: colors.primaryGlow }}
        />
        <div
          className={`border-border bg-surface-hover relative flex h-12 w-12 items-center justify-center ${radius.full.class} border ${shadows.innerHighlightStrong}`}
        >
          <Compass
            size={20}
            strokeWidth={1.5}
            className={`text-accent ${shadows.iconGlowAccent}`}
          />
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <h3 className="text-foreground text-lg font-semibold">No goals yet</h3>
        <p className="text-muted-foreground text-sm">Your first goal is one click away.</p>
      </div>

      <Button onClick={onCreateGoal}>Create Your First Goal</Button>
    </div>
  );
}
