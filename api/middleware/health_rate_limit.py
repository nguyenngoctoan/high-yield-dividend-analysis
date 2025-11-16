"""
Health Check Rate Limiter
Prevents abuse of health check endpoint with simple in-memory rate limiting.
"""

from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)


class HealthCheckRateLimiter:
    """
    Simple in-memory rate limiter for health checks.

    Limits health check requests per IP address to prevent abuse.
    Uses sliding window algorithm for accurate rate limiting.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window (default: 60)
            window_seconds: Time window in seconds (default: 60)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()

    async def is_allowed(self, client_ip: str) -> bool:
        """
        Check if request from this IP is allowed.

        Args:
            client_ip: Client IP address

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        async with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.window_seconds)

            # Remove old requests outside the window
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > cutoff
            ]

            # Check if limit exceeded
            if len(self.requests[client_ip]) >= self.max_requests:
                logger.warning(
                    f"Health check rate limit exceeded for {client_ip}: "
                    f"{len(self.requests[client_ip])} requests in {self.window_seconds}s"
                )
                return False

            # Add this request
            self.requests[client_ip].append(now)
            return True

    def get_remaining(self, client_ip: str) -> int:
        """
        Get remaining requests for this IP.

        Args:
            client_ip: Client IP address

        Returns:
            Number of requests remaining in current window
        """
        return max(0, self.max_requests - len(self.requests.get(client_ip, [])))


# Global instance (10 requests per minute per IP - reasonable for monitoring tools)
health_limiter = HealthCheckRateLimiter(max_requests=10, window_seconds=60)
