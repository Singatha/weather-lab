import json
import logging

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.metrics import router as metrics_router
from app.cache.service import CacheService
from app.core.exceptions import ProviderResponseError, ProviderUnavailableError
from app.observability.logging import JsonFormatter, bind_request_id, reset_request_id
from app.observability.metrics import ObservabilityMetrics
from app.observability.middleware import RequestObservabilityMiddleware, normalized_request_id
from app.providers.open_meteo import OpenMeteoProvider
from app.resilience.retry import RetryPolicy
from app.schemas.location import LocationSearchResponse
from tests.factories import location
from tests.fakes import InMemoryCacheBackend
from tests.fixtures.provider_payloads import geocoding_payload


def test_json_formatter_includes_request_and_diagnostic_context() -> None:
    token = bind_request_id("test-request-42")
    try:
        record = logging.makeLogRecord(
            {
                "name": "weather.test",
                "levelno": logging.INFO,
                "levelname": "INFO",
                "msg": "request_complete",
                "method": "GET",
                "status_code": 200,
            }
        )
        body = json.loads(JsonFormatter().format(record))
    finally:
        reset_request_id(token)

    assert body["event"] == "request_complete"
    assert body["request_id"] == "test-request-42"
    assert body["method"] == "GET"
    assert body["status_code"] == 200
    assert body["timestamp"].endswith("+00:00")


def test_request_id_validation_rejects_unsafe_values() -> None:
    assert normalized_request_id("safe.request-42") == "safe.request-42"
    generated = normalized_request_id("unsafe request\nvalue")
    assert generated != "unsafe request\nvalue"
    assert len(generated) == 36


@pytest.mark.asyncio
async def test_request_middleware_correlates_headers_logs_and_metrics() -> None:
    metrics = ObservabilityMetrics()
    test_app = FastAPI()
    test_app.state.observability_metrics = metrics
    test_app.add_middleware(RequestObservabilityMiddleware, metrics=metrics)
    test_app.include_router(metrics_router)

    @test_app.get("/items/{item_id}")
    async def item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    @test_app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("test failure")

    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        response = await client.get("/items/7", headers={"X-Request-ID": "correlation-7"})
        missing = await client.get("/missing")
        failed = await client.get("/boom", headers={"X-Request-ID": "failure-9"})
        exposition = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "correlation-7"
    assert 'route="/items/{item_id}"' in exposition.text
    assert "weather_http_request_duration_seconds_count" in exposition.text
    assert missing.status_code == 404
    assert failed.status_code == 500
    assert failed.headers["X-Request-ID"] == "failure-9"
    assert failed.json()["error"]["code"] == "INTERNAL_ERROR"
    assert (
        'weather_http_errors_total{method="GET",route="unmatched",status_code="404"} 1.0'
        in exposition.text
    )
    assert exposition.headers["content-type"].startswith("text/plain")


@pytest.mark.asyncio
async def test_cache_results_are_exported_without_cache_keys() -> None:
    metrics = ObservabilityMetrics()
    cache = CacheService(InMemoryCacheBackend(), observability=metrics)
    response = LocationSearchResponse(query="Berlin", locations=[location()])

    await cache.get("location:secret-query", LocationSearchResponse)
    await cache.set(
        "location:secret-query",
        response,
        fresh_ttl_seconds=10,
        retention_ttl_seconds=10,
    )
    await cache.get("location:secret-query", LocationSearchResponse)
    exposition = metrics.render()[0].decode()

    assert 'operation="get",result="miss"' in exposition
    assert 'operation="set",result="success"' in exposition
    assert 'operation="get",result="hit"' in exposition
    assert "secret-query" not in exposition


@pytest.mark.asyncio
async def test_provider_success_and_failure_latency_are_exported() -> None:
    metrics = ObservabilityMetrics()
    responses = iter(
        (
            httpx.Response(200, json=geocoding_payload()),
            httpx.Response(503, json={}),
        )
    )
    transport = httpx.MockTransport(lambda _request: next(responses))
    ticks = iter((1.0, 1.025, 2.0, 2.050))

    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(
            client,
            forecast_url="https://provider.test/forecast",
            geocoding_url="https://provider.test/search",
            retry_policy=RetryPolicy(max_attempts=1),
            observability=metrics,
            clock=lambda: next(ticks),
        )
        await provider.search_locations("Berlin")
        with pytest.raises(ProviderUnavailableError):
            await provider.search_locations("Berlin")

    exposition = metrics.render()[0].decode()
    assert 'operation="geocoding",outcome="success"' in exposition
    assert 'operation="geocoding",outcome="unavailable"' in exposition
    assert "weather_provider_request_duration_seconds_sum" in exposition


@pytest.mark.asyncio
async def test_provider_schema_failure_has_a_failure_outcome() -> None:
    metrics = ObservabilityMetrics()
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"results": "not-a-list"})
    )
    ticks = iter((1.0, 1.01))

    async with httpx.AsyncClient(transport=transport) as client:
        provider = OpenMeteoProvider(
            client,
            forecast_url="https://provider.test/forecast",
            geocoding_url="https://provider.test/search",
            retry_policy=RetryPolicy(max_attempts=1),
            observability=metrics,
            clock=lambda: next(ticks),
        )
        with pytest.raises(ProviderResponseError):
            await provider.search_locations("Berlin")

    exposition = metrics.render()[0].decode()
    assert 'operation="geocoding",outcome="invalid_response"' in exposition
