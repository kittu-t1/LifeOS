import { apiFetch } from "@/lib/api";
import type { Memory, MemoryCategory, MemoryCreateInput, MemoryUpdateInput } from "@/types/memory";

/**
 * Memory Engine client - mirrors app/memory/api/routes.py's routes 1:1.
 * Memories are user-scoped, like Habits (no goal/plan/workspace id in
 * any of these paths - see that file's docstring).
 */

export function createMemory(data: MemoryCreateInput): Promise<Memory> {
  return apiFetch<Memory>("/memories", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** `category` doubles as the backend's "search by category" filter - a
 * query param on the same list call, not a separate endpoint. */
export function listMemories(category?: MemoryCategory): Promise<Memory[]> {
  const query = category ? `?category=${encodeURIComponent(category)}` : "";
  return apiFetch<Memory[]>(`/memories${query}`);
}

export function updateMemory(memoryId: string, data: MemoryUpdateInput): Promise<Memory> {
  return apiFetch<Memory>(`/memories/${memoryId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteMemory(memoryId: string): Promise<void> {
  return apiFetch<void>(`/memories/${memoryId}`, { method: "DELETE" });
}
