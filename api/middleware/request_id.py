"""
Request ID Middleware

Adds unique request ID to every request for tracing and debugging.
The request ID is:
- Generated for each incoming request
- Added to request.state for use in logging
- Added to response headers for client tracking
"""

import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds a unique request ID to every request.

    The request ID can be used to trace requests through logs and is
    returned to the client in the X-Request-ID header.
    """

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store in request state for use in route handlers and logging
        request.state.request_id = request_id

        # Log request start
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log request completion
            logger.info(
                f"[{request_id}] Completed {request.method} {request.url.path} "
                f"with status {response.status_code}"
            )

            return response

        except Exception as e:
            # Log error with request ID
            logger.error(
                f"[{request_id}] Error processing {request.method} {request.url.path}: {e}",
                exc_info=True
            )
            raise


def get_request_id(request: Request) -> str:
    """
    Get the request ID from the request state.

    Usage in route handlers:
        from api.middleware.request_id import get_request_id

        @router.get("/example")
        async def example(request: Request):
            request_id = get_request_id(request)
            logger.info(f"[{request_id}] Processing example request")
            ...
    """
    return getattr(request.state, "request_id", "unknown")
