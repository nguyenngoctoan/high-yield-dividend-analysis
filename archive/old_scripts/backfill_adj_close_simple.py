#!/usr/bin/env python3
"""
Simple and fast backfill for adjusted close prices.

Strategy: For all existing records, fetch adj_close from FMP and UPDATE (not upsert).
This avoids the NOT NULL constraint issue with price column.
"""

import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from time import sleep
from threading import Semaphore
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backfill_adj_close_simple.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

FMP_API_KEY = os.getenv('FMP_API_KEY')
fmp_limiter = Semaphore(25)  # Conservative rate limiting

def fetch_adj_close_from_fmp(symbol):
    """
    Fetch adjusted close prices from FMP API.

    Returns:
        Dict mapping date to adj_close value
    """
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from=1960-01-01&apikey={FMP_API_KEY}"

        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        adj_close_map = {}
        if data and 'historical' in data:
            for item in data['historical']:
                date = item.get('date')
                adj_close = item.get('adjClose')
                if date and adj_close is not None:
                    adj_close_map[date] = float(adj_close)

        return adj_close_map

    except Exception as e:
        logger.debug(f"Error fetching {symbol} from FMP: {e}")
        return {}
    finally:
        fmp_limiter.release()
        sleep(0.05)  # 20 req/sec rate limit

def backfill_symbol(symbol):
    """
    Backfill adj_close for a single symbol using UPDATE.

    Returns:
        Tuple of (symbol, records_updated, matched_count, fallback_count)
    """
    try:
        supabase = get_supabase_client()

        # Get dates for this symbol
        result = supabase.table('raw_stock_prices')\
            .select('date,close')\
            .eq('symbol', symbol)\
            .is_('adj_close', 'null')\
            .execute()

        if not result.data:
            return (symbol, 0, 0, 0)

        total_records = len(result.data)
        logger.info(f"🔄 {symbol}: Processing {total_records} records")

        # Fetch adj_close data from FMP
        adj_close_map = fetch_adj_close_from_fmp(symbol)

        matched = 0
        fallback = 0

        # Update records one by one (batch updates with different values are tricky)
        # We'll update in SQL directly for performance
        for record in result.data:
            date = record['date']

            if date in adj_close_map:
                adj_close_value = adj_close_map[date]
                matched += 1
            else:
                # Fallback to close
                adj_close_value = record['close']
                fallback += 1

            # Update this specific record
            try:
                supabase.table('raw_stock_prices')\
                    .update({'adj_close': adj_close_value})\
                    .eq('symbol', symbol)\
                    .eq('date', date)\
                    .execute()
            except Exception as e:
                logger.error(f"❌ {symbol} {date}: Update failed - {e}")

        logger.info(f"✅ {symbol}: Updated {total_records} records ({matched} from FMP, {fallback} fallback)")
        return (symbol, total_records, matched, fallback)

    except Exception as e:
        logger.error(f"❌ {symbol}: Error - {e}")
        return (symbol, 0, 0, 0)

def get_symbols_by_recency(days_threshold=30):
    """Get symbols updated within threshold."""
    try:
        supabase = get_supabase_client()
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).date()

        result = supabase.table('raw_stock_prices')\
            .select('symbol')\
            .gte('date', str(cutoff_date))\
            .is_('adj_close', 'null')\
            .execute()

        symbols = list(set(row['symbol'] for row in result.data))
        return symbols

    except Exception as e:
        logger.error(f"Error getting symbols: {e}")
        return []

def backfill_active_stocks(max_workers=5, days=30):
    """
    Backfill adj_close for active stocks.

    Args:
        max_workers: Number of parallel workers (reduced from 10 to 5 for stability)
        days: Only process stocks updated in last N days
    """
    logger.info("=" * 80)
    logger.info(f"📊 BACKFILLING ACTIVE STOCKS (last {days} days)")
    logger.info("=" * 80)

    symbols = get_symbols_by_recency(days)

    if not symbols:
        logger.info("✅ No symbols need backfilling!")
        return

    logger.info(f"📋 Found {len(symbols)} symbols to process")
    logger.info(f"🚀 Using {max_workers} parallel workers\n")

    total_records = 0
    total_matched = 0
    total_fallback = 0
    successful = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(backfill_symbol, symbol): symbol
            for symbol in symbols
        }

        for i, future in enumerate(as_completed(future_to_symbol), 1):
            symbol = future_to_symbol[future]
            try:
                symbol, records, matched, fallback = future.result()

                if records > 0:
                    total_records += records
                    total_matched += matched
                    total_fallback += fallback
                    successful += 1
                else:
                    failed += 1

                if i % 50 == 0:
                    logger.info(f"📊 Progress: {i}/{len(symbols)} symbols, {total_records:,} records updated")

            except Exception as e:
                logger.error(f"❌ {symbol}: Task failed - {e}")
                failed += 1

    logger.info("\n" + "=" * 80)
    logger.info("✅ BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Symbols processed: {len(symbols)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total records updated: {total_records:,}")
    logger.info(f"  - From FMP: {total_matched:,}")
    logger.info(f"  - Fallback: {total_fallback:,}")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        days = 30
        if len(sys.argv) > 1:
            days = int(sys.argv[1])
            logger.info(f"Custom threshold: {days} days")

        backfill_active_stocks(max_workers=5, days=days)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
