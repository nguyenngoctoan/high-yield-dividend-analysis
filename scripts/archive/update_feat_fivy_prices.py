#!/usr/bin/env python3
"""
Update FEAT and FIVY Price Data

Fetches price data from Yahoo Finance for FEAT and FIVY symbols
which don't have data from FMP.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.processors.price_processor import PriceProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Update FEAT and FIVY prices from Yahoo Finance."""
    symbols = ['FEAT', 'FIVY']

    logger.info(f"🚀 Starting price update for {len(symbols)} symbols: {', '.join(symbols)}")

    # Create processor
    processor = PriceProcessor()

    # Process each symbol
    results = {}
    for symbol in symbols:
        logger.info(f"\n📊 Processing {symbol}...")

        # Force full refresh to get all historical data
        success = processor.process_and_store(
            symbol,
            use_hybrid=True,
            force_full_refresh=True
        )

        results[symbol] = success

        if success:
            logger.info(f"✅ {symbol}: Successfully updated prices")
        else:
            logger.error(f"❌ {symbol}: Failed to update prices")

    # Summary
    logger.info("\n" + "="*80)
    logger.info("📈 PRICE UPDATE SUMMARY")
    logger.info("="*80)

    successful = [s for s, success in results.items() if success]
    failed = [s for s, success in results.items() if not success]

    logger.info(f"✅ Successful: {len(successful)}")
    if successful:
        logger.info(f"   Symbols: {', '.join(successful)}")

    logger.info(f"❌ Failed: {len(failed)}")
    if failed:
        logger.info(f"   Symbols: {', '.join(failed)}")

    logger.info("="*80)

    # Get statistics
    stats = processor.get_statistics()
    logger.info(f"\n📊 Processing Statistics:")
    logger.info(f"   Total processed: {stats['total_processed']}")
    logger.info(f"   Successful: {stats['successful']}")
    logger.info(f"   Failed: {stats['failed']}")
    logger.info(f"   Success rate: {stats['success_rate']}")

    if stats['error_count'] > 0:
        logger.warning(f"\n⚠️  {stats['error_count']} errors occurred during processing")

    return 0 if len(failed) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
