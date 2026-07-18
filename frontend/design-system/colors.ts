/**
 * Semantic color tokens for LifeOS.
 *
 * These are intentionally CSS custom-property references, not hardcoded
 * hex values - the real colors live in exactly one place
 * (app/globals.css `:root`, with a `prefers-color-scheme: dark`
 * override). This file gives TypeScript code (inline styles, future
 * charts/canvases, anything outside a Tailwind `className`) a typed,
 * semantic, autocompletable way to reach the same colors Tailwind
 * utility classes already read from (`bg-surface`, `text-muted-foreground`,
 * `border-border`, ...). It does not introduce a second source of truth -
 * if the palette changes, it changes in globals.css and every consumer
 * (Tailwind classes and this file alike) picks it up automatically.
 *
 * Concrete values as of the light-first "premium life OS" theme
 * (light is the only theme; see globals.css):
 *   background            #F7F7F5
 *   surface               #FFFFFF
 *   surface-hover         #F1F1EE
 *   surface-elevated      #FFFFFF
 *   border                rgba(28, 27, 24, 0.08)
 *   foreground            #1C1B18
 *   foreground-secondary  #4B4A45
 *   muted-foreground      #86847C
 *   accent                #1F7A8C  (deep ice teal - buttons, highlights,
 *                                   AI elements, progress; ~5:1 contrast
 *                                   against white text)
 *   accent-hover          #2B96AA
 *   accent-glow           rgba(195, 231, 239, 0.5)  (pale sky aqua)
 *   accent-secondary      #4FA8BB  (lighter teal - sparing accent only)
 *   accent-secondary-glow rgba(195, 231, 239, 0.4)
 *   success               #1E9E6B
 *   warning               #C8860D
 *   danger                #D6473B
 */
export const colors = {
  // Surfaces, page background up to floating panels. In the light
  // theme these read as "warm off-white page, white paper cards," not
  // as a literal light-to-dark ramp.
  background: "var(--background)",
  backgroundElevated: "var(--surface-elevated)",
  surface: "var(--surface)",
  surfaceSecondary: "var(--surface-hover)",
  surfaceTertiary: "var(--surface-elevated)",

  // Borders
  border: "var(--border)",
  // Used for the "stronger" hover-state border on Button/Card/
  // EmptyGoalsState (`hover:border-black/[0.14]` in the light theme) -
  // not yet promoted to its own CSS custom property, so it's
  // centralized here instead of being repeated as a literal in three
  // components.
  borderStrong: "rgba(28, 27, 24, 0.14)",

  // Text
  textPrimary: "var(--foreground)",
  textSecondary: "var(--foreground-secondary)",
  textMuted: "var(--muted-foreground)",

  // Brand / accent - keep this to buttons, highlights, AI elements, and
  // progress indicators. Never the whole interface.
  primary: "var(--accent)",
  primaryHover: "var(--accent-hover)",
  primaryGlow: "var(--accent-glow)",
  primaryForeground: "var(--accent-foreground)",

  // Secondary accent (a lighter, pale-aqua-leaning teal) - reserved for
  // tiny details only: small glows, hover highlights, the connection
  // status indicator. Never used for primary actions or large surfaces -
  // it should never compete with `primary` for attention.
  secondary: "var(--accent-secondary)",
  secondaryGlow: "var(--accent-secondary-glow)",

  // A cool metallic gray for "premium hardware" touches (a divider, a
  // badge, an icon tint) - distinct from `border`/`textMuted`, which
  // are both warm-neutral. Used sparingly.
  silver: "var(--silver)",

  // Status
  success: "var(--success)",
  warning: "var(--warning)",
  danger: "var(--danger)",

  // Interaction
  focusRing: "var(--accent)",
} as const;

export type ColorToken = keyof typeof colors;
