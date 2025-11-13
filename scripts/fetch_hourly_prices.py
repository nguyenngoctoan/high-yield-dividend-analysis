#!/usr/bin/env python3
"""
Fetch hourly intraday prices for all stocks in the database.

This script fetches the previous hour's price data and stores it in stock_prices_hourly table.
Designed to run via cron at the top of each hour.
"""

import os
import sys
import requests
from datetime import datetime, timedelta
from time import sleep
from threading import Semaphore
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client, supabase_batch_upsert
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hourly_prices.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

FMP_API_KEY = os.getenv('FMP_API_KEY')
fmp_limiter = Semaphore(25)  # 3000 req/min = 50 req/sec, using 25 for stability

def create_hourly_table_if_not_exists():
    """Create the raw_stock_prices_hourly table if it doesn't exist."""
    supabase = get_supabase_client()

    # Check if table exists
    try:
        supabase.table('raw_stock_prices_hourly').select('symbol').limit(1).execute()
        logger.info("✅ raw_stock_prices_hourly table exists")
        return True
    except Exception as e:
        logger.warning(f"⚠️  raw_stock_prices_hourly table may not exist: {e}")
        logger.info("📝 Please create the table using migrations/create_stock_prices_hourly.sql")
        return False

def get_hourly_price_fmp(symbol, target_hour):
    """
    Fetch hourly price data from FMP API.

    Args:
        symbol: Stock symbol
        target_hour: datetime object for the hour to fetch

    Returns:
        Dict with price data or None
    """
    fmp_limiter.acquire()
    try:
        # FMP intraday endpoint - get 1-hour intervals
        # Format: YYYY-MM-DD HH:MM:SS
        date_str = target_hour.strftime('%Y-%m-%d')

        url = f"https://financialmodelingprep.com/api/v3/historical-chart/1hour/{symbol}?from={date_str}&to={date_str}&apikey={FMP_API_KEY}"

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list):
            # Find the data point for our target hour
            # FMP returns times like "2025-10-09 15:30:00" for the 3PM hour
            # We want to match any time within the target hour
            target_hour_prefix = target_hour.strftime('%Y-%m-%d %H:')

            for item in data:
                item_time = item.get('date', '')
                # Match any minute within the target hour
                if item_time.startswith(target_hour_prefix):
                    close_price = float(item.get('close', 0)) if item.get('close') else None
                    return {
                        'symbol': symbol,
                        'timestamp': target_hour.isoformat(),
                        'date': target_hour.date().isoformat(),
                        'hour': target_hour.hour,
                        'open': float(item.get('open', 0)) if item.get('open') else None,
                        'high': float(item.get('high', 0)) if item.get('high') else None,
                        'low': float(item.get('low', 0)) if item.get('low') else None,
                        'close': close_price,
                        'adj_close': close_price,  # Intraday data doesn't have adjustments; use close
                        'volume': int(item.get('volume', 0)) if item.get('volume') else None,
                        'price': close_price,
                        'source': 'FMP'
                    }

        return None

    except Exception as e:
        logger.debug(f"Error fetching {symbol} from FMP: {e}")
        return None
    finally:
        fmp_limiter.release()
        sleep(0.1)

