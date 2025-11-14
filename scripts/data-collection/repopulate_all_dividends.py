#!/usr/bin/env python3
"""
Re-populate All Dividend Data Script

This script re-fetches dividend data for all symbols in the database
to fix the NULL ex_date issue that affected all dividend records.

The bug was in lib/core/models.py where the Dividend.to_dict() method
was outputting 'date' instead of 'ex_date', causing all ex-dividend dates
to be stored as NULL.

This script will:
1. Fetch all symbols from the database
2. Clear old dividend records (optional)
3. Re-fetch and store dividend data with correct ex_dates
4. Provide progress updates and statistics
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List
from pathlib import Path

# Add parent directory to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from lib.core.config import Config
from lib.processors.dividend_processor import DividendProcessor
from supabase_helpers import (
    test_supabase_connection,
    supabase_select,
    supabase_delete
)

# Setup logger
logger = Config.setup()


def get_all_symbols() -> List[str]:
    """Get all symbols from the database."""
    logger.info("📊 Fetching all symbols from database...")

    try:
        stocks = supabase_select('raw_stocks', columns='symbol', limit=None)
        if not stocks:
            logger.error("❌ No symbols found in database")
            return []

        symbols = [s['symbol'] for s in stocks]
        logger.info(f"✅ Found {len(symbols)} symbols")
        return symbols

    except Exception as e:
        logger.error(f"❌ Failed to fetch symbols: {e}", exc_info=True)
        return []


def clear_dividend_data(symbol: str = None) -> bool:
    """
    Clear dividend data from the database.

    Args:
        symbol: Optional symbol to clear (if None, clears all)

    Returns:
        True if successful
    """
    try:
        if symbol:
            logger.info(f"🗑️  Clearing dividend data for {symbol}...")
            result = supabase_delete('raw_dividends', {'symbol': symbol})
        else:
            logger.warning("🗑️  Clearing ALL dividend data from database...")
            logger.warning("⚠️  This will delete all dividend records!")
            response = input("Are you sure? Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                logger.info("❌ Aborted")
                return False

            result = supabase_delete('raw_dividends', {})

        logger.info(f"✅ Cleared dividend data")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to clear dividend data: {e}")
        return False


def repopulate_dividends(symbols: List[str],
                        from_date: datetime.date = None,
                        batch_size: int = 100) -> dict:
    """
    Re-populate dividend data for all symbols.

    Args:
        symbols: List of symbols to process
        from_date: Optional start date (defaults to 5 years ago)
        batch_size: Number of symbols to process at once

    Returns:
        Dictionary with statistics
    """
    if not from_date:
        from_date = (datetime.now() - timedelta(days=365 * 5)).date()

    logger.info("=" * 60)
    logger.info("DIVIDEND RE-POPULATION")
    logger.info("=" * 60)
    logger.info(f"📊 Processing {len(symbols)} symbols")
    logger.info(f"📅 From date: {from_date}")
    logger.info(f"📦 Batch size: {batch_size}")
    logger.info("=" * 60)

    processor = DividendProcessor()

    total_symbols = len(symbols)
    processed = 0
    successful = 0
    failed = 0
    skipped = 0

    start_time = time.time()

    # Process in batches
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(symbols) + batch_size - 1) // batch_size

        logger.info("")
        logger.info(f"📦 Processing Batch {batch_num}/{total_batches} ({len(batch)} symbols)")
        logger.info("-" * 60)

        # Process batch
        results = processor.process_batch(batch, from_date=from_date)

        # Update statistics
        for symbol, success in results.items():
            processed += 1
            if success:
                # Check if it was skipped or successful
                if processor.stats.skipped > skipped:
                    skipped += 1
                else:
                    successful += 1
            else:
                failed += 1

        # Progress update
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        remaining = (total_symbols - processed) / rate if rate > 0 else 0

        logger.info("")
        logger.info(f"📊 Progress: {processed}/{total_symbols} symbols ({processed/total_symbols*100:.1f}%)")
        logger.info(f"✅ Successful: {successful} | ⏭️  Skipped: {skipped} | ❌ Failed: {failed}")
        logger.info(f"⏱️  Rate: {rate:.1f} symbols/sec | Remaining: {remaining/60:.1f} min")

        # Small delay to avoid overwhelming the API
        if i + batch_size < len(symbols):
            time.sleep(1)

    # Final statistics
    elapsed = time.time() - start_time

    logger.info("")
    logger.info("=" * 60)
    logger.info("✅ RE-POPULATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"📊 Total Processed: {processed}/{total_symbols}")
    logger.info(f"✅ Successful: {successful} ({successful/total_symbols*100:.1f}%)")
    logger.info(f"⏭️  Skipped (no dividends): {skipped} ({skipped/total_symbols*100:.1f}%)")
    logger.info(f"❌ Failed: {failed} ({failed/total_symbols*100:.1f}%)")
    logger.info(f"⏱️  Total Time: {elapsed/60:.1f} minutes")
    logger.info(f"⏱️  Average Rate: {processed/elapsed:.1f} symbols/sec")
    logger.info("=" * 60)

    return {
        'total': total_symbols,
        'processed': processed,
        'successful': successful,
        'skipped': skipped,
        'failed': failed,
        'duration_seconds': elapsed
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Re-populate all dividend data with correct ex_dates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Re-populate all dividend data
  python scripts/repopulate_all_dividends.py

  # Re-populate with custom date range
  python scripts/repopulate_all_dividends.py --from-date 2020-01-01

  # Test with a small batch first
  python scripts/repopulate_all_dividends.py --limit 10

  # Clear old data before re-populating
  python scripts/repopulate_all_dividends.py --clear

  # Process specific symbols
  python scripts/repopulate_all_dividends.py --symbols AAPL MSFT GOOGL
        """
    )

    parser.add_argument('--from-date', type=str, default=None,
                       help='Start date for dividend data (YYYY-MM-DD), default: 5 years ago')

    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of symbols to process (for testing)')

    parser.add_argument('--batch-size', type=int, default=100,
                       help='Batch size for processing (default: 100)')

    parser.add_argument('--clear', action='store_true',
                       help='Clear existing dividend data before re-populating')

    parser.add_argument('--symbols', nargs='+', default=None,
                       help='Specific symbols to process (space-separated)')

    args = parser.parse_args()

    # Test Supabase connection
    logger.info("🔌 Testing Supabase connection...")
    if not test_supabase_connection():
        logger.error("❌ Supabase connection failed - exiting")
        sys.exit(1)
    logger.info("✅ Supabase connection successful")

    # Parse from_date
    from_date = None
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"❌ Invalid date format: {args.from_date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Get symbols
    if args.symbols:
        symbols = [s.upper() for s in args.symbols]
        logger.info(f"📊 Processing {len(symbols)} specified symbols")
    else:
        symbols = get_all_symbols()
        if not symbols:
            logger.error("❌ No symbols found - exiting")
            sys.exit(1)

    # Apply limit if specified
    if args.limit:
        symbols = symbols[:args.limit]
        logger.info(f"📊 Limited to {len(symbols)} symbols for testing")

    # Clear data if requested
    if args.clear:
        if args.symbols:
            for symbol in args.symbols:
                clear_dividend_data(symbol)
        else:
            if not clear_dividend_data():
                sys.exit(1)

    # Run re-population
    try:
        results = repopulate_dividends(
            symbols,
            from_date=from_date,
            batch_size=args.batch_size
        )

        # Exit with appropriate code
        if results['failed'] > 0:
            logger.warning(f"⚠️  Completed with {results['failed']} failures")
            sys.exit(1)
        else:
            logger.info("✅ All symbols processed successfully")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Re-population error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
