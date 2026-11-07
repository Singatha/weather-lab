from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.rate_limit.backend import InMemoryRateLimitBackend
from app.rate_limit.middleware import RateLimitMiddleware
from app.rate_limit.service import RateLimiter


class WallClock:
    def __init__(self) -> None:
        self.current = 100.0

    def __call__(self) -> float:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += seconds


class FailingRateLimitBackend:
    async def hit(self, key: str, *, ttl_seconds: int) -> int:
        del key, ttl_seconds
        raise ConnectionError("redis unavailable")


async def test_rate_limiter_enforces_and_resets_a_fixed_window() -> None:
    clock = WallClock()
    limiter = RateLimiter(
        InMemoryRateLimitBackend(clock=clock),
        limit=2,
        window_seconds=10,
        clock=clock,
    )

    first = await limiter.check("client")
    second = await limiter.check("client")
    denied = await limiter.check("client")
    clock.advance(10)
    reset = await limiter.check("client")

    assert first.allowed is True and first.remaining == 1
    assert second.allowed is True and second.remaining == 0
    assert denied.allowed is False and denied.retry_after_seconds == 10
    assert reset.allowed is True and reset.remaining == 1


async def test_rate_limiter_falls_back_when_redis_fails() -> None:
    clock = WallClock()
    limiter = RateLimiter(
        FailingRateLimitBackend(),
        limit=1,
        window_seconds=60,
        fallback=InMemoryRateLimitBackend(clock=clock),
        clock=clock,
    )

    assert (await limiter.check("client")).allowed is True
    assert (await limiter.check("client")).allowed is False


@pytest.fixture
async def limited_client() -> AsyncIterator[AsyncClient]:
    application = FastAPI()
    application.add_middleware(RateLimitMiddleware)
    clock = WallClock()
    application.state.rate_limiter = RateLimiter(
        InMemoryRateLimitBackend(clock=clock),
        limit=2,
        window_seconds=60,
        clock=clock,
    )

    @application.get("/api/v1/example")
    async def example() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/live")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as client:
        yield client


async def test_rate_limit_middleware_returns_consistent_429(
    limited_client: AsyncClient,
) -> None:
    first = await limited_client.get("/api/v1/example")
    second = await limited_client.get("/api/v1/example")
    denied = await limited_client.get("/api/v1/example")
    health = await limited_client.get("/health/live")

    assert first.status_code == second.status_code == 200
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert denied.status_code == 429
    assert denied.json() == {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again shortly.",
        }
    }
    assert denied.headers["Retry-After"] == "20"
    assert health.status_code == 200
