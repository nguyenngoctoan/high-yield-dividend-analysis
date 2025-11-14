#!/usr/bin/env python3
"""
Optimized International Symbols Cleanup (Batch Mode)

Uses SQL DELETE with LIKE for much faster deletion.
Can clean 1000s of symbols in seconds instead of hours.
"""

import logging
import sys
import os

sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from supabase_helpers import get_supabase_client
from lib.core.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use centralized international exchange suffixes from config
INTERNATIONAL_SUFFIXES = Config.EXCHANGE.BLOCKED_SUFFIXES

# Tables that contain stock symbols
TABLES_TO_CLEAN = [
    'raw_stocks',
    'raw_stock_prices',
    'raw_dividends',
    'dim_stocks',
    'raw_holdings_history',
]


def cleanup_table_batch(supabase, table_name: str) -> int:
    """
    Clean international symbols using batch SQL DELETE.
    Much faster than individual deletions.
    """
    logger.info(f"\n🧹 Cleaning {table_name}...")
    total_deleted = 0

    try:
        # Build OR condition for all suffixes
        # Example: symbol LIKE '%.HK' OR symbol LIKE '%.KS' OR ...
        conditions = []
        for suffix in INTERNATIONAL_SUFFIXES:
            # Use ilike for case-insensitive matching
            result = supabase.table(table_name).delete().ilike('symbol', f'%{suffix}').execute()
            deleted = len(result.data) if result.data else 0
            if deleted > 0:
                logger.info(f"  ✅ Deleted {deleted:,} symbols with {suffix} suffix")
                total_deleted += deleted

        logger.info(f"✅ {table_name}: Total deleted {total_deleted:,} symbols")
        return total_deleted

    except Exception as e:
        logger.error(f"❌ Error cleaning {table_name}: {e}")
        return total_deleted


def cleanup_with_sql(table_name: str, suffixes: list) -> int:
    """
    Alternative: Use raw SQL for even faster deletion.
    Requires direct database access.
    """
    # This would require psycopg2 or direct SQL execution
    # Keeping for reference if Supabase client proves too slow
    pass


def main():
    """Main execution."""
    logger.info("="*80)
    logger.info("Optimized International Symbols Cleanup (Batch Mode)")
    logger.info("="*80)
    logger.info("")
    logger.info("This will DELETE all stocks with international exchange suffixes")
    logger.info("using BATCH operations for maximum speed.")
    logger.info("")
    logger.info("International suffixes to delete:")
    logger.info(f"  {', '.join(INTERNATIONAL_SUFFIXES[:10])}...")
    logger.info(f"  (Total: {len(INTERNATIONAL_SUFFIXES)} suffixes)")
    logger.info("")

    # Get Supabase client
    supabase = get_supabase_client()

    # Confirm
    response = input("Do you want to DELETE all international symbols? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        logger.info("Operation cancelled")
        return 0

    # Clean each table
    logger.info("\nStarting batch cleanup...")
    import time
    start_time = time.time()

    total_deleted = 0

    for table in TABLES_TO_CLEAN:
        try:
            deleted = cleanup_table_batch(supabase, table)
            total_deleted += deleted
        except Exception as e:
            logger.error(f"Failed to clean {table}: {e}")

    elapsed = time.time() - start_time

    logger.info("")
    logger.info("="*80)
    logger.info(f"✅ CLEANUP COMPLETE")
    logger.info(f"   Total deleted: {total_deleted:,} symbols")
    logger.info(f"   Time elapsed: {elapsed:.1f}s")
    logger.info(f"   Avg speed: {total_deleted/elapsed:.0f} symbols/sec")
    logger.info("="*80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
