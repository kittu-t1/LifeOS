"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { radius } from "@/design-system/radius";
import type { NavItem } from "@/components/layout/navConfig";

interface NavigationItemProps {
  item: NavItem;
  /** Called after navigating - Sidebar uses this to close the mobile
   * drawer on tap, so picking a destination doesn't leave the overlay
   * open over the new page. No-op on desktop. */
  onNavigate?: () => void;
  /** Icon-only mode for the collapsed desktop rail (see MainLayout.tsx) -
   * hides the label text and centers the icon; the label still reaches
   * assistive tech and mouse users via `title`, since there's no visible
   * text to read otherwise. Mobile's drawer never passes this - the
   * drawer is only ever shown expanded. */
  collapsed?: boolean;
}

/**
 * One row in the sidebar (see Sidebar.tsx + navConfig.ts). Fully
 * data-driven and self-contained - it reads the current route itself
 * (via usePathname) to decide whether it's active, so nothing in
 * Sidebar.tsx needs to hardcode per-item active-state logic. Items with
 * `available: false` (Agents, Calendar, Documents, Settings - see
 * navConfig.ts) render as a disabled row with a "Soon" badge instead of
 * a broken or dead link.
 */
export default function NavigationItem({
  item,
  onNavigate,
  collapsed = false,
}: NavigationItemProps) {
  const pathname = usePathname();
  const { icon: Icon, label, href, available } = item;
  const isActive = available && href !== undefined && pathname === href;

  const rowClasses = `flex items-center ${collapsed ? "justify-center px-0" : "gap-3 px-3"} ${radius.lg.class} py-2 text-sm font-medium transition-colors`;

  if (!available || !href) {
    return (
      <div
        className={`${rowClasses} text-muted-foreground/50 cursor-default ${collapsed ? "" : "justify-between"}`}
        aria-disabled="true"
        title={collapsed ? `${label} (Soon)` : undefined}
      >
        <span className={`flex items-center ${collapsed ? "" : "gap-3"}`}>
          <Icon size={17} strokeWidth={1.75} />
          {!collapsed && label}
        </span>
        {!collapsed && (
          <span className="bg-surface-hover text-muted-foreground/70 rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase">
            Soon
          </span>
        )}
      </div>
    );
  }

  return (
    <Link
      href={href}
      onClick={onNavigate}
      aria-current={isActive ? "page" : undefined}
      title={collapsed ? label : undefined}
      className={`${rowClasses} ${
        isActive
          ? "bg-accent/10 text-accent"
          : "text-muted-foreground hover:bg-surface-hover hover:text-foreground"
      }`}
    >
      <Icon size={17} strokeWidth={1.75} />
      {!collapsed && label}
    </Link>
  );
}
