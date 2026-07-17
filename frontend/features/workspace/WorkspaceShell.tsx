"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
import Badge from "@/components/ui/Badge";
import { WorkspaceProvider, useWorkspace } from "@/features/workspace/WorkspaceContext";
import { statusMeta } from "@/lib/goal-status";

const TABS = [
  { label: "Overview", segment: "" },
  { label: "Tasks", segment: "tasks" },
  { label: "Planner", segment: "planner" },
  { label: "Knowledge", segment: "knowledge" },
  { label: "Timeline", segment: "timeline" },
  { label: "Chat", segment: "chat" },
];

function WorkspaceTabs({ workspaceId }: { workspaceId: string }) {
  const pathname = usePathname();
  const base = `/workspace/${workspaceId}`;

  return (
    <nav className="border-border flex gap-1 overflow-x-auto border-b px-6">
      {TABS.map((tab) => {
        const href = tab.segment ? `${base}/${tab.segment}` : base;
        const isActive = pathname === href;
        return (
          <Link
            key={tab.label}
            href={href}
            className={`border-b-2 px-3 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
              isActive
                ? "border-accent text-foreground"
                : "text-muted-foreground hover:text-foreground border-transparent"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}

function WorkspaceTitleBar() {
  const { workspace, loading, error } = useWorkspace();

  if (loading) {
    return <div className="text-muted-foreground px-6 py-6 text-sm">Loading workspace…</div>;
  }
  if (error || !workspace) {
    return (
      <div className="text-danger px-6 py-6 text-sm">
        Couldn&apos;t load this workspace. Is the backend running?
      </div>
    );
  }

  const status = statusMeta[workspace.goal.status];

  return (
    <div className="flex items-center justify-between px-6 py-5">
      <div className="flex items-center gap-3">
        <Link href="/" className="text-muted-foreground hover:text-foreground">
          <ArrowLeft size={18} />
        </Link>
        <h1 className="text-foreground text-lg font-semibold">{workspace.goal.title}</h1>
        <Badge tone={status.tone}>{status.label}</Badge>
      </div>
    </div>
  );
}

export default function WorkspaceShell({
  workspaceId,
  children,
}: {
  workspaceId: string;
  children: ReactNode;
}) {
  return (
    // key={workspaceId} forces a remount (not just a re-render) when
    // navigating between workspaces, so WorkspaceContext's loading state
    // starts fresh without needing a synchronous setState reset - see the
    // comment in WorkspaceContext.tsx.
    <WorkspaceProvider key={workspaceId} workspaceId={workspaceId}>
      <div className="flex flex-1 flex-col">
        <WorkspaceTitleBar />
        <WorkspaceTabs workspaceId={workspaceId} />
        <div className="flex-1">{children}</div>
      </div>
    </WorkspaceProvider>
  );
}
