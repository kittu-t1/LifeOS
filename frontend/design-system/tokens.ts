import { colors } from "@/design-system/colors";
import { gradients } from "@/design-system/gradients";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";
import { spacing, spacingHalfSteps } from "@/design-system/spacing";
import { typography } from "@/design-system/typography";

/**
 * The complete LifeOS design language, combined into a single object.
 *
 * This is the central reference for the whole app: colors, spacing,
 * radius, shadows, typography, gradients, and motion all live here so
 * any future screen (Goals, Workspace, Timeline, Calendar, AI Coach,
 * Analytics) can build entirely from `tokens` instead of introducing a
 * new hardcoded value. Individual modules can still be imported
 * directly (`import { colors } from "@/design-system/colors"`) when a
 * component only needs one slice.
 */
export const tokens = {
  colors,
  spacing,
  spacingHalfSteps,
  radius,
  shadows,
  typography,
  gradients,
  motion,
} as const;

export type DesignTokens = typeof tokens;

export default tokens;
