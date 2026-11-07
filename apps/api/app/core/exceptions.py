from collections.abc import Sequence
from typing import Any


class ApplicationError(Exception):
    """Base exception with an HTTP-safe application error contract."""

    status_code = 500
    code = "INTERNAL_ERROR"
    default_message = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Sequence[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.details = list(details) if details is not None else None


class ProviderError(ApplicationError):
    """Base class for upstream provider failures eligible for stale fallback."""


class ProviderTimeoutError(ProviderError):
    status_code = 504
    code = "WEATHER_PROVIDER_TIMEOUT"
    default_message = "The weather provider took too long to respond."


class ProviderRateLimitError(ProviderError):
    status_code = 503
    code = "WEATHER_PROVIDER_RATE_LIMITED"
    default_message = "The weather provider is temporarily rate limited."


class ProviderUnavailableError(ProviderError):
    status_code = 502
    code = "WEATHER_PROVIDER_UNAVAILABLE"
    default_message = "The weather provider is currently unavailable."


class ProviderResponseError(ProviderError):
    status_code = 502
    code = "INVALID_PROVIDER_RESPONSE"
    default_message = "The weather provider returned an invalid response."
