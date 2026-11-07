from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Stable response contract shared by health probes."""

    status: Literal["ok", "ready"]


@router.get("/live", response_model=HealthResponse, summary="Liveness probe")
async def liveness() -> HealthResponse:
    """Confirm that the API process can serve requests."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def readiness() -> HealthResponse:
    """Confirm that the Phase 1 application has initialized successfully.

    Redis is not an application dependency until the caching phase, so this
    endpoint deliberately avoids probing it for now.
    """
    return HealthResponse(status="ready")
