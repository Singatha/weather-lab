from typing import Any

import httpx
import pytest

from app.core.exceptions import (
    ProviderCircuitOpenError,
    ProviderRateLimitError,
    ProviderRequestRejectedError,
    ProviderResponseError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.providers.open_meteo import OpenMeteoProvider
from app.resilience.circuit_breaker import CircuitBreaker, CircuitState
from app.resilience.retry import RetryPolicy
from tests.fixtures.provider_payloads import forecast_payload, geocoding_payload


def _provider(client: httpx.AsyncClient) -> OpenMeteoProvider:
    return OpenMeteoProvider(
        client,
        forecast_url="https://provider.test/v1/forecast",
        geocoding_url="https://provider.test/v1/search",
        retry_policy=RetryPolicy(max_attempts=1),
    )


@pytest.mark.asyncio
async def test_search_locations_normalizes_provider_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["name"] == "Berlin"
        assert request.url.params["count"] == "10"
        return httpx.Response(200, json=geocoding_payload())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        locations = await _provider(client).search_locations("Berlin")

    assert len(locations) == 1
    assert locations[0].name == "Berlin"
    assert locations[0].country_code == "DE"
    assert locations[0].timezone == "Europe/Berlin"


@pytest.mark.asyncio
async def test_search_locations_returns_empty_list_for_no_matches() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json={}))
    async with httpx.AsyncClient(transport=transport) as client:
        locations = await _provider(client).search_locations("Nowhere")

    assert locations == []


@pytest.mark.asyncio
async def test_get_weather_maps_metric_forecast_in_location_timezone() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["timezone"] == "auto"
        assert request.url.params["forecast_days"] == "7"
        assert request.url.params["temperature_unit"] == "celsius"
        return httpx.Response(200, json=forecast_payload())

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        weather = await _provider(client).get_weather(52.52, 13.41)

    assert weather.location.timezone == "Europe/Berlin"
    assert weather.current.time.isoformat() == "2025-08-05T15:00:00+02:00"
    assert weather.current.condition.category == "clear"
    assert weather.hourly[1].condition.category == "partly_cloudy"
    assert weather.daily[1].condition.category == "rain"
    assert weather.daily[0].sunrise.isoformat() == "2025-08-05T05:31:00+02:00"
    assert weather.units.temperature == "celsius"
    assert weather.metadata.cache_status == "not_cached"


@pytest.mark.asyncio
async def test_get_weather_rejects_misaligned_provider_arrays() -> None:
    payload = forecast_payload()
    hourly = payload["hourly"]
    assert isinstance(hourly, dict)
    temperatures = hourly["temperature_2m"]
    assert isinstance(temperatures, list)
    temperatures.pop()
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json=payload))

    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ProviderResponseError):
            await _provider(client).get_weather(52.52, 13.41)


@pytest.mark.asyncio
async def test_provider_timeout_is_translated() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderTimeoutError):
            await _provider(client).search_locations("Berlin")


@pytest.mark.asyncio
async def test_provider_rate_limit_is_translated() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(429, json={}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ProviderRateLimitError):
            await _provider(client).get_weather(52.52, 13.41)


@pytest.mark.asyncio
async def test_transient_failures_retry_with_exponential_backoff_and_jitter() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            return httpx.Response(503, json={})
        return httpx.Response(200, json=geocoding_payload())

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenMeteoProvider(
            client,
            forecast_url="https://provider.test/v1/forecast",
            geocoding_url="https://provider.test/v1/search",
            retry_policy=RetryPolicy(
                max_attempts=3,
                base_delay_seconds=0.5,
                max_delay_seconds=2,
                jitter_ratio=0.5,
            ),
            sleep=record_sleep,
            randomizer=lambda: 0.4,
        )
        locations = await provider.search_locations("Berlin")

    assert locations[0].name == "Berlin"
    assert attempts == 3
    assert delays == pytest.approx([0.6, 1.2])


@pytest.mark.asyncio
async def test_non_retryable_provider_rejection_is_attempted_once() -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(400, json={})

    async def sleeper(_delay: float) -> None:
        raise AssertionError("non-retryable response must not sleep")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenMeteoProvider(
            client,
            forecast_url="https://provider.test/v1/forecast",
            geocoding_url="https://provider.test/v1/search",
            retry_policy=RetryPolicy(max_attempts=3),
            sleep=sleeper,
        )
        with pytest.raises(ProviderRequestRejectedError):
            await provider.search_locations("Berlin")

    assert attempts == 1


@pytest.mark.asyncio
async def test_exhausted_retries_open_circuit_and_next_call_fails_fast() -> None:
    attempts = 0
    breaker = CircuitBreaker(failure_threshold=1, recovery_timeout_seconds=30)

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, json={})

    async def no_wait(_delay: float) -> None:
        return None

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenMeteoProvider(
            client,
            forecast_url="https://provider.test/v1/forecast",
            geocoding_url="https://provider.test/v1/search",
            retry_policy=RetryPolicy(max_attempts=2, base_delay_seconds=0),
            geocoding_circuit=breaker,
            sleep=no_wait,
        )
        with pytest.raises(ProviderUnavailableError):
            await provider.search_locations("Berlin")
        with pytest.raises(ProviderCircuitOpenError):
            await provider.search_locations("Berlin")

    assert attempts == 2
    assert breaker.state is CircuitState.OPEN


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [[], "invalid", None])
async def test_provider_rejects_non_object_json(payload: Any) -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json=payload))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ProviderResponseError):
            await _provider(client).search_locations("Berlin")
