from typing import Any

import httpx
import pytest

from app.core.exceptions import (
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.providers.open_meteo import OpenMeteoProvider
from tests.fixtures.provider_payloads import forecast_payload, geocoding_payload


def _provider(client: httpx.AsyncClient) -> OpenMeteoProvider:
    return OpenMeteoProvider(
        client,
        forecast_url="https://provider.test/v1/forecast",
        geocoding_url="https://provider.test/v1/search",
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
@pytest.mark.parametrize("payload", [[], "invalid", None])
async def test_provider_rejects_non_object_json(payload: Any) -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json=payload))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(ProviderResponseError):
            await _provider(client).search_locations("Berlin")
