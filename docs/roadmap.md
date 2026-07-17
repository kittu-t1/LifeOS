# LifeOS — 90-Day MVP Roadmap

This roadmap sequences the MVP into four phases, roughly three weeks
each. Each phase has a single objective it exists to prove — the items
inside it are only there in service of that objective, per
`docs/product_principles.md`'s decision rule.

## Phase 1 — Foundation (Days 1–20)

**Objective:** Build the skeletal product experience and backend
architecture so every later phase has a real place to plug into, without
yet asking the product to be intelligent. This phase proves the shape of
LifeOS - Goal in, Workspace out - is right before any AI is layered on
top of it.

- **Authentication** — real user accounts. (Currently a placeholder: a
  single demo user, no login UI — see `docs/roadmap.md` history in
  `app/core/deps.py`.)
- **Dashboard** — the home screen: greeting, goal list, Create Goal.
  *(Implemented.)*
- **Goal Workspace** — the dedicated environment every goal
  automatically creates. *(Implemented: model, API, auto-creation on
  goal creation.)*
- **Planner UI** — the screen where a plan will be reviewed and edited.
  *(UI shell in place as a placeholder; no plan to review yet — that's
  Phase 2.)*
- **Knowledge** — the workspace section for reference material tied to a
  goal. *(Placeholder today.)*
- **Timeline** — the workspace section for a goal's chronological
  history. *(Placeholder today.)*
- **Daily Check-in** — a lightweight recurring prompt asking what
  happened and what's next, feeding both Progress and Memory.
- **Core Backend** — models, schemas, services, API structure, database
  migrations. *(Implemented: User/Goal/Workspace, Alembic migration,
  REST endpoints.)*

## Phase 2 — Intelligence (Days 21–45)

**Objective:** Make the product actually think. Phase 1 proved the
skeleton; Phase 2 turns the Planner and Knowledge sections from static
placeholders into the AI-driven core that justifies calling LifeOS an
execution system rather than a form for storing goals.

- **Planner Engine** — the Planner Agent generates a real, structured
  plan from a stated goal rather than the user having to write one by
  hand.
- **Task Generation** — the plan is broken down into concrete, trackable
  tasks inside the Workspace.
- **Goal Breakdown** — large or vague goals are decomposed into smaller,
  achievable milestones rather than one undifferentiated block of work.
- **Adaptive Planning** — the plan updates itself when tasks slip, get
  blocked, or circumstances change, instead of silently going stale (see
  Product Principle 6: Adapt, Don't Judge).
- **Knowledge Engine** — the Knowledge section becomes a real,
  AI-assisted store of context relevant to the goal, not just a folder.
- **AI Chat** — a conversational surface for stating goals and querying
  progress, built on top of the same planning/memory intelligence rather
  than as a separate feature (see Product Principle 4: Execution Over
  Conversation - chat is an interface to the system, not the product).

## Phase 3 — Automation (Days 46–70)

**Objective:** Connect LifeOS to the outside world and let it act, not
just plan. Phases 1–2 proved LifeOS can think about a goal; Phase 3
proves it can actually move work forward with less manual effort from
the user, which is the core promise in `docs/vision.md`.

- **Calendar Integration** — plan steps and tasks sync with a real
  calendar instead of only LifeOS's internal one.
- **GitHub Integration** — for engineering-flavored goals, LifeOS can
  see and reference real repository activity as part of tracking
  progress.
- **Execution Engine** — moves from the MVP's simulated execution (see
  `docs/mvp_scope.md`) toward carrying out real, approved actions.
- **Notifications** — timely, non-intrusive nudges about what needs
  attention - deliberately singular and calm per the Design Principles,
  not a notification feed.
- **Voice Input** — stating goals and updates by voice, lowering the
  friction of keeping LifeOS current.
- **Agent Coordination** — the Planner, Memory, Execution, Research, and
  Approval agents (see `docs/agents.md`) operate together on a single
  goal rather than in isolation, with the Agent Orchestrator managing
  handoffs.

## Phase 4 — MVP Completion (Days 71–90)

**Objective:** Harden, polish, and ship. The first three phases build
capability; Phase 4 exists to turn a working prototype into something
reliable enough to put in front of real users - and in front of the
people evaluating Krishna's work.

- **Testing** — automated coverage across backend services/routes and
  critical frontend flows, closing gaps left during earlier phases.
- **UI Polish** — consistent application of the design system
  (`components/ui/`) across every screen built in Phases 1–3.
- **Performance** — audit and fix slow queries, unnecessary re-fetches,
  and bundle size before real users hit them.
- **Deployment** — a real, reachable production environment (not just
  local `pnpm dev` / `uvicorn --reload`).
- **Documentation** — this `docs/` folder brought fully up to date with
  what was actually built, not just what was planned.
- **Portfolio** — a presentable write-up of LifeOS as a project,
  demonstrating the full Goal → Workspace → Planner → Agents →
  Execution → Memory pipeline end-to-end.
- **GitHub** — the public repository polished as a credible engineering
  artifact: clean commit history, working README, no dead scaffolding.
- **LinkedIn** — a public account of the build, positioning LifeOS (and
  the work behind it) for the people who'll see it.

## MVP Success Criteria

The 90-day MVP is successful if a user can:

1. State a goal in plain language and get a genuinely structured plan
   back - not just their own words repeated as a checklist.
2. Watch that plan turn into real progress inside the Workspace, with
   tasks moving from pending to done.
3. See LifeOS reference something it remembered from an earlier goal or
   session, unprompted, in a later planning or chat interaction.
4. Trust that anything consequential asks for approval first, and
   understand why LifeOS did what it did after the fact.
5. Rely on at least one real external integration (Calendar or GitHub)
   actually reflecting their work, not just a simulated stand-in.
6. Open the Dashboard and immediately understand, across every goal they
   have, what's done, what's in progress, and what needs their
   attention - with nothing extraneous competing for that attention.

If all six hold true, LifeOS has demonstrated the thing it exists to
prove: that it closes the gap between knowing what to do and actually
doing it, not just that it can talk about the gap convincingly.
