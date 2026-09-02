"""Onboarding configuration, profile and compiled-policy schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DIMENSIONS: tuple[str, ...] = ("role", "intent", "support", "mode")

# Personalisation conflict order; global rules remain absolute.
PRECEDENCE: tuple[str, ...] = ("support", "intent", "role", "mode")


# Configuration
class ChoiceConfig(BaseModel):
    """One selectable answer, with the policy fragments it contributes."""

    model_config = ConfigDict(frozen=True)

    code: str
    label: str
    description: str = ""
    instructions: tuple[str, ...] = ()


class QuestionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    dimension: Literal["role", "intent", "support", "mode"]
    order: int
    required: bool
    prompt: str
    help_text: str = ""
    choices: tuple[ChoiceConfig, ...]


class LocaleOption(BaseModel):
    """One language offered by the onboarding interface."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")
    display_name: str
    native_name: str


class OnboardingUIConfig(BaseModel):
    """Interface copy that surrounds the configurable questions."""

    model_config = ConfigDict(frozen=True)

    language_label: str
    progress: str
    not_chosen: str
    choose_option_error: str
    back: str
    cancel: str
    next: str
    finish: str
    no_questions: str
    step_titles: dict[str, str]


class LocalizedChoiceConfig(BaseModel):
    """Translated presentation copy for one stable policy choice code."""

    model_config = ConfigDict(frozen=True)

    label: str
    description: str = ""


class LocalizedQuestionConfig(BaseModel):
    """Translated presentation copy keyed by the stable question and choice IDs."""

    model_config = ConfigDict(frozen=True)

    prompt: str
    help_text: str = ""
    choices: dict[str, LocalizedChoiceConfig]


class OnboardingTranslation(BaseModel):
    """A complete non-default-language rendering of the onboarding."""

    model_config = ConfigDict(frozen=True)

    locale: str = Field(pattern=r"^[a-z]{2}(?:-[A-Z]{2})?$")
    ui: OnboardingUIConfig
    questions: dict[str, LocalizedQuestionConfig]


class OverrideConfig(BaseModel):
    """Add or suppress instructions for a matching code combination."""

    model_config = ConfigDict(frozen=True)

    id: str
    description: str = ""
    match: dict[str, str]
    add_instructions: tuple[str, ...] = ()
    suppress_instructions: tuple[str, ...] = ()


class OnboardingConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_version: str
    default_locale: str
    locales: tuple[LocaleOption, ...]
    onboarding_ui: OnboardingUIConfig
    translations: tuple[OnboardingTranslation, ...] = ()
    questions: tuple[QuestionConfig, ...]
    global_guardrails: tuple[str, ...]
    precedence_note: str
    overrides: tuple[OverrideConfig, ...] = ()

    def question_for(self, dimension: str) -> QuestionConfig:
        for question in self.questions:
            if question.dimension == dimension:
                return question
        raise KeyError(f"No question configured for dimension {dimension!r}")

    def codes_for(self, dimension: str) -> tuple[str, ...]:
        return tuple(choice.code for choice in self.question_for(dimension).choices)


# Profile
class OnboardingProfile(BaseModel):
    """Four response-preference codes and their policy version."""

    model_config = ConfigDict(frozen=True)

    role_code: str = Field(pattern=r"^R[1-9]\d*$")
    intent_code: str = Field(pattern=r"^I[1-9]\d*$")
    support_code: str = Field(pattern=r"^S[1-9]\d*$")
    mode_code: str = Field(pattern=r"^M[1-9]\d*$")
    policy_version: str

    def code_for(self, dimension: str) -> str:
        return {
            "role": self.role_code,
            "intent": self.intent_code,
            "support": self.support_code,
            "mode": self.mode_code,
        }[dimension]

    def as_log_fields(self) -> dict[str, str]:
        return self.model_dump()


class CompiledPolicy(BaseModel):
    """Inspectable output of the policy compiler."""

    profile: OnboardingProfile
    role_instructions: list[str]
    intent_instructions: list[str]
    support_instructions: list[str]
    mode_instructions: list[str]
    global_guardrails: list[str]
    applied_overrides: list[str]
    compiled_system_instructions: str


# API models
class CompileRequest(BaseModel):
    profile: OnboardingProfile


class CompileResponse(BaseModel):
    policy: CompiledPolicy
