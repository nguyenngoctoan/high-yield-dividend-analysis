"""
Market Hours Utility Module

Provides utilities for checking if markets are open and determining optimal update times.
"""

import logging
from datetime import datetime, time
from typing import Tuple

logger = logging.getLogger(__name__)


class MarketHours:
    """
    Utilities for checking market hours and determining optimal update times.

    US Stock Market Hours (EST/EDT):
    - Pre-market: 4:00 AM - 9:30 AM
    - Regular: 9:30 AM - 4:00 PM
    - After-hours: 4:00 PM - 8:00 PM
    """

    # Regular market hours (EST/EDT)
    MARKET_OPEN = time(9, 30)   # 9:30 AM
    MARKET_CLOSE = time(16, 0)  # 4:00 PM

    # Extended hours
    PREMARKET_OPEN = time(4, 0)    # 4:00 AM
    AFTERHOURS_CLOSE = time(20, 0) # 8:00 PM

    # Optimal update time (after market close, before EOD processing)
    OPTIMAL_UPDATE_TIME = time(22, 0)  # 10:00 PM EST

    @staticmethod
    def is_weekday(dt: datetime = None) -> bool:
        """
        Check if the given datetime is a weekday (Monday-Friday).

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if weekday, False if weekend
        """
        dt = dt or datetime.now()
        return dt.weekday() < 5  # 0-4 = Mon-Fri

    @staticmethod
    def is_weekend(dt: datetime = None) -> bool:
        """
        Check if the given datetime is a weekend (Saturday-Sunday).

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if weekend, False if weekday
        """
        return not MarketHours.is_weekday(dt)

    @staticmethod
    def is_market_hours(dt: datetime = None) -> bool:
        """
        Check if the given datetime is during regular market hours.

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if during market hours
        """
        dt = dt or datetime.now()

        # Weekend check
        if not MarketHours.is_weekday(dt):
            return False

        # Time check
        current_time = dt.time()
        return MarketHours.MARKET_OPEN <= current_time <= MarketHours.MARKET_CLOSE

    @staticmethod
    def is_extended_hours(dt: datetime = None) -> bool:
        """
        Check if the given datetime is during extended hours (pre-market or after-hours).

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if during extended hours
        """
        dt = dt or datetime.now()

        # Weekend check
        if not MarketHours.is_weekday(dt):
            return False

        # Time check
        current_time = dt.time()
        return (MarketHours.PREMARKET_OPEN <= current_time < MarketHours.MARKET_OPEN or
                MarketHours.MARKET_CLOSE < current_time <= MarketHours.AFTERHOURS_CLOSE)

    @staticmethod
    def is_trading_hours(dt: datetime = None) -> bool:
        """
        Check if the given datetime is during any trading hours (regular + extended).

        Args:
            dt: Datetime to check (default: now)

        Returns:
            True if during trading hours
        """
        dt = dt or datetime.now()

        if not MarketHours.is_weekday(dt):
            return False

        current_time = dt.time()
        return MarketHours.PREMARKET_OPEN <= current_time <= MarketHours.AFTERHOURS_CLOSE

    @staticmethod
    def should_run_daily_update(dt: datetime = None, allow_weekends: bool = False) -> Tuple[bool, str]:
        """
        Determine if daily update should run based on current time and day.

        Args:
            dt: Datetime to check (default: now)
            allow_weekends: Allow updates on weekends (default: False)

        Returns:
            Tuple of (should_run: bool, reason: str)
        """
        dt = dt or datetime.now()
        current_time = dt.time()
        day_name = dt.strftime('%A')

        # Weekend check
        if not allow_weekends and MarketHours.is_weekend(dt):
            return False, f"Weekend ({day_name}) - markets closed"

        # Don't run during market hours (could cause stale data or rate limit issues)
        if MarketHours.is_market_hours(dt):
            return False, f"During market hours ({current_time.strftime('%H:%M')}) - wait until close"

        # Optimal: Run after market close (around 10 PM EST)
        # This allows for EOD data to be available from data providers
        optimal_window_start = time(18, 0)  # 6:00 PM
        optimal_window_end = time(23, 59)   # 11:59 PM

        if optimal_window_start <= current_time <= optimal_window_end:
            return True, f"Optimal time for daily update ({current_time.strftime('%H:%M')})"

        # Early morning updates (before market open) are acceptable
        early_window_start = time(0, 0)   # 12:00 AM
        early_window_end = time(9, 0)     # 9:00 AM

        if early_window_start <= current_time <= early_window_end:
            return True, f"Early morning update ({current_time.strftime('%H:%M')})"

        # During extended hours - can run but not optimal
        if MarketHours.is_extended_hours(dt):
            return True, f"Extended hours ({current_time.strftime('%H:%M')}) - acceptable but not optimal"

        return True, "Outside trading hours - OK to run"

    @staticmethod
    def get_market_status(dt: datetime = None) -> str:
        """
        Get a human-readable market status string.

        Args:
            dt: Datetime to check (default: now)

        Returns:
            Status string (e.g., "Market Open", "Market Closed", "Pre-Market", etc.)
        """
        dt = dt or datetime.now()

        if MarketHours.is_weekend(dt):
            return "Weekend - Markets Closed"

        if MarketHours.is_market_hours(dt):
            return "Market Open (Regular Hours)"

        if MarketHours.is_extended_hours(dt):
            current_time = dt.time()
            if current_time < MarketHours.MARKET_OPEN:
                return "Pre-Market Trading"
            else:
                return "After-Hours Trading"

        return "Markets Closed"

    @staticmethod
    def log_market_status(dt: datetime = None):
        """
        Log the current market status.

        Args:
            dt: Datetime to check (default: now)
        """
        dt = dt or datetime.now()
        status = MarketHours.get_market_status(dt)
        should_run, reason = MarketHours.should_run_daily_update(dt)

        logger.info(f"🕐 Market Status: {status}")
        logger.info(f"🕐 Current Time: {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        if should_run:
            logger.info(f"✅ Update Recommendation: {reason}")
        else:
            logger.info(f"⏸️  Update Recommendation: Skip - {reason}")


# Export main class
__all__ = ['MarketHours']
