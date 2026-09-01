"""Remove repeated page headers, footers and page numbers."""

from __future__ import annotations

import re
from collections import Counter

from app.schemas.chunks import PageText

# Required share of non-empty pages.
REPEAT_RATIO = 0.6
# Lines checked at each page edge.
EDGE_LINES = 3
# Maximum header or footer length.
MAX_HEADER_CHARS = 120
# Minimum document length for detection.
MIN_PAGES_FOR_DETECTION = 4

_PAGE_NUMBER = re.compile(r"^(page\s*)?\d{1,4}(\s*(/|of)\s*\d{1,4})?$", re.IGNORECASE)


def detect_repeated_lines(pages: list[PageText]) -> set[str]:
    """Find lines that behave like running headers or footers."""
    populated = [page for page in pages if not page.is_empty]
    if len(populated) < MIN_PAGES_FOR_DETECTION:
        return set()

    counter: Counter[str] = Counter()
    for page in populated:
        lines = [line for line in page.text.split("\n") if line.strip()]
        edges = lines[:EDGE_LINES] + lines[-EDGE_LINES:]
        for line in set(edges):
            if len(line) <= MAX_HEADER_CHARS:
                counter[_canonical(line)] += 1

    threshold = max(2, int(len(populated) * REPEAT_RATIO))
    return {line for line, count in counter.items() if count >= threshold and line}


def clean_pages(pages: list[PageText]) -> list[PageText]:
    """Strip repeated headers/footers and bare page numbers from every page."""
    repeated = detect_repeated_lines(pages)
    cleaned: list[PageText] = []
    for page in pages:
        lines = page.text.split("\n")
        kept = [
            line
            for line in lines
            if _canonical(line) not in repeated and not _PAGE_NUMBER.match(line.strip())
        ]
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()
        cleaned.append(page.model_copy(update={"text": text, "char_count": len(text.strip())}))
    return cleaned


def _canonical(line: str) -> str:
    """Normalise so 'Page 3 of 40' and 'Page 12 of 40' compare equal."""
    return re.sub(r"\d+", "#", line.strip().lower())
