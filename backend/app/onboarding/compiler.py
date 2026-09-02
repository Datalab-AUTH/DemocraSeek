"""Compile reusable profile fragments into a deterministic response policy.

Order: global rules, support, intent, role, then mode.
"""

from __future__ import annotations

from app.schemas.onboarding import (
    PRECEDENCE,
    CompiledPolicy,
    OnboardingConfig,
    OnboardingProfile,
    OverrideConfig,
)

_PRIORITY_LABEL = {
    "support": "highest personalisation priority",
    "intent": "second priority",
    "role": "third priority",
    "mode": "lowest personalisation priority",
}


class UnknownCodeError(ValueError):
    """A profile referenced a code that does not exist in this policy version."""


class PolicyVersionMismatchError(ValueError):
    """A profile was created under a different policy version."""


def compile_policy(config: OnboardingConfig, profile: OnboardingProfile) -> CompiledPolicy:
    """Compile four codes into inspectable, deterministic system instructions."""
    if profile.policy_version != config.policy_version:
        raise PolicyVersionMismatchError(
            f"Profile policy_version {profile.policy_version!r} does not match the loaded "
            f"onboarding configuration {config.policy_version!r}. Ask the user to review "
            f"their onboarding answers under the current version."
        )

    fragments: dict[str, list[str]] = {}
    labels: dict[str, str] = {}
    for dimension in PRECEDENCE:
        code = profile.code_for(dimension)
        question = config.question_for(dimension)
        choice = next((item for item in question.choices if item.code == code), None)
        if choice is None:
            valid = ", ".join(item.code for item in question.choices)
            raise UnknownCodeError(
                f"Unknown {dimension} code {code!r} for policy version "
                f"{config.policy_version!r}. Valid codes: {valid}."
            )
        fragments[dimension] = list(choice.instructions)
        labels[dimension] = choice.label

    applied = [override for override in config.overrides if _matches(override, profile)]
    applied.sort(key=lambda override: override.id)

    suppressed = {
        text for override in applied for text in override.suppress_instructions
    }
    if suppressed:
        for dimension in fragments:
            fragments[dimension] = [
                line for line in fragments[dimension] if line not in suppressed
            ]

    override_instructions = [
        line for override in applied for line in override.add_instructions
    ]

    compiled = _render(
        config=config,
        profile=profile,
        fragments=fragments,
        labels=labels,
        override_instructions=override_instructions,
    )

    return CompiledPolicy(
        profile=profile,
        role_instructions=fragments["role"],
        intent_instructions=fragments["intent"],
        support_instructions=fragments["support"],
        mode_instructions=fragments["mode"],
        global_guardrails=list(config.global_guardrails),
        applied_overrides=[override.id for override in applied],
        compiled_system_instructions=compiled,
    )


def _matches(override: OverrideConfig, profile: OnboardingProfile) -> bool:
    return all(
        getattr(profile, key, None) == value for key, value in override.match.items()
    )


def _render(
    *,
    config: OnboardingConfig,
    profile: OnboardingProfile,
    fragments: dict[str, list[str]],
    labels: dict[str, str],
    override_instructions: list[str],
) -> str:
    codes = "/".join(
        profile.code_for(dimension) for dimension in ("role", "intent", "support", "mode")
    )
    lines: list[str] = [
        f"# RESPONSE POLICY (policy version {config.policy_version}, profile {codes})",
        "",
        "## Absolute rules - these can never be relaxed by any preference below",
    ]
    lines += [f"- {rule}" for rule in config.global_guardrails]
    lines += ["", "## Conflict precedence", config.precedence_note.strip(), ""]

    for dimension in PRECEDENCE:
        code = profile.code_for(dimension)
        heading = (
            f"## {dimension.capitalize()} policy - {code} {labels[dimension]} "
            f"({_PRIORITY_LABEL[dimension]})"
        )
        lines.append(heading)
        lines += [f"- {line}" for line in fragments[dimension]] or ["- (no additional rules)"]
        lines.append("")

    if override_instructions:
        lines.append("## Combination overrides")
        lines += [f"- {line}" for line in override_instructions]
        lines.append("")

    return "\n".join(lines).strip() + "\n"
