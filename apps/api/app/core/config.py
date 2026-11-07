from functools import lru_cache
from typing import Literal

from pydantic import (
    AnyHttpUrl,
    Field,
    NonNegativeFloat,
    PositiveFloat,
    PositiveInt,
    RedisDsn,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration sourced from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "Weather API"
    api_cors_origins: list[AnyHttpUrl] = Field(
        default_factory=lambda: [AnyHttpUrl("http://localhost:5173")]
    )
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    redis_socket_timeout_seconds: PositiveFloat = 1.0
    redis_max_connections: PositiveInt = 20
    location_cache_ttl_seconds: PositiveInt = 86400
    weather_cache_ttl_seconds: PositiveInt = 900
    weather_cache_stale_ttl_seconds: PositiveInt = 7200
    open_meteo_forecast_url: AnyHttpUrl = AnyHttpUrl("https://api.open-meteo.com/v1/forecast")
    open_meteo_geocoding_url: AnyHttpUrl = AnyHttpUrl(
        "https://geocoding-api.open-meteo.com/v1/search"
    )
    weather_provider_connect_timeout_seconds: PositiveFloat = 3.0
    weather_provider_read_timeout_seconds: PositiveFloat = 10.0
    weather_provider_write_timeout_seconds: PositiveFloat = 5.0
    weather_provider_pool_timeout_seconds: PositiveFloat = 3.0
    weather_provider_max_connections: PositiveInt = 20
    weather_provider_max_keepalive_connections: PositiveInt = 10
    weather_provider_max_attempts: PositiveInt = 3
    weather_provider_retry_base_delay_seconds: NonNegativeFloat = 0.2
    weather_provider_retry_max_delay_seconds: PositiveFloat = 2.0
    weather_provider_retry_jitter_ratio: float = Field(default=0.25, ge=0, le=1)
    weather_provider_circuit_failure_threshold: PositiveInt = 5
    weather_provider_circuit_recovery_seconds: PositiveFloat = 30.0
    api_rate_limit_requests: PositiveInt = 60
    api_rate_limit_window_seconds: PositiveInt = 60

    @model_validator(mode="after")
    def validate_cache_ttls(self) -> "Settings":
        if self.weather_cache_stale_ttl_seconds < self.weather_cache_ttl_seconds:
            raise ValueError(
                "weather_cache_stale_ttl_seconds must be greater than or equal to "
                "weather_cache_ttl_seconds"
            )
        if (
            self.weather_provider_retry_max_delay_seconds
            < self.weather_provider_retry_base_delay_seconds
        ):
            raise ValueError(
                "weather_provider_retry_max_delay_seconds must be greater than or equal to "
                "weather_provider_retry_base_delay_seconds"
            )
        if self.weather_provider_max_keepalive_connections > self.weather_provider_max_connections:
            raise ValueError(
                "weather_provider_max_keepalive_connections must not exceed "
                "weather_provider_max_connections"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""
    return Settings()
