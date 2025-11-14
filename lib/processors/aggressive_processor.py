"""
Aggressive Throughput Processor

Maximizes API call throughput by batching database writes and reducing I/O.
Target: 700+ API calls per minute (close to 750 req/min limit).
"""

import logging
from typing import List, Dict, Any
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from queue import Queue
import threading
import time

from lib.core.config import Config
from lib.processors.price_processor import PriceProcessor
from lib.processors.dividend_processor import DividendProcessor
from supabase_helpers import supabase_batch_upsert

logger = logging.getLogger(__name__)


class AggressiveProcessor:
    """
    High-throughput processor that batches database writes aggressively.

    Key optimizations:
    - Batch database writes every 100 symbols (not per symbol)
    - Use 200+ concurrent workers
    - Reduce logging I/O
    - Pipeline fetch and write operations
    """

    def __init__(self, max_workers: int = 200):
        """
        Initialize aggressive processor.

        Args:
            max_workers: Number of concurrent workers (default: 200)
        """
        self.max_workers = max_workers
        self.price_processor = PriceProcessor()
        self.dividend_processor = DividendProcessor()

        # Batching queues
        self.price_queue = Queue()
        self.dividend_queue = Queue()
        self.write_batch_size = Config.DATABASE.AGGRESSIVE_BATCH_SIZE if Config.DATABASE.AGGRESSIVE_MODE else 100

        # Statistics
        self.total_processed = 0
        self.total_api_calls = 0
        self.start_time = None

        # Background writer thread
        self.writer_thread = None
        self.stop_writing = threading.Event()

    def _batch_writer(self):
        """Background thread that writes batches to database."""
        price_batch = []
        dividend_batch = []

        while not self.stop_writing.is_set():
            # Collect items from queues
            try:
                while not self.price_queue.empty() and len(price_batch) < self.write_batch_size:
                    price_batch.append(self.price_queue.get_nowait())

                while not self.dividend_queue.empty() and len(dividend_batch) < self.write_batch_size:
                    dividend_batch.append(self.dividend_queue.get_nowait())

                # Write batches if we have enough items or timeout
                if len(price_batch) >= self.write_batch_size or (len(price_batch) > 0 and self.stop_writing.is_set()):
                    if price_batch:
                        supabase_batch_upsert('raw_stock_prices', price_batch, batch_size=len(price_batch))
                        logger.info(f"📊 Batch wrote {len(price_batch)} price records")
                        price_batch = []

                if len(dividend_batch) >= self.write_batch_size or (len(dividend_batch) > 0 and self.stop_writing.is_set()):
                    if dividend_batch:
                        supabase_batch_upsert('raw_dividends', dividend_batch, batch_size=len(dividend_batch))
                        logger.info(f"💰 Batch wrote {len(dividend_batch)} dividend records")
                        dividend_batch = []

                # Small sleep to avoid busy waiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ Batch writer error: {e}")
                time.sleep(1)

        # Final flush
        if price_batch:
            supabase_batch_upsert('raw_stock_prices', price_batch, batch_size=len(price_batch))
            logger.info(f"📊 Final flush: {len(price_batch)} price records")

        if dividend_batch:
            supabase_batch_upsert('raw_dividends', dividend_batch, batch_size=len(dividend_batch))
            logger.info(f"💰 Final flush: {len(dividend_batch)} dividend records")

    def _process_symbol_aggressive(self, symbol: str) -> Dict[str, Any]:
        """
        Process single symbol with aggressive batching.

        Args:
            symbol: Symbol to process

        Returns:
            Result dictionary
        """
        from lib.core.models import StockPrice, Dividend
        from datetime import datetime

        result = {
            'symbol': symbol,
            'price_success': False,
            'dividend_success': False,
            'api_calls': 0
        }

        # Fetch price data
        try:
            price_data = self.price_processor.fetch_prices(symbol, from_date=None, use_hybrid=True)
            result['api_calls'] += 1

            if price_data and price_data.get('data'):
                # Convert to StockPrice models (proper field names)
                for record in price_data['data']:
                    try:
                        price_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                        price = StockPrice(
                            symbol=symbol,
                            date=price_date,
                            open=record.get('open'),
                            high=record.get('high'),
                            low=record.get('low'),
                            close=record.get('close'),
                            adj_close=record.get('adjClose'),  # Convert camelCase to snake_case
                            volume=record.get('volume'),
                            change=record.get('change'),
                            change_percent=record.get('changePercent'),
                            vwap=record.get('vwap'),
                            label=record.get('label'),
                            change_over_time=record.get('changeOverTime'),
                            aum=record.get('aum'),
                            iv=record.get('iv')
                        )
                        if price.is_valid:
                            self.price_queue.put(price.to_dict())
                    except Exception as e:
                        logger.debug(f"⚠️ {symbol}: Invalid price record - {e}")
                        continue

                result['price_success'] = True
                result['price_count'] = len(price_data['data'])
        except Exception as e:
            logger.debug(f"⚠️ {symbol}: Price fetch failed - {e}")

        # Fetch dividend data
        try:
            dividend_data = self.dividend_processor.fetch_dividends(symbol, from_date=None)
            result['api_calls'] += 1

            if dividend_data and dividend_data.get('data'):
                # Convert to Dividend models
                for record in dividend_data['data']:
                    try:
                        div_date = datetime.strptime(record['date'], '%Y-%m-%d').date()
                        dividend = Dividend(
                            symbol=symbol,
                            date=div_date,
                            dividend=record.get('dividend'),
                            adj_dividend=record.get('adjDividend'),
                            declaration_date=record.get('declarationDate'),
                            record_date=record.get('recordDate'),
                            payment_date=record.get('paymentDate'),
                            label=record.get('label')
                        )
                        if dividend.is_valid:
                            self.dividend_queue.put(dividend.to_dict())
                    except Exception as e:
                        logger.debug(f"⚠️ {symbol}: Invalid dividend record - {e}")
                        continue

                result['dividend_success'] = True
                result['dividend_count'] = len(dividend_data['data'])
        except Exception as e:
            logger.debug(f"⚠️ {symbol}: Dividend fetch failed - {e}")

        return result

    def process_batch_aggressive(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Process symbols with maximum throughput.

        Args:
            symbols: List of symbols to process

        Returns:
            Processing statistics
        """
        self.start_time = time.time()
        logger.info(f"🚀 AGGRESSIVE MODE: Processing {len(symbols):,} symbols with {self.max_workers} workers")
        logger.info(f"⚡ Target throughput: 700+ API calls/minute")
        logger.info(f"📦 Batch write size: {self.write_batch_size} records")

        # Start background writer thread
        self.stop_writing.clear()
        self.writer_thread = threading.Thread(target=self._batch_writer, daemon=True)
        self.writer_thread.start()

        # Process symbols in parallel
        results = []
        successful_prices = 0
        successful_dividends = 0
        total_api_calls = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all symbols
            futures = {executor.submit(self._process_symbol_aggressive, symbol): symbol
                      for symbol in symbols}

            # Collect results with progress logging every 100 symbols
            for i, future in enumerate(as_completed(futures), 1):
                try:
                    result = future.result()
                    results.append(result)

                    if result['price_success']:
                        successful_prices += 1
                    if result['dividend_success']:
                        successful_dividends += 1
                    total_api_calls += result['api_calls']

                    # Log progress every 100 symbols
                    if i % 100 == 0:
                        elapsed = time.time() - self.start_time
                        rate = total_api_calls / (elapsed / 60) if elapsed > 0 else 0
                        logger.info(
                            f"📊 Progress: {i:,}/{len(symbols):,} symbols "
                            f"({rate:.0f} API calls/min)"
                        )

                except Exception as e:
                    logger.error(f"❌ Error: {e}")

        # Stop background writer and wait for final flush
        self.stop_writing.set()
        if self.writer_thread:
            self.writer_thread.join(timeout=30)

        # Final statistics
        elapsed = time.time() - self.start_time
        api_rate = total_api_calls / (elapsed / 60) if elapsed > 0 else 0

        summary = {
            'total_symbols': len(symbols),
            'successful_prices': successful_prices,
            'successful_dividends': successful_dividends,
            'total_api_calls': total_api_calls,
            'duration_seconds': elapsed,
            'api_calls_per_minute': api_rate,
            'throughput_percentage': (api_rate / 750) * 100 if api_rate > 0 else 0
        }

        logger.info("")
        logger.info("=" * 70)
        logger.info("🚀 AGGRESSIVE MODE COMPLETE")
        logger.info("=" * 70)
        logger.info(f"📊 Processed: {len(symbols):,} symbols in {elapsed:.1f}s")
        logger.info(f"✅ Successful: {successful_prices:,} prices, {successful_dividends:,} dividends")
        logger.info(f"📡 API calls: {total_api_calls:,} total")
        logger.info(f"⚡ Throughput: {api_rate:.0f} API calls/minute ({summary['throughput_percentage']:.1f}% of limit)")
        logger.info("=" * 70)

        return summary


# Export main class
__all__ = ['AggressiveProcessor']
