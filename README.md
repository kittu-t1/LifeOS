# LifeOS — Agentic Execution Operating System

## What LifeOS is

LifeOS takes a goal and drives it to a completed outcome. You state what
you want done; LifeOS plans it, orchestrates specialized AI agents to
carry it out, checks in with you before anything consequential happens,
and tracks progress until it's actually finished — not just discussed.

## Why it exists

Chatbots reason well but forget everything and do nothing on their own.
Productivity tools store structured work but have no intelligence behind
them. LifeOS is the layer in between: persistent memory, real planning,
and agents that execute — with the user approving what matters and out of
the loop for what doesn't.

## LifeOS vs. ChatGPT

| | ChatGPT | LifeOS |
|---|---|---|
| Core unit | A conversation | A **Goal**, which creates a **Workspace** |
| Memory | Stateless | Persistent, inspectable, tied to the user |
| Output | An answer | A plan, executed to completion, with tracked progress |
| Agents | One general-purpose model | Specialized, collaborating agents (Planner, Memory, Execution, Research, Approval) |
| Action | Talks about doing things | Actually does things (simulated in MVP, real in later versions) |

Full detail in [`docs/vision.md`](docs/vision.md).

## Core execution workflow

```
User Goal
    ↓
Planning
    ↓
Agent Orchestration
    ↓
Approval
    ↓
Execution
    ↓
Memory Update
    ↓
Continuous Progress Tracking
```

Diagrams and stage-by-stage detail in [`docs/architecture.md`](docs/architecture.md).

## Primary object: Goal → Workspace

Everything revolves around a **Goal**. Creating a goal creates a
**Workspace**, holding its Tasks, Documents, Conversations, Memories, AI
Plans, Progress, and Agents. Every future feature belongs to a Workspace
— this keeps the product anchored to execution rather than sprawling into
unrelated features.

## Documentation

| Doc | Covers |
|---|---|
| [`docs/product_principles.md`](docs/product_principles.md) | The product constitution — 10 principles every feature/design/architecture decision is checked against |
| [`docs/vision.md`](docs/vision.md) | What LifeOS is, why it exists, LifeOS vs. ChatGPT |
| [`docs/architecture.md`](docs/architecture.md) | System diagrams, backend/frontend module maps |
| [`docs/mvp_scope.md`](docs/mvp_scope.md) | What's in/out of scope for the MVP, and why |
| [`docs/agents.md`](docs/agents.md) | The five core agents: purpose, inputs/outputs, MVP behavior |
| [`docs/roadmap.md`](docs/roadmap.md) | Build phases, from foundation to post-MVP integrations |
| [`docs/day-2-product-design.md`](docs/day-2-product-design.md) | **Legacy** — pre-pivot UX exploration, kept for reference only |

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js + TypeScript + Tailwind CSS | Type-safe UI, flexible rendering for future dashboard + chat interfaces |
| Backend | FastAPI (Python) | Native async, fits an I/O-heavy system (LLM calls, DB, vector search running concurrently) |
| Database | PostgreSQL | Relational integrity for goals/workspaces/tasks/memories |
| ORM | SQLAlchemy | Clean model layer, migration-ready via Alembic (added later) |
| Auth | JWT | Stateless, scales across a multi-agent architecture |
| Vector DB | Chroma (planned) | Embedded, zero-ops for local dev; swappable later via the memory/ interface |
| Agent framework | LangGraph (planned) | Orchestration layer for the five core agents |
| Package managers | pnpm (frontend), uv or venv+pip (backend) | Fast, strict dependency resolution |
| Containerization | Docker / docker-compose | Consistent environment across machines |

Chroma and LangGraph are named as intended future choices but are **not
installed or wired up yet**.

## Folder structure

