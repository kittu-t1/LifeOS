import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import ConnectionIndicator from "@/components/ConnectionIndicator";
import NavigationItem from "@/components/layout/NavigationItem";
import { NAV_SECTIONS } from "@/components/layout/navConfig";
import { radius } from "@/design-system/radius";

interface SidebarProps {
  /** Passed through to every NavigationItem - MainLayout uses this to
   * close the mobile drawer after a tap. Desktop's fixed rail leaves it
   * undefined since there's no overlay to dismiss. */
  onNavigate?: () => void;
  /** Icon-only rail mode (desktop only - see MainLayout.tsx). Hides
   * section headings, nav labels, the "LifeOS" wordmark, and the dev
   * connection indicator, keeping just icons. */
  collapsed?: boolean;
  /** Renders the collapse/expand toggle when provided - MainLayout's
   * mobile drawer instance omits this since a drawer only makes sense
   * expanded (collapsing it would leave nothing to tap). */
  onToggleCollapse?: () => void;
}

/**
 * The sidebar's actual content (logo + grouped nav sections) - rendered
 * by MainLayout.tsx in two places: once inside the fixed desktop rail,
 * once inside the mobile drawer overlay. Keeping the content itself
 * layout-agnostic (no fixed/absolute positioning in here) is what lets
 * both call sites reuse it as-is.
 *
 * Nav sections come entirely from navConfig.ts - adding a future module
 * (a real Calendar page, say) means flipping `available: true` and
 * adding an `href` there, not touching this component.
 */
export default function Sidebar({ onNavigate, collapsed = false, onToggleCollapse }: SidebarProps) {
  const isDev = process.env.NODE_ENV === "development";

  return (
    <div className="flex h-full flex-col gap-6 py-6">
      <div
        className={`flex items-center ${collapsed ? "justify-center px-2" : "justify-between px-4"}`}
      >
        <Link
          href="/"
          onClick={onNavigate}
          className="text-foreground flex items-center gap-2.5 text-[15px] font-semibold"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/favicon.ico" alt="" className={`h-5 w-5 shrink-0 ${radius.sm.class}`} />
          {!collapsed && <span className="tracking-tight">LifeOS</span>}
        </Link>

        {onToggleCollapse && !collapsed && (
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label="Collapse sidebar"
            className={`text-muted-foreground hover:bg-surface-hover hover:text-foreground flex h-7 w-7 items-center justify-center ${radius.lg.class} transition-colors`}
          >
            <ChevronLeft size={16} />
          </button>
        )}
      </div>

      {onToggleCollapse && collapsed && (
        <button
          type="button"
          onClick={onToggleCollapse}
          aria-label="Expand sidebar"
          className={`text-muted-foreground hover:bg-surface-hover hover:text-foreground mx-auto flex h-7 w-7 items-center justify-center ${radius.lg.class} transition-colors`}
        >
          <ChevronLeft size={16} className="rotate-180" />
        </button>
      )}

      <nav className={`flex flex-1 flex-col gap-6 overflow-y-auto ${collapsed ? "px-2" : "px-4"}`}>
        {NAV_SECTIONS.map((section) => (
          <div key={section.heading} className="flex flex-col gap-1">
            {!collapsed && (
              <p className="text-muted-foreground/70 px-3 text-[11px] font-semibold tracking-wide uppercase">
                {section.heading}
              </p>
            )}
            {section.items.map((item) => (
              <NavigationItem
                key={item.label}
                item={item}
                onNavigate={onNavigate}
                collapsed={collapsed}
              />
            ))}
          </div>
        ))}
      </nav>

      {isDev && !collapsed && (
        <div className="px-4">
          <ConnectionIndicator />
        </div>
      )}
    </div>
  );
}
