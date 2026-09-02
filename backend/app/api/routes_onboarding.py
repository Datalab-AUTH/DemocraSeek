"""Expose onboarding configuration and compile response policies."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import ApplicationContext, get_context
from app.onboarding.compiler import compile_policy
from app.schemas.onboarding import CompileRequest, CompileResponse, OnboardingConfig

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("/config", response_model=OnboardingConfig)
def get_onboarding_config(context: ApplicationContext = Depends(get_context)) -> OnboardingConfig:
    """Return the active versioned onboarding configuration."""
    return context.onboarding_config


@router.post("/compile", response_model=CompileResponse)
def compile_profile(
    payload: CompileRequest, context: ApplicationContext = Depends(get_context)
) -> CompileResponse:
    """Validate four profile codes and compile their response policy."""
    policy = compile_policy(context.onboarding_config, payload.profile)
    return CompileResponse(policy=policy)