```
LifeOS/
├── frontend/
│   ├── app/                   # Next.js App Router pages
│   ├── components/            # Shared, reusable UI components
│   ├── features/              # Feature-scoped UI, mirrors backend domains
│   │   ├── workspace/          # Workspace shell/nav + Overview (implemented)
│   │   ├── dashboard/           # Goal list + Create Goal (implemented)
│   │   ├── planner/            # Goal input, plan review (placeholder)
│   │   ├── memory/             # Inspectable memory surface (placeholder)
│   │   └── agents/             # Agent activity, approval prompts (placeholder)
│   ├── services/               # Typed API client wrappers (goals, workspaces)
│   ├── hooks/                  # Shared React hooks
│   ├── types/                  # Shared TypeScript domain types
│   ├── lib/                    # Low-level utilities (API fetcher)
│   ├── .env.example
│   └── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── main.py              # App entrypoint
│   │   ├── api/v1/              # Route handlers (thin, no business logic)
│   │   ├── core/                 # Settings/config (env-driven)
│   │   ├── database/              # SQLAlchemy engine/session
│   │   ├── models/                 # ORM models: User, Goal, Workspace (implemented)
│   │   ├── schemas/                 # Pydantic schemas: Goal, Workspace (implemented)
│   │   ├── services/                 # goal_service, workspace_service (implemented)
│   │   ├── planner/                   # Planning logic, wrapped by Planner Agent (placeholder)
│   │   ├── execution/                  # Execution logic, wrapped by Execution Agent (placeholder)
│   │   ├── memory/                      # Memory logic, wrapped by Memory Agent (placeholder)
│   │   ├── research/                     # Research logic, wrapped by Research Agent (placeholder)
│   │   ├── workspaces/                    # Workspace domain logic (placeholder)
│   │   ├── agents/                         # Orchestration-facing agent stubs (placeholder)
│   │   ├── integrations/                    # External adapters (empty until post-MVP)
│   │   └── vectorstore/                      # Vector DB interface (Chroma today)
│   ├── alembic/                # Migrations (initial: users, goals, workspaces)
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docs/                       # See Documentation table above
├── docker-compose.yml
└── README.md
```

Route handlers stay thin by design — business logic lives in
`planner/`, `execution/`, `memory/`, `workspaces/`, and `services/`, and
`agents/` orchestrates across them. Full rationale in
[`docs/architecture.md`](docs/architecture.md).

## MVP scope

The MVP proves the execution loop end-to-end (goal → plan → approval →
simulated execution → memory → tracking) before any real external
integrations are built. Gmail, Slack, Jira, Spotify, banking, and real
booking systems are explicitly deferred to post-MVP. Full scope in
[`docs/mvp_scope.md`](docs/mvp_scope.md).

## Running the project

### Backend

The Goal/Workspace API needs a real Postgres database (the health check
alone didn't, but creating a Goal now writes rows). Start Postgres first
- easiest via Docker:

```bash
docker run --name lifeos-postgres -e POSTGRES_USER=lifeos -e POSTGRES_PASSWORD=lifeos \
  -e POSTGRES_DB=lifeos -p 5432:5432 -d postgres:16-alpine
```

(Or use `docker compose up -d postgres` once you have `backend/.env` set
up - see below.)

Then:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

(If you have [`uv`](https://astral.sh/uv) installed, you can use
`uv venv .venv` + `uv pip install -e ".[dev]" --python .venv/bin/python`
instead — faster, same result.)

Backend runs at `http://localhost:8000` — visit `/docs` for interactive
API docs, `/api/v1/health` for the health check, `/api/v1/goals` to
create/list goals.

### Frontend

```bash
cd frontend
npm install -g pnpm   # if pnpm isn't already installed
cp .env.example .env.local
pnpm install
pnpm dev
```

Frontend runs at `http://localhost:3000` - the Dashboard, where you can
create a Goal and it automatically opens a Workspace for it. A small
connection indicator in the header shows if the backend is reachable.

### Linting & formatting

```bash
# backend
cd backend
ruff check app tests
black app tests

# frontend
cd frontend
pnpm lint
pnpm format:check
```

### Docker (optional, full stack)

```bash
docker compose up --build
```

Runs Postgres, backend, and frontend together. Requires `backend/.env`
and `frontend/.env.local` to exist first.

## Status

- [x] Vision, architecture, MVP scope, agent definitions documented (`docs/`)
- [x] Backend restructured around Goal/Workspace/Planner/Agents/Execution/Memory
- [x] Frontend restructured with `features/` mirroring backend domains
- [x] Goal/Workspace models + Alembic migration
- [x] Goal API (create/list/get) and Workspace API (get) - tested, live-verified
- [x] Dashboard (greeting, Create Goal, Goal Cards) - implemented
- [x] Workspace UI (nav, Overview functional; Tasks/Planner/Knowledge/Timeline/Chat placeholders)
- [x] Dark-first design system (`components/ui/`)
- [x] Linting/formatting configured and passing (ESLint/Prettier, Ruff/Black)
- [ ] Auth (JWT) — placeholder only (single demo user, no login UI)
- [ ] Planner Agent (real planning logic) — not yet implemented
- [ ] Agent Orchestrator, Approval flow, Execution Agent — not yet implemented
- [ ] Memory Engine — not yet implemented

See [`docs/roadmap.md`](docs/roadmap.md) for the build sequence.
