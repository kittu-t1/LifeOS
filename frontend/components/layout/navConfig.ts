import {
  Bot,
  Brain,
  Calendar,
  FileText,
  Home,
  Repeat,
  Settings,
  Target,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  icon: LucideIcon;
  label: string;
  /** Absent (or `available: false`) means "not built yet" - rendered as
   * a disabled row rather than a dead link. Per the sidebar architecture
   * spec: "Do not implement unavailable features. Only add routes/
   * features that already exist or have placeholders." */
  href?: string;
  available: boolean;
}

export interface NavSection {
  heading: string;
  items: NavItem[];
}

/**
 * Single source of truth for the sidebar's navigation structure (see
 * Sidebar.tsx and NavigationItem.tsx, which just render this data - no
 * menu item is hardcoded in a component). Mirrors the IA spec's
 * suggested structure section-for-section; a few real-route decisions
 * worth calling out:
 *
 * - Home (/) and Goals (/goals) are two separate pages, on purpose: Home
 *   is a plain welcome screen (see features/home/HomeView.tsx - a
 *   greeting, two lines about LifeOS, and the orbit illustration), Goals
 *   is where the actual Create Goal / Goal Showcase / goal list work
 *   happens (see features/goals/GoalsView.tsx). Home answers "what is
 *   this app," Goals answers "what am I trying to accomplish" - the
 *   sidebar's own job is the third question, "what tools help me."
 * - Habits (/habits) and Memory (/memory) are real, fully built routes -
 *   this sidebar is the *only* place they're reachable from now (see
 *   DashboardActions.tsx, which no longer links to either).
 * - Agents, Calendar, Documents, and Settings have no route yet
 *   (features/agents/ is an empty placeholder module; the rest don't
 *   exist at all) - `available: false` renders them as a visible-but-
 *   disabled preview of where LifeOS is headed, without linking
 *   anywhere or claiming they work.
 */
export const NAV_SECTIONS: NavSection[] = [
  {
    heading: "Main",
    items: [{ icon: Home, label: "Home", href: "/", available: true }],
  },
  {
    heading: "Work",
    items: [
      { icon: Target, label: "Goals", href: "/goals", available: true },
      { icon: Repeat, label: "Habits", href: "/habits", available: true },
    ],
  },
  {
    heading: "Intelligence",
    items: [
      { icon: Brain, label: "Memory", href: "/memory", available: true },
      { icon: Bot, label: "Agents", available: false },
    ],
  },
  {
    heading: "Tools",
    items: [
      { icon: Calendar, label: "Calendar", available: false },
      { icon: FileText, label: "Documents", available: false },
    ],
  },
  {
    heading: "System",
    items: [{ icon: Settings, label: "Settings", available: false }],
  },
];
