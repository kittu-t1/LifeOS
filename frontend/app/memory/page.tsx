import MemoryView from "@/features/memory/MemoryView";

/**
 * Memories are user-scoped, not Goal-scoped (see backend/app/memory/
 * models/memory.py), so this route lives at the top level rather than
 * nested under /workspace/[workspaceId] - same reasoning as /habits
 * (see app/habits/page.tsx).
 */
export default function MemoryPage() {
  return <MemoryView />;
}
