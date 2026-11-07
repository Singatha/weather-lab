import asyncio
import time
from collections.abc import Callable
from typing import Any, Protocol

from redis.asyncio import Redis

_FIXED_WINDOW_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


class RateLimitBackend(Protocol):
    async def hit(self, key: str, *, ttl_seconds: int) -> int: ...


class RedisRateLimitBackend:
    """Atomic Redis counter using INCR and EXPIRE in one Lua script."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def hit(self, key: str, *, ttl_seconds: int) -> int:
        result: Any = await self._client.eval(_FIXED_WINDOW_SCRIPT, 1, key, ttl_seconds)
        if not isinstance(result, int):
            raise TypeError("Redis rate limit script must return an integer")
        return result


class InMemoryRateLimitBackend:
    """Process-local fallback used when Redis is temporarily unavailable."""

    def __init__(self, *, clock: Callable[[], float] = time.time) -> None:
        self._clock = clock
        self._entries: dict[str, tuple[float, int]] = {}
        self._lock = asyncio.Lock()

    async def hit(self, key: str, *, ttl_seconds: int) -> int:
        async with self._lock:
            now = self._clock()
            expires_at, count = self._entries.get(key, (now + ttl_seconds, 0))
            if now >= expires_at:
                expires_at, count = now + ttl_seconds, 0
            count += 1
            self._entries[key] = (expires_at, count)
            if len(self._entries) > 1024:
                self._entries = {
                    entry_key: entry for entry_key, entry in self._entries.items() if entry[0] > now
                }
            return count
