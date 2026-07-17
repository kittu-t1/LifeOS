/**
 * Semantic color tokens for LifeOS.
 *
 * These are intentionally CSS custom-property references, not hardcoded
 * hex values - the real colors live in exactly one place
 * (app/globals.css `:root`, with a light-mode override under
 * `prefers-color-scheme: light`). This file gives TypeScript code
 * (inline styles, future charts/canvases, anything outside a Tailwind
 * `className`) a typed, semantic, autocompletable way to reach the same
 * colors Tailwind utility classes already read from (`bg-surface`,
 * `text-muted-foreground`, `border-border`, ...). It does not introduce
 * a second source of truth - if the palette changes, it changes in
 * globals.css and every consumer (Tailwind classes and this file alike)
 * picks it up automatically.
 *
 * Concrete values as of the current homepage (dark theme - see
 * globals.css for the light-mode override):
 *   background            #09090B
 *   surface               #111114
 *   surface-hover         #17171C
 *   surface-elevated      #1D1D24
 *   border                rgba(255, 255, 255, 0.08)
 *   foreground            #FAFAFB
 *   foreground-secondary  #C2C2CC
 *   muted-foreground      #8E8E98
 *   accent                #7C6CFF
 *   accent-hover          #8F81FF
 *   accent-glow           rgba(124, 108, 255, 0.18)
 *   success               #3DD68C
 *   warning               #F5B942
 *   danger                #F0654F
 */
export const colors = {
  // Surfaces, darkest (page) to lightest (floating panels)
  background: "var(--background)",
  backgroundElevated: "var(--surface-elevated)",
  surface: "var(--surface)",
  surfaceSecondary: "var(--surface-hover)",
  surfaceTertiary: "var(--surface-elevated)",

  // Borders
  border: "var(--border)",
  // Used for the "stronger" hover-state border on Button/Card/
  // EmptyGoalsState (`hover:border-white/[0.14]`) - not yet promoted to
  // its own CSS custom property, so it's centralized here instead of
  // being repeated as a literal in three components.
  borderStrong: "rgba(255, 255, 255, 0.14)",

  // Text
  textPrimary: "var(--foreground)",
  textSecondary: "var(--foreground-secondary)",
  textMuted: "var(--muted-foreground)",

  // Brand / accent
  primary: "var(--accent)",
  primaryHover: "var(--accent-hover)",
  primaryGlow: "var(--accent-glow)",
  primaryForeground: "var(--accent-foreground)",

  // Status
  success: "var(--success)",
  warning: "var(--warning)",
  danger: "var(--danger)",

  // Interaction
  focusRing: "var(--accent)",
} as const;

export type ColorToken = keyof typeof colors;
