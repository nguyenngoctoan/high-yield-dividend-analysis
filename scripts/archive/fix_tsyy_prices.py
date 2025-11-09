#!/usr/bin/env python3
"""
Quick test script to fix TSYY prices specifically.
"""

import logging
import sys

sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from lib.processors.price_processor import PriceProcessor
from lib.data_sources.yahoo_client import YahooClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Updating TSYY prices with fixed Yahoo client...")

    processor = PriceProcessor(yahoo_client=YahooClient())

    # Force full refresh for TSYY
    success = processor.process_and_store(
        'TSYY',
        from_date=None,  # Use incremental logic
        use_hybrid=True,
        force_full_refresh=False
    )

    if success:
        logger.info("✅ TSYY prices updated successfully!")
        logger.info("\nVerifying the fix...")

        # Query the database to verify
        from supabase_helpers import get_supabase_client
        supabase = get_supabase_client()

        response = supabase.table('raw_stock_prices').select(
            'date, close, adj_close'
        ).eq('symbol', 'TSYY').order('date', desc=True).limit(5).execute()

        if response.data:
            logger.info("\nMost recent TSYY prices:")
            logger.info(f"{'Date':<12} {'Close':>10} {'Adj Close':>10} {'Difference':>12}")
            logger.info("-" * 48)
            for row in response.data:
                diff = float(row['close']) - float(row['adj_close'])
                logger.info(
                    f"{row['date']:<12} "
                    f"{float(row['close']):>10.2f} "
                    f"{float(row['adj_close']):>10.2f} "
                    f"{diff:>12.2f}"
                )
    else:
        logger.error("❌ Failed to update TSYY prices")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
