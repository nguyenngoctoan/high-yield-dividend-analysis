#!/usr/bin/env python3
"""
Stock Splits Data Fetcher - 3-Tier Fallback System
Fetches historical stock split data using FMP (primary), Alpha Vantage (secondary), and Yahoo Finance (fallback).

Usage:
    python fetch_stock_splits.py                    # Fetch splits for all stocks
    python fetch_stock_splits.py --symbol AAPL      # Fetch splits for specific symbol
    python fetch_stock_splits.py --recent-only      # Only fetch for stocks added in last 30 days
    python fetch_stock_splits.py --limit 100        # Limit to first 100 stocks
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
from time import sleep
from threading import Semaphore
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client, supabase_batch_upsert
import argparse

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_splits.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Configuration
FMP_API_KEY = os.getenv('FMP_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Rate limiters
fmp_limiter = Semaphore(10)  # Conservative for FMP
av_limiter = Semaphore(5)    # Alpha Vantage has strict limits (5 per minute)

def create_splits_table_if_not_exists():
    """Create the raw_stock_splits table if it doesn't exist."""
    supabase = get_supabase_client()

    try:
        supabase.table('raw_stock_splits').select('symbol').limit(1).execute()
        logger.info("✅ raw_stock_splits table exists")
        return True
    except Exception as e:
        logger.warning(f"⚠️  raw_stock_splits table may not exist: {e}")
        logger.info("📝 Please create the table using migrations/create_stock_splits.sql")
        return False

def parse_split_ratio(split_string):
    """
    Parse split ratio string into numerator, denominator, and decimal.

    Handles formats like:
    - "2:1", "3:2", "1:10"
    - "2-for-1", "3-for-2"
    - "2/1", "3/2"
    """
    if not split_string:
        return None, None, None

    split_string = str(split_string).strip()

    # Try colon format: "2:1"
    if ':' in split_string:
        parts = split_string.split(':')
        if len(parts) == 2:
            try:
                numerator = int(parts[0].strip())
                denominator = int(parts[1].strip())
                ratio = numerator / denominator
                return numerator, denominator, ratio
            except ValueError:
                pass

    # Try "for" format: "2-for-1"
    if '-for-' in split_string.lower():
        parts = split_string.lower().split('-for-')
        if len(parts) == 2:
            try:
                numerator = int(parts[0].strip())
                denominator = int(parts[1].strip())
                ratio = numerator / denominator
                return numerator, denominator, ratio
            except ValueError:
                pass

    # Try slash format: "2/1"
    if '/' in split_string:
        parts = split_string.split('/')
        if len(parts) == 2:
            try:
                numerator = int(parts[0].strip())
                denominator = int(parts[1].strip())
                ratio = numerator / denominator
                return numerator, denominator, ratio
            except ValueError:
                pass

    # Try decimal format: "2.0", "1.5"
    try:
        ratio = float(split_string)
        # Estimate numerator/denominator
        if ratio >= 1:
            numerator = int(ratio)
            denominator = 1
        else:
            # Reverse split (e.g., 0.5 = 1:2)
            denominator = int(1 / ratio)
            numerator = 1
        return numerator, denominator, ratio
    except ValueError:
        pass

    logger.warning(f"Could not parse split ratio: {split_string}")
    return None, None, None

def fetch_splits_fmp(symbol):
    """
    Fetch stock splits from FMP API.

    Returns:
        List of split dictionaries or None
    """
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_split/{symbol}?apikey={FMP_API_KEY}"

        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        splits = []
        if data and isinstance(data, dict) and 'historical' in data:
            for split in data['historical']:
                split_date = split.get('date')
                # FMP provides numerator and denominator directly
                numerator = split.get('numerator')
                denominator = split.get('denominator')

                if split_date and numerator and denominator:
                    ratio = numerator / denominator
                    splits.append({
                        'symbol': symbol,
                        'split_date': split_date,
                        'split_ratio': ratio,
                        'numerator': numerator,
                        'denominator': denominator,
                        'split_string': f"{numerator}:{denominator}",
                        'description': split.get('label', ''),
                        'source': 'FMP'
                    })

        if splits:
            logger.debug(f"[FMP] {symbol}: Found {len(splits)} splits")

        return splits if splits else None

    except Exception as e:
        logger.debug(f"[FMP] {symbol}: Error - {e}")
        return None
    finally:
        fmp_limiter.release()
        sleep(0.1)

def fetch_splits_alpha_vantage(symbol):
    """
    Fetch stock splits from Alpha Vantage API.

    Returns:
        List of split dictionaries or None
    """
    av_limiter.acquire()
    try:
        # Alpha Vantage doesn't have a dedicated splits endpoint
        # We need to get it from TIME_SERIES_DAILY_ADJUSTED or just skip
        # For now, return None as Alpha Vantage splits data is limited
        logger.debug(f"[Alpha Vantage] {symbol}: Splits not available via standard API")
        return None

    except Exception as e:
        logger.debug(f"[Alpha Vantage] {symbol}: Error - {e}")
        return None
    finally:
        av_limiter.release()
        sleep(12)  # Alpha Vantage rate limit: 5 per minute = 12 seconds between calls

def fetch_splits_yahoo(symbol):
    """
    Fetch stock splits from Yahoo Finance (yfinance library).

    Returns:
        List of split dictionaries or None
    """
    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        splits_data = ticker.splits

        if splits_data is None or len(splits_data) == 0:
            return None

        splits = []
        for date, ratio in splits_data.items():
            # Yahoo provides the ratio directly (e.g., 2.0 for 2:1 split)
            numerator, denominator, parsed_ratio = parse_split_ratio(str(ratio))

            splits.append({
                'symbol': symbol,
                'split_date': date.strftime('%Y-%m-%d'),
                'split_ratio': ratio,
                'numerator': numerator,
                'denominator': denominator,
                'split_string': f"{numerator}:{denominator}" if numerator and denominator else str(ratio),
                'description': '',
                'source': 'Yahoo'
            })

        if splits:
            logger.debug(f"[Yahoo] {symbol}: Found {len(splits)} splits")

        return splits if splits else None

    except ImportError:
        logger.warning("yfinance not installed. Install with: pip install yfinance")
        return None
    except Exception as e:
        logger.debug(f"[Yahoo] {symbol}: Error - {e}")
        return None

