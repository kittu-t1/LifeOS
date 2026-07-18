/**
 * Motion tokens for LifeOS - durations, easing curves, and the
 * transition/transform/animation class fragments built from them.
 *
 * LifeOS currently uses one "premium" ease curve
 * (`cubic-bezier(0.16, 1, 0.3, 1)`) for both hover interactions and
 * on-load reveals, so `spring` and `decelerate` intentionally point at
 * the same value today - keeping them as separate names means either
 * can diverge later (e.g. a snappier curve for hover, a gentler one for
 * page entry) without renaming every call site.
 */
export const duration = {
  /** 200ms - Input's focus-ring color transition. */
  fast: "200ms",
  /** 300ms - the default for hover transitions app-wide (Button, Card,
   *  chips, the empty-state panel). */
  normal: "300ms",
  /** 600ms - matches the `fade-in-up` keyframe duration in globals.css. */
  slow: "600ms",
} as const;

export const easing = {
  /** Tailwind's default transition timing function - used implicitly
   *  wherever a component doesn't set a custom `ease-*` class. */
  standard: "cubic-bezier(0.4, 0, 0.2, 1)",
  /** The app's signature "premium" curve for hover/interaction motion. */
  spring: "cubic-bezier(0.16, 1, 0.3, 1)",
  /** Same curve, used for entrance/reveal animation - see the file
   *  comment above for why these two names currently share a value. */
  decelerate: "cubic-bezier(0.16, 1, 0.3, 1)",
} as const;

/**
 * Ready-to-use Tailwind class fragments, so components stop repeating
 * `transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]`
 * (previously duplicated across Button, Card, DashboardView,
 * EmptyGoalsState, and InspirationChips) and instead spread one named
 * token.
 */
export const transition = {
  buttonHover: "transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]",
  cardHover: "transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]",
  chipHover: "transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]",
  /** Input's plain color-only transition. */
  fade: "transition-colors duration-200",
  /** The Create Goal button's hover arrow nudge. */
  lift: "transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]",
} as const;

// Bare transform utilities - callers compose these with whatever
// variant prefix the moment calls for (usually `hover:`, e.g.
// `` `hover:${transform.hoverLift}` `` ), since a handful of components
// use the same lift as a plain, unprefixed transform.
export const transform = {
  /** Secondary/ghost button hover lift (1px). */
  hoverLiftSm: "-translate-y-px",
  /** Primary button, Card, chip, and empty-state panel hover lift (2px). */
  hoverLift: "-translate-y-0.5",
  /** Button's press-down feedback on `:active`. */
  buttonPress: "active:scale-[0.98] active:translate-y-0",
  /** Alias of `hoverLift`, named for Card's specific use. */
  cardLift: "-translate-y-0.5",
} as const;

export const animation = {
  /** The shared entrance fade + upward rise, used to stagger the hero,
   *  goal list, and workflow steps in on load. */
  pageEnter: "animate-fade-in-up",
  workflowReveal: "animate-fade-in-up",
  /** Gentle breathing used on the empty-state illustration's glow ring. */
  softPulse: "animate-soft-pulse",
  /** Slow vertical float for section illustrations (Hero, AI Intelligence). */
  floatSlow: "animate-float-slow",
} as const;

/**
 * The empty-state workflow steps (Goal -> AI Planning -> Tasks ->
 * Progress -> Achievement) reveal one after another rather than all at
 * once - this replaces the inline `180 + i * 110` formula that used to
 * live directly in EmptyGoalsState.tsx.
 */
export const stagger = {
  workflowStepBaseDelayMs: 180,
  workflowStepIntervalMs: 110,
  /** DashboardView's goal list/empty-state section entrance, staggered
   *  just after the hero. */
  heroSectionDelayMs: 120,
} as const;

export function heroSectionDelay(): string {
  return `${stagger.heroSectionDelayMs}ms`;
}

export function workflowStepDelay(index: number): string {
  return `${stagger.workflowStepBaseDelayMs + index * stagger.workflowStepIntervalMs}ms`;
}

/**
 * General-purpose stagger delay for any row of cards revealing one
 * after another (How LifeOS Works, Goal Showcase, AI Intelligence) -
 * same base+interval math as `workflowStepDelay`, just not tied to that
 * one component's naming.
 */
export function staggerDelay(index: number, baseMs = 100, intervalMs = 90): string {
  return `${baseMs + index * intervalMs}ms`;
}

export const motion = {
  duration,
  easing,
  transition,
  transform,
  animation,
  stagger,
  workflowStepDelay,
  heroSectionDelay,
  staggerDelay,
} as const;
