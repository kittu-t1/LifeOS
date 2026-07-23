"use client";

import { Pencil, Trash2 } from "lucide-react";
import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import { radius } from "@/design-system/radius";
import type { Memory } from "@/types/memory";
import { CATEGORY_OPTIONS } from "@/features/memory/MemoryFormModal";

const CATEGORY_LABELS: Record<Memory["category"], string> = Object.fromEntries(
  CATEGORY_OPTIONS.map((opt) => [opt.value, opt.label]),
) as Record<Memory["category"], string>;

interface MemoryCardProps {
  memory: Memory;
  onEdit: () => void;
  onDelete: () => void;
  deleting: boolean;
}

/** One Memory's card - category + key up top, the free-form value below.
 * No occurrence/streak complexity like HabitCard - a Memory is just a
 * stored fact, so the card is just "what it is" plus edit/delete. */
export default function MemoryCard({ memory, onEdit, onDelete, deleting }: MemoryCardProps) {
  return (
    <Card>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="accent">{CATEGORY_LABELS[memory.category]}</Badge>
            {memory.source === "system" && <Badge tone="neutral">System</Badge>}
            <h3 className="text-foreground text-sm font-semibold">{memory.key}</h3>
          </div>
          <p className="text-muted-foreground mt-1.5 text-sm whitespace-pre-wrap">{memory.value}</p>
        </div>

        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            onClick={onEdit}
            aria-label="Edit memory"
            className={`text-muted-foreground hover:bg-surface-hover hover:text-foreground flex h-8 w-8 items-center justify-center ${radius.lg.class} transition-colors`}
          >
            <Pencil size={15} />
          </button>
          <button
            type="button"
            onClick={onDelete}
            disabled={deleting}
            aria-label="Delete memory"
            className={`text-muted-foreground hover:bg-surface-hover hover:text-danger flex h-8 w-8 items-center justify-center ${radius.lg.class} transition-colors disabled:opacity-50`}
          >
            <Trash2 size={15} />
          </button>
        </div>
      </div>
    </Card>
  );
}
