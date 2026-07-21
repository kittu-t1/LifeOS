"""
Planner module.

Owns the AI Planner MVP's actual planning logic: the versioned prompt
(prompts.py), the LLM provider abstraction and its OpenAI adapter
(llm/), and structured-output parsing/validation (parser.py).
app/services/planner_service.py is the orchestration layer that calls
into this module and persists the result - see that file for the full
request -> LLM -> validate -> save flow.

app/agents/planner_agent.py (a separate, still-unimplemented placeholder)
is intentionally NOT wired up here. The AI Planner MVP spec is explicit
that this phase stays a simple, direct call chain with no multi-agent
orchestration - PlannerAgent is left for a later phase where agents
genuinely need to collaborate (see docs/agents.md), not routed through
today just to satisfy the file's existence.
"""
