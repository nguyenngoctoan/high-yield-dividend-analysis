#!/usr/bin/env python3
"""
Backfill adjusted close prices for existing historical data.

This script fetches adjusted close prices from FMP API for all symbols
that already have price data but are missing adj_close values.
"""

import os
import sys
import logging
import requests
from datetime import datetime
from time import sleep
from threading import Semaphore
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client, supabase_batch_upsert

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backfill_adj_close.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

FMP_API_KEY = os.getenv('FMP_API_KEY')
fmp_limiter = Semaphore(25)  # Conservative rate limiting

def fetch_adj_close_from_fmp(symbol, from_date='1960-01-01'):
    """
    Fetch adjusted close prices from FMP API.

    Args:
        symbol: Stock symbol
        from_date: Start date for historical data

    Returns:
        Dict mapping date to adj_close value
    """
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={from_date}&apikey={FMP_API_KEY}"

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

def backfill_symbol_adj_close(symbol, batch_mode=False):
    """
    Backfill adj_close for a single symbol.

    Args:
        symbol: Stock symbol to backfill
        batch_mode: If True, return records instead of upserting directly

    Returns:
        List of updated records (in batch mode) or number of records updated
    """
    try:
        supabase = get_supabase_client()

        # Get all price records for this symbol that need adj_close
        result = supabase.table('raw_stock_prices')\
            .select('symbol,date,close')\
            .eq('symbol', symbol)\
            .is_('adj_close', 'null')\
            .execute()

        if not result.data:
            logger.debug(f"✅ {symbol}: No records need backfilling")
            return [] if batch_mode else 0

        logger.info(f"🔄 {symbol}: Found {len(result.data)} records missing adj_close")

        # Fetch adj_close data from FMP
        adj_close_map = fetch_adj_close_from_fmp(symbol)

        if not adj_close_map:
            logger.warning(f"⚠️  {symbol}: No adj_close data available from FMP")
            # Fallback: use close price as adj_close
            update_records = []
            for record in result.data:
                update_records.append({
                    'symbol': record['symbol'],
                    'date': record['date'],
                    'adj_close': record['close']  # Fallback to close
                })

            if batch_mode:
                return update_records
            else:
                if update_records:
                    supabase_batch_upsert('stock_prices', update_records, batch_size=500)
                    logger.info(f"✅ {symbol}: Backfilled {len(update_records)} records (using close as fallback)")
                return len(update_records)

        # Match FMP data to database records
        update_records = []
        matched = 0
        unmatched = 0

        for record in result.data:
            date = record['date']
            if date in adj_close_map:
                update_records.append({
                    'symbol': record['symbol'],
                    'date': date,
                    'adj_close': adj_close_map[date]
                })
                matched += 1
            else:
                # Use close as fallback if no adj_close data
                update_records.append({
                    'symbol': record['symbol'],
                    'date': date,
                    'adj_close': record['close']
                })
                unmatched += 1

        if batch_mode:
            return update_records
        else:
            # Update database
            if update_records:
                supabase_batch_upsert('stock_prices', update_records, batch_size=500)
                logger.info(f"✅ {symbol}: Updated {matched} records from FMP, {unmatched} with fallback")
            return len(update_records)

    except Exception as e:
        logger.error(f"❌ {symbol}: Error backfilling - {e}")
        return [] if batch_mode else 0

def backfill_all_symbols(max_workers=10, limit_symbols=None):
    """
    Backfill adj_close for all symbols with missing data.

    Args:
        max_workers: Number of parallel workers
        limit_symbols: Limit to first N symbols (for testing)
    """
    logger.info("=" * 80)
    logger.info("📊 BACKFILLING ADJUSTED CLOSE PRICES")
    logger.info("=" * 80)

    supabase = get_supabase_client()

    # Get all unique symbols that have price data but missing adj_close
    logger.info("\n🔍 Finding symbols with missing adj_close data...")

    # Query for symbols with null adj_close
    result = supabase.table('raw_stock_prices')\
        .select('symbol')\
        .is_('adj_close', 'null')\
        .execute()

    if not result.data:
        logger.info("✅ All price records already have adj_close!")
        return

    # Get unique symbols
    symbols_with_missing = list(set(row['symbol'] for row in result.data))

    if limit_symbols:
        symbols_with_missing = symbols_with_missing[:limit_symbols]
        logger.info(f"⚠️  LIMIT MODE: Processing only {limit_symbols} symbols")

    logger.info(f"📋 Found {len(symbols_with_missing)} symbols needing backfill")
    logger.info(f"🚀 Using {max_workers} parallel workers\n")

    # Process symbols in parallel
    total_updated = 0
    successful = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_symbol = {
            executor.submit(backfill_symbol_adj_close, symbol): symbol
            for symbol in symbols_with_missing
        }

        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_symbol), 1):
            symbol = future_to_symbol[future]
            try:
                num_updated = future.result()
                if num_updated > 0:
                    total_updated += num_updated
                    successful += 1
                else:
                    failed += 1

                # Progress update
                if i % 50 == 0:
                    logger.info(f"📊 Progress: {i}/{len(symbols_with_missing)} symbols ({total_updated:,} records updated)")

            except Exception as e:
                logger.error(f"❌ {symbol}: Task failed - {e}")
                failed += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total symbols processed: {len(symbols_with_missing)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total records updated: {total_updated:,}")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        # Optional: limit for testing
        limit = None
        if len(sys.argv) > 1:
            try:
                limit = int(sys.argv[1])
                logger.info(f"⚠️  Running in TEST MODE with limit={limit} symbols")
            except ValueError:
                logger.error("Invalid limit argument. Usage: python backfill_adj_close.py [limit]")
                sys.exit(1)

        backfill_all_symbols(max_workers=10, limit_symbols=limit)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
