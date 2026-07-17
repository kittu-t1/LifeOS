import { apiFetch } from "@/lib/api";
import type { Workspace } from "@/types/workspace";

export function getWorkspace(workspaceId: string): Promise<Workspace> {
  return apiFetch<Workspace>(`/workspaces/${workspaceId}`);
}
