#!/usr/bin/env python3
"""
Fix Yahoo Finance Price Data

Re-fetches and updates stock prices for all stocks to ensure we have
correct unadjusted close prices (not just adjusted prices in both fields).

This script:
1. Gets all unique symbols from the stocks table
2. Re-fetches price data using the fixed YahooClient
3. Upserts corrected data into stock_prices table
"""

import logging
import sys
from datetime import date
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from lib.core.config import Config
from lib.processors.price_processor import PriceProcessor
from lib.data_sources.yahoo_client import YahooClient
from lib.data_sources.fmp_client import FMPClient
from supabase_helpers import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_symbols() -> List[str]:
    """Get all symbols from the raw_stocks table."""
    try:
        supabase = get_supabase_client()
        response = supabase.table('raw_stocks').select('symbol').execute()

        if response.data:
            symbols = [row['symbol'] for row in response.data]
            logger.info(f"Found {len(symbols)} symbols in raw_stocks table")
            return symbols
        else:
            logger.error("No symbols found in raw_stocks table")
            return []
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        return []


def update_prices_for_symbols(symbols: List[str], batch_size: int = 100):
    """
    Update prices for all symbols using hybrid approach.

    Uses FMP first (primary source), falls back to Yahoo if needed.
    """
    logger.info(f"Updating prices for {len(symbols)} symbols")

    # Initialize processor with both clients
    processor = PriceProcessor(
        fmp_client=FMPClient(),
        yahoo_client=YahooClient()
    )

    # Process in batches
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(symbols) + batch_size - 1) // batch_size

        logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} symbols)")

        results = processor.process_batch(
            batch,
            from_date=None,  # Will use incremental logic
            use_hybrid=True  # Use hybrid fetching (FMP + Yahoo fallback)
        )

        # Log summary
        successful = sum(1 for success in results.values() if success)
        failed = len(batch) - successful
        logger.info(
            f"Batch {batch_num} complete: {successful} successful, {failed} failed"
        )

    # Get final stats
    stats = processor.get_statistics()
    logger.info(f"\n{'='*60}")
    logger.info(f"FINAL RESULTS:")
    logger.info(f"  Total processed: {stats['total_processed']}")
    logger.info(f"  Successful: {stats['successful']}")
    logger.info(f"  Skipped: {stats['skipped']}")
    logger.info(f"  Failed: {stats['failed']}")
    logger.info(f"  Duration: {stats['duration_seconds']:.2f}s")
    if stats.get('errors'):
        logger.info(f"  Errors: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            logger.info(f"    - {error}")
    logger.info(f"{'='*60}\n")


def main():
    """Main execution function."""
    logger.info("="*60)
    logger.info("Yahoo Finance Price Data Fix Script")
    logger.info("="*60)
    logger.info("")
    logger.info("This script will re-fetch and update ALL stock prices")
    logger.info("to ensure we have correct unadjusted close prices.")
    logger.info("")

    # Get all symbols
    symbols = get_all_symbols()

    if not symbols:
        logger.error("No symbols to process. Exiting.")
        return 1

    logger.info(f"Found {len(symbols)} symbols to update")
    logger.info("")

    # Confirm with user
    print("WARNING: This will update price data for ALL stocks in the database.")
    print("This may take a while and will use API quota.")
    response = input("Do you want to continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        logger.info("Operation cancelled by user")
        return 0

    # Update prices
    try:
        update_prices_for_symbols(symbols, batch_size=50)
        logger.info("✅ Price update complete!")
        return 0
    except Exception as e:
        logger.error(f"❌ Error during price update: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
