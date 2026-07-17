import { ChevronDown, Compass, ListTodo, Sparkles, Target, TrendingUp, Trophy } from "lucide-react";
import { colors } from "@/design-system/colors";
import { gradients } from "@/design-system/gradients";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";
import InspirationChips from "@/features/dashboard/InspirationChips";

// The same "goal in, outcome out" loop described in docs/vision.md,
// reduced to five nodes so a first-time visitor can read the whole
// product in one glance before they've created anything. This is the
// empty state's "visual journey" - deliberately the only explanation on
// the page, rather than pairing it with a separate feature list that
// would just repeat the same point in a second format.
const WORKFLOW_STEPS = [
  { label: "Goal", icon: Target },
  { label: "AI Planning", icon: Sparkles },
  { label: "Tasks", icon: ListTodo },
  { label: "Progress", icon: TrendingUp },
  { label: "Achievement", icon: Trophy },
];

/**
 * Onboarding empty state (Apple-philosophy redesign pass) - the first
 * thing a new user sees, so it carries the product's whole pitch in as
 * few elements as possible: a quiet illustration, one headline, one
 * line of explanation, and the Goal -> AI Planning -> Tasks -> Progress
 * -> Achievement journey, whose five nodes reveal in sequence rather
 * than all at once. Still a single floating-material container, still
 * leads straight into the inspiration chips.
 *
 * Colors, shadows, gradients, and motion all come from the design
 * system (@/design-system). Two intentional exceptions stay as literal
 * Tailwind classes: `hover:border-white/[0.14]` (see Card.tsx's comment
 * - a raw rgba string can't safely become a bracket value) and the
 * `mt-[18px]` connector alignment below it, which is a one-off visual
 * fudge rather than a real spacing-scale value.
 */
export default function EmptyGoalsState({
  onSelectExample,
}: {
  onSelectExample: (title: string) => void;
}) {
  return (
    <div
      className={`border-border bg-surface relative overflow-hidden ${radius.xl.class} border px-8 py-20 text-center ${shadows.floating} ${motion.transition.cardHover} hover:${motion.transform.hoverLift} hover:border-white/[0.14] hover:${shadows.floatingHoverLarge} sm:py-24`}
    >
      {/* Faint radial tint, not a full gradient background - reads as
          texture rather than decoration. */}
      <div
        aria-hidden
        className={`pointer-events-none absolute inset-0 ${gradients.heroGlow} opacity-40`}
      />

      <div className="relative flex flex-col items-center gap-14">
        <div className="flex flex-col items-center gap-5">
          {/* Monochrome illustration - a quiet glowing ring behind a
              compass, standing in for "you have a direction, LifeOS
              finds the route." No emoji, no color outside the accent. */}
          <div className="relative flex h-20 w-20 items-center justify-center">
            <div
              aria-hidden
              className={`${motion.animation.softPulse} absolute inset-0 rounded-full blur-2xl`}
              style={{ background: colors.primaryGlow }}
            />
            <div
              className={`border-border bg-surface-hover relative flex h-16 w-16 items-center justify-center ${radius.full.class} border ${shadows.innerHighlightStrong}`}
            >
              <Compass size={26} strokeWidth={1.5} className="text-accent" />
            </div>
          </div>

          <div className="flex flex-col items-center gap-3">
            <h2 className="text-foreground text-2xl font-semibold tracking-tight">
              Every goal deserves a workspace.
            </h2>
            <p className="text-muted-foreground max-w-sm text-sm leading-relaxed">
              LifeOS plans, executes, and tracks progress so you can focus on the work that matters.
            </p>
          </div>
        </div>

        <div className="border-border/60 w-full max-w-md border-t pt-10">
          <div className="flex flex-col items-center gap-1.5 sm:flex-row sm:items-start sm:justify-between sm:gap-0">
            {WORKFLOW_STEPS.map((step, i) => (
              <div
                key={step.label}
                className={`${motion.animation.workflowReveal} flex flex-col items-center sm:flex-1`}
                style={{ animationDelay: motion.workflowStepDelay(i) }}
              >
                <div className="flex flex-col items-center gap-1.5">
                  <div
                    className={`border-border bg-surface-hover flex h-9 w-9 shrink-0 items-center justify-center ${radius.full.class} border`}
                  >
                    <step.icon size={15} className="text-accent" />
                  </div>
                  <span className="text-muted-foreground text-[11px] font-medium whitespace-nowrap">
                    {step.label}
                  </span>
                </div>
                {i < WORKFLOW_STEPS.length - 1 && (
                  <>
                    <ChevronDown size={12} className="text-muted-foreground/40 my-0.5 sm:hidden" />
                    {/* mt-[18px] is a one-off alignment fudge (roughly
                        half the icon-circle height) rather than a
                        spacing-scale value - it centers the connector
                        line against the icon circles above it. */}
                    <div
                      aria-hidden
                      className="bg-border mt-[18px] hidden h-px w-full flex-1 sm:block"
                    />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col items-center gap-4">
          <span className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
            Need inspiration?
          </span>
          <InspirationChips onSelect={onSelectExample} />
        </div>
      </div>
    </div>
  );
}
