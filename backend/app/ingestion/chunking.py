"""Split each page into chunks with deterministic, page-scoped IDs."""

from __future__ import annotations

import re

from app.ingestion.headings import heading_at_or_before
from app.schemas.chunks import Chunk, ChunkMetadata, PageText

# Bump when code changes would produce different chunks for the same file.
CHUNKING_VERSION = "1"

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def build_chunk_id(document_id: str, page_number: int, position: int) -> str:
    return f"{document_id}-p{page_number}-c{position:02d}"


def split_page_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split one page into overlapping windows, preferring natural boundaries."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    units = _semantic_units(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for unit in units:
        unit_len = len(unit) + 1
        if current and current_len + unit_len > chunk_size:
            chunks.append(" ".join(current).strip())
            carry = _tail_units(current, chunk_overlap)
            current = list(carry)
            current_len = sum(len(part) + 1 for part in carry)
        if unit_len > chunk_size:
            # Hard-slice one oversized unit instead of dropping it.
            if current:
                chunks.append(" ".join(current).strip())
                current, current_len = [], 0
            step = chunk_size - chunk_overlap
            for start in range(0, len(unit), step):
                piece = unit[start : start + chunk_size].strip()
                if piece:
                    chunks.append(piece)
            continue
        current.append(unit)
        current_len += unit_len

    if current:
        chunks.append(" ".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def chunk_page(
    page: PageText,
    *,
    document_id: str,
    chunk_size: int,
    chunk_overlap: int,
    metadata_template: dict[str, object],
) -> list[Chunk]:
    """Turn one page into chunks, each carrying full provenance."""
    pieces = split_page_text(page.text, chunk_size, chunk_overlap)
    lines = page.text.split("\n")
    chunks: list[Chunk] = []
    for position, piece in enumerate(pieces, start=1):
        chunk_id = build_chunk_id(document_id, page.page_number, position)
        metadata = ChunkMetadata(
            **metadata_template,  # type: ignore[arg-type]
            page_number=page.page_number,
            section=_section_for(lines, piece),
            chunk_id=chunk_id,
        )
        chunks.append(Chunk(chunk_id=chunk_id, chunk_text=piece, metadata=metadata))
    return chunks


def _semantic_units(text: str) -> list[str]:
    units: list[str] = []
    for paragraph in _PARAGRAPH_BREAK.split(text):
        for line_group in paragraph.split("\n"):
            stripped = line_group.strip()
            if not stripped:
                continue
            units.extend(part for part in _SENTENCE_END.split(stripped) if part.strip())
    return units


def _tail_units(units: list[str], overlap_chars: int) -> list[str]:
    """Trailing units whose combined length is closest to the overlap budget."""
    if overlap_chars <= 0:
        return []
    carried: list[str] = []
    total = 0
    for unit in reversed(units):
        if total + len(unit) > overlap_chars and carried:
            break
        carried.insert(0, unit)
        total += len(unit) + 1
    return carried


def _section_for(lines: list[str], chunk_text: str) -> str:
    """Nearest heading above where this chunk starts. Empty when undetectable."""
    opening = chunk_text[:60]
    for index, line in enumerate(lines):
        if opening and opening.startswith(line.strip()[:30]) and line.strip():
            return heading_at_or_before(lines, index)
    return heading_at_or_before(lines, 0)
