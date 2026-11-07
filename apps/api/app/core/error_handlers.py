import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import ApplicationError
from app.schemas.errors import ErrorDetail, ErrorEnvelope

logger = logging.getLogger("weather.errors")


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    body = ErrorEnvelope(error=ErrorDetail(code=code, message=message, details=details)).model_dump(
        mode="json", exclude_none=True
    )
    return JSONResponse(status_code=status_code, content=body)


def register_error_handlers(application: FastAPI) -> None:
    """Register the shared JSON error contract for expected API failures."""

    @application.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
        logger.warning(
            "application_error",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": exc.status_code,
                "error_code": exc.code,
            },
        )
        return error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(
            "validation_error",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 422,
                "error_code": "VALIDATION_ERROR",
            },
        )
        details = [
            {
                "location": [str(part) for part in error["loc"]],
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="The request parameters are invalid.",
            details=details,
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unexpected_error",
            exc_info=exc,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "error_code": "INTERNAL_ERROR",
            },
        )
        return error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
        )
