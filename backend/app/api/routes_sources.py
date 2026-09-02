"""Serve only source files and figures registered in the approved corpus."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from app.api.deps import ApplicationContext, get_context
from app.corpus.registry import DocumentNotFoundError
from app.schemas.figures import Figure
from app.schemas.sources import SourcePage, SourceResponse

router = APIRouter(prefix="/api/sources", tags=["sources"])

# Maximum source-page preview length.
MAX_PAGE_PREVIEW_CHARS = 6000


@router.get("/{document_id}", response_model=SourceResponse)
def get_source(
    document_id: str,
    page: int | None = Query(default=None, ge=1),
    context: ApplicationContext = Depends(get_context),
) -> SourceResponse:
    record = context.registry.get(document_id)

    page_payload: SourcePage | None = None
    if page is not None and record.source_type == "internal":
        if page > record.page_count:
            raise DocumentNotFoundError(f"{document_id}#p{page}")
        page_text = context.registry.get_page(document_id, page)
        text = page_text.text if page_text else ""
        truncated = len(text) > MAX_PAGE_PREVIEW_CHARS
        page_payload = SourcePage(
            page_number=page,
            text=text[:MAX_PAGE_PREVIEW_CHARS],
            truncated=truncated,
            figures=[
                Figure(
                    figure_id=figure.figure_id,
                    document_id=figure.document_id,
                    document_title=record.document_title,
                    page_number=figure.page_number,
                    caption=figure.caption,
                    width=figure.width,
                    height=figure.height,
                    image_url=f"/api/sources/{figure.document_id}/figures/{figure.figure_id}",
                    source_url=f"/api/sources/{figure.document_id}?page={figure.page_number}",
                )
                for figure in context.registry.figures_for_page(document_id, page)
            ],
        )

    return SourceResponse(
        document_id=record.document_id,
        document_title=record.document_title,
        filename=record.filename,
        source_type=record.source_type,
        authors=record.authors,
        publishers=record.publishers,
        external_url=record.external_url,
        document_type=record.document_type,
        deliverable_id=record.deliverable_id,
        publication_date=record.publication_date,
        page_count=record.page_count,
        corpus_version=record.corpus_version,
        page=page_payload,
        file_url=(
            f"/api/sources/{record.document_id}/file"
            if record.source_type == "internal"
            else None
        ),
    )


@router.get("/{document_id}/figures/{figure_id}")
def get_figure_image(
    document_id: str, figure_id: str, context: ApplicationContext = Depends(get_context)
) -> FileResponse:
    """Serve one extracted figure. Path comes from the registry only."""
    if context.registry.get(document_id).source_type == "external":
        raise DocumentNotFoundError(document_id)
    path = context.registry.resolve_figure_path(document_id, figure_id)
    return FileResponse(path, media_type="image/png")


# Known source-file media types.
_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


@router.get("/{document_id}/file")
def get_source_file(
    document_id: str, context: ApplicationContext = Depends(get_context)
) -> FileResponse:
    """Serve only internal original files."""
    record = context.registry.get(document_id)
    if record.source_type == "external":
        raise DocumentNotFoundError(document_id)
    path = context.registry.resolve_source_path(document_id)
    return FileResponse(
        path,
        media_type=_MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream"),
        filename=record.filename,
        content_disposition_type="inline",
    )
