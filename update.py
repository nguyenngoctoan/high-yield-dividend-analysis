#!/usr/bin/env python3
"""
Unified Stock Data Update Script

All-in-one script for stock data updates with multiple modes:
- batch: Ultra-fast daily price updates (recommended, 1-5 min)
- aggressive: High-throughput mode with 200+ workers (700+ calls/min)
- discover: Find and validate new symbols (weekly task)
- refresh: Update company names, dividends, ETF classifications

Usage Examples:
    # Daily price updates (recommended)
    python3 update.py --mode batch

    # Aggressive mode (fallback if batch has issues)
    python3 update.py --mode aggressive --workers 200

    # Weekly symbol discovery
    python3 update.py --mode discover --limit 1000 --validate

    # Refresh company data
    python3 update.py --mode refresh-companies --limit 500

Performance:
    - Batch mode: 1-5 min for 16k+ symbols (38,000+ equiv calls/min)
    - Aggressive mode: 5-10 min for 16k+ symbols (700+ calls/min)
    - Discovery mode: 1-2 hours for validation
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.processors.batch_eod_processor import BatchEODProcessor
from lib.processors.aggressive_processor import AggressiveProcessor
from lib.core.config import Config
from supabase_helpers import test_supabase_connection, supabase_select

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def filter_special_securities(symbols: list) -> tuple:
    """
    Filter out warrants, units, and other special securities.

    Returns:
        (regular_symbols, excluded_symbols)
    """
    excluded = []
    regular = []

    for symbol in symbols:
        is_excluded = False

        # Pattern 1: Ends with separator + suffix (SYMBOL-W, SYMBOL.U)
        if any(symbol.endswith(sep + suf) for sep in ['-', '.']
               for suf in ['W', 'WS', 'WT', 'U', 'UN', 'UU', 'R', 'RT']):
            is_excluded = True

        # Pattern 2: Ends with U (units) - ARBGU, ARCKU, ARGUU
        elif len(symbol) >= 5 and symbol.endswith('U') and symbol[-2].isalpha():
            if symbol.endswith('UU') or (symbol.endswith('U') and not symbol.endswith('RU')):
                is_excluded = True

        # Pattern 3: Ends with W (warrants) - ARCKW, ARGUW, ASPSW
        elif len(symbol) >= 5 and symbol.endswith('W') and symbol[-2].isalpha():
            is_excluded = True

        # Pattern 4: Money market funds (XX, FX suffix)
        elif symbol.endswith('XX') or symbol.endswith('FX'):
            is_excluded = True

        # Pattern 5: Foreign exchanges (.V, .TO)
        elif '.V' in symbol or '.TO' in symbol:
            is_excluded = True

        if is_excluded:
            excluded.append(symbol)
        else:
            regular.append(symbol)

    return regular, excluded


def run_batch_mode(args):
    """Run ultra-fast batch EOD mode."""
    # Parse target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = date.today() - timedelta(days=1)

    logger.info("✅ Configuration validated successfully")

    # Initialize processor
    processor = BatchEODProcessor()

    # Run batch EOD update
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


def run_aggressive_mode(args):
    """Run aggressive high-throughput mode."""
    # Test Supabase connection
    logger.info("🔌 Testing Supabase connection...")
    if not test_supabase_connection():
        logger.error("❌ Supabase connection failed - exiting")
        sys.exit(1)
    logger.info("✅ Supabase connection successful")

    # Get symbols
    logger.info("📊 Fetching symbols from database...")
    db_symbols = supabase_select('raw_stocks', 'symbol', limit=None)
    all_symbols = [s['symbol'] for s in db_symbols] if db_symbols else []

    # Filter out special securities
    logger.info("🔍 Filtering out warrants, units, and special securities...")
    symbols, excluded = filter_special_securities(all_symbols)

    logger.info(f"✅ Found {len(all_symbols):,} total symbols")
    if excluded:
        logger.info(f"🚫 Excluded {len(excluded):,} warrants/units/rights from price updates")
        logger.info(f"📊 Processing {len(symbols):,} regular securities")

    if args.test:
        symbols = symbols[:100]
        logger.info(f"🧪 TEST MODE: Processing first 100 symbols")
    elif args.limit:
        symbols = symbols[:args.limit]
        logger.info(f"✅ Limited to {args.limit:,} symbols")

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


def run_discovery_mode(args):
    """Run symbol discovery and validation mode."""
    from lib.pipelines.stock_data_pipeline import StockDataPipeline

    # Test Supabase connection
    logger.info("🔌 Testing Supabase connection...")
    if not test_supabase_connection():
        logger.error("❌ Supabase connection failed - exiting")
        sys.exit(1)
    logger.info("✅ Supabase connection successful")

    # Initialize pipeline
    pipeline = StockDataPipeline()

    # Run discovery
    results = pipeline.run_discovery_mode(
        limit=args.limit,
        validate=args.validate
    )
    logger.info(f"📊 Discovery Results: {results}")


def run_refresh_mode(args):
    """Run data refresh mode (companies, dividends, etc)."""
    from lib.pipelines.stock_data_pipeline import StockDataPipeline

    # Test Supabase connection
    logger.info("🔌 Testing Supabase connection...")
    if not test_supabase_connection():
        logger.error("❌ Supabase connection failed - exiting")
        sys.exit(1)
    logger.info("✅ Supabase connection successful")

    # Initialize pipeline
    pipeline = StockDataPipeline()

    # Execute based on submode
    if args.submode == 'companies':
        logger.info("🏢 Refreshing company data...")
        results = pipeline.run_refresh_companies_mode(limit=args.limit)
    elif args.submode == 'dividends':
        days_ahead = args.days_ahead if hasattr(args, 'days_ahead') else 90
        logger.info(f"💰 Fetching future dividends ({days_ahead} days ahead)...")
        results = pipeline.run_future_dividends_mode(days_ahead=days_ahead)
    elif args.submode == 'etfs':
        logger.info("📊 Classifying ETFs...")
        results = pipeline.run_classify_etfs_mode()

    logger.info(f"📊 Refresh Results: {results}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Unified Stock Data Update Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Daily price updates (recommended - fastest)
  python3 update.py --mode batch
  python3 update.py --mode batch --date 2025-11-12

  # Aggressive mode (fallback if batch has issues)
  python3 update.py --mode aggressive --workers 200
  python3 update.py --mode aggressive --test

  # Weekly symbol discovery
  python3 update.py --mode discover --limit 1000
  python3 update.py --mode discover --validate

  # Refresh data
  python3 update.py --mode refresh --submode companies --limit 500
  python3 update.py --mode refresh --submode dividends --days-ahead 90
  python3 update.py --mode refresh --submode etfs

Modes:
  batch        Ultra-fast batch price updates (1-5 min, recommended for daily)
  aggressive   High-throughput mode with workers (5-10 min, fallback)
  discover     Find and validate new symbols (weekly task)
  refresh      Refresh company data, dividends, ETF classifications
        """
    )

    parser.add_argument(
        '--mode',
        type=str,
        required=True,
        choices=['batch', 'aggressive', 'discover', 'refresh'],
        help='Operation mode'
    )

    parser.add_argument(
        '--submode',
        type=str,
        choices=['companies', 'dividends', 'etfs'],
        help='Refresh submode (for --mode refresh)'
    )

    # Batch mode options
    parser.add_argument(
        '--date',
        type=str,
        help='Target date for batch mode (YYYY-MM-DD). Defaults to yesterday.'
    )

    # Aggressive mode options
    parser.add_argument(
        '--workers',
        type=int,
        default=200,
        help='Number of concurrent workers for aggressive mode (default: 200)'
    )

    # Common options
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of symbols to process'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode with limited symbols'
    )

    # Discovery mode options
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate discovered symbols (discovery mode)'
    )

    # Refresh mode options
    parser.add_argument(
        '--days-ahead',
        type=int,
        default=90,
        help='Days ahead for future dividends (default: 90)'
    )

    args = parser.parse_args()

    # Validate submode requirement
    if args.mode == 'refresh' and not args.submode:
        parser.error("--mode refresh requires --submode (companies|dividends|etfs)")

    try:
        if args.mode == 'batch':
            run_batch_mode(args)
        elif args.mode == 'aggressive':
            run_aggressive_mode(args)
        elif args.mode == 'discover':
            run_discovery_mode(args)
        elif args.mode == 'refresh':
            run_refresh_mode(args)

        sys.exit(0)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("⚠️  Interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Error during update: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
