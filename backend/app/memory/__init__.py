"""
Memory module.

Owns the logic for storing and retrieving durable context about the user
and their Workspaces (facts, past decisions, progress history). Distinct
from app/vectorstore/, which is the low-level embeddings/vector-DB
interface (Chroma today) - this module is the business-logic layer that
decides what gets remembered and how it's surfaced, and may use the
vectorstore as one of its storage backends. The Memory Agent (see
app/agents/memory_agent.py) is the orchestration-facing wrapper around
this module.

Empty placeholder - no implementation yet. See docs/agents.md and
docs/architecture.md for the intended design.
"""
