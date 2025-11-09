"""
Rate Limiting Module

Provides thread-safe rate limiting for API calls to prevent hitting
rate limits on external services (FMP, Alpha Vantage, Yahoo Finance).
"""

import logging
import time
from threading import Semaphore
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe rate limiter using semaphores.

    Limits the number of concurrent requests to an API.
    """

    def __init__(self, max_concurrent: int, name: str = "API"):
        """
        Initialize rate limiter.

        Args:
            max_concurrent: Maximum number of concurrent requests allowed
            name: Name of the API for logging purposes
        """
        self.semaphore = Semaphore(max_concurrent)
        self.max_concurrent = max_concurrent
        self.name = name
        self._acquired_count = 0

    def acquire(self, timeout: Optional[float] = None):
        """
        Acquire the rate limiter (blocks until available).

        Args:
            timeout: Optional timeout in seconds
        """
        acquired = self.semaphore.acquire(timeout=timeout)
        if acquired:
            self._acquired_count += 1
            logger.debug(f"[{self.name}] Rate limiter acquired ({self._acquired_count} active)")
        return acquired

    def release(self):
        """Release the rate limiter."""
        self.semaphore.release()
        self._acquired_count = max(0, self._acquired_count - 1)
        logger.debug(f"[{self.name}] Rate limiter released ({self._acquired_count} active)")

    @contextmanager
    def limit(self):
        """
        Context manager for rate limiting.

        Usage:
            with limiter.limit():
                make_api_call()
        """
        self.acquire()
        try:
            yield
        finally:
            self.release()

    def __enter__(self):
        """Support using as context manager."""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release on context exit."""
        self.release()
        return False


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that backs off when rate limits are hit.

    Automatically adjusts request rate when 429 errors are encountered.
    """

    def __init__(self, max_concurrent: int, name: str = "API",
                 backoff_factor: float = 2.0, max_backoff: float = 60.0):
        """
        Initialize adaptive rate limiter.

        Args:
            max_concurrent: Maximum number of concurrent requests
            name: Name of the API
            backoff_factor: Multiplier for backoff delay
            max_backoff: Maximum backoff delay in seconds
        """
        super().__init__(max_concurrent, name)
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        self._current_backoff = 0.0
        self._consecutive_success = 0
        self._consecutive_failures = 0

    def report_success(self):
        """Report a successful API call."""
        self._consecutive_success += 1
        self._consecutive_failures = 0

        # Gradually reduce backoff on consecutive successes
        if self._consecutive_success >= 10:
            self._current_backoff = max(0, self._current_backoff / self.backoff_factor)
            self._consecutive_success = 0
            if self._current_backoff > 0:
                logger.info(f"[{self.name}] Reducing backoff to {self._current_backoff:.2f}s")

    def report_rate_limit(self):
        """Report a rate limit error (429)."""
        self._consecutive_failures += 1
        self._consecutive_success = 0

        # Increase backoff exponentially
        if self._current_backoff == 0:
            self._current_backoff = 1.0
        else:
            self._current_backoff = min(
                self._current_backoff * self.backoff_factor,
                self.max_backoff
            )

        logger.warning(
            f"[{self.name}] Rate limit hit. Backing off to {self._current_backoff:.2f}s "
            f"({self._consecutive_failures} consecutive failures)"
        )

    def report_error(self):
        """Report a general error."""
        self._consecutive_failures += 1
        self._consecutive_success = 0

    @contextmanager
    def limit(self):
        """Context manager with backoff support."""
        # Apply backoff delay if needed
        if self._current_backoff > 0:
            logger.debug(f"[{self.name}] Applying backoff delay: {self._current_backoff:.2f}s")
            time.sleep(self._current_backoff)

        self.acquire()
        try:
            yield
        finally:
            self.release()


class GlobalRateLimiters:
    """
    Global rate limiter instances for different APIs.

    This provides a singleton-like access to rate limiters.
    """

    _fmp_limiter: Optional[RateLimiter] = None
    _alpha_vantage_limiter: Optional[RateLimiter] = None
    _yahoo_limiter: Optional[RateLimiter] = None

    @classmethod
    def get_fmp_limiter(cls, max_concurrent: int = 144) -> RateLimiter:
        """
        Get FMP rate limiter.

        Args:
            max_concurrent: Max concurrent requests (default: 144 for Ultimate plan)
        """
        if cls._fmp_limiter is None:
            cls._fmp_limiter = AdaptiveRateLimiter(
                max_concurrent=max_concurrent,
                name="FMP",
                backoff_factor=2.0,
                max_backoff=30.0
            )
            logger.info(f"✅ Initialized FMP rate limiter (max_concurrent={max_concurrent})")
        return cls._fmp_limiter

    @classmethod
    def get_alpha_vantage_limiter(cls, max_concurrent: int = 2) -> RateLimiter:
        """
        Get Alpha Vantage rate limiter.

        Args:
            max_concurrent: Max concurrent requests (default: 2 for Premium)
        """
        if cls._alpha_vantage_limiter is None:
            cls._alpha_vantage_limiter = AdaptiveRateLimiter(
                max_concurrent=max_concurrent,
                name="Alpha Vantage",
                backoff_factor=2.0,
                max_backoff=60.0
            )
            logger.info(f"✅ Initialized Alpha Vantage rate limiter (max_concurrent={max_concurrent})")
        return cls._alpha_vantage_limiter

    @classmethod
    def get_yahoo_limiter(cls, max_concurrent: int = 3) -> RateLimiter:
        """
        Get Yahoo Finance rate limiter.

        Args:
            max_concurrent: Max concurrent requests (default: 3)
        """
        if cls._yahoo_limiter is None:
            cls._yahoo_limiter = AdaptiveRateLimiter(
                max_concurrent=max_concurrent,
                name="Yahoo Finance",
                backoff_factor=2.0,
                max_backoff=60.0
            )
            logger.info(f"✅ Initialized Yahoo Finance rate limiter (max_concurrent={max_concurrent})")
        return cls._yahoo_limiter

    @classmethod
    def reset_all(cls):
        """Reset all rate limiters (useful for testing)."""
        cls._fmp_limiter = None
        cls._alpha_vantage_limiter = None
        cls._yahoo_limiter = None
        logger.info("♻️  Reset all rate limiters")


# Convenience function for backward compatibility
def create_rate_limiter(max_concurrent: int, name: str = "API") -> RateLimiter:
    """
    Create a new rate limiter instance.

    Args:
        max_concurrent: Maximum concurrent requests
        name: Name for logging

    Returns:
        RateLimiter instance
    """
    return AdaptiveRateLimiter(max_concurrent=max_concurrent, name=name)


# Export main classes and functions
__all__ = [
    'RateLimiter',
    'AdaptiveRateLimiter',
    'GlobalRateLimiters',
    'create_rate_limiter'
]
