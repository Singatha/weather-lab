from typing import Protocol

from redis.asyncio import Redis


class CacheBackend(Protocol):
    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def ping(self) -> bool: ...

    async def aclose(self) -> None: ...


class RedisCacheBackend:
    """Small redis-py adapter that keeps vendor types out of cache services."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        value = await self._client.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("Redis cache client must decode responses as strings")
        return value

    async def set(self, key: str, value: str, *, ttl_seconds: int) -> None:
        await self._client.set(name=key, value=value, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def ping(self) -> bool:
        return bool(await self._client.ping())

    async def aclose(self) -> None:
        await self._client.aclose()
