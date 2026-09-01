"""Onboarding configuration and policy compilation.

The frontend renders questions from this endpoint. It never contains onboarding
wording or policy fragments of its own - changing config/onboarding.v2.yaml is
enough to change the interface.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ApplicationContext, get_context
from app.onboarding.compiler import compile_policy
from app.schemas.onboarding import CompileRequest, CompileResponse, OnboardingConfig

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("/config", response_model=OnboardingConfig)
def get_onboarding_config(context: ApplicationContext = Depends(get_context)) -> OnboardingConfig:
    """The active versioned onboarding configuration.

    Policy fragments are included deliberately: they describe how an answer will
    be adapted, and showing that supports the source-reliability need (S3). They are
    not the system prompt, which is never exposed.
    """
    return context.onboarding_config


@router.post("/compile", response_model=CompileResponse)
def compile_profile(
    payload: CompileRequest, context: ApplicationContext = Depends(get_context)
) -> CompileResponse:
    """Validate four codes and compile them into inspectable instructions.

    The backend is the authority here. A profile held in browser storage is only
    a convenience; it is re-validated and re-compiled on every request.
    """
    policy = compile_policy(context.onboarding_config, payload.profile)
    return CompileResponse(policy=policy)
