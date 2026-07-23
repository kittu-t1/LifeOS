"use client";

import { Menu, X } from "lucide-react";
import Link from "next/link";
import { useState, type ReactNode } from "react";
import Sidebar from "@/components/layout/Sidebar";
import { radius } from "@/design-system/radius";

/**
 * App-wide shell: a fixed sidebar on desktop, a collapsible drawer on
 * mobile, main content alongside/below it. Replaces AppHeader's floating
 * pill nav (see components/AppHeader.tsx - no longer imported from
 * app/layout.tsx, left in place unused rather than deleted) as the
 * primary way to move around LifeOS, per the "sidebar architecture"
 * redesign: Goals stay centered in the main content area, everything
 * else (Habits, Memory, and future modules) lives in the sidebar - see
 * components/layout/navConfig.ts for the actual nav structure.
 *
 * Desktop (md and up): Sidebar is `fixed`, full height, `md:w-64` wide
 * (`md:w-16` collapsed - an icon-only rail, toggled via the chevron
 * button in Sidebar.tsx); main content's `md:pl-*` tracks whichever
 * width is active so it always sits flush beside the rail. No separate
 * top bar - the sidebar carries the logo. Collapse state is plain
 * component state (not persisted) - it resets to expanded on reload,
 * which keeps this simple and avoids a hydration-mismatch class of bug;
 * worth revisiting with localStorage if that resistance turns out to
 * bother anyone in practice.
 *
 * Mobile (below md): the fixed sidebar is hidden entirely; a slim top
 * bar (logo + hamburger) takes its place, and tapping the hamburger
 * opens Sidebar inside a full-screen drawer overlay - always expanded
 * (collapsing a drawer would leave nothing to tap), so it gets no
 * `collapsed`/`onToggleCollapse` props. Selecting a nav item closes the
 * drawer (see Sidebar's `onNavigate` prop) so users land on the new page
 * without the overlay still open over it.
 */
export default function MainLayout({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex min-h-full flex-1">
      {/* Desktop fixed sidebar - `fixed` takes it out of flow entirely,
          so its placement here doesn't affect the flex layout below. */}
      <aside
        className={`border-border bg-surface fixed inset-y-0 left-0 z-30 hidden border-r transition-[width] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] md:block ${
          collapsed ? "md:w-16" : "md:w-64"
        }`}
      >
        <Sidebar collapsed={collapsed} onToggleCollapse={() => setCollapsed((v) => !v)} />
      </aside>

      {/* Mobile drawer overlay - also out of flow. */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setDrawerOpen(false)}
          />
          <div className="border-border bg-surface relative flex h-full w-72 max-w-[80vw] flex-col border-r">
            <button
              type="button"
              onClick={() => setDrawerOpen(false)}
              aria-label="Close navigation"
              className={`text-muted-foreground hover:bg-surface-hover hover:text-foreground absolute top-4 right-4 flex h-8 w-8 items-center justify-center ${radius.lg.class} transition-colors`}
            >
              <X size={17} />
            </button>
            <Sidebar onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      {/* Everything else stacks in a column, offset on desktop to clear
          the fixed sidebar. The mobile top bar lives in here (not as a
          sibling of aside) so it sits above `main` instead of beside it. */}
      <div
        className={`flex min-h-full flex-1 flex-col transition-[padding] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] ${
          collapsed ? "md:pl-16" : "md:pl-64"
        }`}
      >
        <header className="border-border bg-surface/90 sticky top-0 z-40 flex items-center justify-between border-b px-4 py-3 backdrop-blur-md md:hidden">
          <Link
            href="/"
            className="text-foreground flex items-center gap-2.5 text-[15px] font-semibold"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/favicon.ico" alt="" className={`h-5 w-5 ${radius.sm.class}`} />
            <span className="tracking-tight">LifeOS</span>
          </Link>
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open navigation"
            className={`text-muted-foreground hover:bg-surface-hover hover:text-foreground flex h-9 w-9 items-center justify-center ${radius.lg.class} transition-colors`}
          >
            <Menu size={20} />
          </button>
        </header>

        <main className="flex flex-1 flex-col">{children}</main>
      </div>
    </div>
  );
}
