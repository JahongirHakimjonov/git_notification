import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

# Millisecond conversion factor (avoid magic numbers).
_MS = 1000


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with its method, path, status code and duration."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * _MS
        logger.info(
            "{method} {path} -> {status} ({elapsed:.1f}ms)",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed=elapsed_ms,
        )
        return response
