"""Health check endpoint.

Intentionally trivial: it proves routing, container startup, and networking
work end-to-end. It performs no business logic and checks no dependencies yet.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.schemas.health import HealthResponse
from app.core.config import get_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", environment=settings.environment.value)
