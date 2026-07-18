/**
 * Shadow tokens for LifeOS - "floating paper" cards on a warm
 * off-white page (Notion/Linear light-mode territory), rather than
 * heavy, high-contrast drop shadows or the dark-theme inset-highlight
 * trick (a white top-edge highlight makes sense on a dark material
 * catching light; it's invisible on a white card, so neutral surfaces
 * now rely on a soft warm-black ambient shadow instead). The one
 * exception is the primary button: as a solid accent-teal surface it
 * still benefits from a subtle glossy top highlight, so it keeps one.
 *
 * Values are full Tailwind arbitrary-value utility classes (e.g.
 * `"shadow-[0_1px_2px_...]"`), not bare CSS - that's deliberate.
 * Tailwind v4 finds utility classes by scanning the literal text of
 * every source file, including this one, so exporting the complete
 * class string here and writing `className={shadows.floating}` in a
 * component produces the exact same generated CSS as writing the
 * bracket expression inline, while removing the duplication.
 *
 * A CSS `box-shadow` is a single property, so these are composed,
 * complete looks rather than layers meant to be combined with each
 * other on the same element - use one of the composite tokens, not
 * several at once.
 *
 * `iconGlowAccent` and `iconGlowAccentHover` use `drop-shadow-[...]`
 * (a `filter`, not a `box-shadow`) for the very subtle glow on accent-
 * colored icons - same "literal string lives here" reasoning applies.
 */
export const shadows = {
  // Tailwind's standard elevation scale - reserved for future use;
  // nothing on the current homepage needs a plain drop shadow, since
  // the floating-paper tokens below are used instead.
  sm: "shadow-sm",
  md: "shadow-md",
  lg: "shadow-lg",
  /** Modal's backdrop-floating dialog. */
  xl: "shadow-2xl",

  // The floating-paper resting/hover pair - Card and the empty-state
  // onboarding panel both rest on `floating` and lift into one of the
  // hover variants. Warm near-black at low opacity, not pure black -
  // keeps the shadow feeling soft rather than harsh.
  floating: "shadow-[0_1px_2px_rgba(28,27,24,0.04),0_8px_24px_-12px_rgba(28,27,24,0.10)]",
  floatingHover: "shadow-[0_2px_4px_rgba(28,27,24,0.05),0_20px_40px_-16px_rgba(28,27,24,0.16)]",
  /** EmptyGoalsState's larger panel lifts with a slightly deeper, wider shadow than a regular Card. */
  floatingHoverLarge:
    "shadow-[0_4px_8px_rgba(28,27,24,0.05),0_28px_56px_-20px_rgba(28,27,24,0.18)]",

  // Standalone pieces. Kept as a subtle *warm-white* top highlight,
  // meant for surfaces that are themselves slightly tinted/gray (like
  // the illustration circle's `surface-hover` fill) rather than pure
  // white - on an actual white card these would do nothing, which is
  // why Card/EmptyGoalsState use `floating`/`floatingHover` instead.
  innerHighlight: "shadow-[inset_0_1px_0_rgba(255,255,255,0.6)]",
  innerHighlightStrong: "shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
  glow: "shadow-[0_10px_28px_-10px_var(--accent-glow)]",

  // Composite looks tied to a specific component.
  /** Button primary, resting - a solid accent-teal surface still reads
   *  well with a soft glossy top highlight, unlike the neutral cards.
   *  Deliberately *no* glow layer here - the app's rule is "calm by
   *  default, glow responds to interaction," so the accent glow only
   *  appears in `buttonPrimaryHover`, not at rest. */
  buttonPrimary: "shadow-[inset_0_1px_0_rgba(255,255,255,0.25),0_1px_2px_rgba(28,27,24,0.15)]",
  /** Button primary, hover - this is where the glow appears, spreading
   *  wider/softer rather than brighter, so the lift reads as premium,
   *  not glaring. */
  buttonPrimaryHover:
    "shadow-[inset_0_1px_0_rgba(255,255,255,0.3),0_2px_4px_rgba(28,27,24,0.18),0_18px_36px_-8px_var(--accent-glow)]",
  /** InspirationChips / Goal Showcase cards, hover. */
  chipGlowHover: "shadow-[0_10px_20px_-12px_var(--accent-glow)]",
  /** ConnectionIndicator's "connected" dot - subtle green glow. */
  statusRingSuccess: "shadow-[0_0_0_3px_rgba(30,158,107,0.16)]",

  // Very subtle icon glows (filter: drop-shadow, not box-shadow) - see
  // the "Icons" section of the theme spec: accent-teal icons glow
  // faintly at rest, and gain a lighter aqua highlight on hover. Used
  // sparingly - not applied to every icon in the app.
  iconGlowAccent: "drop-shadow-[0_0_4px_rgba(31,122,140,0.3)]",
  iconGlowAccentHover: "drop-shadow-[0_0_4px_rgba(79,168,187,0.4)]",
} as const;

export type ShadowToken = keyof typeof shadows;
