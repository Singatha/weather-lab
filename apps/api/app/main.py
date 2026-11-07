from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.providers.open_meteo import OpenMeteoProvider
from app.services.weather import WeatherService


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Own the shared provider client for the duration of the API process."""
    settings = get_settings()
    timeout = httpx.Timeout(settings.weather_provider_timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        application.state.weather_service = WeatherService(
            OpenMeteoProvider(
                client,
                forecast_url=str(settings.open_meteo_forecast_url),
                geocoding_url=str(settings.open_meteo_geocoding_url),
            )
        )
        yield


def create_app() -> FastAPI:
    """Build the ASGI application and register its dependencies."""
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
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
