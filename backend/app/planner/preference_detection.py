"""
Deterministic preference-statement detector for the Planner's opt-in
"Would you like LifeOS to remember this?" suggestion (see
PlanRead.suggested_memory and app/services/planner_service.py's
generate_plan/regenerate_plan).

Explicitly NOT automatic memory extraction - the Memory Personalization
sprint's "Out of Scope" list still holds (no embeddings, no vector
search, no AI-generated ranking, no automatic behavior analysis that
writes without asking). This module never touches the database and never
writes a Memory row itself; it only returns a candidate sentence for the
API/frontend to show as a suggestion. Nothing is persisted unless the
user explicitly clicks Accept, which goes through the existing
POST /api/v1/memories endpoint exactly like a memory typed by hand (see
app/memory/api/routes.py) - "detect and suggest," never "detect and
save."

Deterministic and phrase-based on purpose - no LLM call, no embeddings,
same "no vector search or embeddings" constraint the Memory ranking
sprint already established. A short, fixed list of first-person
preference phrasings is a blunt instrument, but a predictable one: it
either finds an obvious preference sentence or it doesn't, with no
hidden model behavior to reason about or evaluate.
"""

from __future__ import annotations

import re

# Matched against the START of a sentence (not anywhere inside it), so a
# subordinate clause like "...but I only have evenings free" doesn't
# false-positive on a sentence that isn't really a standalone preference
# statement. Case-insensitive. Order doesn't affect correctness (each
# sentence is tested against all of them), only which phrasing a given
# sentence happens to satisfy first if it somehow matched more than one.
_PREFERENCE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^\s*i\s+only\b",
        r"^\s*i\s+always\b",
        r"^\s*i\s+never\b",
        r"^\s*i\s+usually\b",
        r"^\s*i\s+typically\b",
        r"^\s*i\s+prefer\b",
        r"^\s*i\s+like\s+to\b",
        r"^\s*i\s+need\s+to\b",
        r"^\s*i\s+want\s+to\b",
        r"^\s*i\s+work\s+best\b",
    ]
]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def detect_preference_statement(*texts: str | None) -> str | None:
    """Scans free-text planner input (a goal's stated constraints, an
    Improve Plan adjustment) for the first sentence that reads like a
    first-person preference statement, and returns it verbatim (trimmed,
    original casing/punctuation) - or None if nothing matches.

    Checks `texts` in the order given, and within each text, sentence by
    sentence in reading order, so the result is always "the first
    candidate a human skimming top-to-bottom would also have noticed,"
    not a scored or ranked guess across everything the user has ever
    typed."""
    for text in texts:
        if not text:
            continue
        for sentence in _SENTENCE_SPLIT.split(text):
            sentence = sentence.strip()
            if not sentence:
                continue
            if any(pattern.match(sentence) for pattern in _PREFERENCE_PATTERNS):
                return sentence
    return None
