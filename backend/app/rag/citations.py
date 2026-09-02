"""Validate model citations against retrieved evidence and trusted metadata.

Unknown IDs or markers reject the answer; source fields always come from chunks.
"""

from __future__ import annotations

import re
from typing import Literal

from app.rag.evidence import EvidenceItem, excerpt_head
from app.rag.generator import RawAnswer, RawCitation
from app.schemas.chat import Citation

_MARKER = re.compile(r"\[(C\d+)\]")
# Evidence IDs are internal and must not remain in visible text.
_EVIDENCE_MARKER = re.compile(r"\[E\d+\]")
# Minimum length for a distinctive verified quote.
MIN_VERIFIABLE_QUOTE_CHARS = 20
MAX_EXCERPT_CHARS = 400


class CitationValidationError(ValueError):
    """The answer cannot be trusted and must not be shown to the user."""

    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def validate_and_build_citations(
    raw: RawAnswer, evidence: list[EvidenceItem], *, source_url_template: str
) -> tuple[str, list[Citation]]:
    """Return (answer_text, verified_citations) or raise CitationValidationError."""
    known = {item.evidence_id: item for item in evidence}

    if not raw.citations:
        raise CitationValidationError(
            "A grounded answer was returned without any citation.", "no_citations"
        )

    seen_ids: set[str] = set()
    for citation in raw.citations:
        if not re.fullmatch(r"C\d+", citation.citation_id):
            raise CitationValidationError(
                f"Malformed citation identifier {citation.citation_id!r}.", "malformed_citation_id"
            )
        if citation.citation_id in seen_ids:
            raise CitationValidationError(
                f"Duplicate citation identifier {citation.citation_id!r}.", "duplicate_citation_id"
            )
        seen_ids.add(citation.citation_id)
        if citation.evidence_id not in known:
            raise CitationValidationError(
                f"Citation {citation.citation_id} refers to evidence "
                f"{citation.evidence_id!r}, which was not retrieved.",
                "invented_evidence_id",
            )

    # Rewrite E-markers only when the model supplied an unambiguous citation.
    answer_text = _rewrite_evidence_markers(raw.answer, raw.citations)
    stray_evidence = _EVIDENCE_MARKER.findall(answer_text)
    if stray_evidence:
        raise CitationValidationError(
            f"Answer text contains raw evidence identifier(s) {sorted(set(stray_evidence))} "
            f"with no matching citation; they resolve to nothing for the reader.",
            "evidence_id_in_answer",
        )

    markers_in_text = _MARKER.findall(answer_text)
    unknown_markers = [marker for marker in markers_in_text if marker not in seen_ids]
    if unknown_markers:
        raise CitationValidationError(
            f"Answer text cites unknown marker(s): {sorted(set(unknown_markers))}.",
            "unknown_marker",
        )
    if not markers_in_text:
        raise CitationValidationError(
            "A grounded answer contained no citation markers.", "no_markers"
        )
    raw = raw.model_copy(update={"answer": answer_text})

    # Keep marked citations in first-use order.
    order: list[str] = []
    for marker in markers_in_text:
        if marker not in order:
            order.append(marker)
    by_id = {citation.citation_id: citation for citation in raw.citations}

    citations: list[Citation] = []
    renumbering: dict[str, str] = {}
    # Collapse repeated citations of the same evidence.
    by_evidence: dict[str, str] = {}
    for old_id in order:
        raw_citation = by_id[old_id]
        existing = by_evidence.get(raw_citation.evidence_id)
        if existing is not None:
            renumbering[old_id] = existing
            continue

        new_id = f"C{len(citations) + 1}"
        renumbering[old_id] = new_id
        by_evidence[raw_citation.evidence_id] = new_id
        item = known[raw_citation.evidence_id]
        metadata = item.retrieved.chunk.metadata
        if metadata.modality == "figure":
            # Figure excerpts are derived descriptions checked against the image.
            excerpt = excerpt_head(item.retrieved.chunk.chunk_text, MAX_EXCERPT_CHARS)
            excerpt_source: Literal[
                "model_quote_verified", "chunk_head", "figure_description"
            ] = "figure_description"
        else:
            excerpt, excerpt_source = _build_excerpt(
                item.retrieved.chunk.chunk_text, raw_citation.supporting_quote
            )
        # External text supports validation but is never returned to the browser.
        if metadata.source_type == "external":
            excerpt = ""
        citations.append(
            Citation(
                citation_id=new_id,
                evidence_id=raw_citation.evidence_id,
                document_id=metadata.document_id,
                document_title=metadata.document_title,
                source_type=metadata.source_type,
                authors=metadata.authors,
                publishers=metadata.publishers,
                publication_date=metadata.publication_date,
                external_url=metadata.external_url,
                deliverable_id=metadata.deliverable_id,
                page_number=metadata.page_number,
                chunk_id=metadata.chunk_id,
                supporting_excerpt=excerpt,
                excerpt_source=excerpt_source,
                modality=metadata.modality,
                source_url=source_url_template.format(
                    document_id=metadata.document_id, page=metadata.page_number
                ),
            )
        )

    return _renumber_markers(raw.answer, renumbering), citations


def _rewrite_evidence_markers(answer: str, citations: list[RawCitation]) -> str:
    """Map an E-marker to its model-supplied C-marker when unambiguous."""
    by_evidence: dict[str, str] = {}
    for citation in citations:
        by_evidence.setdefault(citation.evidence_id, citation.citation_id)
    if not by_evidence:
        return answer

    def replace(match: re.Match[str]) -> str:
        evidence_id = match.group(0).strip("[]")
        citation_id = by_evidence.get(evidence_id)
        return f"[{citation_id}]" if citation_id else match.group(0)

    return _EVIDENCE_MARKER.sub(replace, answer)


def _renumber_markers(answer: str, renumbering: dict[str, str]) -> str:
    """Rewrite [Cn] markers using placeholders so swaps cannot collide."""

    def to_placeholder(match: re.Match[str]) -> str:
        return "\x00" + renumbering[match.group(1)] + "\x00"

    staged = _MARKER.sub(to_placeholder, answer)
    return re.sub(r"\x00(C\d+)\x00", r"[\1]", staged)


def _build_excerpt(
    chunk_text: str, quote: str
) -> tuple[str, Literal["model_quote_verified", "chunk_head"]]:
    """Excerpt sliced from the chunk. Model text is never returned verbatim."""
    normalised_chunk = " ".join(chunk_text.split())
    normalised_quote = " ".join(quote.split())
    if len(normalised_quote) >= MIN_VERIFIABLE_QUOTE_CHARS:
        position = normalised_chunk.find(normalised_quote)
        if position >= 0:
            end = position + len(normalised_quote)
            sliced = normalised_chunk[position:end][:MAX_EXCERPT_CHARS]
            return sliced, "model_quote_verified"
    return excerpt_head(chunk_text), "chunk_head"
