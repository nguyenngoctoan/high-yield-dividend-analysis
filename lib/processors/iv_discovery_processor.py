"""
Implied Volatility (IV) Discovery Processor Module

Discovers and tracks Implied Volatility data from Alpha Vantage Premium options chain.
Especially useful for covered call ETFs where IV indicates potential distribution levels.
"""

import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timedelta

from lib.core.config import Config
from lib.core.models import ProcessingStats
from lib.data_sources.alpha_vantage_client import AlphaVantageClient
from lib.utils.data_source_tracker import (
    DataSourceTracker, DataType, DataSource, get_tracker
)
from supabase_helpers import supabase_update, supabase_select, supabase_raw_query

logger = logging.getLogger(__name__)


class IVDiscoveryProcessor:
    """
    Discovers Implied Volatility data from options chains.

    Features:
    - Fetches IV from Alpha Vantage Premium options API
    - Tracks IV for covered call ETFs (key distribution indicator)
    - Records source availability
    - Updates both raw_stocks and raw_stock_prices tables
    - Calculates call vs put IV separately
    """

    def __init__(self,
                 av_client: Optional[AlphaVantageClient] = None,
                 tracker: Optional[DataSourceTracker] = None):
        """
        Initialize IV discovery processor.

        Args:
            av_client: Optional AlphaVantage client (Premium required)
            tracker: Optional data source tracker
        """
        self.av_client = av_client or AlphaVantageClient()
        self.tracker = tracker or get_tracker()
        self.stats = ProcessingStats()

    def fetch_iv_from_alphavantage(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch IV from Alpha Vantage Premium options API.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Dictionary with IV data or None
        """
        try:
            result = self.av_client.get_implied_volatility(
                symbol=symbol,
                contract_type='both',  # Get both call and put IV
                closest_to_money=True
            )

            if result and result.get('iv'):
                logger.debug(
                    f"[AlphaVantage] Found IV for {symbol}: {result['iv']:.4f} "
                    f"(calls: {result.get('call_iv', 0):.4f}, puts: {result.get('put_iv', 0):.4f})"
                )
                return result

        except Exception as e:
            logger.debug(f"[AlphaVantage] Error fetching IV for {symbol}: {e}")

        return None

    def discover_iv(self, symbol: str,
                   force_rediscover: bool = False) -> Optional[Dict[str, Any]]:
        """
        Discover IV for a symbol.

        Strategy:
        1. Check if we already know IV source (currently only AlphaVantage Premium)
        2. If known, use that source directly
        3. If unknown or force_rediscover, try to fetch
        4. Record results for future reference

        Args:
            symbol: Stock/ETF symbol
            force_rediscover: Force checking even if we have a preference

        Returns:
            Dictionary with 'source', 'iv', 'call_iv', 'put_iv', and 'success' keys
        """
        logger.debug(f"[IV Discovery] Starting discovery for {symbol}")

        # Currently only AlphaVantage Premium has IV
        # In the future, could add Polygon, Tradier, etc.

        if not force_rediscover:
            preferred = self.tracker.get_preferred_source(symbol, DataType.IV)
            if preferred:
                logger.info(
                    f"[IV Discovery] Using preferred source {preferred.value} for {symbol}"
                )

                if preferred == DataSource.ALPHA_VANTAGE:
                    result = self.fetch_iv_from_alphavantage(symbol)
                    if result:
                        return {
                            'source': preferred.value,
                            'iv': result.get('iv'),
                            'call_iv': result.get('call_iv'),
                            'put_iv': result.get('put_iv'),
                            'contracts_analyzed': result.get('contracts_analyzed'),
                            'success': True
                        }

        # Try Alpha Vantage (currently only source)
        result = self.fetch_iv_from_alphavantage(symbol)

        if result:
            # Record success
            self.tracker.record_check(
                symbol=symbol,
                data_type=DataType.IV,
                source=DataSource.ALPHA_VANTAGE,
                has_data=True,
                notes=f"IV: {result.get('iv'):.4f}"
            )

            return {
                'source': 'AlphaVantage',
                'iv': result.get('iv'),
                'call_iv': result.get('call_iv'),
                'put_iv': result.get('put_iv'),
                'contracts_analyzed': result.get('contracts_analyzed'),
                'success': True
            }

        # Record failure
        self.tracker.record_check(
            symbol=symbol,
            data_type=DataType.IV,
            source=DataSource.ALPHA_VANTAGE,
            has_data=False,
            notes="No options data available"
        )

        logger.warning(f"❌ [IV Discovery] No IV found for {symbol}")
        return {
            'source': None,
            'iv': None,
            'call_iv': None,
            'put_iv': None,
            'success': False
        }

    def process_and_store(self, symbol: str,
                         force_rediscover: bool = False,
                         update_prices: bool = True) -> bool:
        """
        Discover IV and store in database.

        Updates:
        - raw_stock_prices.iv (most recent price record)
        - Can also track in separate analytics table

        Args:
            symbol: Stock/ETF symbol
            force_rediscover: Force checking all sources
            update_prices: Also update most recent price record

        Returns:
            True if successful
        """
        self.stats.total_processed += 1

        try:
            # Discover IV
            result = self.discover_iv(symbol, force_rediscover)

            if not result['success']:
                logger.debug(f"⚠️  {symbol}: No IV data available")
                self.stats.skipped += 1
                return False

            iv = result['iv']
            call_iv = result.get('call_iv')
            put_iv = result.get('put_iv')
            source = result['source']

            # Update most recent price record with IV
            if update_prices:
                try:
                    # Get most recent price date for this symbol
                    query = """
                        SELECT date
                        FROM raw_stock_prices
                        WHERE symbol = %s
                        ORDER BY date DESC
                        LIMIT 1
                    """
                    price_result = supabase_raw_query(query, (symbol,))

                    if price_result and len(price_result) > 0:
                        latest_date = price_result[0]['date']

                        # Update IV on most recent price record
                        price_update = supabase_update(
                            'raw_stock_prices',
                            {'symbol': symbol, 'date': latest_date},
                            {'iv': float(iv)}
                        )

                        if price_update:
                            logger.info(
                                f"✅ {symbol}: Updated IV = {iv:.4f} "
                                f"(calls: {call_iv:.4f}, puts: {put_iv:.4f}) "
                                f"(source: {source}, date: {latest_date})"
                            )
                            self.stats.successful += 1
                            return True
                        else:
                            logger.error(f"❌ {symbol}: Failed to update price record")

                except Exception as e:
                    logger.error(f"❌ {symbol}: Error updating price record - {e}")

            self.stats.failed += 1
            return False

        except Exception as e:
            logger.error(f"❌ {symbol}: IV processing error - {e}")
            self.stats.failed += 1
            self.stats.add_error(f"{symbol}: {str(e)}")
            return False

    def process_batch(self, symbols: List[str],
                     force_rediscover: bool = False,
                     update_prices: bool = True) -> Dict[str, bool]:
        """
        Process IV discovery for multiple symbols.

        Args:
            symbols: List of symbols
            force_rediscover: Force checking all sources
            update_prices: Also update price records

        Returns:
            Dictionary mapping symbol -> success status
        """
        self.stats.start()
        logger.info(f"📊 Discovering IV for {len(symbols)} symbols")

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
            f"🎉 IV discovery complete: {self.stats.successful} found, "
            f"{self.stats.skipped} skipped (no IV), {self.stats.failed} failed, "
            f"{len(symbols)} total in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def discover_covered_call_etf_iv(self,
                                    limit: Optional[int] = None,
                                    force_rediscover: bool = False) -> Dict[str, Any]:
        """
        Discover IV for covered call ETFs specifically.

        Covered call ETFs use IV as a key indicator for distribution levels,
        making this metric especially important for these securities.

        Args:
            limit: Optional limit on number to process
            force_rediscover: Force checking all sources

        Returns:
            Summary dictionary
        """
        logger.info(
            f"🔍 Finding covered call ETFs for IV discovery (limit: {limit or 'None'})"
        )

        try:
            # Query for covered call ETFs
            # Look for ETFs with "covered call" or "option income" in their investment strategy
            query = """
                SELECT symbol, name, investment_strategy
                FROM raw_stocks
                WHERE is_etf = true
                  AND (
                      LOWER(investment_strategy) LIKE '%covered call%'
                      OR LOWER(investment_strategy) LIKE '%option income%'
                      OR LOWER(investment_strategy) LIKE '%call%'
                      OR LOWER(name) LIKE '%covered call%'
                      OR LOWER(name) LIKE '%option income%'
                  )
                ORDER BY symbol
            """

            if limit:
                query += f" LIMIT {limit}"

            etfs = supabase_raw_query(query, ())

            if not etfs:
                logger.info("✅ No covered call ETFs found")
                return {
                    'processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'success_rate': 'N/A'
                }

            symbols = [etf['symbol'] for etf in etfs]
            logger.info(
                f"📊 Found {len(symbols)} covered call ETFs for IV discovery"
            )

            # Log some examples
            for etf in etfs[:5]:
                logger.info(
                    f"  - {etf['symbol']}: {etf['name']} "
                    f"({etf.get('investment_strategy', 'N/A')})"
                )

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
                'success_rate': f"{(self.stats.successful / len(results) * 100):.2f}%" if results else "N/A",
                'etfs_analyzed': [etf['symbol'] for etf in etfs]
            }

            logger.info(
                f"🎉 Covered call ETF IV discovery summary: "
                f"{self.stats.successful} found, "
                f"{self.stats.skipped} skipped (no IV), "
                f"{self.stats.failed} failed"
            )

            return summary

        except Exception as e:
            logger.error(f"❌ Error in discover_covered_call_etf_iv: {e}")
            return {
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'error': str(e)
            }

    def discover_all_iv(self,
                       limit: Optional[int] = None,
                       force_rediscover: bool = False,
                       symbols_with_options_only: bool = True) -> Dict[str, Any]:
        """
        Discover IV for all symbols in database.

        Args:
            limit: Optional limit on symbols to process
            force_rediscover: Force checking all sources
            symbols_with_options_only: Only process symbols likely to have options

        Returns:
            Summary dictionary
        """
        logger.info(
            f"🔍 Starting IV discovery for all symbols (limit: {limit or 'None'})"
        )

        try:
            # Get symbols
            # Options are typically only available for liquid stocks and ETFs
            # Focus on those with recent trading activity
            if symbols_with_options_only:
                query = """
                    SELECT DISTINCT s.symbol
                    FROM raw_stocks s
                    INNER JOIN raw_stock_prices p ON s.symbol = p.symbol
                    WHERE p.date > NOW() - INTERVAL '7 days'
                      AND p.volume > 100000  -- Liquid stocks
                    ORDER BY s.symbol
                """
            else:
                query = "SELECT symbol FROM raw_stocks ORDER BY symbol"

            if limit:
                query += f" LIMIT {limit}"

            symbols_data = supabase_raw_query(query, ())

            if not symbols_data:
                logger.info("✅ No symbols found")
                return {
                    'processed': 0,
                    'successful': 0,
                    'failed': 0,
                    'skipped': 0,
                    'success_rate': 'N/A'
                }

            symbols = [s['symbol'] for s in symbols_data]
            logger.info(f"📊 Found {len(symbols)} symbols for IV discovery")

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
                f"🎉 IV discovery summary: {self.stats.successful} found, "
                f"{self.stats.skipped} skipped (no options), "
                f"{self.stats.failed} failed"
            )

            return summary

        except Exception as e:
            logger.error(f"❌ Error in discover_all_iv: {e}")
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
        """Get data source tracking statistics for IV."""
        return self.tracker.get_statistics(DataType.IV)


# Convenience functions
def discover_iv(symbol: str, force_rediscover: bool = False) -> Optional[Dict[str, Any]]:
    """
    Quick function to discover IV for a symbol.

    Args:
        symbol: Stock/ETF symbol
        force_rediscover: Force checking all sources

    Returns:
        Dictionary with source, iv, call_iv, put_iv, and success

    Example:
        result = discover_iv('XYLD')  # Covered call ETF
        if result['success']:
            print(f"IV: {result['iv']:.4f} (calls: {result['call_iv']:.4f})")
    """
    processor = IVDiscoveryProcessor()
    return processor.discover_iv(symbol, force_rediscover)


def discover_covered_call_etf_iv(limit: Optional[int] = None,
                                force_rediscover: bool = False) -> Dict[str, Any]:
    """
    Quick function to discover IV for covered call ETFs.

    Covered call ETFs use IV to determine distribution levels,
    making this metric critical for these securities.

    Args:
        limit: Optional limit on ETFs to process
        force_rediscover: Force checking all sources

    Returns:
        Summary dictionary

    Example:
        summary = discover_covered_call_etf_iv(limit=50)
        print(f"Found IV for {summary['successful']} covered call ETFs")
        print(f"ETFs analyzed: {', '.join(summary['etfs_analyzed'][:10])}")
    """
    processor = IVDiscoveryProcessor()
    return processor.discover_covered_call_etf_iv(limit, force_rediscover)


# Export main classes and functions
__all__ = [
    'IVDiscoveryProcessor',
    'discover_iv',
    'discover_covered_call_etf_iv'
]
