"""
Audit Logging Middleware

Logs all API access to audit_api_access table for security audit trails.
Tracks which API key accessed which endpoint, when, and with what result.
"""

import logging
import time
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import asyncio

from supabase_helpers import get_supabase_admin_client

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all API requests to the audit table.

    Records:
    - user_id (from request.state.user_id set by auth dependency)
    - key_id (from request.state.key_id set by auth dependency)
    - endpoint (request path)
    - method (GET, POST, etc.)
    - status_code (response status)
    - ip_address (client IP)
    - user_agent (User-Agent header)
    - response_time_ms (time taken to process request)
    """

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/login",
            "/callback",
            "/logout",
            "/",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response to audit table"""

        # Skip audit logging for excluded paths
        if self._should_skip_audit(request):
            return await call_next(request)

        # Record request start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Log to audit table in background (don't block response)
        # Use asyncio.create_task to run in background without awaiting
        try:
            asyncio.create_task(
                self._log_to_audit(request, response, response_time_ms)
            )
        except Exception as e:
            logger.error(f"Error creating audit log task: {e}")

        return response

    def _should_skip_audit(self, request: Request) -> bool:
        """Check if this path should be excluded from audit logging"""
        for excluded in self.exclude_paths:
            if excluded == "/" and request.url.path == "/":
                return True
            elif excluded != "/" and request.url.path.startswith(excluded):
                return True
        return False

    async def _log_to_audit(
        self,
        request: Request,
        response: Response,
        response_time_ms: int
    ) -> None:
        """
        Log request to audit table.

        This runs in background and doesn't block the response.
        """
        try:
            # Extract auth info from request state (set by require_api_key dependency)
            user_id = getattr(request.state, "user_id", None)
            key_id = getattr(request.state, "key_id", None)

            # Skip logging if no user_id (unauthenticated request)
            if not user_id:
                logger.debug(f"Skipping audit log for unauthenticated request: {request.url.path}")
                return

            # Get client IP
            client_ip = request.client.host if request.client else "unknown"

            # Get User-Agent
            user_agent = request.headers.get("user-agent", "unknown")

            # Get endpoint path
            endpoint = str(request.url.path)

            # Get method
            method = request.method

            # Get status code
            status_code = response.status_code

            # Prepare audit record
            audit_record = {
                "user_id": user_id,
                "key_id": key_id,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "ip_address": client_ip,
                "user_agent": user_agent,
                "response_time_ms": response_time_ms,
            }

            # Insert to database
            supabase = get_supabase_admin_client()
            result = supabase.table("audit_api_access").insert([audit_record]).execute()

            logger.debug(
                f"Audit logged: user={user_id[:8]}..., "
                f"endpoint={endpoint}, status={status_code}, "
                f"time={response_time_ms}ms"
            )

        except Exception as e:
            logger.error(
                f"Error logging to audit table: {e}",
                exc_info=True
            )
            # Don't raise - this shouldn't block the API response


class AuditLogger:
    """Helper class for manual audit logging"""

    @staticmethod
    async def log_api_access(
        user_id: str,
        key_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> bool:
        """
        Manually log API access to audit table.

        Args:
            user_id: User ID
            key_id: API key ID
            endpoint: Request endpoint path
            method: HTTP method
            status_code: Response status code
            ip_address: Client IP address
            user_agent: User-Agent header
            response_time_ms: Response time in milliseconds

        Returns:
            True if logged successfully, False otherwise
        """
        try:
            audit_record = {
                "user_id": user_id,
                "key_id": key_id,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "ip_address": ip_address or "unknown",
                "user_agent": user_agent or "unknown",
                "response_time_ms": response_time_ms or 0,
            }

            supabase = get_supabase_admin_client()
            result = supabase.table("audit_api_access").insert([audit_record]).execute()

            logger.info(f"Audit logged: {user_id[:8]}... accessed {endpoint}")
            return True

        except Exception as e:
            logger.error(f"Error logging audit record: {e}", exc_info=True)
            return False

    @staticmethod
    async def get_user_audit_log(
        user_id: str,
        limit: int = 100,
        days: int = 30
    ) -> list:
        """
        Get audit log for a user.

        Args:
            user_id: User ID
            limit: Maximum number of records to return
            days: Only return logs from last N days

        Returns:
            List of audit log records
        """
        try:
            from datetime import datetime, timedelta, timezone

            # Calculate date threshold
            threshold_date = (
                datetime.now(timezone.utc) - timedelta(days=days)
            ).isoformat()

            supabase = get_supabase_admin_client()
            result = (
                supabase.table("audit_api_access")
                .select("*")
                .eq("user_id", user_id)
                .gte("request_time", threshold_date)
                .order("request_time", desc=True)
                .limit(limit)
                .execute()
            )

            return result.data or []

        except Exception as e:
            logger.error(f"Error retrieving audit log: {e}", exc_info=True)
            return []

    @staticmethod
    async def get_suspicious_activity(
        hours: int = 24,
        min_failed_requests: int = 10
    ) -> list:
        """
        Get suspicious activity (high rate of failed requests).

        Args:
            hours: Check last N hours
            min_failed_requests: Minimum number of failed requests to flag

        Returns:
            List of suspicious IPs and their failure counts
        """
        try:
            from datetime import datetime, timedelta, timezone

            # Calculate time threshold
            threshold_time = (
                datetime.now(timezone.utc) - timedelta(hours=hours)
            ).isoformat()

            supabase = get_supabase_admin_client()

            # Query for failed requests
            result = (
                supabase.table("audit_api_access")
                .select("ip_address, status_code")
                .gte("request_time", threshold_time)
                .gte("status_code", 400)
                .lt("status_code", 500)  # Client errors (4xx)
                .execute()
            )

            # Aggregate by IP
            ip_failures = {}
            for record in result.data or []:
                ip = record.get("ip_address", "unknown")
                ip_failures[ip] = ip_failures.get(ip, 0) + 1

            # Filter to suspicious ones
            suspicious = [
                {"ip_address": ip, "failed_requests": count}
                for ip, count in ip_failures.items()
                if count >= min_failed_requests
            ]

            return suspicious

        except Exception as e:
            logger.error(f"Error checking suspicious activity: {e}", exc_info=True)
            return []
