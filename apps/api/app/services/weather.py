from collections.abc import Callable
from datetime import UTC, datetime
from typing import Literal

from app.cache.coalescing import RequestCoalescer
from app.cache.keys import location_search_cache_key, weather_cache_key
from app.cache.service import CacheLookup, CacheService
from app.core.exceptions import ProviderError
from app.providers.base import WeatherProvider
from app.schemas.location import LocationSearchResponse
from app.schemas.weather import WeatherMetadata, WeatherResponse

CacheStatus = Literal["miss", "hit", "stale", "bypass"]


class WeatherService:
    """Coordinate provider access, caching, and stale-data fallback."""

    def __init__(
        self,
        provider: WeatherProvider,
        cache: CacheService,
        *,
        location_ttl_seconds: int = 86400,
        weather_ttl_seconds: int = 900,
        weather_stale_ttl_seconds: int = 7200,
        coalescer: RequestCoalescer | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._location_ttl_seconds = location_ttl_seconds
        self._weather_ttl_seconds = weather_ttl_seconds
        self._weather_stale_ttl_seconds = weather_stale_ttl_seconds
        self._coalescer = coalescer or RequestCoalescer()
        self._clock = clock or (lambda: datetime.now(UTC))

    async def search_locations(self, query: str) -> LocationSearchResponse:
        normalized_query = query.strip()
        key = location_search_cache_key(normalized_query)
        lookup = await self._cache.get(key, LocationSearchResponse)
        if lookup.state == "fresh" and lookup.value is not None:
            return lookup.value

        async with self._coalescer.hold(key):
            lookup = await self._cache.get(key, LocationSearchResponse)
            if lookup.state == "fresh" and lookup.value is not None:
                return lookup.value

            locations = await self._provider.search_locations(normalized_query)
            response = LocationSearchResponse(query=normalized_query, locations=locations)
            await self._cache.set(
                key,
                response,
                fresh_ttl_seconds=self._location_ttl_seconds,
                retention_ttl_seconds=self._location_ttl_seconds,
            )
            return response

    async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
        key = weather_cache_key(latitude, longitude)
        lookup = await self._cache.get(key, WeatherResponse)
        if lookup.state == "fresh" and lookup.value is not None:
            return _with_cache_metadata(lookup.value, status="hit")
        stale = _stale_value(lookup)

        async with self._coalescer.hold(key):
            lookup = await self._cache.get(key, WeatherResponse)
            if lookup.state == "fresh" and lookup.value is not None:
                return _with_cache_metadata(lookup.value, status="hit")
            stale = _stale_value(lookup) or stale

            try:
                response = await self._provider.get_weather(latitude, longitude)
            except ProviderError:
                if stale is not None:
                    return _with_cache_metadata(stale, status="stale")
                raise

            cached_at = self._clock()
            cache_candidate = _with_cache_metadata(
                response,
                status="miss",
                cached_at=cached_at,
            )
            stored = await self._cache.set(
                key,
                cache_candidate,
                fresh_ttl_seconds=self._weather_ttl_seconds,
                retention_ttl_seconds=self._weather_stale_ttl_seconds,
            )
            if stored:
                return cache_candidate
            return _with_cache_metadata(response, status="bypass")


def _stale_value(lookup: CacheLookup[WeatherResponse]) -> WeatherResponse | None:
    if lookup.state == "stale":
        return lookup.value
    return None


def _with_cache_metadata(
    response: WeatherResponse,
    *,
    status: CacheStatus,
    cached_at: datetime | None = None,
) -> WeatherResponse:
    existing = response.metadata
    metadata = WeatherMetadata(
        provider=existing.provider,
        fetched_at=existing.fetched_at,
        provider_generation_time_ms=existing.provider_generation_time_ms,
        cache_status=status,
        is_stale=status == "stale",
        cached_at=cached_at if cached_at is not None else existing.cached_at,
    )
    return response.model_copy(update={"metadata": metadata})
