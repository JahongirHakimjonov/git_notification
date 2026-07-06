from typing import Any

from aiogram.exceptions import TelegramAPIError
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy.exc import SQLAlchemyError


class APIException(Exception):
    status_code: int = 400
    default_code: str = "error"
    default_detail: str = "Something went wrong."

    def __init__(
        self,
        detail: str | None = None,
        code: str | None = None,
        values: dict[str, Any] | None = None,
        status_code: int | None = None,
    ):
        self.detail = detail or self.default_detail
        self.code = code or self.default_code
        self.values = values or {}
        self.status_code = status_code or self.status_code

        super().__init__(self.detail)


def _envelope(status_code: int, detail: str, code: str, variables: dict[str, Any] | None = None) -> JSONResponse:
    """Build the standard error envelope response."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "code": code, "variables": variables or {}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers.

    Covers the domain :class:`APIException`, request validation errors, database
    errors, Telegram API errors, and any otherwise-unhandled exception. All
    responses share the ``{detail, code, variables}`` envelope; server-side
    failures are logged with a stack trace.
    """

    @app.exception_handler(APIException)
    async def _handle_api_exceptions(request: Request, exc: APIException) -> JSONResponse:
        return _envelope(exc.status_code, exc.detail, exc.code, exc.values)

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_errors(request: Request, exc: RequestValidationError) -> JSONResponse:
        return _envelope(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation error.",
            "validation_error",
            {"errors": exc.errors()},
        )

    @app.exception_handler(SQLAlchemyError)
    async def _handle_database_errors(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error while handling {} {}", request.method, request.url.path)
        return _envelope(status.HTTP_500_INTERNAL_SERVER_ERROR, "Database error.", "database_error")

    @app.exception_handler(TelegramAPIError)
    async def _handle_telegram_errors(request: Request, exc: TelegramAPIError) -> JSONResponse:
        logger.exception("Telegram API error while handling {} {}", request.method, request.url.path)
        return _envelope(status.HTTP_502_BAD_GATEWAY, "Telegram API error.", "telegram_error")

    @app.exception_handler(Exception)
    async def _handle_unexpected_errors(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error while handling {} {}", request.method, request.url.path)
        return _envelope(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error.", "internal_error")
