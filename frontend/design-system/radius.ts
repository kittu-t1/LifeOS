/**
 * Border radius tokens for LifeOS - mirrors the rounded corners already
 * in use across the app (Tailwind's default radius scale, which the
 * codebase already draws from consistently). Each entry carries both
 * the Tailwind class to put in a `className` and the raw pixel value
 * for anywhere a numeric radius is needed outside Tailwind (canvas,
 * inline `style`, etc.).
 */
export interface RadiusToken {
  class: string;
  px: number;
}

export const radius = {
  /** 4px - Tailwind's default `rounded`. Not currently used on the
   *  homepage; smallest step, reserved for tiny elements. */
  xs: { class: "rounded", px: 4 },
  /** 6px - AppHeader's logo mark rounds to this (previously a one-off
   *  `rounded-[5px]`; nudged onto the scale, imperceptible at 20px). */
  sm: { class: "rounded-md", px: 6 },
  /** 8px - reserved. */
  md: { class: "rounded-lg", px: 8 },
  /** 12px - the app's default control radius: Button, Card, Input, Modal. */
  lg: { class: "rounded-xl", px: 12 },
  /** 16px - reserved for medium surfaces. */
  xl: { class: "rounded-2xl", px: 16 },
  /** 24px - Card, Modal, and the empty-state onboarding panel all use
   *  this - Apple-style "premium floating card" surfaces read best with
   *  a generous radius rather than the tighter control radius used for
   *  buttons/inputs. */
  "2xl": { class: "rounded-3xl", px: 24 },
  /** Fully round - chips, badges, avatars, status dots. */
  pill: { class: "rounded-full", px: 9999 },
  /** Alias of `pill`, for perfectly circular elements (icon circles). */
  full: { class: "rounded-full", px: 9999 },
} as const satisfies Record<string, RadiusToken>;

export type RadiusTokenName = keyof typeof radius;
