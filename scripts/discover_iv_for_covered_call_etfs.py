#!/usr/bin/env python3
"""
Discover Implied Volatility for Covered Call ETFs

This script discovers and tracks IV data for covered call ETFs using
Alpha Vantage Premium's options chain API. IV is a critical indicator
for covered call ETFs as it directly impacts distribution levels.

Usage:
    python scripts/discover_iv_for_covered_call_etfs.py

Options:
    --limit N          Process only N ETFs (default: all)
    --force            Force rediscovery even if IV was previously found
    --all-symbols      Discover IV for all symbols, not just covered call ETFs
    --test SYMBOL      Test IV discovery for a single symbol
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from lib.core.config import Config
from lib.processors.iv_discovery_processor import (
    IVDiscoveryProcessor, discover_iv, discover_covered_call_etf_iv
)
from lib.data_sources.alpha_vantage_client import AlphaVantageClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_single_symbol(symbol: str):
    """Test IV discovery for a single symbol."""
    logger.info("=" * 80)
    logger.info(f"Testing IV Discovery for {symbol}")
    logger.info("=" * 80)

    # Test Alpha Vantage client directly
    logger.info("\n1. Testing Alpha Vantage Client...")
    av_client = AlphaVantageClient()

    if not av_client.is_available():
        logger.error("❌ Alpha Vantage API key not configured!")
        return False

    logger.info("✅ Alpha Vantage client initialized")

    # Try to fetch options chain
    logger.info(f"\n2. Fetching options chain for {symbol}...")
    options = av_client.fetch_options_chain(symbol, include_greeks=True)

    if options:
        logger.info(f"✅ Found {options['count']} option contracts")
        # Show a sample contract
        if options['data']:
            sample = options['data'][0]
            logger.info("\nSample contract:")
            for key, value in list(sample.items())[:10]:
                logger.info(f"  {key}: {value}")
    else:
        logger.warning(f"⚠️  No options chain found for {symbol}")
        logger.info("Possible reasons:")
        logger.info("  - Symbol doesn't have options")
        logger.info("  - API rate limit reached")
        logger.info("  - Premium subscription not active")
        return False

    # Try to get IV
    logger.info(f"\n3. Calculating IV for {symbol}...")
    iv_data = av_client.get_implied_volatility(symbol)

    if iv_data:
        logger.info(f"✅ IV calculated successfully:")
        logger.info(f"  Overall IV: {iv_data.get('iv', 0):.4f}")
        logger.info(f"  Call IV: {iv_data.get('call_iv', 0):.4f}")
        logger.info(f"  Put IV: {iv_data.get('put_iv', 0):.4f}")
        logger.info(f"  Contracts analyzed: {iv_data.get('contracts_analyzed', 0)}")
    else:
        logger.warning(f"⚠️  Could not calculate IV for {symbol}")
        return False

    # Test using the processor
    logger.info(f"\n4. Testing IV Discovery Processor...")
    result = discover_iv(symbol, force_rediscover=True)

    if result['success']:
        logger.info(f"✅ IV Discovery successful:")
        logger.info(f"  Source: {result['source']}")
        logger.info(f"  IV: {result['iv']:.4f}")
        logger.info(f"  Call IV: {result.get('call_iv', 0):.4f}")
        logger.info(f"  Put IV: {result.get('put_iv', 0):.4f}")
    else:
        logger.error(f"❌ IV Discovery failed")
        return False

    logger.info("\n" + "=" * 80)
    logger.info("✅ All tests passed!")
    logger.info("=" * 80)
    return True


def discover_covered_call_etfs(limit: Optional[int], force: bool):
    """Discover IV for covered call ETFs."""
    logger.info("=" * 80)
    logger.info("Covered Call ETF IV Discovery")
    logger.info("=" * 80)

    logger.info(f"""
Covered call ETFs generate income by selling call options on their holdings.
The implied volatility (IV) of these options is a KEY INDICATOR of potential
distribution levels - higher IV generally means higher premiums and distributions.

Configuration:
  - Limit: {limit or 'None (process all)'}
  - Force Rediscovery: {force}
  - Source: Alpha Vantage Premium
