from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_weather_service
from app.cache.service import CacheService
from app.core.exceptions import ProviderCircuitOpenError, ProviderTimeoutError
from app.main import app
from app.providers.base import WeatherProvider
from app.schemas.location import Location
from app.schemas.weather import WeatherResponse
from app.services.weather import WeatherService
from tests.factories import location, weather_response
from tests.fakes import InMemoryCacheBackend


class StubProvider(WeatherProvider):
    async def search_locations(self, query: str, *, limit: int = 10) -> list[Location]:
        del query, limit
        return [location()]

    async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
        del latitude, longitude
        return weather_response()


@pytest_asyncio.fixture
async def api_client() -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_weather_service] = lambda: WeatherService(
        StubProvider(), CacheService(InMemoryCacheBackend())
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


async def test_location_search_endpoint_returns_normalized_results(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/locations/search", params={"q": " Berlin "})

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "Berlin"
    assert body["locations"][0]["country_code"] == "DE"


async def test_weather_endpoint_returns_normalized_forecast(api_client: AsyncClient) -> None:
    response = await api_client.get(
        "/api/v1/weather",
        params={"latitude": 52.52, "longitude": 13.41},
        headers={"X-Request-ID": "api-contract-test"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "api-contract-test"
    body = response.json()
    assert body["current"]["temperature"] == 20
    assert body["daily"][0]["condition"]["category"] == "clear"
    assert body["units"]["wind_speed"] == "km/h"


async def test_invalid_coordinates_use_consistent_error_contract(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/weather", params={"latitude": 91, "longitude": 13.41})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_short_search_query_uses_consistent_error_contract(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/api/v1/locations/search", params={"q": "B"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_provider_timeout_uses_consistent_error_contract(
    api_client: AsyncClient,
) -> None:
    class TimeoutProvider(StubProvider):
        async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
            del latitude, longitude
            raise ProviderTimeoutError()

    app.dependency_overrides[get_weather_service] = lambda: WeatherService(
        TimeoutProvider(), CacheService(InMemoryCacheBackend())
    )
    response = await api_client.get(
        "/api/v1/weather", params={"latitude": 52.52, "longitude": 13.41}
    )

    assert response.status_code == 504
    assert response.json() == {
        "error": {
            "code": "WEATHER_PROVIDER_TIMEOUT",
            "message": "The weather provider took too long to respond.",
        }
    }


async def test_open_circuit_uses_consistent_error_contract(
    api_client: AsyncClient,
) -> None:
    class OpenCircuitProvider(StubProvider):
        async def get_weather(self, latitude: float, longitude: float) -> WeatherResponse:
            del latitude, longitude
            raise ProviderCircuitOpenError()

    app.dependency_overrides[get_weather_service] = lambda: WeatherService(
        OpenCircuitProvider(), CacheService(InMemoryCacheBackend())
    )
    response = await api_client.get(
        "/api/v1/weather", params={"latitude": 52.52, "longitude": 13.41}
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "WEATHER_PROVIDER_CIRCUIT_OPEN"


async def test_openapi_includes_versioned_endpoints_and_rate_limit_responses(
    api_client: AsyncClient,
) -> None:
    response = await api_client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert response.json()["info"]["version"] == "0.7.0"
    assert "/api/v1/locations/search" in paths
    assert "/api/v1/weather" in paths
    assert "429" in paths["/api/v1/weather"]["get"]["responses"]
    assert "/metrics" not in paths
