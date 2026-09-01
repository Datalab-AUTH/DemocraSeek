"""Validate questions and add limited context to dependent follow-ups.

Retrieval uses the question and history only, never the onboarding profile.
"""

from __future__ import annotations

import re

from app.schemas.chat import ConversationMessage

_ANAPHORA = {
    "it", "its", "this", "that", "these", "those", "they", "them", "their",
    "he", "she", "his", "her", "there", "one", "ones", "same",
}
_CONTINUATION_OPENERS = (
    "and ", "but ", "so ", "what about", "how about", "why", "and why", "what else",
    "tell me more", "more about", "can you expand", "explain more", "who", "when",
)
# Short questions are treated as context-dependent.
SHORT_QUESTION_CHARS = 60
# Previous user turns allowed in retrieval.
MAX_CONTEXT_TURNS = 2
# Maximum constructed query length.
MAX_QUERY_CHARS = 1000

_WORD = re.compile(r"[\w']+")


class InvalidQuestionError(ValueError):
    """The question is empty or exceeds the configured length limit."""


def normalise_question(question: str, max_chars: int) -> str:
    """Trim, collapse whitespace and enforce the configured length limit."""
    cleaned = " ".join(question.split())
    if not cleaned:
        raise InvalidQuestionError("The question is empty.")
    if len(cleaned) > max_chars:
        raise InvalidQuestionError(
            f"The question is {len(cleaned)} characters long; the limit is {max_chars}."
        )
    return cleaned


def looks_context_dependent(question: str) -> bool:
    lowered = question.lower().strip()
    if len(lowered) < SHORT_QUESTION_CHARS:
        return True
    if lowered.startswith(_CONTINUATION_OPENERS):
        return True
    words = set(_WORD.findall(lowered))
    return bool(words & _ANAPHORA)


def build_retrieval_query(
    question: str, history: list[ConversationMessage] | None = None
) -> str:
    """Build the retrieval text, adding history only when needed."""
    if not history or not looks_context_dependent(question):
        return question[:MAX_QUERY_CHARS]

    previous = [
        message.content.strip()
        for message in history
        if message.role == "user" and message.content.strip()
    ][-MAX_CONTEXT_TURNS:]
    if not previous:
        return question[:MAX_QUERY_CHARS]

    combined = " ".join([*previous, question])
    return " ".join(combined.split())[:MAX_QUERY_CHARS]


def trim_history(
    history: list[ConversationMessage], max_messages: int
) -> list[ConversationMessage]:
    """Keep only the most recent messages, as configured."""
    return history[-max_messages:] if max_messages > 0 else []