""")

    # Check API key
    av_client = AlphaVantageClient()
    if not av_client.is_available():
        logger.error("\n❌ Alpha Vantage API key not configured!")
        logger.error("Please set ALPHA_VANTAGE_API_KEY in your .env file")
        return False

    logger.info("✅ Alpha Vantage Premium access confirmed\n")

    # Run discovery
    try:
        summary = discover_covered_call_etf_iv(
            limit=limit,
            force_rediscover=force
        )

        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("DISCOVERY SUMMARY")
        logger.info("=" * 80)
        logger.info(f"ETFs Processed: {summary['processed']}")
        logger.info(f"IV Found: {summary['successful']}")
        logger.info(f"No Options Data: {summary['skipped']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success Rate: {summary['success_rate']}")

        if summary.get('etfs_analyzed'):
            logger.info(f"\nCovered Call ETFs Analyzed ({len(summary['etfs_analyzed'])}):")
            for i, symbol in enumerate(summary['etfs_analyzed'][:20], 1):
                logger.info(f"  {i}. {symbol}")
            if len(summary['etfs_analyzed']) > 20:
                logger.info(f"  ... and {len(summary['etfs_analyzed']) - 20} more")

        logger.info("\n" + "=" * 80)

        if summary['successful'] > 0:
            logger.info("\n✅ SUCCESS! IV data has been stored in the database.")
            logger.info("\nYou can now:")
            logger.info("  1. Query IV from raw_stock_prices table")
            logger.info("  2. Use IV for distribution analysis")
            logger.info("  3. Track IV changes over time")
            logger.info("  4. Compare IV across different covered call ETFs")

            logger.info("\nExample SQL query:")
            logger.info("""
  SELECT symbol, date, close, iv
  FROM raw_stock_prices
  WHERE symbol IN (SELECT symbol FROM raw_stocks
                   WHERE investment_strategy LIKE '%covered call%')
    AND iv IS NOT NULL
  ORDER BY date DESC, iv DESC
  LIMIT 20;
""")

        return True

    except Exception as e:
        logger.error(f"\n❌ Error during discovery: {e}")
        import traceback
        traceback.print_exc()
        return False


def discover_all_symbols_iv(limit: Optional[int], force: bool):
    """Discover IV for all symbols."""
    logger.info("=" * 80)
    logger.info("IV Discovery for All Symbols")
    logger.info("=" * 80)

    logger.info(f"""
Configuration:
  - Limit: {limit or 'None (process all liquid symbols)'}
  - Force Rediscovery: {force}
  - Source: Alpha Vantage Premium
  - Filter: Symbols with recent trading activity and volume > 100k
""")

    processor = IVDiscoveryProcessor()

    try:
        summary = processor.discover_all_iv(
            limit=limit,
            force_rediscover=force,
            symbols_with_options_only=True
        )

        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("DISCOVERY SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Symbols Processed: {summary['processed']}")
        logger.info(f"IV Found: {summary['successful']}")
        logger.info(f"No Options Data: {summary['skipped']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success Rate: {summary['success_rate']}")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"\n❌ Error during discovery: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Discover Implied Volatility for Covered Call ETFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with a single covered call ETF
  python scripts/discover_iv_for_covered_call_etfs.py --test XYLD

  # Discover IV for all covered call ETFs
  python scripts/discover_iv_for_covered_call_etfs.py

  # Discover IV for first 10 covered call ETFs
  python scripts/discover_iv_for_covered_call_etfs.py --limit 10

  # Force rediscovery (ignore cached preferences)
  python scripts/discover_iv_for_covered_call_etfs.py --force

  # Discover IV for all liquid symbols
  python scripts/discover_iv_for_covered_call_etfs.py --all-symbols --limit 100

Popular Covered Call ETFs to test:
  XYLD - Global X S&P 500 Covered Call ETF
  QYLD - Global X NASDAQ 100 Covered Call ETF
  RYLD - Global X Russell 2000 Covered Call ETF
  JEPI - JPMorgan Equity Premium Income ETF
  DIVO - Amplify CWP Enhanced Dividend Income ETF
"""
    )

    parser.add_argument(
        '--test',
        type=str,
        metavar='SYMBOL',
        help='Test IV discovery for a single symbol'
    )
    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Process only N ETFs/symbols'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rediscovery even if IV was previously found'
    )
    parser.add_argument(
        '--all-symbols',
        action='store_true',
        help='Discover IV for all liquid symbols, not just covered call ETFs'
    )

    args = parser.parse_args()

    # Initialize config
    try:
        Config.setup()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Run appropriate discovery mode
    try:
        if args.test:
            success = test_single_symbol(args.test.upper())
        elif args.all_symbols:
            success = discover_all_symbols_iv(args.limit, args.force)
        else:
            success = discover_covered_call_etfs(args.limit, args.force)

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.info("\n\nDiscovery interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