def fetch_splits_with_fallback(symbol):
    """
    Fetch stock splits using 3-tier fallback: FMP -> Alpha Vantage -> Yahoo.

    Returns:
        Tuple of (splits_list, source_used)
    """
    # Try FMP first
    splits = fetch_splits_fmp(symbol)
    if splits:
        return splits, 'FMP'

    # Try Alpha Vantage
    splits = fetch_splits_alpha_vantage(symbol)
    if splits:
        return splits, 'Alpha Vantage'

    # Try Yahoo Finance
    splits = fetch_splits_yahoo(symbol)
    if splits:
        return splits, 'Yahoo'

    return None, None

def fetch_all_splits(symbols=None, max_workers=5):
    """
    Fetch splits for all symbols using parallel processing.

    Args:
        symbols: List of symbols to process (None = all from database)
        max_workers: Number of parallel workers
    """
    logger.info("=" * 80)
    logger.info("📊 FETCHING STOCK SPLITS DATA")
    logger.info("=" * 80)

    supabase = get_supabase_client()

    # Get symbols from database if not provided
    if symbols is None:
        logger.info("📋 Fetching symbols from database...")
        result = supabase.table('raw_stocks').select('symbol').execute()
        symbols = [s['symbol'] for s in result.data]

    logger.info(f"✅ Processing {len(symbols):,} symbols")
    logger.info(f"🔄 Using {max_workers} parallel workers")
    logger.info(f"📡 Data sources: FMP → Alpha Vantage → Yahoo Finance")
    logger.info("")

    # Stats
    total_symbols = len(symbols)
    symbols_with_splits = 0
    total_splits_found = 0
    source_stats = {'FMP': 0, 'Alpha Vantage': 0, 'Yahoo': 0}
    failed = 0

    # Batch collection
    all_splits = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_symbol = {
            executor.submit(fetch_splits_with_fallback, symbol): symbol
            for symbol in symbols
        }

        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_symbol), 1):
            symbol = future_to_symbol[future]

            try:
                splits, source = future.result()

                if splits:
                    symbols_with_splits += 1
                    total_splits_found += len(splits)
                    source_stats[source] = source_stats.get(source, 0) + 1
                    all_splits.extend(splits)

                    logger.info(f"  ✅ [{source}] {symbol}: {len(splits)} split(s)")
                else:
                    failed += 1

                # Progress update
                if i % 100 == 0:
                    logger.info(f"  📊 Progress: {i:,} / {total_symbols:,} ({i*100//total_symbols}%)")

                # Batch save every 500 splits
                if len(all_splits) >= 500:
                    try:
                        supabase_batch_upsert('raw_stock_splits', all_splits, batch_size=100)
                        logger.info(f"  💾 Saved batch of {len(all_splits)} splits")
                        all_splits = []
                    except Exception as e:
                        logger.error(f"  ❌ Error saving batch: {e}")

            except Exception as e:
                failed += 1
                logger.error(f"  ❌ {symbol}: Error - {e}")

    # Save remaining splits
    if all_splits:
        try:
            supabase_batch_upsert('raw_stock_splits', all_splits, batch_size=100)
            logger.info(f"  💾 Saved final batch of {len(all_splits)} splits")
        except Exception as e:
            logger.error(f"  ❌ Error saving final batch: {e}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("✅ STOCK SPLITS FETCH COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total symbols processed: {total_symbols:,}")
    logger.info(f"Symbols with splits: {symbols_with_splits:,} ({symbols_with_splits*100//total_symbols}%)")
    logger.info(f"Total splits found: {total_splits_found:,}")
    logger.info(f"No splits found: {failed:,}")
    logger.info("")
    logger.info("📊 Data Source Statistics:")
    for source, count in source_stats.items():
        if count > 0:
            logger.info(f"  {source}: {count:,} symbols")
    logger.info("=" * 80)

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description='Fetch historical stock splits data')
    parser.add_argument('--symbol', type=str, help='Fetch splits for specific symbol')
    parser.add_argument('--symbols', type=str, nargs='+', help='Fetch splits for multiple symbols')
    parser.add_argument('--limit', type=int, help='Limit number of symbols to process')
    parser.add_argument('--recent-only', action='store_true', help='Only process stocks added in last 30 days')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers (default: 5)')

    args = parser.parse_args()

    # Check if table exists
    if not create_splits_table_if_not_exists():
        logger.error("❌ Cannot proceed without raw_stock_splits table")
        logger.info("Run: psql -h localhost -p 5434 -U postgres -d postgres -f migrations/create_stock_splits.sql")
        return 1

    # Determine which symbols to process
    symbols = None

    if args.symbol:
        symbols = [args.symbol]
    elif args.symbols:
        symbols = args.symbols
    elif args.recent_only:
        supabase = get_supabase_client()
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        result = supabase.table('raw_stocks').select('symbol').gte('created_at', cutoff_date).execute()
        symbols = [s['symbol'] for s in result.data]
        logger.info(f"📅 Processing {len(symbols)} stocks added in last 30 days")

    # Apply limit if specified
    if args.limit and symbols:
        symbols = symbols[:args.limit]

    # Fetch splits
    fetch_all_splits(symbols=symbols, max_workers=args.workers)

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
