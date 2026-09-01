"""Figure schemas.

A "figure" is an image extracted from an approved PDF page. Figures are never
generated, described or selected by the language model: they are attached to an
answer because a *validated citation* points at the page they live on. That is
what keeps the visual part of an answer as grounded as the textual part.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FigureRecord(BaseModel):
    """One extracted figure, as stored by the ingestion pipeline."""

    model_config = ConfigDict(frozen=True)

    figure_id: str
    document_id: str
    page_number: int = Field(ge=1)
    #: Path relative to the figures directory. Never user-supplied.
    stored_file: str
    #: Caption text found on the page ("Figure 3: ..."), or empty. Never invented.
    caption: str = ""
    width: int
    height: int
    #: sha256 of the decoded image, used to drop repeated logos and watermarks.
    content_hash: str


class Figure(BaseModel):
    """A figure as returned by the API, alongside the citation that surfaced it."""

    figure_id: str
    document_id: str
    document_title: str
    page_number: int
    caption: str = ""
    width: int
    height: int
    image_url: str
    source_url: str
