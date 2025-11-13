"""
Rate limiting middleware for the Dividend API.

Implements token bucket rate limiting with Redis backend (or in-memory fallback).
"""

from fastapi import Request, HTTPException, status
from typing import Dict, Optional
import time
from collections import defaultdict
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter with multiple time windows.

    Supports per-minute, per-hour, and per-day rate limiting.
    Uses in-memory storage (can be upgraded to Redis for distributed systems).
    """

    def __init__(self):
        """Initialize the rate limiter with storage dictionaries."""
        self._buckets: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: {"tokens": 0, "last_update": time.time()})
        )
        self._lock = Lock()

    def _get_bucket_key(self, identifier: str, window: str) -> str:
        """
        Generate a unique bucket key for identifier and time window.

        Args:
            identifier: User/API key identifier
            window: Time window (minute, hour, day)

        Returns:
            Unique bucket key
        """
        return f"{identifier}:{window}"

    def _refill_tokens(
        self,
        bucket: Dict[str, float],
        max_tokens: int,
        refill_rate: float,
        now: float
    ) -> None:
        """
        Refill tokens in a bucket based on elapsed time.

        Args:
            bucket: The token bucket dictionary
            max_tokens: Maximum tokens in the bucket
            refill_rate: Tokens added per second
            now: Current timestamp
        """
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(
            max_tokens,
            bucket["tokens"] + (elapsed * refill_rate)
        )
        bucket["last_update"] = now

    async def check_rate_limit(
        self,
        identifier: str,
        limits: Dict[str, int]
    ) -> Dict[str, any]:
        """
        Check if a request should be rate limited.

        Args:
            identifier: Unique identifier for the user/API key
            limits: Dictionary with rate limit configuration
                   {
                       "requests_per_minute": 60,
                       "requests_per_hour": 1000,
                       "requests_per_day": 10000
                   }

        Returns:
            Dictionary with rate limit status:
            {
                "allowed": bool,
                "limit": int,
                "remaining": int,
                "reset": float (unix timestamp)
            }

        Raises:
            HTTPException: If rate limit is exceeded
        """
        now = time.time()

        # Define time windows and their configurations
        windows = {
            "minute": {
                "limit": limits.get("requests_per_minute", 60),
                "window_seconds": 60,
                "reset_window": 60
            },
            "hour": {
                "limit": limits.get("requests_per_hour", 1000),
                "window_seconds": 3600,
                "reset_window": 3600
            },
            "day": {
                "limit": limits.get("requests_per_day", 10000),
                "window_seconds": 86400,
                "reset_window": 86400
            }
        }

        with self._lock:
            # Check each time window
            for window_name, config in windows.items():
                bucket_key = self._get_bucket_key(identifier, window_name)
                bucket = self._buckets[identifier][window_name]

                # Initialize bucket if needed
                if bucket["tokens"] == 0 and bucket["last_update"] == now:
                    bucket["tokens"] = config["limit"]

                # Refill tokens based on elapsed time
                refill_rate = config["limit"] / config["window_seconds"]
                self._refill_tokens(bucket, config["limit"], refill_rate, now)

                # Check if we have tokens available
                if bucket["tokens"] < 1:
                    reset_time = bucket["last_update"] + (
                        (1 - bucket["tokens"]) / refill_rate
                    )

                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": {
                                "type": "rate_limit_error",
                                "message": f"Rate limit exceeded for {window_name} window. "
                                          f"Limit: {config['limit']} requests per {window_name}.",
                                "code": "rate_limit_exceeded"
                            }
                        },
                        headers={
                            "X-RateLimit-Limit": str(config["limit"]),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(reset_time)),
                            "Retry-After": str(int(reset_time - now))
                        }
                    )

                # Consume one token
                bucket["tokens"] -= 1

            # Return rate limit info for the minute window (most restrictive)
            minute_bucket = self._buckets[identifier]["minute"]
            minute_config = windows["minute"]

            return {
                "allowed": True,
                "limit": minute_config["limit"],
                "remaining": int(minute_bucket["tokens"]),
                "reset": int(minute_bucket["last_update"] + minute_config["reset_window"])
            }

    def get_rate_limit_headers(self, rate_limit_info: Dict[str, any]) -> Dict[str, str]:
        """
        Generate rate limit headers for the response.

        Args:
            rate_limit_info: Rate limit information from check_rate_limit

        Returns:
            Dictionary of HTTP headers
        """
        return {
            "X-RateLimit-Limit": str(rate_limit_info["limit"]),
            "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
            "X-RateLimit-Reset": str(rate_limit_info["reset"])
        }


# Global rate limiter instance
_rate_limiter = RateLimiter()


async def rate_limit_middleware(
    request: Request,
    user_info: Optional[Dict[str, any]] = None
) -> Dict[str, any]:
    """
    Middleware function to enforce rate limiting.

    Args:
        request: The FastAPI request
        user_info: User information from authentication (optional)

    Returns:
        Rate limit information to add to response headers
    """
    # Get identifier (API key ID or IP address)
    if user_info and user_info.get("api_key_id"):
        identifier = f"api_key:{user_info['api_key_id']}"
        limits = user_info.get("rate_limit", {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        })
    else:
        # Use IP address for unauthenticated requests
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"
        limits = {
            "requests_per_minute": 20,
            "requests_per_hour": 200,
            "requests_per_day": 1000
        }

    # Check rate limit
    rate_limit_info = await _rate_limiter.check_rate_limit(identifier, limits)

    return rate_limit_info
