import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.cache.backend import CacheBackend
from app.observability.metrics import ObservabilityMetrics

CacheState = Literal["fresh", "stale", "miss", "unavailable"]


@dataclass(frozen=True)
class CacheLookup[T: BaseModel]:
    state: CacheState
    value: T | None = None
    stored_at: datetime | None = None


@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0
    stale_hits: int = 0
    writes: int = 0
    errors: int = 0

    def snapshot(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "stale_hits": self.stale_hits,
            "writes": self.writes,
            "errors": self.errors,
        }


class CacheService:
    """Serialize validated models and degrade safely when Redis is unavailable."""

    def __init__(
        self,
        backend: CacheBackend,
        *,
        clock: Callable[[], datetime] | None = None,
        metrics: CacheMetrics | None = None,
        observability: ObservabilityMetrics | None = None,
    ) -> None:
        self._backend = backend
        self._clock = clock or (lambda: datetime.now(UTC))
        self.metrics = metrics or CacheMetrics()
        self._observability = observability

    async def get[T: BaseModel](self, key: str, model_type: type[T]) -> CacheLookup[T]:
        try:
            raw = await self._backend.get(key)
        except Exception:
            self.metrics.errors += 1
            self._observe("get", "error")
            return CacheLookup(state="unavailable")

        if raw is None:
            self.metrics.misses += 1
            self._observe("get", "miss")
            return CacheLookup(state="miss")

        try:
            envelope = json.loads(raw)
            if not isinstance(envelope, dict):
                raise TypeError("Cache envelope must be an object")
            stored_at = datetime.fromisoformat(str(envelope["stored_at"]))
            fresh_until = datetime.fromisoformat(str(envelope["fresh_until"]))
            value = model_type.model_validate(envelope["value"])
            if stored_at.tzinfo is None or fresh_until.tzinfo is None:
                raise ValueError("Cache timestamps must be timezone-aware")
        except (KeyError, TypeError, ValueError, ValidationError):
            self.metrics.errors += 1
            self.metrics.misses += 1
            self._observe("get", "invalid")
            await self._delete_safely(key)
            return CacheLookup(state="miss")

        if self._clock() <= fresh_until:
            self.metrics.hits += 1
            self._observe("get", "hit")
            return CacheLookup(state="fresh", value=value, stored_at=stored_at)

        self.metrics.stale_hits += 1
        self._observe("get", "stale")
        return CacheLookup(state="stale", value=value, stored_at=stored_at)

    async def set(
        self,
        key: str,
        value: BaseModel,
        *,
        fresh_ttl_seconds: int,
        retention_ttl_seconds: int,
    ) -> bool:
        if retention_ttl_seconds < fresh_ttl_seconds:
            raise ValueError("Retention TTL cannot be shorter than the fresh TTL")

        stored_at = self._clock()
        envelope = {
            "stored_at": stored_at.isoformat(),
            "fresh_until": (stored_at + timedelta(seconds=fresh_ttl_seconds)).isoformat(),
            "value": value.model_dump(mode="json"),
        }
        serialized = json.dumps(envelope, separators=(",", ":"), sort_keys=True)
        try:
            await self._backend.set(
                key,
                serialized,
                ttl_seconds=retention_ttl_seconds,
            )
        except Exception:
            self.metrics.errors += 1
            self._observe("set", "error")
            return False
        self.metrics.writes += 1
        self._observe("set", "success")
        return True

    async def ping(self) -> bool:
        try:
            available = await self._backend.ping()
        except Exception:
            self.metrics.errors += 1
            self._observe("ping", "error")
            return False
        self._observe("ping", "success" if available else "unavailable")
        return available

    async def aclose(self) -> None:
        await self._backend.aclose()

    async def _delete_safely(self, key: str) -> None:
        try:
            await self._backend.delete(key)
        except Exception:
            self.metrics.errors += 1
            self._observe("delete", "error")

    def _observe(self, operation: str, result: str) -> None:
        if self._observability is not None:
            self._observability.observe_cache(operation=operation, result=result)
