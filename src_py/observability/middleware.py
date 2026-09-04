"""
Request Middleware for FINRES.
Adds request IDs, timing, structured logging, and metrics collection to every request.
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src_py.observability.logging import log_request, get_logger
from src_py.observability.metrics import record_request


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Adds request_id, logs every request, records metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()

        # Attach request_id to request state for downstream handlers
        request.state.request_id = request_id

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = (time.perf_counter() - start) * 1000
            get_logger("finres.api").error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration, 2),
                    "status_code": 500,
                },
                exc_info=True
            )
            raise

        duration = (time.perf_counter() - start) * 1000
        user_id = None
        try:
            user_id = request.cookies.get("finres_user")
        except Exception:
            pass

        log_request(request_id, request.method, request.url.path, response.status_code, duration, user_id)
        record_request(request.method, request.url.path, response.status_code, duration)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = str(round(duration, 2))
        return response
