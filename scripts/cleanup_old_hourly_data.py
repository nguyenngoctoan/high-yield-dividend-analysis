#!/usr/bin/env python3
"""
Clean up old hourly price data.

This script deletes hourly price records older than 1 day.
Designed to run via cron daily.
"""

import sys
from datetime import datetime, timedelta
from supabase_helpers import get_supabase_client
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hourly_cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def cleanup_old_hourly_data(days_to_keep=1):
    """
    Delete hourly price data older than specified days.

    Args:
        days_to_keep: Number of days to retain (default: 1)
    """
    logger.info("=" * 80)
    logger.info(f"🗑️  CLEANING UP HOURLY DATA OLDER THAN {days_to_keep} DAY(S)")
    logger.info("=" * 80)

    supabase = get_supabase_client()

    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')

    logger.info(f"Cutoff: {cutoff_str}")
    logger.info(f"Deleting records older than: {cutoff_date.strftime('%Y-%m-%d')}")

    try:
        # Count records to be deleted
        count_result = supabase.table('raw_stock_prices_hourly').select('id', count='exact').lt('timestamp', cutoff_date.isoformat()).execute()
        records_to_delete = len(count_result.data)

        if records_to_delete == 0:
            logger.info("✅ No old records to delete")
            return

        logger.info(f"📊 Found {records_to_delete:,} records to delete")

        # Delete old records
        delete_result = supabase.table('raw_stock_prices_hourly').delete().lt('timestamp', cutoff_date.isoformat()).execute()

        deleted_count = len(delete_result.data) if delete_result.data else 0

        logger.info(f"✅ Deleted {deleted_count:,} old hourly records")

        # Check remaining data
        remaining_result = supabase.table('raw_stock_prices_hourly').select('id', count='exact').execute()
        remaining_count = len(remaining_result.data)

        logger.info(f"📊 Remaining records: {remaining_count:,}")

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        raise

    logger.info("=" * 80)
    logger.info("✅ CLEANUP COMPLETE")
    logger.info("=" * 80)

if __name__ == "__main__":
    try:
        cleanup_old_hourly_data(days_to_keep=1)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
