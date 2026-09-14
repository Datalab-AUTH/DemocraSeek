"""Curated starter questions for the chat start screen.

They used to be generated from detected section headings and translated
through a static dictionary in the frontend, which silently dropped every
question the dictionary did not know. Now an operator writes them by hand, in
every interface locale at once, and the loader refuses a file where any locale
would end up with fewer questions than another.
"""

from __future__ import annotations

from pathlib import Path

import yaml


class StarterQuestionsError(ValueError):
    """The starter-questions file is missing, malformed, or incomplete."""


def load_starter_questions(path: Path, locales: list[str]) -> list[dict[str, str]]:
    """Return one ``{locale: text}`` mapping per question, in file order.

    ``locales`` is the full list of interface locales from the onboarding
    configuration; every question must provide all of them.
    """
    if not path.is_file():
        raise StarterQuestionsError(
            f"Starter questions file not found: {path}. "
            "Create it from config/starter_questions.yaml or set STARTER_QUESTIONS_PATH."
        )
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise StarterQuestionsError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict) or "questions" not in raw:
        raise StarterQuestionsError(f"{path} must contain a top-level `questions` list.")
    entries = raw["questions"]
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise StarterQuestionsError(f"{path}: `questions` must be a list.")

    expected = set(locales)
    problems: list[str] = []
    questions: list[dict[str, str]] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            problems.append(f"question {index} must be a mapping of locale code to text.")
            continue
        texts = {str(code): value for code, value in entry.items()}
        missing = sorted(expected - texts.keys())
        unknown = sorted(texts.keys() - expected)
        empty = sorted(code for code, value in texts.items() if not isinstance(value, str) or not value.strip())
        if missing:
            problems.append(f"question {index} is missing locale(s): {', '.join(missing)}.")
        if unknown:
            problems.append(f"question {index} has unknown locale(s): {', '.join(unknown)}.")
        if empty:
            problems.append(f"question {index} has empty text for: {', '.join(empty)}.")
        if not (missing or unknown or empty):
            questions.append({code: value.strip() for code, value in texts.items()})

    if problems:
        joined = "\n  - ".join(problems)
        raise StarterQuestionsError(f"{path} is incomplete:\n  - {joined}")
    return questions


def by_locale(questions: list[dict[str, str]], locales: list[str]) -> dict[str, list[str]]:
    """Regroup per locale, preserving question order. Same length for every locale."""
    return {locale: [question[locale] for question in questions] for locale in locales}
