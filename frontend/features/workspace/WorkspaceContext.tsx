"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getWorkspace } from "@/services/workspaces";
import type { Workspace } from "@/types/workspace";

interface WorkspaceContextValue {
  workspace: Workspace | null;
  loading: boolean;
  error: boolean;
}

const WorkspaceContext = createContext<WorkspaceContextValue>({
  workspace: null,
  loading: true,
  error: false,
});

/**
 * Fetches the Workspace once per workspace id and shares it across the
 * nav header and every section page (Overview/Tasks/Planner/...) via
 * context, so switching tabs doesn't re-fetch the same data.
 */
export function WorkspaceProvider({
  workspaceId,
  children,
}: {
  workspaceId: string;
  children: ReactNode;
}) {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Note: WorkspaceShell mounts this provider with `key={workspaceId}`, so
  // a workspace switch remounts the component (fresh `loading = true` from
  // the initial state below) rather than needing a synchronous setState
  // reset here - state updates only ever happen inside the async
  // callbacks, which is the pattern React's effect rules recommend.
  useEffect(() => {
    let cancelled = false;
    getWorkspace(workspaceId)
      .then((ws) => {
        if (!cancelled) {
          setWorkspace(ws);
          setError(false);
        }
      })
      .catch(() => {
        if (!cancelled) setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [workspaceId]);

  return (
    <WorkspaceContext.Provider value={{ workspace, loading, error }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace(): WorkspaceContextValue {
  return useContext(WorkspaceContext);
}
