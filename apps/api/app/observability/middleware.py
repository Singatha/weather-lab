import logging
import re
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.error_handlers import error_response
from app.observability.logging import bind_request_id, reset_request_id
from app.observability.metrics import ObservabilityMetrics

logger = logging.getLogger("weather.http")
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def normalized_request_id(value: str | None) -> str:
    if value is not None and _REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid4())


class RequestObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, *, metrics: ObservabilityMetrics) -> None:
        super().__init__(app)
        self._metrics = metrics

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = normalized_request_id(request.headers.get("X-Request-ID"))
        token = bind_request_id(request_id)
        started = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception:
            logger.exception(
                "request_failed",
                extra={"method": request.method, "path": request.url.path},
            )
            response = error_response(
                status_code=500,
                code="INTERNAL_ERROR",
                message="An unexpected error occurred.",
            )
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_seconds = perf_counter() - started
            route = _route_template(request)
            if request.url.path != "/metrics":
                self._metrics.observe_http(
                    method=request.method,
                    route=route,
                    status_code=status_code,
                    duration_seconds=duration_seconds,
                )
            logger.info(
                "request_complete",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "route": route,
                    "status_code": status_code,
                    "duration_ms": round(duration_seconds * 1000, 3),
                },
            )
            reset_request_id(token)


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    return template if isinstance(template, str) else "unmatched"
