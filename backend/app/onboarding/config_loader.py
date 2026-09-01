"""Loading and validation of the versioned onboarding configuration."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.schemas.onboarding import DIMENSIONS, OnboardingConfig


class OnboardingConfigError(ValueError):
    """The onboarding configuration file is missing or invalid."""


def load_onboarding_config(path: Path) -> OnboardingConfig:
    """Read, parse and validate the onboarding configuration."""
    if not path.is_file():
        raise OnboardingConfigError(
            f"Onboarding configuration not found at {path}. "
            f"Set ONBOARDING_CONFIG_PATH to a readable versioned YAML file."
        )
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise OnboardingConfigError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise OnboardingConfigError(f"{path} must contain a YAML mapping at the top level.")

    try:
        config = OnboardingConfig.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError
        raise OnboardingConfigError(f"{path} does not match the expected schema: {exc}") from exc

    _validate_semantics(config, path)
    return config


def _validate_semantics(config: OnboardingConfig, path: Path) -> None:
    problems: list[str] = []

    if not config.policy_version.strip():
        problems.append("policy_version must not be empty.")
    if not config.global_guardrails:
        problems.append("global_guardrails must contain at least one rule.")
    if not config.precedence_note.strip():
        problems.append("precedence_note must not be empty.")

    locale_codes = [locale.code for locale in config.locales]
    if len(locale_codes) != len(set(locale_codes)):
        problems.append("locales contains duplicate locale codes.")
    if config.default_locale not in locale_codes:
        problems.append("default_locale must reference an entry in locales.")
    if set(config.onboarding_ui.step_titles) != set(DIMENSIONS):
        problems.append("onboarding_ui.step_titles must contain exactly the four dimensions.")
    progress = config.onboarding_ui.progress
    if "{current}" not in progress or "{total}" not in progress:
        problems.append("onboarding_ui.progress must contain {current} and {total} placeholders.")

    for dimension in DIMENSIONS:
        matches = sum(1 for question in config.questions if question.dimension == dimension)
        if matches != 1:
            problems.append(
                f"exactly one question must be configured for dimension {dimension!r}."
            )

    orders = sorted(question.order for question in config.questions)
    if orders != list(range(1, len(config.questions) + 1)):
        problems.append("question 'order' values must be 1..N with no gaps or duplicates.")

    all_codes: set[str] = set()
    question_ids: set[str] = set()
    for question in config.questions:
        if question.id in question_ids:
            problems.append(f"duplicate question id {question.id!r}.")
        question_ids.add(question.id)
        if not question.choices:
            problems.append(f"question {question.id!r} has no choices.")
        codes = [choice.code for choice in question.choices]
        if len(set(codes)) != len(codes):
            problems.append(f"question {question.id!r} has duplicate choice codes.")
        for choice in question.choices:
            if not choice.instructions:
                problems.append(f"choice {choice.code!r} has no policy instructions.")
            if not choice.label.strip():
                problems.append(f"choice {choice.code!r} has an empty label.")
        all_codes.update(codes)

    translation_locales = [translation.locale for translation in config.translations]
    if len(translation_locales) != len(set(translation_locales)):
        problems.append("translations contains duplicate locale codes.")
    expected_translation_locales = set(locale_codes) - {config.default_locale}
    if set(translation_locales) != expected_translation_locales:
        problems.append(
            "translations must contain every non-default locale exactly once and must not "
            "duplicate the default locale."
        )
    for translation in config.translations:
        if set(translation.ui.step_titles) != set(DIMENSIONS):
            problems.append(
                f"translation {translation.locale!r} step_titles must contain exactly "
                "the four dimensions."
            )
        translated_progress = translation.ui.progress
        if "{current}" not in translated_progress or "{total}" not in translated_progress:
            problems.append(
                f"translation {translation.locale!r} progress must contain "
                "{current} and {total} placeholders."
            )
        if set(translation.questions) != question_ids:
            problems.append(
                f"translation {translation.locale!r} must contain exactly all configured "
                "question IDs."
            )
            continue
        for question in config.questions:
            localized = translation.questions[question.id]
            expected_codes = {choice.code for choice in question.choices}
            if set(localized.choices) != expected_codes:
                problems.append(
                    f"translation {translation.locale!r}, question {question.id!r} must contain "
                    "exactly all configured choice codes."
                )

    valid_match_keys = {f"{dimension}_code" for dimension in DIMENSIONS}
    override_ids: set[str] = set()
    for override in config.overrides:
        if override.id in override_ids:
            problems.append(f"duplicate override id {override.id!r}.")
        override_ids.add(override.id)
        if not override.match:
            problems.append(f"override {override.id!r} has an empty match (it would match all).")
        for key, value in override.match.items():
            if key not in valid_match_keys:
                problems.append(
                    f"override {override.id!r} matches unknown key {key!r}; "
                    f"expected one of {sorted(valid_match_keys)}."
                )
            elif value not in all_codes:
                problems.append(f"override {override.id!r} references unknown code {value!r}.")
        if not override.add_instructions and not override.suppress_instructions:
            problems.append(f"override {override.id!r} has no effect.")

    if problems:
        raise OnboardingConfigError(
            f"Invalid onboarding configuration in {path}:\n  - " + "\n  - ".join(problems)
        )
