# LifeOS — MVP Scope

## Goal of the MVP

Prove that the core execution loop works, end to end, for a single user:

```
Goal → Plan → Approval → (Simulated) Execution → Memory Update → Progress Tracking
```

The MVP is not about breadth of integrations or polish — it's about
proving the *pipeline* is real and trustworthy before investing in
connecting it to the outside world.

## In scope

- **Authentication** — basic account creation and login (JWT), so goals
  and memory can be tied to a real user.
- **Goal Creation** — the user can state a goal in plain language.
- **Workspace Creation** — every goal creates its Workspace, holding its
  tasks, plan, conversation, and progress.
- **AI Planner** — the Planner Agent turns a goal into a structured plan.
- **Task Generation** — the plan is broken into concrete, trackable tasks.
- **Progress Tracking** — the user can see what's planned, in progress,
  and done, per Workspace and overall.
- **Memory Engine** — context (goals, decisions, outcomes) is stored and
  retrieved to inform future planning. Inspectable by the user.
- **Planner Agent** — the first fully-specified agent (see
  `docs/agents.md`); the MVP's centerpiece.
- **Internal Calendar** — a LifeOS-native calendar for scheduling
  tasks/plan steps. Not synced to any external calendar provider.
- **AI Chat** — a conversational surface for stating goals, asking about
  progress, and interacting with agents directly.
- **Approval Flow** — before any plan step executes, the user explicitly
  approves it (or a batch of low-risk steps, per the Approval Agent's
  judgment — see `docs/agents.md`).
- **Simulated Execution** — the Execution Agent "runs" approved steps
  without calling any real external system, producing realistic outcomes
  so the full loop (including Memory Update and Progress Tracking) can be
  validated.

## Explicitly out of scope for MVP

- **Gmail integration**
- **Slack**
- **Jira**
- **Spotify**
- **Banking**
- **Real booking systems**

These are all real **External Integrations** in the architecture (see
`docs/architecture.md`) and belong to future versions. Reason: each one
brings its own auth flow, API quirks, rate limits, and failure modes.
Building them before the core orchestration/approval/execution loop is
proven would mean debugging integration problems and architecture
problems at the same time. Simulated Execution lets the MVP validate the
*shape* of execution (sequencing, approval gating, memory writes,
progress visibility) independent of any specific integration's
reliability.

## Success criteria

The MVP is successful if a user can:

1. State a goal in plain language.
2. Receive a plan that's genuinely structured (not just a restated goal).
3. Approve (or reject/edit) that plan before anything happens.
4. Watch simulated execution move tasks from pending → done.
5. See LifeOS reference something it remembered from an earlier goal or
   session, unprompted, in a later planning or chat interaction.
6. Look at a dashboard and immediately understand what's done, what's
   pending, and what needs their approval — across more than one
   Workspace.

If all six hold true, the core thesis of LifeOS (an execution system, not
a chatbot or a static tracker) is validated and future versions can
safely build real integrations on top of it.
