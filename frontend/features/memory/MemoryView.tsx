"use client";

import { Brain } from "lucide-react";
import { useEffect, useState } from "react";
import Button from "@/components/ui/Button";
import { colors } from "@/design-system/colors";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";
import MemoryCard from "@/features/memory/MemoryCard";
import MemoryFormModal, { CATEGORY_OPTIONS } from "@/features/memory/MemoryFormModal";
import { createMemory, deleteMemory, listMemories, updateMemory } from "@/services/memory";
import type { Memory, MemoryCategory, MemoryCreateInput } from "@/types/memory";

const FILTER_OPTIONS: { value: MemoryCategory | "all"; label: string }[] = [
  { value: "all", label: "All" },
  ...CATEGORY_OPTIONS,
];

/**
 * Top-level page for the Memory Engine (see backend/app/memory/). Like
 * Habits, memories are user-scoped rather than Goal-scoped, so this
 * lives at the top level (/memory) rather than nested under a Workspace -
 * see AppHeader.tsx for the nav entry. Deliberately simple per the
 * sprint spec ("Keep the UI simple") - list, filter by category,
 * create/edit/delete. No ranking or search-by-relevance UI since V1's
 * get_relevant_memories is just list_memories (see memory_service.py).
 */
export default function MemoryView() {
  const [memories, setMemories] = useState<Memory[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<MemoryCategory | "all">("all");
  const [modalOpen, setModalOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState<Memory | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listMemories(activeFilter === "all" ? undefined : activeFilter)
      .then((rows) => {
        if (cancelled) return;
        setMemories(rows);
        setLoadError(null);
      })
      .catch(() => {
        if (!cancelled) setLoadError("Couldn't reach LifeOS. Is the backend running?");
      });
    return () => {
      cancelled = true;
    };
  }, [activeFilter]);

  async function loadMemories(filter: MemoryCategory | "all") {
    try {
      const rows = await listMemories(filter === "all" ? undefined : filter);
      setMemories(rows);
      setLoadError(null);
    } catch {
      setLoadError("Couldn't reach LifeOS. Is the backend running?");
    }
  }

  function openCreateModal() {
    setEditingMemory(null);
    setFormError(null);
    setModalOpen(true);
  }

  function openEditModal(memory: Memory) {
    setEditingMemory(memory);
    setFormError(null);
    setModalOpen(true);
  }

  async function handleSubmit(data: MemoryCreateInput) {
    setSubmitting(true);
    setFormError(null);
    try {
      if (editingMemory) {
        await updateMemory(editingMemory.id, data);
      } else {
        await createMemory(data);
      }
      setModalOpen(false);
      await loadMemories(activeFilter);
    } catch {
      setFormError("Couldn't save this memory. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(memory: Memory) {
    setDeletingId(memory.id);
    const previous = memories;
    setMemories((prev) => prev?.filter((m) => m.id !== memory.id) ?? prev);
    try {
      await deleteMemory(memory.id);
    } catch {
      setMemories(previous);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-foreground text-xl font-semibold">Memory</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Long-term context about you - preferences, planning patterns, and notes the Planner can
            draw on later.
          </p>
        </div>
        <Button onClick={openCreateModal}>New Memory</Button>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {FILTER_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => setActiveFilter(opt.value)}
            className={`${radius.lg.class} border px-3 py-1.5 text-xs font-medium transition-colors ${
              activeFilter === opt.value
                ? "border-accent bg-accent/15 text-accent"
                : "border-border bg-surface text-muted-foreground hover:bg-surface-hover"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {loadError && <p className="text-danger text-sm">{loadError}</p>}

      {memories === null && !loadError && (
        <p className="text-muted-foreground px-1 text-sm">Loading memories…</p>
      )}

      {memories !== null && memories.length === 0 && (
        <EmptyMemoryState onCreate={openCreateModal} filtered={activeFilter !== "all"} />
      )}

      {memories !== null && memories.length > 0 && (
        <div className="flex flex-col gap-3">
          {memories.map((memory) => (
            <MemoryCard
              key={memory.id}
              memory={memory}
              onEdit={() => openEditModal(memory)}
              onDelete={() => handleDelete(memory)}
              deleting={deletingId === memory.id}
            />
          ))}
        </div>
      )}

      <MemoryFormModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
        submitting={submitting}
        error={formError}
        editingMemory={editingMemory}
      />
    </div>
  );
}

function EmptyMemoryState({ onCreate, filtered }: { onCreate: () => void; filtered: boolean }) {
  return (
    <div className="flex flex-col items-center gap-5 py-16 text-center">
      <div className="relative flex h-14 w-14 items-center justify-center">
        <div
          aria-hidden
          className={`${motion.animation.softPulse} absolute inset-0 rounded-full blur-xl`}
          style={{ background: colors.primaryGlow }}
        />
        <div
          className={`border-border bg-surface-hover relative flex h-12 w-12 items-center justify-center ${radius.full.class} border ${shadows.innerHighlightStrong}`}
        >
          <Brain size={20} strokeWidth={1.5} className={`text-accent ${shadows.iconGlowAccent}`} />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <h3 className="text-foreground text-lg font-semibold">
          {filtered ? "No memories in this category" : "No memories yet"}
        </h3>
        <p className="text-muted-foreground text-sm">
          {filtered
            ? "Try a different category, or add one here."
            : "Add a preference, a note, or a pattern you've noticed about how you work."}
        </p>
      </div>
      <Button onClick={onCreate}>Create Your First Memory</Button>
    </div>
  );
}
