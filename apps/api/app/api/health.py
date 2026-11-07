from typing import Literal, cast

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.cache.service import CacheService

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"]


class DependencyStatus(BaseModel):
    redis: Literal["ok", "degraded"]


class ReadinessResponse(BaseModel):
    status: Literal["ready"]
    dependencies: DependencyStatus


@router.get("/live", response_model=LivenessResponse, summary="Liveness probe")
async def liveness() -> LivenessResponse:
    """Confirm that the API process can serve requests."""
    return LivenessResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
async def readiness(request: Request) -> ReadinessResponse:
    """Report Redis health without making the degradable cache a hard dependency."""
    cache = cast(CacheService | None, getattr(request.app.state, "cache_service", None))
    redis_available = cache is not None and await cache.ping()
    return ReadinessResponse(
        status="ready",
        dependencies=DependencyStatus(redis="ok" if redis_available else "degraded"),
    )
