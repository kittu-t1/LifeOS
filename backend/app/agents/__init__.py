"""
Agents module.

Holds the orchestration-facing definition of each specialized agent
(Planner, Memory, Execution, Research, Approval). Each agent here is a
thin coordinator - the actual capability logic lives in its matching
module (app/planner/, app/memory/, app/execution/, etc.) or, for
Research and Approval, in app/services/. This separation lets the
Agent Orchestrator (future: LangGraph-based) invoke a consistent agent
interface without caring how each capability is implemented underneath.

See docs/agents.md for full definitions of each agent's purpose, inputs,
outputs, and where it sits in the execution flow.

Empty placeholders - no implementation yet.
"""
