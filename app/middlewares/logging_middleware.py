import time
import uuid

from fastapi import Request, HTTPException
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class StructLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        structlog.contextvars.clear_contextvars()

        request_id = str(uuid.uuid4())
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time

            await logger.ainfo(
                "request_processed",
                status_code=response.status_code,
                duration_ms=round(process_time * 1000, 2),
            )

            return response
        except HTTPException as e:
            process_time = time.perf_counter() - start_time
            await logger.aerror(
                "request_failed",
                exception=str(e.with_traceback()),
                status_code=e.status_code,
                duration_ms=round(process_time * 1000, 2),
                exc_info=True,
            )
            raise
