"""
Data Discovery Processor Module

Discovers and tracks data availability (dividends, volume, prices) across multiple sources.
Uses data source tracking to avoid redundant API calls.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import date

from lib.core.config import Config
from lib.core.models import ProcessingStats
from lib.data_sources.fmp_client import FMPClient
from lib.data_sources.alpha_vantage_client import AlphaVantageClient
from lib.data_sources.yahoo_client import YahooClient
from lib.utils.data_source_tracker import (
    DataSourceTracker, DataType, DataSource, get_tracker
)
from supabase_helpers import supabase_raw_query

logger = logging.getLogger(__name__)


class DataDiscoveryProcessor:
    """
    Discovers data availability across multiple sources and tracks results.

    Features:
    - Intelligent source selection based on historical success
    - Records which sources have data for each symbol
    - Avoids redundant API calls
    - Supports dividends, volume, and price data
    """

    def __init__(self,
                 fmp_client: Optional[FMPClient] = None,
                 av_client: Optional[AlphaVantageClient] = None,
                 yahoo_client: Optional[YahooClient] = None,
                 tracker: Optional[DataSourceTracker] = None):
        """
        Initialize data discovery processor.

        Args:
            fmp_client: Optional FMP client
            av_client: Optional AlphaVantage client
            yahoo_client: Optional Yahoo client
            tracker: Optional data source tracker
        """
        self.fmp_client = fmp_client or FMPClient()
        self.av_client = av_client or AlphaVantageClient()
        self.yahoo_client = yahoo_client or YahooClient()
        self.tracker = tracker or get_tracker()
        self.stats = ProcessingStats()

    # =========================================================================
    # DIVIDEND DATA METHODS
    # =========================================================================

    def fetch_dividends_from_fmp(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch dividend data from FMP."""
        try:
            result = self.fmp_client.fetch_dividends(symbol)
            if result and result.get('count', 0) > 0:
                logger.debug(
                    f"[FMP] Found {result['count']} dividends for {symbol}"
                )
                return result
        except Exception as e:
            logger.debug(f"[FMP] Error fetching dividends for {symbol}: {e}")
        return None

    def fetch_dividends_from_av(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch dividend data from AlphaVantage."""
        try:
            result = self.av_client.fetch_dividends(symbol)
            if result and result.get('count', 0) > 0:
                logger.debug(
                    f"[AlphaVantage] Found {result['count']} dividends for {symbol}"
                )
                return result
        except Exception as e:
            logger.debug(
                f"[AlphaVantage] Error fetching dividends for {symbol}: {e}"
            )
        return None

    def fetch_dividends_from_yahoo(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch dividend data from Yahoo Finance."""
        try:
            result = self.yahoo_client.fetch_dividends(symbol)
            if result and result.get('count', 0) > 0:
                logger.debug(
                    f"[Yahoo] Found {result['count']} dividends for {symbol}"
                )
                return result
        except Exception as e:
            logger.debug(f"[Yahoo] Error fetching dividends for {symbol}: {e}")
        return None

    def discover_dividends(self, symbol: str,
                          force_rediscover: bool = False
                          ) -> Optional[Dict[str, Any]]:
        """
        Discover dividend data from the best available source.

        Args:
            symbol: Stock/ETF symbol
            force_rediscover: Force checking all sources

        Returns:
            Dictionary with 'source', 'data', 'count', and 'success' keys
        """
        logger.debug(f"[Dividend Discovery] Starting discovery for {symbol}")

        # Check for preferred source
        if not force_rediscover:
            preferred = self.tracker.get_preferred_source(symbol, DataType.DIVIDENDS)
            if preferred:
                logger.debug(
                    f"[Dividend Discovery] Using preferred source {preferred.value} "
                    f"for {symbol}"
                )

                # Fetch from preferred source
                if preferred == DataSource.FMP:
                    result = self.fetch_dividends_from_fmp(symbol)
                elif preferred == DataSource.ALPHA_VANTAGE:
                    result = self.fetch_dividends_from_av(symbol)
                elif preferred == DataSource.YAHOO:
                    result = self.fetch_dividends_from_yahoo(symbol)
                else:
                    result = None

                if result:
                    return {
                        'source': preferred.value,
                        'data': result.get('data', []),
                        'count': result.get('count', 0),
                        'success': True
                    }

        # Discover across all sources
        fetch_callbacks = {
            DataSource.FMP: self.fetch_dividends_from_fmp,
            DataSource.ALPHA_VANTAGE: self.fetch_dividends_from_av,
            DataSource.YAHOO: self.fetch_dividends_from_yahoo,
        }

        result = self.tracker.discover_and_record(
            symbol=symbol,
            data_type=DataType.DIVIDENDS,
            sources_to_try=[DataSource.FMP, DataSource.YAHOO, DataSource.ALPHA_VANTAGE],
            fetch_callbacks=fetch_callbacks
        )

        if result:
            source, data = result
            return {
                'source': source.value,
                'data': data.get('data', []),
                'count': data.get('count', 0),
                'success': True
            }

        logger.debug(f"[Dividend Discovery] No dividends found for {symbol}")
        return {
            'source': None,
            'data': [],
            'count': 0,
            'success': False
        }

    # =========================================================================
    # VOLUME DATA METHODS
    # =========================================================================

    def fetch_volume_from_fmp(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch volume data from FMP."""
        try:
            result = self.fmp_client.fetch_prices(symbol)
            if result and result.get('count', 0) > 0:
                # Check if volume data exists
                has_volume = any(
                    item.get('volume', 0) > 0
                    for item in result.get('data', [])[:10]  # Check first 10 records
                )
                if has_volume:
                    logger.debug(
                        f"[FMP] Found volume data for {symbol} "
                        f"({result['count']} records)"
                    )
                    return result
        except Exception as e:
            logger.debug(f"[FMP] Error fetching volume for {symbol}: {e}")
        return None

    def fetch_volume_from_av(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch volume data from AlphaVantage."""
        try:
            result = self.av_client.fetch_prices(symbol)
            if result and result.get('count', 0) > 0:
                # Check if volume data exists
                has_volume = any(
                    item.get('volume', 0) > 0
                    for item in result.get('data', [])[:10]
                )
                if has_volume:
                    logger.debug(
                        f"[AlphaVantage] Found volume data for {symbol} "
                        f"({result['count']} records)"
                    )
                    return result
        except Exception as e:
            logger.debug(
                f"[AlphaVantage] Error fetching volume for {symbol}: {e}"
            )
        return None

    def fetch_volume_from_yahoo(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch volume data from Yahoo Finance."""
        try:
            result = self.yahoo_client.fetch_prices(symbol)
            if result and result.get('count', 0) > 0:
                # Check if volume data exists
                has_volume = any(
                    item.get('volume', 0) > 0
                    for item in result.get('data', [])[:10]
                )
                if has_volume:
                    logger.debug(
                        f"[Yahoo] Found volume data for {symbol} "
                        f"({result['count']} records)"
                    )
                    return result
        except Exception as e:
            logger.debug(f"[Yahoo] Error fetching volume for {symbol}: {e}")
        return None

    def discover_volume(self, symbol: str,
                       force_rediscover: bool = False
                       ) -> Optional[Dict[str, Any]]:
        """
        Discover volume data from the best available source.

        Args:
            symbol: Stock/ETF symbol
            force_rediscover: Force checking all sources

        Returns:
            Dictionary with 'source', 'has_volume', and 'success' keys
        """
        logger.debug(f"[Volume Discovery] Starting discovery for {symbol}")

        # Check for preferred source
        if not force_rediscover:
            preferred = self.tracker.get_preferred_source(symbol, DataType.VOLUME)
            if preferred:
                logger.debug(
                    f"[Volume Discovery] Using preferred source {preferred.value} "
                    f"for {symbol}"
                )

                # Fetch from preferred source
                if preferred == DataSource.FMP:
                    result = self.fetch_volume_from_fmp(symbol)
                elif preferred == DataSource.ALPHA_VANTAGE:
                    result = self.fetch_volume_from_av(symbol)
                elif preferred == DataSource.YAHOO:
                    result = self.fetch_volume_from_yahoo(symbol)
                else:
                    result = None

                if result:
                    return {
                        'source': preferred.value,
                        'has_volume': True,
                        'success': True
                    }

        # Discover across all sources
        fetch_callbacks = {
            DataSource.FMP: self.fetch_volume_from_fmp,
            DataSource.ALPHA_VANTAGE: self.fetch_volume_from_av,
            DataSource.YAHOO: self.fetch_volume_from_yahoo,
        }

        result = self.tracker.discover_and_record(
            symbol=symbol,
            data_type=DataType.VOLUME,
            sources_to_try=[DataSource.FMP, DataSource.YAHOO, DataSource.ALPHA_VANTAGE],
            fetch_callbacks=fetch_callbacks
        )

        if result:
            source, data = result
            return {
                'source': source.value,
                'has_volume': True,
                'success': True
            }

        logger.debug(f"[Volume Discovery] No volume data found for {symbol}")
        return {
            'source': None,
            'has_volume': False,
            'success': False
        }

    # =========================================================================
    # BATCH PROCESSING METHODS
    # =========================================================================

    def discover_all_data_types(self,
                               symbol: str,
                               data_types: Optional[List[DataType]] = None,
                               force_rediscover: bool = False
                               ) -> Dict[str, Dict[str, Any]]:
        """
        Discover multiple data types for a single symbol.

        Args:
            symbol: Stock/ETF symbol
            data_types: List of data types to discover (default: all)
            force_rediscover: Force checking all sources

        Returns:
            Dictionary mapping data type -> discovery result
        """
        if data_types is None:
            data_types = [DataType.DIVIDENDS, DataType.VOLUME]

        logger.info(
            f"🔍 Discovering {len(data_types)} data types for {symbol}"
        )

        results = {}

        for data_type in data_types:
            if data_type == DataType.DIVIDENDS:
                result = self.discover_dividends(symbol, force_rediscover)
            elif data_type == DataType.VOLUME:
                result = self.discover_volume(symbol, force_rediscover)
            else:
                logger.warning(f"⚠️  Unsupported data type: {data_type}")
                result = {'success': False, 'error': 'Unsupported data type'}

            results[data_type.value] = result

        return results

    def discover_batch(self,
                      symbols: List[str],
                      data_types: Optional[List[DataType]] = None,
                      force_rediscover: bool = False
                      ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Discover data types for multiple symbols.

        Args:
            symbols: List of symbols
            data_types: List of data types to discover
            force_rediscover: Force checking all sources

        Returns:
            Dictionary mapping symbol -> data_type -> discovery result
        """
        self.stats.start()
        logger.info(
            f"🔍 Discovering data for {len(symbols)} symbols "
            f"(types: {[dt.value for dt in (data_types or [DataType.DIVIDENDS, DataType.VOLUME])]}) "
        )

        results = {}

        for symbol in symbols:
            self.stats.total_processed += 1
            try:
                symbol_results = self.discover_all_data_types(
                    symbol,
                    data_types,
                    force_rediscover
                )
                results[symbol] = symbol_results

                # Count successes
                success_count = sum(
                    1 for r in symbol_results.values() if r.get('success')
                )
                if success_count > 0:
                    self.stats.successful += 1
                else:
                    self.stats.failed += 1

            except Exception as e:
                logger.error(f"❌ {symbol}: Discovery error - {e}")
                self.stats.failed += 1
                self.stats.add_error(f"{symbol}: {str(e)}")
                results[symbol] = {'error': str(e)}

        self.stats.complete()

        logger.info(
            f"🎉 Discovery complete: {self.stats.successful} successful, "
            f"{self.stats.failed} failed, {len(symbols)} total "
            f"in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def discover_all_symbols(self,
                           data_types: Optional[List[DataType]] = None,
                           limit: Optional[int] = None,
                           force_rediscover: bool = False
                           ) -> Dict[str, Any]:
        """
        Discover data types for all symbols in database.

        Args:
            data_types: List of data types to discover
            limit: Optional limit on symbols to process
            force_rediscover: Force checking all sources

        Returns:
            Summary dictionary
        """
        logger.info(
            f"🔍 Starting data discovery for all symbols (limit: {limit or 'None'})"
        )

        try:
            # Get all symbols
            from supabase_helpers import supabase_select
            symbols = supabase_select(
                'raw_stocks',
                'symbol',
                limit=limit
            )

            if not symbols:
                logger.info("✅ No symbols found")
                return {
                    'processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 'N/A'
                }

            symbol_list = [s['symbol'] for s in symbols]
            logger.info(f"📊 Found {len(symbol_list)} symbols for discovery")

            # Process them
            results = self.discover_batch(
                symbol_list,
                data_types,
                force_rediscover
            )

            # Summary
            summary = {
                'processed': len(results),
                'successful': self.stats.successful,
                'failed': self.stats.failed,
                'success_rate': f"{(self.stats.successful / len(results) * 100):.2f}%" if results else "N/A"
            }

            logger.info(
                f"🎉 Discovery summary: {self.stats.successful} successful, "
                f"{self.stats.failed} failed"
            )

            return summary

        except Exception as e:
            logger.error(f"❌ Error in discover_all_symbols: {e}")
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'error': str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.to_dict()

    def get_source_statistics(self,
                             data_type: Optional[DataType] = None
                             ) -> Dict[str, Any]:
        """Get data source tracking statistics."""
        return self.tracker.get_statistics(data_type)


# Convenience functions
def discover_dividends(symbol: str, force_rediscover: bool = False) -> Dict[str, Any]:
    """
    Quick function to discover dividend data.

    Args:
        symbol: Stock/ETF symbol
        force_rediscover: Force checking all sources

    Returns:
        Dictionary with source, data, count, and success

    Example:
        result = discover_dividends('AAPL')
        if result['success']:
            print(f"Found {result['count']} dividends from {result['source']}")
    """
    processor = DataDiscoveryProcessor()
    return processor.discover_dividends(symbol, force_rediscover)


def discover_volume(symbol: str, force_rediscover: bool = False) -> Dict[str, Any]:
    """
    Quick function to discover volume data.

    Args:
        symbol: Stock/ETF symbol
        force_rediscover: Force checking all sources

    Returns:
        Dictionary with source, has_volume, and success

    Example:
        result = discover_volume('AAPL')
        if result['success']:
            print(f"Volume data available from {result['source']}")
    """
    processor = DataDiscoveryProcessor()
    return processor.discover_volume(symbol, force_rediscover)


def discover_all_data(symbol: str,
                     data_types: Optional[List[DataType]] = None,
                     force_rediscover: bool = False
                     ) -> Dict[str, Dict[str, Any]]:
    """
    Quick function to discover all data types for a symbol.

    Args:
        symbol: Stock/ETF symbol
        data_types: List of data types (default: dividends, volume)
        force_rediscover: Force checking all sources

    Returns:
        Dictionary mapping data type -> result

    Example:
        results = discover_all_data('AAPL')
        for data_type, result in results.items():
            if result['success']:
                print(f"{data_type}: {result['source']}")
    """
    processor = DataDiscoveryProcessor()
    return processor.discover_all_data_types(symbol, data_types, force_rediscover)


# Export main classes and functions
__all__ = [
    'DataDiscoveryProcessor',
    'discover_dividends',
    'discover_volume',
    'discover_all_data'
]
