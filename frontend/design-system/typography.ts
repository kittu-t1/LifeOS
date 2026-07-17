/**
 * Typography tokens for LifeOS.
 *
 * Each size is grounded in what the current homepage actually renders
 * (see the fontSize/lineHeight/letterSpacing comments on each token) -
 * this file documents the live UI rather than proposing a new one.
 * `displayLarge` and `heading2` are the two exceptions: the homepage
 * doesn't use those exact sizes yet, so they're filled in one Tailwind
 * type-scale step below their neighbor, ready for future pages
 * (Goals, Workspace, Timeline, Calendar, AI Coach, Analytics) to reach
 * for instead of inventing a new size.
 */
export interface TypographyToken {
  /** CSS font-size. */
  fontSize: string;
  fontWeight: number;
  /** Unitless line-height ratio (or a fixed value for the responsive tokens below). */
  lineHeight: string;
  letterSpacing: string;
  textTransform?: "uppercase" | "none";
  /** Present only on tokens with a distinct mobile size (currently just Display XL). */
  responsive?: {
    fontSize: string;
    lineHeight: string;
  };
}

export const typography = {
  // DashboardView hero headline ("Good afternoon. / What will you build
  // today?"). Mobile-first: text-[2.75rem] leading-[1.08], stepping up
  // to text-6xl leading-[1.05] at the `sm` breakpoint.
  displayXL: {
    fontSize: "2.75rem",
    fontWeight: 600,
    lineHeight: "1.08",
    letterSpacing: "-0.025em",
    responsive: { fontSize: "3.75rem", lineHeight: "1.05" },
  },

  // Reserved for large section headers on future pages - one Tailwind
  // step below Display XL (text-5xl), not yet used on the homepage.
  displayLarge: {
    fontSize: "3rem",
    fontWeight: 600,
    lineHeight: "1.1",
    letterSpacing: "-0.025em",
  },

  // EmptyGoalsState headline ("Every goal deserves a workspace.").
  heading1: {
    fontSize: "1.5rem",
    fontWeight: 600,
    lineHeight: "1.333",
    letterSpacing: "-0.025em",
  },

  // Reserved for dialog/section headings one step below Heading 1
  // (text-lg - matches CreateGoalModal's dialog title and
  // WorkspaceShell's title, both font-semibold).
  heading2: {
    fontSize: "1.125rem",
    fontWeight: 600,
    lineHeight: "1.556",
    letterSpacing: "-0.025em",
  },

  // GoalCard title (text-base font-semibold) - card/list-item level
  // headings.
  heading3: {
    fontSize: "1rem",
    fontWeight: 600,
    lineHeight: "1.5",
    letterSpacing: "normal",
  },

  // DashboardView hero subtitle ("LifeOS turns every goal into an
  // intelligent workspace.") - text-base leading-relaxed.
  bodyLarge: {
    fontSize: "1rem",
    fontWeight: 400,
    lineHeight: "1.625",
    letterSpacing: "normal",
  },

  // The default UI text size - buttons, inputs, links, most paragraphs
  // (text-sm).
  body: {
    fontSize: "0.875rem",
    fontWeight: 400,
    lineHeight: "1.4286",
    letterSpacing: "normal",
  },

  // Secondary/metadata text - Badge labels, GoalCard date & progress
  // (text-xs).
  small: {
    fontSize: "0.75rem",
    fontWeight: 500,
    lineHeight: "1.333",
    letterSpacing: "normal",
  },

  // Smallest size - uppercase eyebrow/status labels (ConnectionIndicator,
  // the workflow step labels in EmptyGoalsState). The one homepage size
  // that falls outside Tailwind's default scale (text-[11px]), which is
  // exactly why it's worth centralizing here.
  caption: {
    fontSize: "0.6875rem",
    fontWeight: 500,
    lineHeight: "1.36",
    letterSpacing: "0.025em",
    textTransform: "uppercase",
  },
} as const satisfies Record<string, TypographyToken>;

export type TypographyTokenName = keyof typeof typography;
