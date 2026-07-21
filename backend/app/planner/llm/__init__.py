"""
LLM provider abstraction.

Planner Service -> LLMProvider (this module's interface) -> a concrete
adapter (OpenAI today - see openai_provider.py). Deliberately just an
interface plus one adapter, not a multi-provider registry or an
orchestration framework (no LangChain, no agent framework) - the AI
Planner MVP spec is explicit that this stays simple. Swapping or adding
a provider later means writing one more adapter class and pointing
get_llm_provider() at it; nothing above this layer changes.
"""
