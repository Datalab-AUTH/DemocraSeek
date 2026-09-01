"""Extract PDF text per page and flag pages that may need OCR."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.schemas.chunks import PageText

# Empty-page character threshold.
EMPTY_PAGE_CHAR_THRESHOLD = 20
# OCR-review threshold for pages with images.
OCR_REVIEW_CHAR_THRESHOLD = 120


class PdfExtractionError(RuntimeError):
    """The file could not be opened or parsed as a PDF."""


def compute_checksum(path: Path) -> str:
    """Stable content identity of a source PDF (sha256 of the raw bytes)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def slugify_document_id(filename: str) -> str:
    """Human-readable, deterministic document id derived from the filename."""
    stem = Path(filename).stem
    normalised = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalised).strip("-").lower()
    return slug or "document"


def read_pdf_title(path: Path) -> str:
    """Title from PDF metadata, or an empty string. Never guessed."""
    try:
        metadata = PdfReader(str(path)).metadata
        title = metadata.get("/Title") if metadata else None
    except Exception:  # a broken metadata dict must not stop ingestion
        return ""
    if isinstance(title, str) and title.strip():
        return title.strip()
    return ""


def extract_pages(path: Path) -> list[PageText]:
    """Extract one PageText per PDF page, 1-indexed."""
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise PdfExtractionError(f"Cannot read PDF {path.name}: {type(exc).__name__}") from exc

    pages: list[PageText] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text() or ""
        except Exception:
            raw = ""
        text = _normalise_whitespace(raw)
        char_count = len(text.strip())
        has_images = _page_has_images(page)

        is_empty = char_count < EMPTY_PAGE_CHAR_THRESHOLD
        needs_ocr = False
        reason = ""
        if has_images and char_count < OCR_REVIEW_CHAR_THRESHOLD:
            needs_ocr = True
            reason = "image_present_with_little_text"
        elif is_empty:
            needs_ocr = True
            reason = "no_extractable_text"

        pages.append(
            PageText(
                page_number=index,
                text=text,
                char_count=char_count,
                is_empty=is_empty,
                needs_ocr_review=needs_ocr,
                ocr_reason=reason,
            )
        )
    return pages


def _page_has_images(page: Any) -> bool:
    """Detect XObject images without decoding them (cheap and dependency-free)."""
    try:
        xobjects = page["/Resources"]["/XObject"].get_object()
        return any(
            xobjects[name].get_object().get("/Subtype") == "/Image" for name in xobjects
        )
    except Exception:  # absent keys are the common case, not an error
        return False


def _normalise_whitespace(text: str) -> str:
    """Collapse extraction artefacts while preserving line structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("­", "")  # soft hyphen
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")  # common ligatures
    # De-hyphenate words broken across lines: "partici-\npation" -> "participation"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Collapse intra-line whitespace while preserving line breaks.
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()
