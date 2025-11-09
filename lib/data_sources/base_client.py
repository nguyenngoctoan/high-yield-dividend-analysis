"""
Base Data Source Client

Abstract base class for all data source clients with common functionality
like retry logic, error handling, and rate limiting.
"""

import logging
import time
import requests
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime, date

from lib.core.rate_limiters import RateLimiter

logger = logging.getLogger(__name__)


class DataSourceClient(ABC):
    """
    Abstract base class for all data source clients.

    Provides common functionality:
    - Rate limiting
    - Retry logic with exponential backoff
    - Error handling and logging
    - Response parsing
    """

    def __init__(self, name: str, rate_limiter: Optional[RateLimiter] = None,
                 timeout: int = 30, max_retries: int = 3):
        """
        Initialize the data source client.

        Args:
            name: Name of the data source (for logging)
            rate_limiter: Optional rate limiter instance
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.name = name
        self.rate_limiter = rate_limiter
        self.timeout = timeout
        self.max_retries = max_retries
        self._stats = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'rate_limits': 0
        }

    def _fetch_with_retry(self, url: str, symbol: Optional[str] = None,
                         params: Optional[Dict] = None) -> Optional[Any]:
        """
        Fetch data with retry logic and rate limiting.

        Args:
            url: URL to fetch
            symbol: Optional symbol for logging context
            params: Optional query parameters

        Returns:
            Parsed JSON response or None on failure
        """
        self._stats['requests'] += 1

        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting if configured
                if self.rate_limiter:
                    self.rate_limiter.acquire()

                try:
                    response = requests.get(url, params=params, timeout=self.timeout)
                finally:
                    if self.rate_limiter:
                        self.rate_limiter.release()

                # Handle different response codes
                if response.status_code == 200:
                    self._stats['successes'] += 1
                    # Report success to adaptive rate limiter
                    if hasattr(self.rate_limiter, 'report_success'):
                        self.rate_limiter.report_success()
                    return response.json()

                elif response.status_code == 429:
                    # Rate limited
                    self._stats['rate_limits'] += 1
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"[{self.name}] Rate limited, waiting {wait_time}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    # Report to adaptive rate limiter
                    if hasattr(self.rate_limiter, 'report_rate_limit'):
                        self.rate_limiter.report_rate_limit()
                    time.sleep(wait_time)

                elif response.status_code == 404:
                    # Not found - expected for invalid symbols
                    symbol_info = f" for {symbol}" if symbol else ""
                    logger.debug(f"[{self.name}] Not found (404){symbol_info}")
                    self._stats['failures'] += 1
                    return None

                elif response.status_code == 401:
                    # Authentication error
                    symbol_info = f" for {symbol}" if symbol else ""
                    logger.warning(f"[{self.name}] Authentication failed (401){symbol_info}")
                    self._stats['failures'] += 1
                    return None

                else:
                    # Other error
                    symbol_info = f" for {symbol}" if symbol else ""
                    logger.error(
                        f"[{self.name}] HTTP {response.status_code}{symbol_info}: "
                        f"{response.text[:200]}"
                    )
                    self._stats['failures'] += 1

            except requests.exceptions.Timeout:
                symbol_info = f" for {symbol}" if symbol else ""
                logger.error(
                    f"[{self.name}] Timeout after {self.timeout}s{symbol_info} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

            except Exception as e:
                symbol_info = f" for {symbol}" if symbol else ""
                logger.error(
                    f"[{self.name}] Request failed{symbol_info}: {e} "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )
                # Report error to adaptive rate limiter
                if hasattr(self.rate_limiter, 'report_error'):
                    self.rate_limiter.report_error()
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        self._stats['failures'] += 1
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        stats = self._stats.copy()
        if stats['requests'] > 0:
            stats['success_rate'] = f"{(stats['successes'] / stats['requests']) * 100:.2f}%"
        else:
            stats['success_rate'] = "N/A"
        return stats

    def reset_stats(self):
        """Reset client statistics."""
        self._stats = {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'rate_limits': 0
        }

    # Abstract methods that must be implemented by subclasses

    @abstractmethod
    def fetch_prices(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch price data for a symbol.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date for historical data

        Returns:
            Dictionary with price data or None
        """
        pass

    @abstractmethod
    def fetch_dividends(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch dividend data for a symbol.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date for historical data

        Returns:
            Dictionary with dividend data or None
        """
        pass

    @abstractmethod
    def fetch_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company/ETF information.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Dictionary with company info or None
        """
        pass

    @abstractmethod
    def discover_symbols(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discover available symbols from this data source.

        Args:
            limit: Optional limit on number of symbols to return

        Returns:
            List of symbol dictionaries
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this data source is available and properly configured.

        Returns:
            True if available, False otherwise
        """
        pass


class DataSourceResponse:
    """
    Standardized response wrapper for data source operations.

    Provides consistent structure for all data source responses.
    """

    def __init__(self, source: str, success: bool, data: Optional[Any] = None,
                 error: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Initialize response.

        Args:
            source: Name of data source
            success: Whether operation was successful
            data: Response data (if successful)
            error: Error message (if failed)
            metadata: Additional metadata
        """
        self.source = source
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source': self.source,
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def success_response(cls, source: str, data: Any, **metadata) -> 'DataSourceResponse':
        """Create a success response."""
        return cls(source=source, success=True, data=data, metadata=metadata)

    @classmethod
    def error_response(cls, source: str, error: str, **metadata) -> 'DataSourceResponse':
        """Create an error response."""
        return cls(source=source, success=False, error=error, metadata=metadata)


# Export main classes
__all__ = ['DataSourceClient', 'DataSourceResponse']
