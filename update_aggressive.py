#!/usr/bin/env python3
"""
Aggressive Update Script - Maximum Throughput Mode

Uses aggressive batching and 200+ workers to maximize API throughput.
Target: 700+ API calls per minute (close to 750 req/min limit).
"""

import sys
import argparse
from datetime import datetime

from lib.core.config import Config
from lib.processors.aggressive_processor import AggressiveProcessor
from supabase_helpers import test_supabase_connection, supabase_select

# Setup logger
logger = Config.setup()


def main():
    parser = argparse.ArgumentParser(
        description='Aggressive Update Script - Maximum Throughput Mode',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--workers', type=int, default=200,
                       help='Number of concurrent workers (default: 200)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of symbols to process')
    parser.add_argument('--test', action='store_true',
                       help='Test mode with 100 symbols')

    args = parser.parse_args()

    # Test Supabase connection
    logger.info("🔌 Testing Supabase connection...")
    if not test_supabase_connection():
        logger.error("❌ Supabase connection failed - exiting")
        sys.exit(1)
    logger.info("✅ Supabase connection successful")

    # Get symbols
    logger.info("📊 Fetching symbols from database...")
    db_symbols = supabase_select('raw_stocks', 'symbol', limit=None)
    symbols = [s['symbol'] for s in db_symbols] if db_symbols else []

    if args.test:
        symbols = symbols[:100]
        logger.info(f"🧪 TEST MODE: Processing first 100 symbols")
    elif args.limit:
        symbols = symbols[:args.limit]
        logger.info(f"✅ Found {len(symbols):,} symbols (limited to {args.limit:,})")
    else:
        logger.info(f"✅ Found {len(symbols):,} symbols")

    if not symbols:
        logger.warning("⚠️ No symbols to process")
        sys.exit(0)

    # Initialize aggressive processor
    processor = AggressiveProcessor(max_workers=args.workers)

    # Process with aggressive mode
    logger.info("")
    logger.info("=" * 70)
    logger.info("🚀 AGGRESSIVE THROUGHPUT MODE")
    logger.info("=" * 70)
    logger.info(f"Workers: {args.workers}")
    logger.info(f"Batch size: {Config.DATABASE.AGGRESSIVE_BATCH_SIZE if Config.DATABASE.AGGRESSIVE_MODE else 100}")
    logger.info(f"Target: 700+ API calls/minute")
    logger.info("=" * 70)
    logger.info("")

    start_time = datetime.now()

    try:
        summary = processor.process_batch_aggressive(symbols)

        logger.info("")
        logger.info("=" * 70)
        logger.info("📊 FINAL SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total symbols: {summary['total_symbols']:,}")
        logger.info(f"Successful prices: {summary['successful_prices']:,}")
        logger.info(f"Successful dividends: {summary['successful_dividends']:,}")
        logger.info(f"Total API calls: {summary['total_api_calls']:,}")
        logger.info(f"Duration: {summary['duration_seconds']:.1f}s ({summary['duration_seconds']/60:.1f}m)")
        logger.info(f"Throughput: {summary['api_calls_per_minute']:.0f} calls/min ({summary['throughput_percentage']:.1f}% of 750/min limit)")
        logger.info("=" * 70)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
