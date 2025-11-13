"""
Price Processor Module

Processes and stores stock price data from multiple sources.
Handles hybrid fetching (FMP -> Alpha Vantage -> Yahoo) with fallback logic.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from lib.core.config import Config
from lib.core.models import StockPrice, ProcessingStats
from lib.data_sources.fmp_client import FMPClient
from lib.data_sources.yahoo_client import YahooClient
from lib.data_sources.alpha_vantage_client import AlphaVantageClient
from lib.processors.incremental_processor import IncrementalProcessor
from supabase_helpers import supabase_batch_upsert

logger = logging.getLogger(__name__)


class PriceProcessor:
    """
    Processes stock price data from multiple sources.

    Features:
    - Hybrid fetching with fallback logic
    - Batch database operations
    - AUM tracking for ETFs
    - IV (Implied Volatility) support
    - Statistics tracking
    """

    def __init__(self,
                 fmp_client: Optional[FMPClient] = None,
                 yahoo_client: Optional[YahooClient] = None,
                 av_client: Optional[AlphaVantageClient] = None):
        """
        Initialize price processor.

        Args:
            fmp_client: Optional FMP client
            yahoo_client: Optional Yahoo client
            av_client: Optional Alpha Vantage client
        """
        self.fmp_client = fmp_client or FMPClient()
        self.yahoo_client = yahoo_client or YahooClient()
        self.av_client = av_client or AlphaVantageClient()

        self.stats = ProcessingStats()
        self.excluded_symbols = set()  # Track auto-excluded symbols in this session

    def _auto_exclude_symbol(self, symbol: str, reason: str):
        """
        Automatically add symbol to exclusion list.

        Args:
            symbol: Symbol to exclude
            reason: Reason for exclusion
        """
        # Avoid duplicate exclusions in same session
        if symbol in self.excluded_symbols:
            return

        try:
            from supabase_helpers import supabase_insert

            exclusion_record = {
                'symbol': symbol,
                'reason': reason,
                'validation_attempts': 1,
                'auto_excluded': True
            }

            supabase_insert('raw_excluded_symbols', [exclusion_record], batch_size=1)
            self.excluded_symbols.add(symbol)
            logger.info(f"🚫 {symbol}: Auto-excluded - {reason}")

        except Exception as e:
            logger.warning(f"⚠️  {symbol}: Could not auto-exclude - {e}")

    def fetch_prices(self, symbol: str,
                    from_date: Optional[date] = None,
                    use_hybrid: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch price data with hybrid fallback strategy.

        Strategy:
        1. Try FMP (primary source)
        2. If FMP fails and hybrid enabled, try Alpha Vantage
        3. If Alpha Vantage fails, try Yahoo Finance

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date
            use_hybrid: Enable hybrid fallback (default: True)

        Returns:
            Dictionary with price data or None
        """
        logger.debug(f"📊 Fetching prices for {symbol}")

        # Try FMP first (primary source)
        try:
            prices = self.fmp_client.fetch_prices(symbol, from_date=from_date)
            if prices and prices.get('data'):
                logger.debug(f"✅ {symbol}: Got {prices['count']} prices from FMP")
                return prices
        except Exception as e:
            logger.debug(f"⚠️  {symbol}: FMP prices failed - {e}")

        # Fallback to Alpha Vantage if hybrid enabled
        if use_hybrid and self.av_client.is_available():
            try:
                prices = self.av_client.fetch_prices(symbol, from_date=from_date)
                if prices and prices.get('data'):
                    logger.debug(f"✅ {symbol}: Got {prices['count']} prices from Alpha Vantage")
                    return prices
            except Exception as e:
                logger.debug(f"⚠️  {symbol}: Alpha Vantage prices failed - {e}")

        # Final fallback to Yahoo Finance
        if use_hybrid and Config.DATA_FETCH.FALLBACK_TO_YAHOO:
            try:
                prices = self.yahoo_client.fetch_prices(symbol, from_date=from_date)
                if prices and prices.get('data'):
                    logger.debug(f"✅ {symbol}: Got {prices['count']} prices from Yahoo")
                    return prices
            except Exception as e:
                logger.debug(f"⚠️  {symbol}: Yahoo prices failed - {e}")

        logger.warning(f"❌ {symbol}: All price sources failed")
        return None

    def process_and_store(self, symbol: str,
                         from_date: Optional[date] = None,
                         use_hybrid: bool = True,
                         force_full_refresh: bool = False) -> bool:
        """
        Fetch and store price data for a symbol with intelligent incremental updates.

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
                latest_date = IncrementalProcessor.get_latest_price_date(symbol)
                from_date = IncrementalProcessor.calculate_from_date(
                    latest_date,
                    default_lookback_days=365 * 5,
                    add_buffer_days=0  # No buffer needed, upsert handles duplicates
                )
                logger.debug(f"📊 {symbol}: Using incremental update from {from_date}")
            elif from_date is None:
                # Full refresh requested
                from_date = datetime.now().date() - timedelta(days=365 * 5)
                logger.debug(f"📊 {symbol}: Full refresh from {from_date}")

            # Fetch prices
            price_data = self.fetch_prices(symbol, from_date, use_hybrid)

            if not price_data or not price_data.get('data'):
                logger.debug(f"❌ {symbol}: No price data available from any source")

                # Auto-exclude symbols with no price data after trying all sources
                self._auto_exclude_symbol(symbol, 'No price data from any source (FMP, Alpha Vantage, Yahoo)')

                self.stats.failed += 1
                return False

            # Convert to StockPrice models for validation
            price_records = []
            for record in price_data['data']:
                try:
                    # Parse date
                    price_date = datetime.strptime(record['date'], '%Y-%m-%d').date()

                    # Create StockPrice model
                    price = StockPrice(
                        symbol=symbol,
                        date=price_date,
                        open=record.get('open'),
                        high=record.get('high'),
                        low=record.get('low'),
                        close=record.get('close'),
                        adj_close=record.get('adjClose'),
                        volume=record.get('volume'),
                        change=record.get('change'),
                        change_percent=record.get('changePercent'),
                        vwap=record.get('vwap'),
                        label=record.get('label'),
                        change_over_time=record.get('changeOverTime'),
                        aum=record.get('aum'),
                        iv=record.get('iv')
                    )

                    # Only add valid prices
                    if price.is_valid:
                        price_records.append(price.to_dict())

                except Exception as e:
                    logger.debug(f"⚠️  {symbol}: Skipping invalid price record - {e}")
                    continue

            if not price_records:
                logger.warning(f"❌ {symbol}: No valid price records")
                self.stats.failed += 1
                return False

            # Batch upsert to database
            result = supabase_batch_upsert(
                'raw_stock_prices',
                price_records,
                batch_size=Config.DATABASE.UPSERT_BATCH_SIZE
            )

            if result:
                logger.info(
                    f"✅ {symbol}: Stored {len(price_records)} price records "
                    f"(source: {price_data['source']})"
                )
                self.stats.successful += 1
                return True
            else:
                logger.error(f"❌ {symbol}: Failed to store price records")
                self.stats.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {symbol}: Price processing error - {e}")
            self.stats.failed += 1
            self.stats.add_error(f"{symbol}: {str(e)}")
            return False

    def process_batch(self, symbols: List[str],
                     from_date: Optional[date] = None,
                     use_hybrid: bool = True,
                     max_workers: int = None,
                     skip_excluded: bool = True) -> Dict[str, bool]:
        """
        Process prices for multiple symbols in parallel.

        Args:
            symbols: List of symbols
            from_date: Optional start date
            use_hybrid: Enable hybrid fallback
            max_workers: Maximum parallel workers (default: FMP concurrent requests)
            skip_excluded: Skip symbols already in exclusion list (default: True)

        Returns:
            Dictionary mapping symbol -> success status
        """
        if max_workers is None:
            max_workers = Config.API.FMP_CONCURRENT_REQUESTS

        # Filter out already-excluded symbols to save API calls
        original_count = len(symbols)
        if skip_excluded:
            from supabase_helpers import supabase_select
            try:
                excluded_records = supabase_select('raw_excluded_symbols', 'symbol', limit=None)
                if excluded_records:
                    excluded_set = {r['symbol'] for r in excluded_records}
                    symbols = [s for s in symbols if s not in excluded_set]
                    skipped = original_count - len(symbols)
                    if skipped > 0:
                        logger.info(f"⏭️  Skipping {skipped} already-excluded symbols (saves ~{skipped * 2}s)")
            except Exception as e:
                logger.debug(f"⚠️  Could not check excluded symbols: {e}")

        self.stats.start()
        logger.info(f"📊 Processing prices for {len(symbols)} symbols with {max_workers} workers")

        results = {}

        # Helper function to process a single symbol
        def process_symbol(symbol):
            success = self.process_and_store(
                symbol,
                from_date=from_date,
                use_hybrid=use_hybrid
            )
            return symbol, success

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_symbol, symbol): symbol for symbol in symbols}

            # Process results with progress bar
            for future in tqdm(as_completed(futures), total=len(symbols), desc="Processing prices", unit="symbol"):
                try:
                    symbol, success = future.result()
                    results[symbol] = success
                except Exception as e:
                    symbol = futures[future]
                    logger.error(f"❌ Error processing {symbol}: {e}")
                    results[symbol] = False

        self.stats.complete()

        logger.info(
            f"✅ Batch complete: {self.stats.successful} successful, "
            f"{self.stats.failed} failed, {len(symbols)} total "
            f"in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.to_dict()


# Convenience functions
def process_prices(symbol: str, from_date: Optional[date] = None) -> bool:
    """
    Quick function to process prices for a symbol.

    Args:
        symbol: Stock/ETF symbol
        from_date: Optional start date

    Returns:
        True if successful

    Example:
        success = process_prices('AAPL', from_date=date(2025, 1, 1))
    """
    processor = PriceProcessor()
    return processor.process_and_store(symbol, from_date=from_date)


def process_prices_batch(symbols: List[str],
                        from_date: Optional[date] = None) -> Dict[str, bool]:
    """
    Quick function to process prices for multiple symbols.

    Args:
        symbols: List of symbols
        from_date: Optional start date

    Returns:
        Dictionary of results

    Example:
        results = process_prices_batch(['AAPL', 'MSFT', 'GOOGL'])
        successful = [s for s, success in results.items() if success]
    """
    processor = PriceProcessor()
    return processor.process_batch(symbols, from_date=from_date)


# Export main classes and functions
__all__ = [
    'PriceProcessor',
    'process_prices',
    'process_prices_batch'
]
