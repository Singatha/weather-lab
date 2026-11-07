import hashlib
import math
import time
from collections.abc import Callable
from dataclasses import dataclass

from app.rate_limit.backend import InMemoryRateLimitBackend, RateLimitBackend


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class RateLimiter:
    """Fixed-window limiter with a Redis primary and local safety fallback."""

    def __init__(
        self,
        backend: RateLimitBackend,
        *,
        limit: int,
        window_seconds: int,
        fallback: RateLimitBackend | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if limit < 1:
            raise ValueError("limit must be at least one")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least one")
        self._backend = backend
        self._limit = limit
        self._window_seconds = window_seconds
        self._clock = clock
        self._fallback = fallback or InMemoryRateLimitBackend(clock=clock)

    async def check(self, identity: str) -> RateLimitDecision:
        now = self._clock()
        window = int(now // self._window_seconds)
        identity_hash = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
        key = f"weather-lab:v1:rate-limit:{identity_hash}:{window}"
        ttl_seconds = self._window_seconds * 2
        try:
            count = await self._backend.hit(key, ttl_seconds=ttl_seconds)
        except Exception:
            count = await self._fallback.hit(key, ttl_seconds=ttl_seconds)

        reset_at = (window + 1) * self._window_seconds
        retry_after = max(1, math.ceil(reset_at - now))
        return RateLimitDecision(
            allowed=count <= self._limit,
            limit=self._limit,
            remaining=max(0, self._limit - count),
            retry_after_seconds=retry_after,
        )
