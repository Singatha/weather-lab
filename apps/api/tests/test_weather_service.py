import asyncio
from datetime import UTC, datetime

import pytest

from app.cache.service import CacheService
from app.core.exceptions import ProviderCircuitOpenError, ProviderTimeoutError
from app.schemas.location import Location
from app.schemas.weather import WeatherResponse
from app.services.weather import WeatherService
from tests.factories import location, weather_response
from tests.fakes import InMemoryCacheBackend, MutableClock


class CountingProvider:
    def __init__(self, *, delay_seconds: float = 0) -> None:
        self.location_calls = 0
        self.weather_calls = 0
        self.fail_weather = False
        self.open_circuit = False
        self.delay_seconds = delay_seconds

    async def search_locations(self, query: str, *, limit: int = 10) -> list[Location]:
        del query, limit
        self.location_calls += 1
        return [location()]

    async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
        del latitude, longitude
        self.weather_calls += 1
        if self.delay_seconds:
            await asyncio.sleep(self.delay_seconds)
        if self.fail_weather:
            raise ProviderTimeoutError()
        if self.open_circuit:
            raise ProviderCircuitOpenError()
        return weather_response()


def _service(
    provider: CountingProvider,
    backend: InMemoryCacheBackend,
    clock: MutableClock,
) -> WeatherService:
    return WeatherService(
        provider,
        CacheService(backend, clock=clock),
        location_ttl_seconds=100,
        weather_ttl_seconds=10,
        weather_stale_ttl_seconds=100,
        clock=clock,
    )


async def test_weather_miss_then_fresh_hit_calls_provider_once() -> None:
    provider = CountingProvider()
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)

    miss = await service.get_weather(52.52, 13.41)
    hit = await service.get_weather(52.52, 13.41)

    assert provider.weather_calls == 1
    assert miss.metadata.cache_status == "miss"
    assert miss.metadata.cached_at == clock.current
    assert hit.metadata.cache_status == "hit"
    assert hit.metadata.is_stale is False


async def test_stale_weather_is_returned_only_when_provider_fails() -> None:
    provider = CountingProvider()
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)
    await service.get_weather(52.52, 13.41)
    clock.advance(seconds=11)
    provider.fail_weather = True

    stale = await service.get_weather(52.52, 13.41)

    assert provider.weather_calls == 2
    assert stale.metadata.cache_status == "stale"
    assert stale.metadata.is_stale is True


async def test_provider_failure_without_retained_stale_data_is_raised() -> None:
    provider = CountingProvider()
    provider.fail_weather = True
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)

    with pytest.raises(ProviderTimeoutError):
        await service.get_weather(52.52, 13.41)


async def test_open_circuit_is_eligible_for_stale_fallback() -> None:
    provider = CountingProvider()
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)
    await service.get_weather(52.52, 13.41)
    clock.advance(seconds=11)

    provider.open_circuit = True
    stale = await service.get_weather(52.52, 13.41)

    assert stale.metadata.cache_status == "stale"
    assert stale.metadata.is_stale is True


async def test_stale_weather_is_refreshed_when_provider_recovers() -> None:
    provider = CountingProvider()
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)
    await service.get_weather(52.52, 13.41)
    clock.advance(seconds=11)

    refreshed = await service.get_weather(52.52, 13.41)

    assert provider.weather_calls == 2
    assert refreshed.metadata.cache_status == "miss"
    assert refreshed.metadata.is_stale is False


async def test_redis_failure_bypasses_cache() -> None:
    provider = CountingProvider()
    backend = InMemoryCacheBackend()
    backend.fail_get = True
    backend.fail_set = True
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)

    response = await service.get_weather(52.52, 13.41)

    assert provider.weather_calls == 1
    assert response.metadata.cache_status == "bypass"
    assert response.metadata.cached_at is None


async def test_location_search_is_cached() -> None:
    provider = CountingProvider()
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)

    first = await service.search_locations(" Berlin ")
    second = await service.search_locations("Berlin")

    assert first == second
    assert provider.location_calls == 1
    assert next(iter(backend.ttls.values())) == 100


async def test_concurrent_weather_misses_are_coalesced() -> None:
    provider = CountingProvider(delay_seconds=0.01)
    backend = InMemoryCacheBackend()
    clock = MutableClock(datetime(2025, 8, 5, 12, tzinfo=UTC))
    service = _service(provider, backend, clock)

    first, second = await asyncio.gather(
        service.get_weather(52.52, 13.41),
        service.get_weather(52.52, 13.41),
    )

    assert provider.weather_calls == 1
    assert {first.metadata.cache_status, second.metadata.cache_status} == {"miss", "hit"}
