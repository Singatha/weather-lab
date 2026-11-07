from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.error_handlers import error_response
from app.core.exceptions import RateLimitExceededError
from app.rate_limit.service import RateLimitDecision, RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Limit versioned API requests by direct client address."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        limiter = getattr(request.app.state, "rate_limiter", None)
        if not isinstance(limiter, RateLimiter):
            return await call_next(request)

        identity = request.client.host if request.client is not None else "unknown"
        decision = await limiter.check(identity)
        response: Response
        if not decision.allowed:
            error = RateLimitExceededError()
            response = error_response(
                status_code=error.status_code,
                code=error.code,
                message=error.message,
            )
        else:
            response = await call_next(request)

        _set_headers(response, decision)
        return response


def _set_headers(response: Response, decision: RateLimitDecision) -> None:
    response.headers["X-RateLimit-Limit"] = str(decision.limit)
    response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
    response.headers["X-RateLimit-Reset"] = str(decision.retry_after_seconds)
    if not decision.allowed:
        response.headers["Retry-After"] = str(decision.retry_after_seconds)
