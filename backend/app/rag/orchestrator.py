"""Coordinate policy compilation, retrieval, generation and validation.

One failed validation may be corrected once; a second failure discards the answer.
"""

from __future__ import annotations

import logging

from app.corpus.registry import CorpusRegistry, DocumentNotFoundError
from app.onboarding.compiler import compile_policy
from app.providers.base import LLMProvider, ProviderError
from app.rag.citations import CitationValidationError, validate_and_build_citations
from app.rag.generator import GenerationParseError, parse_model_reply
from app.rag.prompt import SYSTEM_PROMPT, build_user_prompt
from app.rag.query import normalise_question, trim_history
from app.rag.retriever import Retriever
from app.schemas.chat import Citation, ConversationMessage, GroundedAnswer
from app.schemas.figures import Figure
from app.schemas.onboarding import OnboardingConfig, OnboardingProfile

logger = logging.getLogger(__name__)

INSUFFICIENT_EVIDENCE_TEXT = (
    "I could not find sufficient supporting information in the current "
    "INNOVADE knowledge base."
)

SOURCE_URL_TEMPLATE = "/api/sources/{document_id}?page={page}"
FIGURE_URL_TEMPLATE = "/api/sources/{document_id}/figures/{figure_id}"

# Correction used before the model has accepted the evidence.
_RETRY_NOTE = (
    "\n\n===== CORRECTION REQUIRED =====\n"
    "Your previous reply was rejected: {problem}\n"
    "Reply again with a single valid JSON object. Cite only the evidence "
    "identifiers listed above, place a [C...] marker for every citation you list, "
    "never write [E...] identifiers in the answer text, and copy supporting quotes "
    "verbatim. If the evidence does not support an answer, return status "
    "\"insufficient_evidence\"."
)

# Format-only correction after the model has accepted the evidence.
_RETRY_NOTE_FORMAT_ONLY = (
    "\n\n===== CORRECTION REQUIRED =====\n"
    "Your previous reply was rejected for its FORM, not its content: {problem}\n"
    "The evidence above is unchanged, and you already judged it sufficient. Do "
    "NOT switch to \"insufficient_evidence\" - that would be wrong here. Write "
    "the same answer again with the citation markers in place: put a [C1], [C2] "
    "marker directly after each claim, list one citation object per marker, and "
    "use [C...] never [E...]. Example: \"Trust affects participation [C1]. "
    "Support at physical locations helps [C2].\""
)


class RagOrchestrator:
    def __init__(
        self,
        *,
        llm: LLMProvider,
        retriever: Retriever,
        onboarding_config: OnboardingConfig,
        max_user_input_chars: int,
        max_conversation_messages: int,
        registry: CorpusRegistry | None = None,
    ) -> None:
        self._llm = llm
        self._retriever = retriever
        self._onboarding_config = onboarding_config
        self._max_user_input_chars = max_user_input_chars
        self._max_conversation_messages = max_conversation_messages
        # Used only to attach figures after citation validation.
        self._registry = registry

    def answer(
        self,
        *,
        question: str,
        profile: OnboardingProfile,
        history: list[ConversationMessage] | None = None,
    ) -> GroundedAnswer:
        question = normalise_question(question, self._max_user_input_chars)
        recent = trim_history(list(history or []), self._max_conversation_messages)
        policy = compile_policy(self._onboarding_config, profile)
        evidence = self._retriever.retrieve(question, recent)

        if not evidence:
            logger.info(
                "insufficient_evidence",
                extra={"reason_code": "no_relevant_evidence", **profile.as_log_fields()},
            )
            return self._insufficient(profile, "no_relevant_evidence")

        base_prompt = build_user_prompt(
            compiled_policy=policy.compiled_system_instructions,
            history=recent,
            evidence=evidence,
            question=question,
            # Support outranks mode in presentation conflicts.
            presentation=policy.support_instructions + policy.mode_instructions,
        )

        problem = ""
        # Tracks whether a retry may only correct the output format.
        claimed_grounded = False
        for attempt in (1, 2):
            if attempt == 1:
                user_prompt = base_prompt
            else:
                note = _RETRY_NOTE_FORMAT_ONLY if claimed_grounded else _RETRY_NOTE
                user_prompt = base_prompt + note.format(problem=problem)
            try:
                reply = self._llm.generate_json(SYSTEM_PROMPT, user_prompt)
            except ProviderError:
                logger.exception("llm_call_failed", extra={"attempt": attempt})
                return self._insufficient(profile, "generation_unavailable")

            try:
                raw = parse_model_reply(reply)
            except GenerationParseError as exc:
                problem = str(exc)
                logger.warning(
                    "generation_parse_rejected", extra={"attempt": attempt, "problem": problem}
                )
                continue

            if raw.status == "insufficient_evidence":
                if claimed_grounded:
                    # A format retry cannot reverse an earlier grounded verdict.
                    logger.warning(
                        "model_capitulated_after_format_correction",
                        extra={"reason_code": "unverifiable_answer"},
                    )
                    return self._insufficient(profile, "unverifiable_answer")
                logger.info(
                    "insufficient_evidence",
                    extra={"reason_code": "model_reported_insufficient", **profile.as_log_fields()},
                )
                return self._insufficient(profile, "model_reported_insufficient")
            claimed_grounded = True

            try:
                answer_text, citations = validate_and_build_citations(
                    raw, evidence, source_url_template=SOURCE_URL_TEMPLATE
                )
            except CitationValidationError as exc:
                problem = str(exc)
                logger.warning(
                    "citation_validation_rejected",
                    extra={"attempt": attempt, "reason_code": exc.reason_code},
                )
                continue

            citations = self._attach_figures(citations)
            logger.info(
                "grounded_answer",
                extra={
                    "attempt": attempt,
                    "citation_count": len(citations),
                    "evidence_count": len(evidence),
                    "document_ids": sorted({c.document_id for c in citations}),
                    **profile.as_log_fields(),
                },
            )
            return GroundedAnswer(
                status="grounded",
                answer=answer_text,
                citations=citations,
                policy_version=profile.policy_version,
            )

        logger.warning(
            "answer_discarded_after_retry", extra={"reason_code": "unverifiable_answer"}
        )
        return self._insufficient(profile, "unverifiable_answer")

    def _attach_figures(self, citations: list[Citation]) -> list[Citation]:
        """Attach registered images found on each validated citation page."""
        if self._registry is None:
            return citations

        enriched: list[Citation] = []
        for citation in citations:
            if citation.source_type == "external":
                enriched.append(citation)
                continue
            try:
                records = self._registry.figures_for_page(
                    citation.document_id, citation.page_number
                )
            except DocumentNotFoundError:  # pragma: no cover - registry drift
                records = []
            if not records:
                enriched.append(citation)
                continue

            figures = [
                Figure(
                    figure_id=record.figure_id,
                    document_id=record.document_id,
                    document_title=citation.document_title,
                    page_number=record.page_number,
                    caption=record.caption,
                    width=record.width,
                    height=record.height,
                    image_url=FIGURE_URL_TEMPLATE.format(
                        document_id=record.document_id, figure_id=record.figure_id
                    ),
                    source_url=citation.source_url,
                )
                for record in records
            ]
            enriched.append(citation.model_copy(update={"figures": figures}))
        return enriched

    @staticmethod
    def _insufficient(profile: OnboardingProfile, reason_code: str) -> GroundedAnswer:
        return GroundedAnswer(
            status="insufficient_evidence",
            answer=INSUFFICIENT_EVIDENCE_TEXT,
            citations=[],
            policy_version=profile.policy_version,
            reason_code=reason_code,
        )
