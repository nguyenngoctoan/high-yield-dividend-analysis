"""
Data Source Tracker Module

Tracks which data sources have specific data types for each symbol
to avoid redundant API calls and optimize data fetching.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta

from supabase_helpers import supabase_raw_query, supabase_select

logger = logging.getLogger(__name__)


class DataType(str, Enum):
    """Supported data types for tracking."""
    AUM = "aum"
    DIVIDENDS = "dividends"
    VOLUME = "volume"
    IV = "iv"
    PRICES = "prices"
    COMPANY_INFO = "company_info"


class DataSource(str, Enum):
    """Supported data sources."""
    FMP = "FMP"
    ALPHA_VANTAGE = "AlphaVantage"
    YAHOO = "Yahoo"


# Priority order for data sources (lower number = higher priority)
SOURCE_PRIORITY = {
    DataSource.FMP: 1,
    DataSource.YAHOO: 2,
    DataSource.ALPHA_VANTAGE: 3
}


class DataSourceTracker:
    """
    Tracks data source availability for symbols.

    Features:
    - Records which sources have which data types
    - Provides preferred source lookup
    - Avoids redundant API calls
    - Tracks fetch success/failure history
    """

    def __init__(self):
        """Initialize data source tracker."""
        self.cache = {}  # In-memory cache for session
        self.cache_ttl = timedelta(hours=1)  # Cache for 1 hour

    def record_check(self,
                    symbol: str,
                    data_type: DataType,
                    source: DataSource,
                    has_data: bool,
                    notes: Optional[str] = None) -> bool:
        """
        Record the result of checking a data source.

        Args:
            symbol: Stock/ETF symbol
            data_type: Type of data checked
            source: Data source checked
            has_data: Whether the source has this data
            notes: Optional notes or error messages

        Returns:
            True if recorded successfully
        """
        try:
            query = """
                SELECT record_data_source_check(%s, %s, %s, %s, %s)
            """
            params = (symbol, data_type.value, source.value, has_data, notes)

            result = supabase_raw_query(query, params)

            if result:
                logger.debug(
                    f"[SourceTracker] {symbol}/{data_type.value}/{source.value}: "
                    f"{'HAS' if has_data else 'NO'} data"
                )
                # Update cache
                cache_key = f"{symbol}:{data_type.value}"
                if cache_key in self.cache:
                    del self.cache[cache_key]
                return True

        except Exception as e:
            logger.error(
                f"[SourceTracker] Failed to record check for {symbol}/{data_type.value}: {e}"
            )

        return False

    def get_preferred_source(self,
                           symbol: str,
                           data_type: DataType,
                           use_cache: bool = True) -> Optional[DataSource]:
        """
        Get the preferred data source for a symbol and data type.

        Args:
            symbol: Stock/ETF symbol
            data_type: Type of data needed
            use_cache: Use cached result if available

        Returns:
            Preferred DataSource or None if no source has this data
        """
        cache_key = f"{symbol}:{data_type.value}"

        # Check cache
        if use_cache and cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                logger.debug(f"[SourceTracker] Cache hit for {cache_key}: {cached_data}")
                return cached_data

        try:
            query = """
                SELECT preferred_source
                FROM v_data_source_preferences
                WHERE symbol = %s AND data_type = %s
            """
            params = (symbol, data_type.value)

            result = supabase_raw_query(query, params)

            if result and len(result) > 0:
                source_str = result[0].get('preferred_source')
                if source_str:
                    source = DataSource(source_str)
                    # Cache result
                    self.cache[cache_key] = (source, datetime.now())
                    logger.debug(
                        f"[SourceTracker] Preferred source for {symbol}/{data_type.value}: {source.value}"
                    )
                    return source

        except Exception as e:
            logger.debug(
                f"[SourceTracker] Error getting preferred source for {symbol}/{data_type.value}: {e}"
            )

        # Cache negative result
        self.cache[cache_key] = (None, datetime.now())
        return None

    def get_available_sources(self,
                            symbol: str,
                            data_type: DataType) -> List[DataSource]:
        """
        Get all available sources for a symbol and data type.

        Args:
            symbol: Stock/ETF symbol
            data_type: Type of data needed

        Returns:
            List of DataSource objects that have this data
        """
        try:
            query = """
                SELECT source
                FROM divv_data_source_tracking
                WHERE symbol = %s
                  AND data_type = %s
                  AND has_data = true
                ORDER BY
                    CASE source
                        WHEN 'FMP' THEN 1
                        WHEN 'Yahoo' THEN 2
                        WHEN 'AlphaVantage' THEN 3
                        ELSE 4
                    END,
                    last_successful_fetch_at DESC NULLS LAST
            """
            params = (symbol, data_type.value)

            result = supabase_raw_query(query, params)

            if result:
                sources = [DataSource(row['source']) for row in result]
                logger.debug(
                    f"[SourceTracker] Available sources for {symbol}/{data_type.value}: "
                    f"{[s.value for s in sources]}"
                )
                return sources

        except Exception as e:
            logger.debug(
                f"[SourceTracker] Error getting available sources for {symbol}/{data_type.value}: {e}"
            )

        return []

    def has_been_checked(self,
                        symbol: str,
                        data_type: DataType,
                        source: DataSource,
                        max_age_days: int = 30) -> bool:
        """
        Check if a source has been checked recently.

        Args:
            symbol: Stock/ETF symbol
            data_type: Type of data
            source: Data source
            max_age_days: Maximum age of check in days

        Returns:
            True if checked within max_age_days
        """
        try:
            query = """
                SELECT last_checked_at
                FROM divv_data_source_tracking
                WHERE symbol = %s
                  AND data_type = %s
                  AND source = %s
                  AND last_checked_at > NOW() - INTERVAL '%s days'
            """
            params = (symbol, data_type.value, source.value, max_age_days)

            result = supabase_raw_query(query, params)

            if result and len(result) > 0:
                logger.debug(
                    f"[SourceTracker] {symbol}/{data_type.value}/{source.value} "
                    f"was checked recently"
                )
                return True

        except Exception as e:
            logger.debug(
                f"[SourceTracker] Error checking if source was checked: {e}"
            )

        return False

    def discover_and_record(self,
                          symbol: str,
                          data_type: DataType,
                          sources_to_try: Optional[List[DataSource]] = None,
                          fetch_callbacks: Optional[Dict[DataSource, callable]] = None
                          ) -> Optional[Tuple[DataSource, Any]]:
        """
        Try multiple sources to find data and record results.

        Args:
            symbol: Stock/ETF symbol
            data_type: Type of data to find
            sources_to_try: List of sources to try (default: all in priority order)
            fetch_callbacks: Dict mapping source to fetch function

        Returns:
            Tuple of (source, data) if found, None otherwise
        """
        if sources_to_try is None:
            sources_to_try = [DataSource.FMP, DataSource.YAHOO, DataSource.ALPHA_VANTAGE]

        if fetch_callbacks is None:
            logger.error("[SourceTracker] No fetch callbacks provided")
            return None

        # Sort sources by priority
        sources_to_try = sorted(
            sources_to_try,
            key=lambda s: SOURCE_PRIORITY.get(s, 99)
        )

        logger.info(
            f"[SourceTracker] Discovering {data_type.value} for {symbol} "
            f"across {len(sources_to_try)} sources"
        )

        for source in sources_to_try:
            # Skip if we already know this source doesn't have the data
            if self.has_been_checked(symbol, data_type, source, max_age_days=7):
                available = self.get_available_sources(symbol, data_type)
                if source not in available:
                    logger.debug(
                        f"[SourceTracker] Skipping {source.value} for {symbol}/{data_type.value} "
                        f"(checked recently, no data)"
                    )
                    continue

            # Get fetch callback for this source
            fetch_fn = fetch_callbacks.get(source)
            if not fetch_fn:
                logger.debug(f"[SourceTracker] No fetch callback for {source.value}")
                continue

            try:
                logger.debug(
                    f"[SourceTracker] Trying {source.value} for {symbol}/{data_type.value}"
                )
                data = fetch_fn(symbol)

                if data:
                    # Success! Record and return
                    self.record_check(symbol, data_type, source, True)
                    logger.info(
                        f"✅ [SourceTracker] Found {data_type.value} for {symbol} "
                        f"from {source.value}"
                    )
                    return (source, data)
                else:
                    # No data from this source
                    self.record_check(
                        symbol, data_type, source, False,
                        notes=f"No {data_type.value} data available"
                    )

            except Exception as e:
                # Error fetching from this source
                self.record_check(
                    symbol, data_type, source, False,
                    notes=f"Error: {str(e)[:200]}"
                )
                logger.debug(
                    f"[SourceTracker] Error with {source.value} for {symbol}/{data_type.value}: {e}"
                )

        logger.warning(
            f"❌ [SourceTracker] No source found with {data_type.value} for {symbol}"
        )
        return None

    def get_statistics(self, data_type: Optional[DataType] = None) -> Dict[str, Any]:
        """
        Get tracking statistics.

        Args:
            data_type: Optional filter by data type

        Returns:
            Dictionary with statistics
        """
        try:
            if data_type:
                query = """
                    SELECT
                        source,
                        COUNT(*) as total_checks,
                        COUNT(*) FILTER (WHERE has_data = true) as successful,
                        COUNT(*) FILTER (WHERE has_data = false) as unsuccessful,
                        COUNT(DISTINCT symbol) as unique_symbols
                    FROM divv_data_source_tracking
                    WHERE data_type = %s
                    GROUP BY source
                    ORDER BY source
                """
                params = (data_type.value,)
            else:
                query = """
                    SELECT
                        data_type,
                        source,
                        COUNT(*) as total_checks,
                        COUNT(*) FILTER (WHERE has_data = true) as successful,
                        COUNT(*) FILTER (WHERE has_data = false) as unsuccessful,
                        COUNT(DISTINCT symbol) as unique_symbols
                    FROM divv_data_source_tracking
                    GROUP BY data_type, source
                    ORDER BY data_type, source
                """
                params = ()

            result = supabase_raw_query(query, params)

            if result:
                return {'stats': result, 'count': len(result)}

        except Exception as e:
            logger.error(f"[SourceTracker] Error getting statistics: {e}")

        return {'stats': [], 'count': 0}

    def clear_cache(self):
        """Clear the in-memory cache."""
        self.cache.clear()
        logger.debug("[SourceTracker] Cache cleared")


# Global tracker instance
_global_tracker = None


def get_tracker() -> DataSourceTracker:
    """Get the global data source tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = DataSourceTracker()
    return _global_tracker


# Convenience functions
def record_check(symbol: str, data_type: DataType, source: DataSource,
                has_data: bool, notes: Optional[str] = None) -> bool:
    """Quick function to record a data source check."""
    return get_tracker().record_check(symbol, data_type, source, has_data, notes)


def get_preferred_source(symbol: str, data_type: DataType) -> Optional[DataSource]:
    """Quick function to get preferred source."""
    return get_tracker().get_preferred_source(symbol, data_type)


def discover_and_record(symbol: str, data_type: DataType,
                       sources_to_try: Optional[List[DataSource]] = None,
                       fetch_callbacks: Optional[Dict[DataSource, callable]] = None
                       ) -> Optional[Tuple[DataSource, Any]]:
    """Quick function to discover and record data source."""
    return get_tracker().discover_and_record(
        symbol, data_type, sources_to_try, fetch_callbacks
    )


# Export main classes and functions
__all__ = [
    'DataSourceTracker',
    'DataType',
    'DataSource',
    'get_tracker',
    'record_check',
    'get_preferred_source',
    'discover_and_record'
]
