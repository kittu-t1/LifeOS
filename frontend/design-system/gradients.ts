/**
 * Gradient tokens for LifeOS.
 *
 * `primaryButton`, `cardSurface`, and `heroGlow` are full Tailwind
 * arbitrary-value `bg-[...]` utility classes (see the note in
 * shadows.ts about why exporting the literal class string here is safe
 * with Tailwind v4's content scanning) - drop them straight into a
 * `className`.
 *
 * `purpleGlow`, `blueGlow`, `vignette`, and `backgroundGlow` are plain
 * CSS `background` values instead, because they describe the page's
 * `body` background in app/globals.css, which is hand-written CSS and
 * can't import from a TypeScript file. They're captured here as the
 * documented, typed reference for that background - if it ever changes,
 * update both this file and globals.css together.
 */
export const gradients = {
  /** Button.tsx primary variant - a soft light-to-base vertical sheen
   *  that reads as a slightly domed, physical surface. */
  primaryButton: "bg-[linear-gradient(180deg,var(--accent-hover)_0%,var(--accent)_100%)]",

  /** Card.tsx's decorative top-left highlight - quiet studio lighting on a material. */
  cardSurface:
    "bg-[radial-gradient(ellipse_60%_50%_at_0%_0%,rgba(255,255,255,0.035),transparent_60%)]",

  /** EmptyGoalsState's soft accent tint behind the headline. */
  heroGlow: "bg-[radial-gradient(ellipse_70%_50%_at_50%_-10%,var(--accent-glow),transparent_70%)]",

  /** Purple glow layer of the page body background (top-left). */
  purpleGlow:
    "radial-gradient(ellipse 55% 40% at 18% -8%, rgba(124, 108, 255, 0.07), transparent 60%)",
  /** Blue glow layer of the page body background (top-right). */
  blueGlow:
    "radial-gradient(ellipse 45% 35% at 88% 4%, rgba(76, 130, 255, 0.045), transparent 65%)",
  /** Vignette layer of the page body background (bottom edge). */
  vignette: "radial-gradient(ellipse 90% 55% at 50% 108%, rgba(0, 0, 0, 0.35), transparent 70%)",
  /** The full composite `body { background: ... }` value from globals.css. */
  backgroundGlow: [
    "radial-gradient(ellipse 55% 40% at 18% -8%, rgba(124, 108, 255, 0.07), transparent 60%)",
    "radial-gradient(ellipse 45% 35% at 88% 4%, rgba(76, 130, 255, 0.045), transparent 65%)",
    "radial-gradient(ellipse 90% 55% at 50% 108%, rgba(0, 0, 0, 0.35), transparent 70%)",
    "var(--background)",
  ].join(", "),
} as const;

export type GradientToken = keyof typeof gradients;
