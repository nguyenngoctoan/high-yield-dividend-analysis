"""
AUM Discovery Processor Module

Discovers and tracks AUM (Assets Under Management) data across multiple sources.
Uses data source tracking to avoid redundant API calls.
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal

from lib.core.config import Config
from lib.core.models import ProcessingStats
from lib.data_sources.fmp_client import FMPClient
from lib.data_sources.yahoo_client import YahooClient
from lib.utils.data_source_tracker import (
    DataSourceTracker, DataType, DataSource, get_tracker
)
from supabase_helpers import supabase_update, supabase_select

logger = logging.getLogger(__name__)


class AUMDiscoveryProcessor:
    """
    Discovers AUM data across multiple sources and tracks availability.

    Features:
    - Intelligent source selection based on historical success
    - Records which sources have AUM for each symbol
    - Avoids redundant API calls
    - Updates both raw_stocks and raw_stock_prices tables
    """

    def __init__(self,
                 fmp_client: Optional[FMPClient] = None,
                 yahoo_client: Optional[YahooClient] = None,
                 tracker: Optional[DataSourceTracker] = None):
        """
        Initialize AUM discovery processor.

        Args:
            fmp_client: Optional FMP client
            yahoo_client: Optional Yahoo client
            tracker: Optional data source tracker
        """
        self.fmp_client = fmp_client or FMPClient()
        self.yahoo_client = yahoo_client or YahooClient()
        self.tracker = tracker or get_tracker()
        self.stats = ProcessingStats()

    def fetch_aum_from_fmp(self, symbol: str) -> Optional[int]:
        """
        Fetch AUM from FMP.

        Args:
            symbol: ETF symbol

        Returns:
            AUM value in dollars or None
        """
        try:
            # Try ETF metadata endpoint
            metadata = self.fmp_client.fetch_etf_metadata(symbol)
            if metadata and metadata.get('aum'):
                aum = int(metadata['aum'])
                logger.debug(f"[FMP] Found AUM for {symbol}: ${aum:,.0f}")
                return aum

            # Try ETF info endpoint
            etf_info = self.fmp_client.fetch_etf_info(symbol)
            if etf_info and etf_info.get('aum'):
                aum = int(etf_info['aum'])
                logger.debug(f"[FMP] Found AUM for {symbol} (ETF info): ${aum:,.0f}")
                return aum

        except Exception as e:
            logger.debug(f"[FMP] Error fetching AUM for {symbol}: {e}")

        return None

    def fetch_aum_from_yahoo(self, symbol: str) -> Optional[int]:
        """
        Fetch AUM from Yahoo Finance.

        Args:
            symbol: ETF symbol

        Returns:
            AUM value in dollars or None
        """
        try:
            info = self.yahoo_client.fetch_company_info(symbol)
            if info and info.get('aum'):
                aum = int(info['aum'])
                logger.debug(f"[Yahoo] Found AUM for {symbol}: ${aum:,.0f}")
                return aum

        except Exception as e:
            logger.debug(f"[Yahoo] Error fetching AUM for {symbol}: {e}")

        return None

    def discover_aum(self, symbol: str,
                    force_rediscover: bool = False) -> Optional[Dict[str, Any]]:
        """
        Discover AUM from the best available source.

        Strategy:
        1. Check if we already know which source has AUM
        2. If known, use that source directly
        3. If unknown or force_rediscover, try all sources
        4. Record results for future reference

        Args:
            symbol: ETF symbol
            force_rediscover: Force checking all sources even if we have a preference

        Returns:
            Dictionary with 'source', 'aum', and 'success' keys
        """
        logger.debug(f"[AUM Discovery] Starting discovery for {symbol}")

        # Check for preferred source (unless forcing rediscovery)
        if not force_rediscover:
            preferred = self.tracker.get_preferred_source(symbol, DataType.AUM)
            if preferred:
                logger.info(
                    f"[AUM Discovery] Using preferred source {preferred.value} for {symbol}"
                )

                # Fetch from preferred source
                if preferred == DataSource.FMP:
                    aum = self.fetch_aum_from_fmp(symbol)
                elif preferred == DataSource.YAHOO:
                    aum = self.fetch_aum_from_yahoo(symbol)
                else:
                    aum = None

                if aum:
                    return {
                        'source': preferred.value,
                        'aum': aum,
                        'success': True
                    }
                else:
                    logger.warning(
                        f"[AUM Discovery] Preferred source {preferred.value} "
                        f"failed for {symbol}, trying other sources"
                    )

        # No preferred source or it failed - discover across all sources
        fetch_callbacks = {
            DataSource.FMP: self.fetch_aum_from_fmp,
            DataSource.YAHOO: self.fetch_aum_from_yahoo,
            # AlphaVantage doesn't have AUM, so we don't include it
        }

        result = self.tracker.discover_and_record(
            symbol=symbol,
            data_type=DataType.AUM,
            sources_to_try=[DataSource.FMP, DataSource.YAHOO],
            fetch_callbacks=fetch_callbacks
        )

        if result:
            source, aum = result
            return {
                'source': source.value,
                'aum': aum,
                'success': True
            }

        logger.warning(f"❌ [AUM Discovery] No AUM found for {symbol}")
        return {
            'source': None,
            'aum': None,
            'success': False
        }

    def process_and_store(self, symbol: str,
                         force_rediscover: bool = False,
                         update_prices: bool = True) -> bool:
        """
        Discover AUM and store in database.

        Updates:
        - raw_stocks.aum (current AUM value)
        - raw_stock_prices.aum (most recent price record)

        Args:
            symbol: ETF symbol
            force_rediscover: Force checking all sources
            update_prices: Also update most recent price record

        Returns:
            True if successful
        """
        self.stats.total_processed += 1

        try:
            # Discover AUM
            result = self.discover_aum(symbol, force_rediscover)

            if not result['success']:
                logger.debug(f"⚠️  {symbol}: No AUM data available")
                self.stats.skipped += 1
                return False

            aum = result['aum']
            source = result['source']

            # Update raw_stocks table with current AUM
            stocks_update = supabase_update(
                'raw_stocks',
                {'symbol': symbol},
                {'aum': aum}
            )

            if not stocks_update:
                logger.error(f"❌ {symbol}: Failed to update raw_stocks")
                self.stats.failed += 1
                return False

            logger.info(
                f"✅ {symbol}: Updated AUM = ${aum:,.0f} (source: {source})"
            )

            # Optionally update most recent price record
            if update_prices:
                try:
                    # Get most recent price date for this symbol
                    from supabase_helpers import supabase_raw_query
                    query = """
                        SELECT date
                        FROM raw_stock_prices
                        WHERE symbol = %s
                        ORDER BY date DESC
                        LIMIT 1
                    """
                    result = supabase_raw_query(query, (symbol,))

                    if result and len(result) > 0:
                        latest_date = result[0]['date']

                        # Update AUM on most recent price record
                        price_update = supabase_update(
                            'raw_stock_prices',
                            {'symbol': symbol, 'date': latest_date},
                            {'aum': aum}
                        )

                        if price_update:
                            logger.debug(
                                f"✅ {symbol}: Updated AUM in price record ({latest_date})"
                            )

                except Exception as e:
                    logger.debug(
                        f"⚠️  {symbol}: Could not update price record - {e}"
                    )

            self.stats.successful += 1
            return True

        except Exception as e:
            logger.error(f"❌ {symbol}: AUM processing error - {e}")
            self.stats.failed += 1
            self.stats.add_error(f"{symbol}: {str(e)}")
            return False

    def process_batch(self, symbols: List[str],
                     force_rediscover: bool = False,
                     update_prices: bool = True) -> Dict[str, bool]:
        """
        Process AUM discovery for multiple symbols.

        Args:
            symbols: List of ETF symbols
            force_rediscover: Force checking all sources
            update_prices: Also update price records

        Returns:
            Dictionary mapping symbol -> success status
        """
        self.stats.start()
        logger.info(f"💰 Discovering AUM for {len(symbols)} symbols")

        results = {}

        for symbol in symbols:
            success = self.process_and_store(
                symbol,
                force_rediscover=force_rediscover,
                update_prices=update_prices
            )
            results[symbol] = success

        self.stats.complete()

        logger.info(
            f"🎉 AUM discovery complete: {self.stats.successful} found, "
            f"{self.stats.skipped} skipped (no AUM), {self.stats.failed} failed, "
            f"{len(symbols)} total in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def discover_all_etf_aum(self,
                            limit: Optional[int] = None,
                            force_rediscover: bool = False) -> Dict[str, Any]:
        """
        Discover AUM for all ETFs in the database.

        Args:
            limit: Optional limit on number to process
            force_rediscover: Force checking all sources

        Returns:
            Summary dictionary
        """
        logger.info(f"🔍 Finding ETFs for AUM discovery (limit: {limit or 'None'})")

        # Query for ETFs with NULL or outdated AUM
        # Prioritize ETFs that we've never checked or have no AUM
        try:
            if force_rediscover:
                # Get all ETFs
                query_conditions = {'is_etf': True}
            else:
                # Get ETFs with no AUM
                query_conditions = {'is_etf': True, 'aum': None}

            etfs = supabase_select(
                'raw_stocks',
                'symbol,name,is_etf',
                where_clause=query_conditions,
                limit=limit
            )

            if not etfs:
                logger.info("✅ No ETFs found needing AUM discovery")
                return {
                    'processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'success_rate': 'N/A'
                }

            symbols = [etf['symbol'] for etf in etfs]
            logger.info(f"📊 Found {len(symbols)} ETFs for AUM discovery")

            # Process them
            results = self.process_batch(
                symbols,
                force_rediscover=force_rediscover,
                update_prices=True
            )

            # Summary
            summary = {
                'processed': len(results),
                'successful': self.stats.successful,
                'failed': self.stats.failed,
                'skipped': self.stats.skipped,
                'success_rate': f"{(self.stats.successful / len(results) * 100):.2f}%" if results else "N/A"
            }

            logger.info(
                f"🎉 AUM discovery summary: {self.stats.successful} found, "
                f"{self.stats.skipped} skipped (no AUM), {self.stats.failed} failed"
            )

            return summary

        except Exception as e:
            logger.error(f"❌ Error in discover_all_etf_aum: {e}")
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'error': str(e)
            }

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.to_dict()

    def get_source_statistics(self) -> Dict[str, Any]:
        """Get data source tracking statistics for AUM."""
        return self.tracker.get_statistics(DataType.AUM)


# Convenience functions
def discover_aum(symbol: str, force_rediscover: bool = False) -> Optional[Dict[str, Any]]:
    """
    Quick function to discover AUM for a symbol.

    Args:
        symbol: ETF symbol
        force_rediscover: Force checking all sources

    Returns:
        Dictionary with source, aum, and success

    Example:
        result = discover_aum('SPY')
        if result['success']:
            print(f"AUM: ${result['aum']:,.0f} from {result['source']}")
    """
    processor = AUMDiscoveryProcessor()
    return processor.discover_aum(symbol, force_rediscover)


def discover_all_etf_aum(limit: Optional[int] = None,
                        force_rediscover: bool = False) -> Dict[str, Any]:
    """
    Quick function to discover AUM for all ETFs.

    Args:
        limit: Optional limit on ETFs to process
        force_rediscover: Force checking all sources

    Returns:
        Summary dictionary

    Example:
        summary = discover_all_etf_aum(limit=100)
        print(f"Found AUM for {summary['successful']} ETFs")
    """
    processor = AUMDiscoveryProcessor()
    return processor.discover_all_etf_aum(limit, force_rediscover)


# Export main classes and functions
__all__ = [
    'AUMDiscoveryProcessor',
    'discover_aum',
    'discover_all_etf_aum'
]
