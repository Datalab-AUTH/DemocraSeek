"""Translate questions into English and validated answers back to the user."""

from __future__ import annotations

import logging
import re

from app.providers.base import LanguageProvider, ProviderError
from app.rag.orchestrator import RagOrchestrator
from app.rag.query import normalise_question, trim_history
from app.schemas.chat import ConversationMessage, MultilingualAnswer
from app.schemas.language import LanguageRoute
from app.schemas.onboarding import OnboardingProfile

logger = logging.getLogger(__name__)

_UNDEFINED_LANGUAGE_CODES = frozenset({"und", "mul", "zxx", "unknown"})
_ENGLISH_SIGNAL = re.compile(
    r"\b(?:what|who|whose|why|where|when|which|how|is|are|was|were|do|does|did|"
    r"can|could|should|would|tell|explain|describe|and|this|that|these|those)\b",
    re.IGNORECASE,
)
_SCRIPT_LANGUAGES = (
    (re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]"), "el", "Greek"),
    (re.compile(r"[\u3040-\u30ff]"), "ja", "Japanese"),
    (re.compile(r"[\uac00-\ud7af]"), "ko", "Korean"),
    (re.compile(r"[\u0e00-\u0e7f]"), "th", "Thai"),
    (re.compile(r"[\u0590-\u05ff]"), "he", "Hebrew"),
    (re.compile(r"[\u0530-\u058f]"), "hy", "Armenian"),
    (re.compile(r"[\u10a0-\u10ff]"), "ka", "Georgian"),
)


class MultilingualChatService:
    def __init__(
        self,
        *,
        rag: RagOrchestrator,
        language: LanguageProvider,
        max_user_input_chars: int,
        max_conversation_messages: int,
    ) -> None:
        self._rag = rag
        self._language = language
        self._max_user_input_chars = max_user_input_chars
        self._max_conversation_messages = max_conversation_messages

    def answer(
        self,
        *,
        question: str,
        profile: OnboardingProfile,
        history: list[ConversationMessage] | None = None,
    ) -> MultilingualAnswer:
        original_question = normalise_question(question, self._max_user_input_chars)
        recent = trim_history(
            list(history or []), self._max_conversation_messages
        )
        route = self._resolve_language(
            self._language.route_to_english(original_question),
            original_question=original_question,
            history=recent,
        )
        canonical_question = normalise_question(
            route.english_text, self._max_user_input_chars
        )
        canonical_history = [self._canonical_message(message) for message in recent]

        grounded = self._rag.answer(
            question=canonical_question,
            profile=profile,
            history=canonical_history,
        )
        canonical_answer = grounded.answer
        displayed_answer = self._language.translate_answer(
            canonical_answer,
            language_code=route.language_code,
            language_name=route.language_name,
        )

        logger.info(
            "multilingual_answer",
            extra={
                "language_code": route.language_code,
                "history_messages": len(canonical_history),
                "status": grounded.status,
            },
        )
        return MultilingualAnswer(
            **grounded.model_dump(exclude={"answer"}),
            answer=displayed_answer,
            language_code=route.language_code,
            language_name=route.language_name,
            canonical_question=canonical_question,
            canonical_answer=canonical_answer,
        )

    def _resolve_language(
        self,
        route: LanguageRoute,
        *,
        original_question: str,
        history: list[ConversationMessage],
    ) -> LanguageRoute:
        code = route.language_code.lower()
        if code not in _UNDEFINED_LANGUAGE_CODES:
            return route.model_copy(update={"language_code": code})

        # A clear current-language signal overrides conversation history.
        current = _deterministic_language(original_question)
        if current is not None:
            fallback_code, fallback_name = current
        else:
            previous = _last_known_language(history)
            if previous is None:
                raise ProviderError(
                    "The language of the current question could not be determined."
                )
            fallback_code, fallback_name = previous

        logger.warning(
            "undefined_language_resolved",
            extra={
                "reported_language_code": code,
                "resolved_language_code": fallback_code,
            },
        )
        return route.model_copy(
            update={"language_code": fallback_code, "language_name": fallback_name}
        )

    def _canonical_message(self, message: ConversationMessage) -> ConversationMessage:
        if message.canonical_content is not None and message.canonical_content.strip():
            english = message.canonical_content.strip()
        elif message.content.strip():
            english = self._language.route_to_english(message.content.strip()).english_text
        else:
            english = ""
        return ConversationMessage(role=message.role, content=english)


def _deterministic_language(text: str) -> tuple[str, str] | None:
    for pattern, code, name in _SCRIPT_LANGUAGES:
        if pattern.search(text):
            return code, name
    if text.isascii() and _ENGLISH_SIGNAL.search(text):
        return "en", "English"
    return None


def _last_known_language(
    history: list[ConversationMessage],
) -> tuple[str, str] | None:
    for message in reversed(history):
        code = (message.language_code or "").lower()
        if code and code not in _UNDEFINED_LANGUAGE_CODES:
            return code, message.language_name or code
        detected = _deterministic_language(message.content)
        if detected is not None:
            return detected
    return None
