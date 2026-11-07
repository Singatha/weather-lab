from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import ApplicationError
from app.schemas.errors import ErrorDetail, ErrorEnvelope


def _error_response(
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
    async def application_error_handler(_request: Request, exc: ApplicationError) -> JSONResponse:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "location": [str(part) for part in error["loc"]],
                "message": error["msg"],
                "type": error["type"],
            }
            for error in exc.errors()
        ]
        return _error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="The request parameters are invalid.",
            details=details,
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return _error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
        )
