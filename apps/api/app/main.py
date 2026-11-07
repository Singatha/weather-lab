import asyncio
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.cache.backend import RedisCacheBackend
from app.cache.coalescing import RequestCoalescer
from app.cache.service import CacheService
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.providers.open_meteo import OpenMeteoProvider
from app.rate_limit.backend import RedisRateLimitBackend
from app.rate_limit.middleware import RateLimitMiddleware
from app.rate_limit.service import RateLimiter
from app.resilience.circuit_breaker import CircuitBreaker
from app.resilience.retry import RetryPolicy
from app.services.weather import WeatherService


def _build_http_client() -> httpx.AsyncClient:
    settings = get_settings()
    timeout = httpx.Timeout(
        connect=settings.weather_provider_connect_timeout_seconds,
        read=settings.weather_provider_read_timeout_seconds,
        write=settings.weather_provider_write_timeout_seconds,
        pool=settings.weather_provider_pool_timeout_seconds,
    )
    limits = httpx.Limits(
        max_connections=settings.weather_provider_max_connections,
        max_keepalive_connections=settings.weather_provider_max_keepalive_connections,
    )
    return httpx.AsyncClient(timeout=timeout, limits=limits)


def _build_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(
        str(settings.redis_url),
        decode_responses=True,
        socket_connect_timeout=settings.redis_socket_timeout_seconds,
        socket_timeout=settings.redis_socket_timeout_seconds,
        max_connections=settings.redis_max_connections,
    )


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Own and reliably close shared provider and Redis clients."""
    settings = get_settings()
    http_client = _build_http_client()
    cache: CacheService | None = None
    try:
        redis_client = _build_redis_client()
        cache = CacheService(RedisCacheBackend(redis_client))
        retry_policy = RetryPolicy(
            max_attempts=settings.weather_provider_max_attempts,
            base_delay_seconds=settings.weather_provider_retry_base_delay_seconds,
            max_delay_seconds=settings.weather_provider_retry_max_delay_seconds,
            jitter_ratio=settings.weather_provider_retry_jitter_ratio,
        )
        provider = OpenMeteoProvider(
            http_client,
            forecast_url=str(settings.open_meteo_forecast_url),
            geocoding_url=str(settings.open_meteo_geocoding_url),
            retry_policy=retry_policy,
            forecast_circuit=CircuitBreaker(
                failure_threshold=settings.weather_provider_circuit_failure_threshold,
                recovery_timeout_seconds=settings.weather_provider_circuit_recovery_seconds,
            ),
            geocoding_circuit=CircuitBreaker(
                failure_threshold=settings.weather_provider_circuit_failure_threshold,
                recovery_timeout_seconds=settings.weather_provider_circuit_recovery_seconds,
            ),
        )
        application.state.cache_service = cache
        application.state.rate_limiter = RateLimiter(
            RedisRateLimitBackend(redis_client),
            limit=settings.api_rate_limit_requests,
            window_seconds=settings.api_rate_limit_window_seconds,
        )
        application.state.weather_service = WeatherService(
            provider,
            cache,
            location_ttl_seconds=settings.location_cache_ttl_seconds,
            weather_ttl_seconds=settings.weather_cache_ttl_seconds,
            weather_stale_ttl_seconds=settings.weather_cache_stale_ttl_seconds,
            coalescer=RequestCoalescer(),
        )
        yield
    finally:
        close_operations: list[Awaitable[None]] = [http_client.aclose()]
        if cache is not None:
            close_operations.append(cache.aclose())
        await asyncio.gather(*close_operations, return_exceptions=True)
        for attribute in ("weather_service", "rate_limiter", "cache_service"):
            if hasattr(application.state, attribute):
                delattr(application.state, attribute)


def create_app() -> FastAPI:
    """Build the ASGI application and register its dependencies."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.5.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.api_cors_origins],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Accept", "Content-Type"],
    )
    application.include_router(health_router)
    application.include_router(v1_router)
    register_error_handlers(application)
    return application


app = create_app()
