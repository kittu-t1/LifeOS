"use client";

import { useState, type FormEvent } from "react";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Modal from "@/components/ui/Modal";
import { radius } from "@/design-system/radius";
import type { Memory, MemoryCategory, MemoryCreateInput } from "@/types/memory";

interface MemoryFormModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: MemoryCreateInput) => void;
  submitting: boolean;
  error: string | null;
  /** Present when editing an existing memory - prefills the form and
   * changes the submit copy. Absent means "create new". Mirrors
   * features/habits/HabitFormModal.tsx's editingHabit convention. */
  editingMemory?: Memory | null;
}

export const CATEGORY_OPTIONS: { value: MemoryCategory; label: string }[] = [
  { value: "preference", label: "Preference" },
  { value: "planning_context", label: "Planning Context" },
  { value: "habit_insight", label: "Habit Insight" },
  { value: "learned_pattern", label: "Learned Pattern" },
  { value: "note", label: "Note" },
];

/**
 * Create/edit form for a Memory (see backend/app/memory/schemas/memory.py).
 * Deliberately plain - category, a short key, and a free-form value - the
 * sprint spec says "Keep the UI simple", and confidence/source are
 * system-managed fields the update schema doesn't even accept (see
 * MemoryUpdate), so there's nothing to expose here for them.
 */
export default function MemoryFormModal({
  open,
  onClose,
  onSubmit,
  submitting,
  error,
  editingMemory,
}: MemoryFormModalProps) {
  const isEditing = Boolean(editingMemory);

  const [category, setCategory] = useState<MemoryCategory>(editingMemory?.category ?? "preference");
  const [key, setKey] = useState(editingMemory?.key ?? "");
  const [value, setValue] = useState(editingMemory?.value ?? "");

  const canSubmit = key.trim().length > 0 && value.trim().length > 0;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit({ category, key: key.trim(), value: value.trim() });
  }

  return (
    <Modal open={open} onClose={onClose}>
      <div className="mb-4">
        <h2 className="text-foreground text-lg font-semibold">
          {isEditing ? "Edit Memory" : "New Memory"}
        </h2>
        <p className="text-muted-foreground mt-1 text-sm">
          Long-term context the Planner can draw on later - a preference, a note, a pattern
          you&apos;ve noticed about how you work.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
            Category
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as MemoryCategory)}
            className={`border-border bg-background text-foreground focus:border-accent focus:ring-accent w-full ${radius.lg.class} border px-3.5 py-2.5 text-sm focus:ring-1 focus:outline-none`}
          >
            {CATEGORY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
            Key
          </label>
          <Input
            autoFocus
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder="e.g. preferred_working_hours"
          />
        </div>

        <div>
          <label className="text-muted-foreground mb-1.5 block text-xs font-medium tracking-wide uppercase">
            Value
          </label>
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="e.g. Preparing for AWS certification."
            rows={4}
            className={`border-border bg-background text-foreground placeholder:text-muted-foreground focus:border-accent focus:ring-accent w-full ${radius.lg.class} border px-3.5 py-2.5 text-sm focus:ring-1 focus:outline-none`}
          />
        </div>

        {error && <p className="text-danger text-sm">{error}</p>}

        <div className="flex items-center justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={!canSubmit || submitting}>
            {submitting ? "Saving…" : isEditing ? "Save changes" : "Create memory"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
