"""
Dividend Processor Module

Processes and stores dividend data from multiple sources.
Handles hybrid fetching with fallback logic and future dividend calendar.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta

from lib.core.config import Config
from lib.core.models import Dividend, ProcessingStats
from lib.data_sources.fmp_client import FMPClient
from lib.data_sources.yahoo_client import YahooClient
from lib.data_sources.alpha_vantage_client import AlphaVantageClient
from lib.processors.incremental_processor import IncrementalProcessor
from supabase_helpers import supabase_batch_upsert

logger = logging.getLogger(__name__)


class DividendProcessor:
    """
    Processes dividend data from multiple sources.

    Features:
    - Hybrid fetching with fallback logic
    - Historical and future dividends
    - Batch database operations
    - Statistics tracking
    """

    def __init__(self,
                 fmp_client: Optional[FMPClient] = None,
                 yahoo_client: Optional[YahooClient] = None,
                 av_client: Optional[AlphaVantageClient] = None):
        """
        Initialize dividend processor.

        Args:
            fmp_client: Optional FMP client
            yahoo_client: Optional Yahoo client
            av_client: Optional Alpha Vantage client
        """
        self.fmp_client = fmp_client or FMPClient()
        self.yahoo_client = yahoo_client or YahooClient()
        self.av_client = av_client or AlphaVantageClient()

        self.stats = ProcessingStats()

    def fetch_dividends(self, symbol: str,
                       from_date: Optional[date] = None,
                       use_hybrid: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch dividend data with hybrid fallback strategy.

        Strategy:
        1. Try FMP (primary source)
        2. If FMP fails and hybrid enabled, try Alpha Vantage
        3. If Alpha Vantage fails, try Yahoo Finance

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date
            use_hybrid: Enable hybrid fallback (default: True)

        Returns:
            Dictionary with dividend data or None
        """
        logger.debug(f"💰 Fetching dividends for {symbol}")

        # Try FMP first (primary source)
        if Config.DATA_FETCH.USE_HYBRID_DIVIDENDS or not use_hybrid:
            try:
                dividends = self.fmp_client.fetch_dividends(symbol, from_date=from_date)
                if dividends and dividends.get('data'):
                    logger.debug(f"✅ {symbol}: Got {dividends['count']} dividends from FMP")
                    return dividends
            except Exception as e:
                logger.debug(f"⚠️  {symbol}: FMP dividends failed - {e}")

        # Fallback to Alpha Vantage if hybrid enabled
        if use_hybrid and self.av_client.is_available():
            try:
                dividends = self.av_client.fetch_dividends(symbol, from_date=from_date)
                if dividends and dividends.get('data'):
                    logger.debug(f"✅ {symbol}: Got {dividends['count']} dividends from Alpha Vantage")
                    return dividends
            except Exception as e:
                logger.debug(f"⚠️  {symbol}: Alpha Vantage dividends failed - {e}")

        # Final fallback to Yahoo Finance
        if use_hybrid and Config.DATA_FETCH.FALLBACK_TO_YAHOO:
            try:
                dividends = self.yahoo_client.fetch_dividends(symbol, from_date=from_date)
                if dividends and dividends.get('data'):
                    logger.debug(f"✅ {symbol}: Got {dividends['count']} dividends from Yahoo")
                    return dividends
            except Exception as e:
                logger.debug(f"⚠️  {symbol}: Yahoo dividends failed - {e}")

        logger.debug(f"ℹ️  {symbol}: No dividend data available (may not pay dividends)")
        return None

    def process_and_store(self, symbol: str,
                         from_date: Optional[date] = None,
                         use_hybrid: bool = True,
                         force_full_refresh: bool = False) -> bool:
        """
        Fetch and store dividend data for a symbol with intelligent incremental updates.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date (if None, checks DB for latest date)
            use_hybrid: Enable hybrid fallback
            force_full_refresh: Force full historical refresh instead of incremental

        Returns:
            True if successful, False otherwise
        """
        self.stats.total_processed += 1

        try:
            # Determine from_date intelligently
            if from_date is None and not force_full_refresh:
                latest_date = IncrementalProcessor.get_latest_dividend_date(symbol)
                from_date = IncrementalProcessor.calculate_from_date(
                    latest_date,
                    default_lookback_days=365 * 5,
                    add_buffer_days=0  # No buffer needed, upsert handles duplicates
                )
                logger.debug(f"💰 {symbol}: Using incremental update from {from_date}")
            elif from_date is None:
                # Full refresh requested
                from_date = datetime.now().date() - timedelta(days=365 * 5)
                logger.debug(f"💰 {symbol}: Full refresh from {from_date}")

            # Fetch dividends
            dividend_data = self.fetch_dividends(symbol, from_date, use_hybrid)

            if not dividend_data or not dividend_data.get('data'):
                logger.debug(f"ℹ️  {symbol}: No dividend data (may not pay dividends)")
                self.stats.skipped += 1
                return True  # Not an error - some stocks don't pay dividends

            # Convert to Dividend models for validation
            dividend_records = []
            for record in dividend_data['data']:
                try:
                    # Parse dates
                    div_date = datetime.strptime(record['date'], '%Y-%m-%d').date()

                    record_date = None
                    if record.get('record_date') or record.get('recordDate'):
                        date_str = record.get('record_date') or record.get('recordDate')
                        record_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    payment_date = None
                    if record.get('payment_date') or record.get('paymentDate'):
                        date_str = record.get('payment_date') or record.get('paymentDate')
                        payment_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    declaration_date = None
                    if record.get('declaration_date') or record.get('declarationDate'):
                        date_str = record.get('declaration_date') or record.get('declarationDate')
                        declaration_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    # Create Dividend model
                    dividend = Dividend(
                        symbol=symbol,
                        date=div_date,
                        amount=record.get('amount') or record.get('dividend'),
                        adj_dividend=record.get('adjDividend') or record.get('adj_dividend'),
                        record_date=record_date,
                        payment_date=payment_date,
                        declaration_date=declaration_date,
                        label=record.get('label')
                    )

                    # Only add valid dividends
                    if dividend.is_valid:
                        dividend_records.append(dividend.to_dict())

                except Exception as e:
                    logger.debug(f"⚠️  {symbol}: Skipping invalid dividend record - {e}")
                    continue

            if not dividend_records:
                logger.debug(f"ℹ️  {symbol}: No valid dividend records")
                self.stats.skipped += 1
                return True

            # Batch upsert to database
            result = supabase_batch_upsert(
                'raw_dividends',
                dividend_records,
                batch_size=Config.DATABASE.UPSERT_BATCH_SIZE
            )

            if result:
                logger.info(
                    f"✅ {symbol}: Stored {len(dividend_records)} dividend records "
                    f"(source: {dividend_data['source']})"
                )
                self.stats.successful += 1
                return True
            else:
                logger.error(f"❌ {symbol}: Failed to store dividend records")
                self.stats.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {symbol}: Dividend processing error - {e}")
            self.stats.failed += 1
            self.stats.add_error(f"{symbol}: {str(e)}")
            return False

    def process_batch(self, symbols: List[str],
                     from_date: Optional[date] = None,
                     use_hybrid: bool = True) -> Dict[str, bool]:
        """
        Process dividends for multiple symbols.

        Args:
            symbols: List of symbols
            from_date: Optional start date
            use_hybrid: Enable hybrid fallback

        Returns:
            Dictionary mapping symbol -> success status
        """
        self.stats.start()
        logger.info(f"💰 Processing dividends for {len(symbols)} symbols")

        results = {}

        for symbol in symbols:
            success = self.process_and_store(
                symbol,
                from_date=from_date,
                use_hybrid=use_hybrid
            )
            results[symbol] = success

        self.stats.complete()

        logger.info(
            f"🎉 Batch complete: {self.stats.successful} successful, "
            f"{self.stats.skipped} skipped (no dividends), "
            f"{self.stats.failed} failed, {len(symbols)} total "
            f"in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def fetch_future_dividends(self,
                              from_date: Optional[date] = None,
                              to_date: Optional[date] = None,
                              symbols: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch future dividend calendar.

        Args:
            from_date: Start date (default: today)
            to_date: End date (default: 90 days from now)
            symbols: Optional list of symbols to filter

        Returns:
            Dictionary with future dividend data
        """
        logger.info("🔮 Fetching future dividend calendar")

        try:
            # Set defaults
            if not from_date:
                from_date = datetime.now().date()
            if not to_date:
                to_date = from_date + timedelta(days=90)

            # Fetch from FMP
            future_divs = self.fmp_client.fetch_dividend_calendar(
                from_date=from_date,
                to_date=to_date,
                symbols=symbols
            )

            if future_divs:
                logger.info(
                    f"✅ Retrieved {future_divs['count']} future dividends "
                    f"from {from_date} to {to_date}"
                )
                return future_divs

        except Exception as e:
            logger.error(f"❌ Future dividend fetch failed: {e}")

        return None

    def store_future_dividends(self,
                              from_date: Optional[date] = None,
                              to_date: Optional[date] = None,
                              symbols: Optional[List[str]] = None) -> bool:
        """
        Fetch and store future dividend calendar.

        Args:
            from_date: Start date
            to_date: End date
            symbols: Optional symbol filter

        Returns:
            True if successful
        """
        try:
            future_divs = self.fetch_future_dividends(from_date, to_date, symbols)

            if not future_divs or not future_divs.get('data'):
                logger.info("ℹ️  No future dividends to store")
                return True

            # Store in dividend_calendar table
            result = supabase_batch_upsert(
                'dividend_calendar',
                future_divs['data'],
                batch_size=Config.DATABASE.UPSERT_BATCH_SIZE
            )

            if result:
                logger.info(f"✅ Stored {len(future_divs['data'])} future dividends")
                return True
            else:
                logger.error("❌ Failed to store future dividends")
                return False

        except Exception as e:
            logger.error(f"❌ Future dividend storage error: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.to_dict()


# Convenience functions
def process_dividends(symbol: str, from_date: Optional[date] = None) -> bool:
    """
    Quick function to process dividends for a symbol.

    Args:
        symbol: Stock/ETF symbol
        from_date: Optional start date

    Returns:
        True if successful

    Example:
        success = process_dividends('AAPL', from_date=date(2025, 1, 1))
    """
    processor = DividendProcessor()
    return processor.process_and_store(symbol, from_date=from_date)


def process_dividends_batch(symbols: List[str],
                           from_date: Optional[date] = None) -> Dict[str, bool]:
    """
    Quick function to process dividends for multiple symbols.

    Args:
        symbols: List of symbols
        from_date: Optional start date

    Returns:
        Dictionary of results

    Example:
        results = process_dividends_batch(['AAPL', 'MSFT', 'GOOGL'])
    """
    processor = DividendProcessor()
    return processor.process_batch(symbols, from_date=from_date)


# Export main classes and functions
__all__ = [
    'DividendProcessor',
    'process_dividends',
    'process_dividends_batch'
]
