/**
 * Gradient tokens for LifeOS.
 *
 * `primaryButton`, `cardSurface`, and `heroGlow` are full Tailwind
 * arbitrary-value `bg-[...]` utility classes (see the note in
 * shadows.ts about why exporting the literal class string here is safe
 * with Tailwind v4's content scanning) - drop them straight into a
 * `className`.
 *
 * `pageGlow` is a plain CSS `background` value instead, because it
 * describes the page's `body` background in app/globals.css, which is
 * hand-written CSS and can't import from a TypeScript file. It's
 * captured here as the documented, typed reference for the light
 * theme's single ambient glow - if it ever changes, update both this
 * file and globals.css together. (The dark-mode fallback's four-layer
 * composite lives only in globals.css, since it's not used by any
 * component directly.)
 */
export const gradients = {
  /** Button.tsx primary variant - a soft light-to-base vertical sheen
   *  that reads as a slightly domed, physical surface. */
  primaryButton: "bg-[linear-gradient(180deg,var(--accent-hover)_0%,var(--accent)_100%)]",

  /** Card.tsx's decorative top-left highlight - a faint teal wash
   *  rather than white, since white-on-white would be invisible on the
   *  light theme's paper-white cards. */
  cardSurface:
    "bg-[radial-gradient(ellipse_60%_50%_at_0%_0%,rgba(31,122,140,0.035),transparent_60%)]",

  /** EmptyGoalsState's soft accent tint behind the headline. */
  heroGlow: "bg-[radial-gradient(ellipse_70%_50%_at_50%_-10%,var(--accent-glow),transparent_70%)]",

  /** The light theme's single ambient page glow (mirrors `--page-gradient` in globals.css). */
  pageGlow:
    "radial-gradient(ellipse 60% 40% at 50% -8%, rgba(31, 122, 140, 0.06), transparent 60%)",
} as const;

export type GradientToken = keyof typeof gradients;
