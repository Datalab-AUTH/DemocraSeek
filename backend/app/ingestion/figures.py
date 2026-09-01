"""Extract, filter and index figures from approved PDFs.

Vision descriptions are derived evidence and remain linked to the source image.
"""

from __future__ import annotations

import hashlib
import io
import logging
import re
from pathlib import Path
from typing import Any

from PIL import Image
from pypdf import PdfReader

from app.providers.base import VisionProvider
from app.schemas.chunks import Chunk, ChunkMetadata, PageText
from app.schemas.figures import FigureRecord

logger = logging.getLogger(__name__)

# Minimum width and height in pixels.
MIN_DIMENSION = 100
# Minimum image area.
MIN_AREA = 20_000
# Maximum width-to-height ratio.
MAX_ASPECT_RATIO = 20.0
# Repeated images at this limit are treated as decoration.
REPEAT_PAGE_LIMIT = 3
# Maximum accepted figures per page.
MAX_FIGURES_PER_PAGE = 8
# Maximum stored long edge.
MAX_STORED_PIXELS = 1400

# English labels such as ``Figure 3``, ``Fig. 2`` and ``Table 1``.
_CAPTION = re.compile(
    r"^\s*(figure|fig|table|chart|diagram|image|graph)\b\.?"
    # Escaped en and em dashes keep the source unambiguous.
    r"(?:\s*([0-9]+(?:\.[0-9]+)*|[ivxlIVXL]+)\s*[.:\-\u2013\u2014)]?|\s*[:\-\u2013\u2014])"
    r"\s*(.*)$",
    re.IGNORECASE,
)
# Maximum caption length.
MAX_CAPTION_CHARS = 300
# Reject prose that begins with a figure reference.
_SENTENCE_BREAK = re.compile(r"[.!?]\s+[A-Z\u0391-\u03a9]")


def extract_figures(
    pdf_path: Path,
    pages: list[PageText],
    *,
    document_id: str,
    output_dir: Path,
) -> list[FigureRecord]:
    """Extract figures and write accepted images as PNG files."""
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        logger.warning("figure_extraction_skipped", extra={"document_id": document_id})
        return []

    captions_by_page = {page.page_number: _captions(page.text) for page in pages}
    candidates: list[tuple[FigureRecord, bytes]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_captions = captions_by_page.get(page_number, [])
        position = 0
        for image in _page_images(page):
            if position >= MAX_FIGURES_PER_PAGE:
                break
            decoded = _decode(image)
            if decoded is None:
                continue
            width, height = decoded.size
            if not _is_figure(width, height):
                continue

            position += 1
            payload = _to_png(decoded)
            caption = page_captions[position - 1] if position <= len(page_captions) else ""
            figure_id = f"{document_id}-p{page_number}-f{position:02d}"
            candidates.append(
                (
                    FigureRecord(
                        figure_id=figure_id,
                        document_id=document_id,
                        page_number=page_number,
                        stored_file=f"{document_id}/p{page_number}-f{position:02d}.png",
                        caption=caption,
                        width=width,
                        height=height,
                        content_hash=hashlib.sha256(payload).hexdigest(),
                    ),
                    payload,
                )
            )

    kept = _drop_repeated(candidates)
    _write(kept, output_dir)
    logger.info(
        "figures_extracted",
        extra={
            "document_id": document_id,
            "candidates": len(candidates),
            "kept": len(kept),
        },
    )
    return [record for record, _ in kept]


# Filtering
def _is_figure(width: int, height: int) -> bool:
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        return False
    if width * height < MIN_AREA:
        return False
    ratio = max(width, height) / max(1, min(width, height))
    return ratio <= MAX_ASPECT_RATIO


def _drop_repeated(
    candidates: list[tuple[FigureRecord, bytes]],
) -> list[tuple[FigureRecord, bytes]]:
    """Remove images that repeat across pages: logos, watermarks, page furniture."""
    pages_per_hash: dict[str, set[int]] = {}
    for record, _ in candidates:
        pages_per_hash.setdefault(record.content_hash, set()).add(record.page_number)
    decorative = {
        content_hash
        for content_hash, pages in pages_per_hash.items()
        if len(pages) >= REPEAT_PAGE_LIMIT
    }
    return [item for item in candidates if item[0].content_hash not in decorative]


# Captions
def _captions(page_text: str) -> list[str]:
    """Caption lines on a page, in reading order. Empty when the page states none."""
    found: list[str] = []
    for line in page_text.split("\n"):
        stripped = line.strip()
        if not stripped or len(stripped) > MAX_CAPTION_CHARS:
            continue
        if _SENTENCE_BREAK.search(stripped):
            continue
        match = _CAPTION.match(stripped)
        if match and match.group(3).strip():
            found.append(stripped)
    return found


# Images
def _page_images(page: Any) -> list[Any]:
    try:
        return list(page.images)
    except Exception:
        return []


def _decode(image: Any) -> Image.Image | None:
    """Return a PIL image, or None if this object cannot be read."""
    try:
        decoded: Image.Image | None = image.image
        if decoded is not None:
            return decoded.convert("RGB")
    except Exception:  # pypdf raises many types for unsupported filters
        pass
    try:
        return Image.open(io.BytesIO(image.data)).convert("RGB")
    except Exception:  # unsupported or corrupt image data
        return None


def _to_png(image: Image.Image) -> bytes:
    if max(image.size) > MAX_STORED_PIXELS:
        image = image.copy()
        image.thumbnail((MAX_STORED_PIXELS, MAX_STORED_PIXELS))
    buffer = io.BytesIO()
    # Stable bytes keep hashes and re-ingestion reproducible.
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _write(kept: list[tuple[FigureRecord, bytes]], output_dir: Path) -> None:
    for record, payload in kept:
        target = output_dir / record.stored_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


# Searchable figure evidence
def build_figure_chunks(
    records: list[FigureRecord],
    *,
    figures_dir: Path,
    vision: VisionProvider | None,
    metadata_template: dict[str, object],
) -> list[Chunk]:
    """Build chunks from captions and optional vision descriptions."""
    chunks: list[Chunk] = []
    for record in records:
        description = ""
        source = "caption_only"
        if vision is not None:
            payload = (figures_dir / record.stored_file).read_bytes()
            description = vision.describe_image(payload, context=record.caption)
            if description:
                source = f"vision:{vision.provider_name}:{vision.model_name}"

        text = "\n".join(part for part in (record.caption, description) if part).strip()
        if not text:
            # Keep unlabelled figures visible, but not searchable.
            continue

        chunk_id = f"{record.document_id}-p{record.page_number}-fig{record.figure_id[-2:]}"
        metadata = ChunkMetadata(
            **metadata_template,  # type: ignore[arg-type]
            page_number=record.page_number,
            section=record.caption,
            chunk_id=chunk_id,
            modality="figure",
            figure_id=record.figure_id,
            description_source=source,
        )
        chunks.append(Chunk(chunk_id=chunk_id, chunk_text=text, metadata=metadata))
    return chunks
