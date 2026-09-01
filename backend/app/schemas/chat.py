"""Chat request/response models and the internal grounded-answer structure."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.figures import Figure
from app.schemas.onboarding import OnboardingProfile

AnswerStatus = Literal["grounded", "insufficient_evidence"]


class ConversationMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["user", "assistant"]
    content: str
    #: Optional English form used only as internal conversation context. The
    #: interface sends it back from the preceding ChatResponse so multilingual
    #: conversations do not need to re-translate every old turn on every request.
    #: ``content`` remains the text that was actually shown to the user.
    canonical_content: str | None = None
    #: Language metadata of the visible turn. Used only when a later, genuinely
    #: ambiguous follow-up cannot identify its own language.
    language_code: str | None = Field(
        default=None, pattern=r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$"
    )
    language_name: str | None = Field(default=None, min_length=1, max_length=80)


class Citation(BaseModel):
    """A verified citation.

    Every field except ``citation_id``/``evidence_id`` is copied from the
    ingestion record of the supporting chunk. None of it comes from the model.
    """

    citation_id: str
    evidence_id: str
    document_id: str
    document_title: str
    deliverable_id: str = ""
    page_number: int
    chunk_id: str
    supporting_excerpt: str
    #: How the excerpt was produced:
    #: "model_quote_verified" - the model's quote was found verbatim in the chunk;
    #: "chunk_head"           - fell back to the start of the chunk;
    #: "figure_description"   - the evidence is a figure; the excerpt is its
    #:                          caption plus an automatically derived description,
    #:                          and the image itself is attached for verification.
    excerpt_source: Literal["model_quote_verified", "chunk_head", "figure_description"]
    source_url: str
    #: "text" or "figure". Figure citations must be presented differently.
    modality: Literal["text", "figure"] = "text"
    #: Images from the cited page. Attached deterministically by the application
    #: from validated citations - the model never selects or describes them.
    figures: list[Figure] = []


class GroundedAnswer(BaseModel):
    """Result of the RAG orchestrator."""

    status: AnswerStatus
    answer: str
    citations: list[Citation]
    policy_version: str
    #: Machine-readable reason when status is insufficient_evidence.
    reason_code: str = ""


class MultilingualAnswer(GroundedAnswer):
    """A grounded English result plus its user-facing language rendering.

    The canonical fields are deliberately returned to the client. They let a
    stateless API preserve English-only RAG context while the visible
    conversation remains in the user's language.
    """

    language_code: str
    language_name: str
    canonical_question: str
    canonical_answer: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    profile: OnboardingProfile
    history: list[ConversationMessage] = []


class ChatResponse(MultilingualAnswer):
    """What the chat endpoint returns: the answer plus the request id.

    Extends GroundedAnswer rather than repeating its five fields, so the wire
    shape and the internal result cannot drift apart.
    """

    request_id: str
