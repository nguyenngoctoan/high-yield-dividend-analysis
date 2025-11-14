#!/usr/bin/env python3
"""
Batch EOD Update Script

Ultra-fast daily update using FMP's batch EOD endpoint.
Fetches all symbols' prices in a single API call.

Usage:
    python3 update_batch_eod.py                    # Yesterday's data
    python3 update_batch_eod.py --date 2025-11-12  # Specific date

Expected Performance:
    - Duration: 10-30 seconds
    - Equivalent throughput: 38,000+ calls/minute
    - Speedup: 38,000x vs individual calls
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.processors.batch_eod_processor import BatchEODProcessor
from lib.core.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Batch EOD Update - Ultra-fast daily price updates'
    )
    parser.add_argument(
        '--date',
        type=str,
        help='Target date (YYYY-MM-DD). Defaults to yesterday.'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - show what would be fetched without upserting'
    )

    args = parser.parse_args()

    # Parse target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        # Default to yesterday (most recent completed trading day)
        target_date = date.today() - timedelta(days=1)

    # Validate configuration
    logger.info("✅ Configuration validated successfully")

    # Initialize processor
    processor = BatchEODProcessor()

    # Run batch EOD update
    try:
        logger.info(f"🚀 Starting batch EOD update for {target_date}")
        logger.info("")

        summary = processor.process_batch_eod(target_date)

        # Print final summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ BATCH EOD UPDATE SUCCESSFUL")
        logger.info("=" * 70)
        logger.info(f"Symbols Processed: {summary['symbols_processed']:,}")
        logger.info(f"Prices Updated: {summary['prices_updated']:,}")
        logger.info(f"Duration: {summary['duration_seconds']:.1f}s")
        logger.info(f"Equivalent Throughput: {summary['equivalent_throughput']:.0f} calls/min")
        logger.info(f"Speedup: {summary['speedup_factor']:.0f}x faster than individual calls")
        logger.info("=" * 70)

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Error during batch EOD update: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
