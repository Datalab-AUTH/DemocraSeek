"""Chat request/response models and the internal grounded-answer structure."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chunks import SourceType
from app.schemas.figures import Figure
from app.schemas.onboarding import OnboardingProfile

AnswerStatus = Literal["grounded", "insufficient_evidence"]
MAX_CHAT_TEXT_CHARS = 20_000
MAX_CHAT_HISTORY_MESSAGES = 100


class ConversationMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_CHAT_TEXT_CHARS)
    # English form reused as internal multilingual context.
    canonical_content: str | None = Field(default=None, max_length=MAX_CHAT_TEXT_CHARS)
    # Visible-turn language used by ambiguous follow-ups.
    language_code: str | None = Field(
        default=None, pattern=r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$"
    )
    language_name: str | None = Field(default=None, min_length=1, max_length=80)


class Citation(BaseModel):
    """A citation backed by trusted chunk metadata."""

    citation_id: str
    evidence_id: str
    document_id: str
    document_title: str
    source_type: SourceType = "internal"
    authors: list[str] = Field(default_factory=list)
    publishers: list[str] = Field(default_factory=list)
    publication_date: str = ""
    external_url: str = ""
    deliverable_id: str = ""
    page_number: int
    chunk_id: str
    supporting_excerpt: str
    # Excerpt origin: verified quote, chunk start or figure description.
    excerpt_source: Literal["model_quote_verified", "chunk_head", "figure_description"]
    source_url: str
    # Evidence type used by the interface.
    modality: Literal["text", "figure"] = "text"
    # Registered images from the cited page.
    figures: list[Figure] = []


class GroundedAnswer(BaseModel):
    """Result of the RAG orchestrator."""

    status: AnswerStatus
    answer: str
    citations: list[Citation]
    policy_version: str
    # Machine-readable failure reason.
    reason_code: str = ""


class MultilingualAnswer(GroundedAnswer):
    """Grounded output plus canonical English context for later turns."""

    language_code: str
    language_name: str
    canonical_question: str
    canonical_answer: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_CHAT_TEXT_CHARS)
    profile: OnboardingProfile
    history: list[ConversationMessage] = Field(
        default_factory=list, max_length=MAX_CHAT_HISTORY_MESSAGES
    )


class ChatResponse(MultilingualAnswer):
    """Chat response with its request ID."""

    request_id: str
