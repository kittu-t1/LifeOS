/**
 * Spacing scale for LifeOS.
 *
 * Every `gap-*`, `p-*`, `px-*`, `py-*`, and `m-*` class in the app
 * already draws from Tailwind's own numeric spacing scale (e.g. `gap-8`
 * is Tailwind's built-in "8" step, which happens to equal 32px) - that
 * scale *is* the spacing token system, so components keep using those
 * utility classes directly rather than re-importing this file just to
 * pick a padding. This module exists for the handful of cases that
 * genuinely need a raw pixel number in TypeScript (the workflow-step
 * animation stagger in motion.ts, for example) and to give the scale a
 * single documented, typed home.
 */
export const spacing = {
  0: 0,
  2: 2,
  4: 4,
  8: 8,
  12: 12,
  16: 16,
  20: 20,
  24: 24,
  32: 32,
  40: 40,
  48: 48,
  64: 64,
  80: 80,
  96: 96,
  128: 128,
} as const;

/**
 * Half-step values Tailwind also ships by default and that the current
 * homepage genuinely uses (e.g. `gap-2.5`, `py-1.5`) - kept separate
 * from the primary scale above so that scale stays a clean 4pt/8pt
 * rhythm, matching the spec this file was built from.
 */
export const spacingHalfSteps = {
  2: 2, // my-0.5
  6: 6, // gap-1.5 / py-1.5
  10: 10, // gap-2.5 / py-2.5 / px-2.5
  14: 14, // px-3.5
} as const;

export type SpacingToken = keyof typeof spacing;

export function toRem(px: number): string {
  return `${px / 16}rem`;
}
