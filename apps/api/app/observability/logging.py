import json
import logging
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import Any

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_EXTRA_FIELDS = (
    "method",
    "path",
    "route",
    "status_code",
    "duration_ms",
    "error_code",
    "provider_operation",
)


def bind_request_id(request_id: str) -> Token[str | None]:
    return _request_id.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _request_id.reset(token)


def get_request_id() -> str | None:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    """Render one JSON object per record for log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id is not None:
            payload["request_id"] = request_id
        for field in _EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def configure_logging(level: str) -> None:
    """Configure application logs without altering server-owned loggers."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    application_logger = logging.getLogger("weather")
    application_logger.handlers.clear()
    application_logger.addHandler(handler)
    application_logger.setLevel(level)
    application_logger.propagate = False
