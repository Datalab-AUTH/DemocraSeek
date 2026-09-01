"""Parse the LLM's raw JSON reply without repairing malformed output."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError

_CODE_FENCE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.DOTALL)


class GenerationParseError(ValueError):
    """The model did not return a usable JSON object."""


class RawCitation(BaseModel):
    citation_id: str
    evidence_id: str
    supporting_quote: str = ""


class RawAnswer(BaseModel):
    status: str
    answer: str = ""
    citations: list[RawCitation] = []


def parse_model_reply(text: str) -> RawAnswer:
    """Parse the model's reply into RawAnswer, or raise GenerationParseError."""
    candidate = text.strip()
    fenced = _CODE_FENCE.match(candidate)
    if fenced:
        candidate = fenced.group(1).strip()

    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise GenerationParseError(f"reply was not valid JSON ({exc.msg})") from exc

    if not isinstance(payload, dict):
        raise GenerationParseError("reply JSON was not an object")

    try:
        answer = RawAnswer.model_validate(payload)
    except ValidationError as exc:
        raise GenerationParseError(f"reply JSON did not match the expected shape: {exc}") from exc

    if answer.status not in {"grounded", "insufficient_evidence"}:
        raise GenerationParseError(f"unknown status {answer.status!r}")
    return answer
