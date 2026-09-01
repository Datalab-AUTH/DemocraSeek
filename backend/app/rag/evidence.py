"""Assign prompt-local evidence IDs and enforce the context budget."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.chunks import RetrievedChunk

# Approximate characters per token.
CHARS_PER_TOKEN = 4
# Default fallback excerpt length.
EXCERPT_CHARS = 320


class EvidenceItem(BaseModel):
    """One retrieved chunk, ready to be rendered into the prompt."""

    evidence_id: str
    retrieved: RetrievedChunk

    @property
    def text(self) -> str:
        return self.retrieved.chunk.chunk_text


def build_evidence(
    retrieved: list[RetrievedChunk], max_context_tokens: int
) -> list[EvidenceItem]:
    """Assign E-IDs and add only complete chunks within the budget."""
    budget_chars = max_context_tokens * CHARS_PER_TOKEN
    items: list[EvidenceItem] = []
    used = 0
    for position, item in enumerate(retrieved, start=1):
        cost = len(item.chunk.chunk_text)
        if items and used + cost > budget_chars:
            break
        items.append(EvidenceItem(evidence_id=f"E{position}", retrieved=item))
        used += cost
    return items


def excerpt_head(text: str, limit: int = EXCERPT_CHARS) -> str:
    """Leading excerpt of a chunk, cut on a word boundary."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    cut = collapsed[:limit]
    space = cut.rfind(" ")
    return (cut[:space] if space > limit // 2 else cut).rstrip() + "..."
