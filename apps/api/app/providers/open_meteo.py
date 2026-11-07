import asyncio
import random
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.exceptions import (
    ProviderRateLimitError,
    ProviderRequestRejectedError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.providers.weather_codes import weather_condition
from app.resilience.circuit_breaker import CircuitBreaker
from app.resilience.retry import RetryPolicy, retry_async
from app.schemas.location import Location
from app.schemas.weather import (
    CurrentWeather,
    DailyForecast,
    HourlyForecast,
    WeatherLocation,
    WeatherMetadata,
    WeatherResponse,
)


class _ProviderModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class _GeocodingResult(_ProviderModel):
    id: int
    name: str
    latitude: float
    longitude: float
    timezone: str | None = None
    country: str | None = None
    country_code: str | None = None
    admin1: str | None = None
    elevation: float | None = None
    population: int | None = None


class _GeocodingResponse(_ProviderModel):
    results: list[_GeocodingResult] = []


class _CurrentPayload(_ProviderModel):
    time: str
    temperature_2m: float
    apparent_temperature: float
    relative_humidity_2m: float
    precipitation: float
    weather_code: int
    wind_speed_10m: float
    is_day: int


class _HourlyPayload(_ProviderModel):
    time: list[str]
    temperature_2m: list[float]
    relative_humidity_2m: list[float]
    precipitation: list[float]
    precipitation_probability: list[float]
    weather_code: list[int]
    wind_speed_10m: list[float]
    is_day: list[int]


class _DailyPayload(_ProviderModel):
    time: list[str]
    temperature_2m_max: list[float]
    temperature_2m_min: list[float]
    precipitation_sum: list[float]
    precipitation_probability_max: list[float]
    weather_code: list[int]
    sunrise: list[str]
    sunset: list[str]


class _ForecastResponse(_ProviderModel):
    latitude: float
    longitude: float
    elevation: float | None = None
    generationtime_ms: float
    utc_offset_seconds: int
    timezone: str
    timezone_abbreviation: str
    current: _CurrentPayload
    hourly: _HourlyPayload
    daily: _DailyPayload


class OpenMeteoProvider:
    """Translate Open-Meteo payloads into application-owned schemas."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        forecast_url: str,
        geocoding_url: str,
        retry_policy: RetryPolicy | None = None,
        forecast_circuit: CircuitBreaker | None = None,
        geocoding_circuit: CircuitBreaker | None = None,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
        randomizer: Callable[[], float] = random.random,
    ) -> None:
        self._client = client
        self._forecast_url = forecast_url
        self._geocoding_url = geocoding_url
        self._retry_policy = retry_policy or RetryPolicy()
        self._forecast_circuit = forecast_circuit or CircuitBreaker()
        self._geocoding_circuit = geocoding_circuit or CircuitBreaker()
        self._sleep = sleep
        self._randomizer = randomizer

    async def search_locations(self, query: str, *, limit: int = 10) -> list[Location]:
        payload = await self._get_json(
            self._geocoding_url,
            params={"name": query, "count": limit, "language": "en", "format": "json"},
            circuit=self._geocoding_circuit,
        )
        try:
            response = _GeocodingResponse.model_validate(payload)
        except ValidationError as exc:
            raise ProviderResponseError() from exc

        locations: list[Location] = []
        for result in response.results:
            if result.country is None or result.country_code is None or result.timezone is None:
                continue
            locations.append(
                Location(
                    id=result.id,
                    name=result.name,
                    country=result.country,
                    country_code=result.country_code.upper(),
                    region=result.admin1 or None,
                    latitude=result.latitude,
                    longitude=result.longitude,
                    timezone=result.timezone,
                    elevation_m=result.elevation,
                    population=result.population,
                )
            )
        return locations

    async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
        payload = await self._get_json(
            self._forecast_url,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "timezone": "auto",
                "forecast_days": 7,
                "temperature_unit": "celsius",
                "wind_speed_unit": "kmh",
                "precipitation_unit": "mm",
                "current": ",".join(
                    (
                        "temperature_2m",
                        "apparent_temperature",
                        "relative_humidity_2m",
                        "precipitation",
                        "weather_code",
                        "wind_speed_10m",
                        "is_day",
                    )
                ),
                "hourly": ",".join(
                    (
                        "temperature_2m",
                        "relative_humidity_2m",
                        "precipitation",
                        "precipitation_probability",
                        "weather_code",
                        "wind_speed_10m",
                        "is_day",
                    )
                ),
                "daily": ",".join(
                    (
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_sum",
                        "precipitation_probability_max",
                        "weather_code",
                        "sunrise",
                        "sunset",
                    )
                ),
            },
            circuit=self._forecast_circuit,
        )
        try:
            response = _ForecastResponse.model_validate(payload)
            timezone = ZoneInfo(response.timezone)
            hourly = self._map_hourly(response.hourly, timezone)
            daily = self._map_daily(response.daily, timezone)
            current = CurrentWeather(
                time=_local_datetime(response.current.time, timezone),
                temperature=response.current.temperature_2m,
                apparent_temperature=response.current.apparent_temperature,
                relative_humidity=round(response.current.relative_humidity_2m),
                precipitation=response.current.precipitation,
                wind_speed=response.current.wind_speed_10m,
                is_day=bool(response.current.is_day),
                condition=weather_condition(response.current.weather_code),
            )
        except (ValidationError, ValueError, ZoneInfoNotFoundError) as exc:
            raise ProviderResponseError() from exc

        return WeatherResponse(
            location=WeatherLocation(
                latitude=response.latitude,
                longitude=response.longitude,
                elevation_m=response.elevation,
                timezone=response.timezone,
                timezone_abbreviation=response.timezone_abbreviation,
                utc_offset_seconds=response.utc_offset_seconds,
            ),
            current=current,
            hourly=hourly,
            daily=daily,
            metadata=WeatherMetadata(
                fetched_at=datetime.now(UTC),
                provider_generation_time_ms=response.generationtime_ms,
            ),
        )

    def _map_hourly(self, payload: _HourlyPayload, timezone: ZoneInfo) -> list[HourlyForecast]:
        arrays: tuple[list[Any], ...] = (
            payload.time,
            payload.temperature_2m,
            payload.relative_humidity_2m,
            payload.precipitation,
            payload.precipitation_probability,
            payload.weather_code,
            payload.wind_speed_10m,
            payload.is_day,
        )
        _require_equal_lengths(arrays)
        return [
            HourlyForecast(
                time=_local_datetime(payload.time[index], timezone),
                temperature=payload.temperature_2m[index],
                relative_humidity=round(payload.relative_humidity_2m[index]),
                precipitation=payload.precipitation[index],
                precipitation_probability=round(payload.precipitation_probability[index]),
                wind_speed=payload.wind_speed_10m[index],
                is_day=bool(payload.is_day[index]),
                condition=weather_condition(payload.weather_code[index]),
            )
            for index in range(len(payload.time))
        ]

    def _map_daily(self, payload: _DailyPayload, timezone: ZoneInfo) -> list[DailyForecast]:
        arrays: tuple[list[Any], ...] = (
            payload.time,
            payload.temperature_2m_max,
            payload.temperature_2m_min,
            payload.precipitation_sum,
            payload.precipitation_probability_max,
            payload.weather_code,
            payload.sunrise,
            payload.sunset,
        )
        _require_equal_lengths(arrays)
        return [
            DailyForecast(
                date=date.fromisoformat(payload.time[index]),
                temperature_max=payload.temperature_2m_max[index],
                temperature_min=payload.temperature_2m_min[index],
                precipitation_sum=payload.precipitation_sum[index],
                precipitation_probability_max=round(payload.precipitation_probability_max[index]),
                sunrise=_local_datetime(payload.sunrise[index], timezone),
                sunset=_local_datetime(payload.sunset[index], timezone),
                condition=weather_condition(payload.weather_code[index]),
            )
            for index in range(len(payload.time))
        ]

    async def _get_json(
        self,
        url: str,
        *,
        params: dict[str, Any],
        circuit: CircuitBreaker,
    ) -> dict[str, Any]:
        await circuit.before_call()
        try:
            payload = await retry_async(
                lambda: self._request_json(url, params=params),
                policy=self._retry_policy,
                is_retryable=_is_retryable,
                sleep=self._sleep,
                randomizer=self._randomizer,
            )
        except Exception as exc:
            if _is_retryable(exc):
                await circuit.record_failure()
            else:
                await circuit.record_success()
            raise
        await circuit.record_success()
        return payload

    async def _request_json(self, url: str, *, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._client.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError() from exc
        except httpx.RequestError as exc:
            raise ProviderUnavailableError() from exc

        if response.status_code == 429:
            raise ProviderRateLimitError()
        if response.status_code in {408, 425} or response.status_code >= 500:
            raise ProviderUnavailableError()
        if response.is_error:
            raise ProviderRequestRejectedError()

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderResponseError() from exc
        if not isinstance(payload, dict):
            raise ProviderResponseError()
        return payload


def _is_retryable(exc: Exception) -> bool:
    return isinstance(
        exc,
        (ProviderTimeoutError, ProviderRateLimitError, ProviderUnavailableError),
    )


def _local_datetime(value: str, timezone: ZoneInfo) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone)
    return parsed.replace(tzinfo=timezone)


def _require_equal_lengths(arrays: tuple[list[Any], ...]) -> None:
    if len({len(values) for values in arrays}) != 1:
        raise ValueError("Provider time-series arrays have different lengths")
