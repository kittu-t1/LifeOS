# LifeOS — Core Agents

Five specialized agents make up the MVP's Agent Orchestration layer (see
`docs/architecture.md`). Each is a thin coordinator in
`backend/app/agents/` wrapping capability logic that lives in its own
module — this keeps "what an agent is responsible for" separate from
"how that responsibility is actually implemented."

All five are currently **placeholders** (`backend/app/agents/*.py`) —
class stubs with no logic, matching Day 3's architectural-alignment scope.

---

## Planner Agent

**Purpose:** Breaks a user's Goal into an executable plan — an ordered
set of steps with dependencies, sized so each step can be reasonably
approved and executed on its own.

**Backed by:** `backend/app/planner/`

**Inputs:** the Goal (plain-language statement), relevant Memory context
for the user (via the Memory Agent).

**Outputs:** a structured Plan (steps, dependencies, estimated scope)
attached to the Goal's Workspace.

**Where it sits in the flow:** immediately after Goal → Workspace
creation, before Agent Orchestration dispatches work to other agents.

**Interactions:** reads from the Memory Agent to ground the plan in prior
context; hands its output to the Agent Orchestrator, which routes
individual steps to the Research and Execution Agents.

**MVP behavior:** generates a real, structured plan from the goal and
available context — this is the centerpiece of the MVP (see
`docs/mvp_scope.md`). Not simulated; this is the one agent whose actual
intelligence the MVP is built to prove out.

---

## Memory Agent

**Purpose:** Stores and retrieves durable context about the user and
their Workspaces, so every other agent (and the user, via the Memory
screen) can draw on real history instead of starting from zero each time.

**Backed by:** `backend/app/memory/` (business logic) +
`backend/app/vectorstore/` (embeddings/retrieval infrastructure, Chroma
today).

**Inputs:** completed goals, plan decisions, execution outcomes, and
explicit user-provided context.

**Outputs:** relevant context surfaced to the Planner Agent (and, later,
Research/Execution Agents) on request; a user-facing, editable/deletable
memory record.

**Where it sits in the flow:** read from at Planning time; written to at
Memory Update time (after execution, whether simulated or real).

**Interactions:** every other agent can query it; nothing writes to it
without a corresponding real event (a plan created, a step completed) —
memory should never contain content the user can't trace back to
something that actually happened.

**MVP behavior:** stores and retrieves structured records tied to Goals/
Workspaces. Full semantic/vector retrieval (via `vectorstore/`) can start
simple (e.g. most-recent-N context) and grow in sophistication without
changing the Memory Agent's interface.

---

## Execution Agent

**Purpose:** Coordinates carrying out an *approved* plan — sequencing
tasks in dependency order, tracking each one's status, and (in future
versions) dispatching real work to External Integrations.

**Backed by:** `backend/app/execution/`

**Inputs:** an approved plan step (post-Approval Agent sign-off).

**Outputs:** a task status update (pending → in progress → done/failed)
and an execution outcome, which the Memory Agent then records.

**Where it sits in the flow:** after Approval, before Memory Update.

**Interactions:** only ever acts on steps the Approval Agent has cleared;
reports outcomes to Memory; in future versions, calls
`backend/app/integrations/` adapters to perform real actions.

**MVP behavior:** **simulated** — produces realistic status transitions
and outcomes without calling any real external system (see
`docs/mvp_scope.md` for why). This validates the orchestration/tracking
mechanics independently of integration reliability.

---

## Research Agent

**Purpose:** Collects supporting information needed to plan or execute a
step well — e.g. background facts, context the Planner needs to size a
step accurately, or information an execution step depends on.

**Backed by:** `backend/app/research/`

**Inputs:** a specific information need, raised by the Planner Agent or
Execution Agent.

**Outputs:** relevant findings, attached to the Workspace (and available
to Memory for future reuse).

**Where it sits in the flow:** invoked on-demand by the Planner or
Execution Agent, not a fixed stage every goal passes through.

**Interactions:** called by Planner/Execution; writes findings that
Memory can later retrieve.

**MVP behavior:** minimal — may return static or lightly-processed
information in the MVP. Full research capability (live web/knowledge
retrieval) is a post-MVP enhancement.

---

## Approval Agent

**Purpose:** Requests explicit user confirmation before consequential
actions are executed — the trust mechanism that keeps LifeOS from acting
on the user's behalf without their knowledge.

**Backed by:** logic in `backend/app/services/` (cross-cutting — approval
applies to steps regardless of which capability module produced them).

**Inputs:** a proposed action or batch of actions from the Agent
Orchestrator, before they reach the Execution Agent.

**Outputs:** either a confirmation gate shown to the user, or (for
explicitly low-risk steps) an auto-clear — the line between the two is a
deliberate product decision, not a default-allow.

**Where it sits in the flow:** between Agent Orchestration and Execution
— nothing consequential reaches Execution without passing through here.

**Interactions:** sits in front of the Execution Agent; its decisions
(and the user's responses) are recorded by the Memory Agent.

**MVP behavior:** every plan-step execution in the MVP passes through an
explicit approval prompt — given execution is simulated, this stage's
main job in the MVP is proving the *UX and data flow* of approval, ready
for real stakes once External Integrations arrive.
