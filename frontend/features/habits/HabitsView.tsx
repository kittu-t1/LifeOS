"use client";

import { Repeat } from "lucide-react";
import { useEffect, useState } from "react";
import Button from "@/components/ui/Button";
import { colors } from "@/design-system/colors";
import { motion } from "@/design-system/motion";
import { radius } from "@/design-system/radius";
import { shadows } from "@/design-system/shadows";
import HabitCard from "@/features/habits/HabitCard";
import HabitFormModal from "@/features/habits/HabitFormModal";
import { createHabit, listHabits, pauseHabit, resumeHabit, updateHabit } from "@/services/habits";
import type { Habit, HabitCreateInput } from "@/types/habit";

/**
 * Top-level page for the Recurring Task system (see backend/app/models/habit.py
 * and the Sprint 5 spec). Habits are user-scoped, not Goal-scoped (unlike
 * every other feature in this app), so this page lives at the top level
 * (/habits) rather than nested under a Workspace - see AppHeader.tsx for
 * the nav entry that reaches it.
 */
export default function HabitsView() {
  const [habits, setHabits] = useState<Habit[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [pauseTogglingId, setPauseTogglingId] = useState<string | null>(null);

  useEffect(() => {
    void loadHabits();
  }, []);

  async function loadHabits() {
    try {
      const rows = await listHabits();
      setHabits(rows);
      setLoadError(null);
    } catch {
      setLoadError("Couldn't reach LifeOS. Is the backend running?");
    }
  }

  function openCreateModal() {
    setEditingHabit(null);
    setFormError(null);
    setModalOpen(true);
  }

  function openEditModal(habit: Habit) {
    setEditingHabit(habit);
    setFormError(null);
    setModalOpen(true);
  }

  async function handleSubmit(data: HabitCreateInput) {
    setSubmitting(true);
    setFormError(null);
    try {
      if (editingHabit) {
        await updateHabit(editingHabit.id, data);
      } else {
        await createHabit(data);
      }
      setModalOpen(false);
      await loadHabits();
    } catch {
      setFormError("Couldn't save this habit. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleTogglePause(habit: Habit) {
    setPauseTogglingId(habit.id);
    try {
      const updated =
        habit.status === "active" ? await pauseHabit(habit.id) : await resumeHabit(habit.id);
      setHabits((prev) => prev?.map((h) => (h.id === updated.id ? updated : h)) ?? prev);
    } catch {
      // Leave the list as-is; the button simply stays in its current
      // state and the user can retry.
    } finally {
      setPauseTogglingId(null);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-8">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-foreground text-xl font-semibold">Habits</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Recurring commitments the Planner works around - create one and it shows up in your
            schedule automatically.
          </p>
        </div>
        <Button onClick={openCreateModal}>New Habit</Button>
      </div>

      {loadError && <p className="text-danger text-sm">{loadError}</p>}

      {habits === null && !loadError && (
        <p className="text-muted-foreground px-1 text-sm">Loading habits…</p>
      )}

      {habits !== null && habits.length === 0 && <EmptyHabitsState onCreate={openCreateModal} />}

      {habits !== null && habits.length > 0 && (
        <div className="flex flex-col gap-3">
          {habits.map((habit) => (
            <HabitCard
              key={habit.id}
              habit={habit}
              onEdit={() => openEditModal(habit)}
              onTogglePause={() => handleTogglePause(habit)}
              pauseToggling={pauseTogglingId === habit.id}
            />
          ))}
        </div>
      )}

      <HabitFormModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
        submitting={submitting}
        error={formError}
        editingHabit={editingHabit}
      />
    </div>
  );
}

function EmptyHabitsState({ onCreate }: { onCreate: () => void }) {
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
          <Repeat size={20} strokeWidth={1.5} className={`text-accent ${shadows.iconGlowAccent}`} />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <h3 className="text-foreground text-lg font-semibold">No habits yet</h3>
        <p className="text-muted-foreground text-sm">
          Add a recurring commitment - a workout, a daily review, anything that repeats.
        </p>
      </div>
      <Button onClick={onCreate}>Create Your First Habit</Button>
    </div>
  );
}
