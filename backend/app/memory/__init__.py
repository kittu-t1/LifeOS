"""
Memory module - the Memory Engine.

Owns the logic for storing and retrieving durable context about the user
(preferences, planning context, habit insights, learned patterns, and
free-form notes - see app/memory/models/memory.py). Distinct from
app/vectorstore/, which is the low-level embeddings/vector-DB interface
(Chroma today, not wired in yet) - this module is the business-logic/
persistence layer that decides what gets remembered and how it's
surfaced today (deterministic CRUD, V1), and may use the vectorstore as
one of its storage backends once semantic search is built. The Memory
Agent (see app/agents/memory_agent.py) remains the future orchestration-
facing wrapper around this module; that wrapper is still unimplemented,
but the module it would wrap is now real.

A Clean-Architecture slice, deliberately organized by layer within this
one feature (models/ schemas/ repositories/ services/ api/) rather than
folded into the rest of the app's flat app/models//app/services/ layout
- this is the one module other features (Planner, Habits, and future
Calendar/Execution Assistant work) are meant to depend on, so it's kept
structurally independent and swappable on purpose (see
app/memory/services/memory_service.py's docstring for the dependency
direction rule: consumers import MemoryService, this module never
imports them back).

See docs/agents.md and docs/architecture.md for the original intended
design this now implements (V1: no embeddings, no LLM calls - see
Future Compatibility in the Memory Engine sprint spec). Memory selection
is deterministic, not semantic: MemoryService.get_relevant_memories
ranks by category priority, recency, and confidence - a plain sort, not
a vector similarity search - and the Planner injects that ranked context
directly into its prompts (see app/services/planner_service.py's
_build_memory_context).
"""