def fetch_hourly_prices_for_all_stocks(target_hour=None):
    """
    Fetch hourly prices for all stocks in the database.

    Args:
        target_hour: datetime object for which hour to fetch (default: previous hour)
    """
    logger.info("=" * 80)
    logger.info("📊 FETCHING HOURLY PRICES")
    logger.info("=" * 80)

    # Determine target hour (previous hour by default)
    if target_hour is None:
        now = datetime.now()
        target_hour = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

    logger.info(f"Target hour: {target_hour.strftime('%Y-%m-%d %H:00')}")

    # Before-state metrics
    try:
        supabase = get_supabase_client()
        total_hourly_before = supabase.table('raw_stock_prices_hourly').select('symbol', count='exact').execute()
        logger.info(f"")
        logger.info(f"📊 BEFORE STATE:")
        logger.info(f"  Total hourly records in database: {total_hourly_before.count:,}")
    except Exception as e:
        logger.warning(f"⚠️  Could not fetch before-state metrics: {e}")

    # Check if table exists
    if not create_hourly_table_if_not_exists():
        logger.error("❌ Cannot proceed without raw_stock_prices_hourly table")
        return

    supabase = get_supabase_client()

    # Get all symbols from raw_stocks table
    logger.info("\n📋 Fetching symbols from database...")
    result = supabase.table('raw_stocks').select('symbol').execute()
    symbols = [s['symbol'] for s in result.data]

    logger.info(f"✅ Found {len(symbols):,} symbols to process")

    # Check which symbols already have data for this hour
    logger.info(f"\n🔍 Checking for existing data...")
    existing_result = supabase.table('raw_stock_prices_hourly').select('symbol').eq('timestamp', target_hour.isoformat()).execute()
    existing_symbols = {s['symbol'] for s in existing_result.data}

    symbols_to_fetch = [s for s in symbols if s not in existing_symbols]

    if existing_symbols:
        logger.info(f"⏭️  Skipping {len(existing_symbols):,} symbols (already have data for this hour)")

    if not symbols_to_fetch:
        logger.info("✅ All symbols already have data for this hour!")
        return

    logger.info(f"🚀 Fetching data for {len(symbols_to_fetch):,} symbols with {25} parallel workers...")

    # Fetch prices using ThreadPoolExecutor for parallel execution
    hourly_records = []
    successful = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=25) as executor:
        # Submit all tasks
        future_to_symbol = {
            executor.submit(get_hourly_price_fmp, symbol, target_hour): symbol
            for symbol in symbols_to_fetch
        }

        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_symbol), 1):
            try:
                price_data = future.result()

                if price_data:
                    hourly_records.append(price_data)
                    successful += 1

                    if successful % 100 == 0:
                        logger.info(f"  ✅ Fetched {successful} / {len(symbols_to_fetch)}")
                else:
                    failed += 1

                # Progress update
                if i % 500 == 0:
                    logger.info(f"  📊 Processed {i:,} / {len(symbols_to_fetch):,} symbols...")

                # Batch insert every 1000 records
                if len(hourly_records) >= 1000:
                    try:
                        supabase_batch_upsert('raw_stock_prices_hourly', hourly_records, batch_size=500)
                        logger.info(f"  💾 Saved batch of {len(hourly_records)} records")
                        hourly_records = []
                    except Exception as e:
                        logger.error(f"  ❌ Error saving batch: {e}")

            except Exception as e:
                failed += 1
                logger.debug(f"  ❌ Error processing symbol: {e}")

    # Insert remaining records
    if hourly_records:
        try:
            supabase_batch_upsert('raw_stock_prices_hourly', hourly_records, batch_size=500)
            logger.info(f"  💾 Saved final batch of {len(hourly_records)} records")
        except Exception as e:
            logger.error(f"  ❌ Error saving final batch: {e}")

    # Detailed metrics and statistics
    logger.info("\n" + "=" * 80)
    logger.info("📊 HOURLY FETCH METRICS")
    logger.info("=" * 80)

    success_rate = (successful / len(symbols_to_fetch) * 100) if symbols_to_fetch else 0
    logger.info(f"Target hour: {target_hour.strftime('%Y-%m-%d %H:00')}")
    logger.info(f"")
    logger.info(f"📈 Fetch Results:")
    logger.info(f"  ✅ Successful: {successful:,}")
    logger.info(f"  ❌ Failed: {failed:,}")
    logger.info(f"  📊 Total processed: {len(symbols_to_fetch):,}")
    logger.info(f"  🎯 Success rate: {success_rate:.1f}%")

    # Get additional metrics from database
    try:
        supabase = get_supabase_client()

        # Total hourly records in database
        total_hourly = supabase.table('raw_stock_prices_hourly').select('symbol', count='exact').execute()
        logger.info(f"")
        logger.info(f"💾 Database Status:")
        logger.info(f"  📋 Total hourly records: {total_hourly.count:,}")

        # Calculate growth (new records added)
        try:
            growth = total_hourly.count - total_hourly_before.count
            logger.info(f"  📈 New records added: +{growth:,}")
        except:
            pass

        # Records for this specific hour
        hour_records = supabase.table('raw_stock_prices_hourly').select('symbol', count='exact').eq('timestamp', target_hour.isoformat()).execute()
        logger.info(f"  🕐 Records for this hour: {hour_records.count:,}")

        # Unique symbols with hourly data
        all_symbols_hourly = supabase.table('raw_stock_prices_hourly').select('symbol').execute()
        unique_symbols = len(set([s['symbol'] for s in all_symbols_hourly.data])) if all_symbols_hourly.data else 0
        logger.info(f"  🏢 Unique symbols tracked: {unique_symbols:,}")

        # Get total symbols for coverage calculation
        all_symbols = supabase.table('raw_stocks').select('symbol', count='exact').execute()
        coverage = (unique_symbols / all_symbols.count * 100) if all_symbols.count > 0 else 0
        logger.info(f"  📊 Hourly data coverage: {coverage:.1f}% ({unique_symbols:,}/{all_symbols.count:,})")

        # Sample prices from this hour
        if hour_records.count > 0:
            sample_prices = supabase.table('raw_stock_prices_hourly').select('symbol, close, volume').eq('timestamp', target_hour.isoformat()).limit(5).execute()
            if sample_prices.data:
                logger.info(f"")
                logger.info(f"💰 Sample prices for {target_hour.strftime('%Y-%m-%d %H:00')}:")
                for p in sample_prices.data:
                    symbol = p.get('symbol', 'N/A')
                    close = p.get('close', 0)
                    volume = p.get('volume', 0)
                    logger.info(f"  - {symbol:8s} ${close:8.2f}  Vol: {volume:,}")

    except Exception as e:
        logger.warning(f"⚠️  Could not fetch additional metrics: {e}")

    # Error Detection and Quality Checks
    logger.info("\n" + "=" * 80)
    logger.info("🔍 ERROR DETECTION & QUALITY CHECKS")
    logger.info("=" * 80)

    critical_errors = []
    warnings = []

    # Check 1: Success rate
    if success_rate < 50:
        critical_errors.append(f"Success rate critically low: {success_rate:.1f}%")
        logger.error(f"🔴 CRITICAL: Success rate critically low: {success_rate:.1f}%")
        logger.error(f"   ACTION REQUIRED: Check FMP API status and credentials")
    elif success_rate < 80:
        warnings.append(f"Success rate below target: {success_rate:.1f}%")
        logger.warning(f"🟡 WARNING: Success rate below target: {success_rate:.1f}%")
        logger.warning(f"   RECOMMENDED: Review API rate limits and errors")
    else:
        logger.info(f"✅ Success rate acceptable: {success_rate:.1f}%")

    # Check 2: No data fetched
    if successful == 0:
        critical_errors.append("No data successfully fetched")
        logger.error(f"🔴 CRITICAL: No data successfully fetched")
        logger.error(f"   ACTION REQUIRED: Verify FMP API connectivity")

    # Check 3: Coverage check
    try:
        if coverage < 50:
            warnings.append(f"Hourly data coverage low: {coverage:.1f}%")
            logger.warning(f"🟡 WARNING: Hourly data coverage low: {coverage:.1f}%")
            logger.warning(f"   RECOMMENDED: Increase symbols tracked hourly")
        else:
            logger.info(f"✅ Coverage acceptable: {coverage:.1f}%")
    except:
        pass

    # Check 4: Market hours check (only warn if during market hours with low success)
    hour_of_day = target_hour.hour
    is_market_hours = (9 <= hour_of_day <= 16) and target_hour.weekday() < 5  # Mon-Fri, 9 AM - 4 PM

    if is_market_hours and success_rate < 90:
        warnings.append(f"Low success rate during market hours: {success_rate:.1f}%")
        logger.warning(f"🟡 WARNING: Low success rate during market hours")
        logger.warning(f"   RECOMMENDED: Market hours should have higher success rate")
    elif is_market_hours:
        logger.info(f"✅ Market hours data collection normal")
    else:
        logger.info(f"ℹ️  INFO: Outside market hours ({target_hour.strftime('%H:00')})")

    # Summary
    if not critical_errors and not warnings:
        logger.info(f"✅ No data quality issues detected")

    logger.info("\n" + "=" * 80)
    if critical_errors:
        logger.error(f"⚠️  HOURLY FETCH COMPLETED WITH ERRORS")
        logger.error(f"🔴 {len(critical_errors)} critical error(s) detected:")
        for err in critical_errors:
            logger.error(f"   - {err}")
        if warnings:
            logger.warning(f"🟡 {len(warnings)} warning(s) detected:")
            for warn in warnings:
                logger.warning(f"   - {warn}")
    elif warnings:
        logger.info(f"✅ HOURLY PRICE FETCH COMPLETE")
        logger.warning(f"⚠️  {len(warnings)} warning(s) detected - review recommended:")
        for warn in warnings:
            logger.warning(f"   - {warn}")
    else:
        logger.info(f"🎉 HOURLY PRICE FETCH COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        # Optional: pass target hour as argument (YYYY-MM-DD-HH format)
        if len(sys.argv) > 1:
            hour_str = sys.argv[1]
            target_hour = datetime.strptime(hour_str, '%Y-%m-%d-%H')
            fetch_hourly_prices_for_all_stocks(target_hour)
        else:
            fetch_hourly_prices_for_all_stocks()

    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
