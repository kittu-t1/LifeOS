/**
 * Shadow tokens for LifeOS - the "Apple-inspired floating material"
 * look (a light inset top edge plus a wide, quiet drop shadow) rather
 * than heavy, high-contrast drop shadows.
 *
 * Values are full Tailwind arbitrary-value utility classes (e.g.
 * `"shadow-[inset_0_1px_0_...]"`), not bare CSS - that's deliberate.
 * Tailwind v4 finds utility classes by scanning the literal text of
 * every source file, including this one, so exporting the complete
 * class string here and writing `className={shadows.floating}` in a
 * component produces the exact same generated CSS as writing the
 * bracket expression inline, while removing the duplication (the
 * "floating" resting shadow, for example, used to be copy-pasted
 * across Card.tsx and EmptyGoalsState.tsx).
 *
 * A CSS `box-shadow` is a single property, so these are composed,
 * complete looks rather than layers meant to be combined with each
 * other on the same element - use `innerHighlight` or `glow` alone,
 * or one of the composite tokens, not several at once.
 */
export const shadows = {
  // Tailwind's standard elevation scale - reserved for future use;
  // nothing on the current homepage needs a plain drop shadow, since
  // the floating-material tokens below are used instead.
  sm: "shadow-sm",
  md: "shadow-md",
  lg: "shadow-lg",
  /** Modal's backdrop-floating dialog. */
  xl: "shadow-2xl",

  // The floating-material resting/hover pair - Card and the empty-state
  // onboarding panel both rest on `floating` and lift into one of the
  // hover variants.
  floating: "shadow-[inset_0_1px_0_rgba(255,255,255,0.05),0_1px_2px_rgba(0,0,0,0.2)]",
  floatingHover: "shadow-[inset_0_1px_0_rgba(255,255,255,0.06),0_16px_32px_-16px_rgba(0,0,0,0.45)]",
  /** EmptyGoalsState's larger panel lifts with a slightly deeper, wider shadow than a regular Card. */
  floatingHoverLarge:
    "shadow-[inset_0_1px_0_rgba(255,255,255,0.06),0_24px_48px_-24px_rgba(0,0,0,0.5)]",

  // Standalone pieces, for anything that wants just one or the other.
  innerHighlight: "shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]",
  /** A touch stronger - EmptyGoalsState's illustration circle. */
  innerHighlightStrong: "shadow-[inset_0_1px_0_rgba(255,255,255,0.08)]",
  glow: "shadow-[0_10px_28px_-10px_var(--accent-glow)]",

  // Composite looks tied to a specific component.
  /** Button primary, resting. */
  buttonPrimary:
    "shadow-[inset_0_1px_0_rgba(255,255,255,0.2),0_1px_2px_rgba(0,0,0,0.3),0_10px_28px_-10px_var(--accent-glow)]",
  /** Button primary, hover. */
  buttonPrimaryHover:
    "shadow-[inset_0_1px_0_rgba(255,255,255,0.24),0_2px_4px_rgba(0,0,0,0.35),0_18px_38px_-10px_var(--accent-glow)]",
  /** InspirationChips, hover. */
  chipGlowHover: "shadow-[0_10px_24px_-12px_var(--accent-glow)]",
  /** ConnectionIndicator's "connected" dot. */
  statusRingSuccess: "shadow-[0_0_0_3px_rgba(61,214,140,0.16)]",
} as const;

export type ShadowToken = keyof typeof shadows;
