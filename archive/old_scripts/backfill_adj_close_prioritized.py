#!/usr/bin/env python3
"""
Prioritized backfill for adjusted close prices.

This script backfills adj_close data in priority order:
1. Stocks with recent price updates (last 30 days) - ACTIVE stocks
2. Stocks with updates in last 90 days - SEMI-ACTIVE
3. Stocks with updates in last 180 days - DORMANT
4. All remaining stocks - INACTIVE (optional)

This ensures the most relevant data gets backfilled first.
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
from supabase_helpers import get_supabase_client, supabase_batch_upsert

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backfill_adj_close_prioritized.log'),
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

def backfill_symbol_adj_close(symbol):
    """
    Backfill adj_close for a single symbol.

    Args:
        symbol: Stock symbol to backfill

    Returns:
        Number of records updated
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
            return 0

        logger.info(f"🔄 {symbol}: Found {len(result.data)} records missing adj_close")

        # Fetch adj_close data from FMP
        adj_close_map = fetch_adj_close_from_fmp(symbol)

        if not adj_close_map:
            logger.warning(f"⚠️  {symbol}: No adj_close data available from FMP - using close as fallback")
            # Fallback: use close price as adj_close
            update_records = []
            for record in result.data:
                update_records.append({
                    'symbol': record['symbol'],
                    'date': record['date'],
                    'adj_close': record['close']  # Fallback to close
                })

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

        # Update database
        if update_records:
            supabase_batch_upsert('stock_prices', update_records, batch_size=500)
            logger.info(f"✅ {symbol}: Updated {matched} records from FMP, {unmatched} with fallback")
        return len(update_records)

    except Exception as e:
        logger.error(f"❌ {symbol}: Error backfilling - {e}")
        return 0

def get_symbols_by_priority(days_threshold):
    """
    Get symbols that have been updated within the threshold.

    Args:
        days_threshold: Number of days to look back

    Returns:
        Set of symbols
    """
    try:
        supabase = get_supabase_client()
        cutoff_date = (datetime.now() - timedelta(days=days_threshold)).date()

        # Get symbols with updates since cutoff_date and missing adj_close
        result = supabase.table('raw_stock_prices')\
            .select('symbol')\
            .gte('date', str(cutoff_date))\
            .is_('adj_close', 'null')\
            .execute()

        symbols = set(row['symbol'] for row in result.data)
        return symbols

    except Exception as e:
        logger.error(f"Error getting symbols for threshold {days_threshold}: {e}")
        return set()

def backfill_prioritized(max_workers=10, priority_levels=None):
    """
    Backfill adj_close in priority order.

    Args:
        max_workers: Number of parallel workers
        priority_levels: List of tuples (days, description) for each priority level
    """
    if priority_levels is None:
        priority_levels = [
            (30, "ACTIVE - Last 30 days"),
            (90, "SEMI-ACTIVE - Last 90 days"),
            (180, "DORMANT - Last 180 days"),
        ]

    logger.info("=" * 80)
    logger.info("📊 PRIORITIZED BACKFILL FOR ADJUSTED CLOSE PRICES")
    logger.info("=" * 80)

    total_updated = 0
    total_symbols = 0

    processed_symbols = set()  # Track symbols already processed

    for days, description in priority_levels:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"🎯 PRIORITY LEVEL: {description}")
        logger.info(f"{'=' * 80}")

        # Get symbols for this priority level
        symbols_in_tier = get_symbols_by_priority(days)

        # Remove already processed symbols
        symbols_to_process = symbols_in_tier - processed_symbols

        if not symbols_to_process:
            logger.info(f"✅ No new symbols in this tier")
            continue

        logger.info(f"📋 Found {len(symbols_to_process)} symbols in this tier")
        logger.info(f"🚀 Using {max_workers} parallel workers\n")

        # Process symbols in parallel
        tier_updated = 0
        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(backfill_symbol_adj_close, symbol): symbol
                for symbol in symbols_to_process
            }

            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_symbol), 1):
                symbol = future_to_symbol[future]
                try:
                    num_updated = future.result()
                    if num_updated > 0:
                        tier_updated += num_updated
                        successful += 1
                    else:
                        failed += 1

                    # Mark as processed
                    processed_symbols.add(symbol)

                    # Progress update
                    if i % 50 == 0:
                        logger.info(f"📊 Progress: {i}/{len(symbols_to_process)} symbols ({tier_updated:,} records updated)")

                except Exception as e:
                    logger.error(f"❌ {symbol}: Task failed - {e}")
                    failed += 1
                    processed_symbols.add(symbol)  # Still mark as processed to avoid retry

        # Tier summary
        logger.info(f"\n{'=' * 80}")
        logger.info(f"✅ {description} COMPLETE")
        logger.info(f"{'=' * 80}")
        logger.info(f"Symbols processed: {len(symbols_to_process)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Records updated: {tier_updated:,}")
        logger.info(f"{'=' * 80}\n")

        total_updated += tier_updated
        total_symbols += len(symbols_to_process)

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("🎉 PRIORITIZED BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total symbols processed: {total_symbols}")
    logger.info(f"Total records updated: {total_updated:,}")
    logger.info("=" * 80)

    # Show remaining work
    try:
        supabase = get_supabase_client()
        remaining_result = supabase.table('raw_stock_prices')\
            .select('symbol', count='exact')\
            .is_('adj_close', 'null')\
            .execute()

        if hasattr(remaining_result, 'count') and remaining_result.count:
            remaining_count = remaining_result.count
            remaining_symbols_result = supabase.table('raw_stock_prices')\
                .select('symbol')\
                .is_('adj_close', 'null')\
                .execute()
            remaining_symbols = len(set(row['symbol'] for row in remaining_symbols_result.data))

            logger.info(f"\n📊 REMAINING WORK:")
            logger.info(f"   Records still need adj_close: {remaining_count:,}")
            logger.info(f"   Symbols still need processing: {remaining_symbols:,}")
            logger.info(f"\n💡 To process remaining symbols, run:")
            logger.info(f"   python backfill_adj_close.py")
    except Exception as e:
        logger.debug(f"Could not fetch remaining work stats: {e}")

if __name__ == "__main__":
    try:
        # Parse command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == '--help':
                print("Usage: python backfill_adj_close_prioritized.py [--active-only | --recent]")
                print("\nOptions:")
                print("  --active-only : Only process stocks updated in last 30 days")
                print("  --recent      : Process stocks updated in last 90 days (30 + 90)")
                print("  (no args)     : Process all priority levels (30 + 90 + 180 days)")
                sys.exit(0)
            elif sys.argv[1] == '--active-only':
                logger.info("⚡ ACTIVE ONLY MODE: Processing only stocks from last 30 days")
                priority_levels = [(30, "ACTIVE - Last 30 days")]
            elif sys.argv[1] == '--recent':
                logger.info("⚡ RECENT MODE: Processing stocks from last 90 days")
                priority_levels = [
                    (30, "ACTIVE - Last 30 days"),
                    (90, "SEMI-ACTIVE - Last 90 days"),
                ]
            else:
                logger.error(f"Unknown option: {sys.argv[1]}")
                logger.error("Run with --help for usage")
                sys.exit(1)
        else:
            logger.info("⚡ FULL PRIORITY MODE: Processing all priority levels")
            priority_levels = None  # Use default

        backfill_prioritized(max_workers=10, priority_levels=priority_levels)

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
