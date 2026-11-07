from datetime import UTC, datetime

from app.cache.service import CacheService
from app.schemas.location import LocationSearchResponse
from tests.factories import location
from tests.fakes import InMemoryCacheBackend, MutableClock


async def test_cache_entry_transitions_from_fresh_to_stale() -> None:
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    cache = CacheService(backend, clock=clock)
    response = LocationSearchResponse(query="Berlin", locations=[location()])

    stored = await cache.set(
        "key",
        response,
        fresh_ttl_seconds=10,
        retention_ttl_seconds=30,
    )
    fresh = await cache.get("key", LocationSearchResponse)
    clock.advance(seconds=11)
    stale = await cache.get("key", LocationSearchResponse)

    assert stored is True
    assert backend.ttls["key"] == 30
    assert fresh.state == "fresh"
    assert fresh.value == response
    assert stale.state == "stale"
    assert cache.metrics.snapshot() == {
        "hits": 1,
        "misses": 0,
        "stale_hits": 1,
        "writes": 1,
        "errors": 0,
    }


async def test_cache_miss_and_corrupt_value_are_safe() -> None:
    backend = InMemoryCacheBackend()
    cache = CacheService(backend)

    missing = await cache.get("missing", LocationSearchResponse)
    backend.values["broken"] = "not-json"
    broken = await cache.get("broken", LocationSearchResponse)

    assert missing.state == "miss"
    assert broken.state == "miss"
    assert "broken" not in backend.values
    assert cache.metrics.misses == 2
    assert cache.metrics.errors == 1


async def test_cache_failures_degrade_without_raising() -> None:
    backend = InMemoryCacheBackend()
    backend.fail_get = True
    backend.fail_set = True
    backend.fail_ping = True
    cache = CacheService(backend)
    response = LocationSearchResponse(query="Berlin", locations=[])

    lookup = await cache.get("key", LocationSearchResponse)
    stored = await cache.set(
        "key",
        response,
        fresh_ttl_seconds=10,
        retention_ttl_seconds=10,
    )
    available = await cache.ping()

    assert lookup.state == "unavailable"
    assert stored is False
    assert available is False
    assert cache.metrics.errors == 3


async def test_cache_close_delegates_to_backend() -> None:
    backend = InMemoryCacheBackend()
    cache = CacheService(backend)

    await cache.aclose()

    assert backend.closed is True
