#!/usr/bin/env python3
"""
Simplified Stock Data Update Script (Version 2)

This is a refactored version of update_stock.py that uses the modular library.
Reduced from 3,821 lines to ~400 lines (90% reduction) while maintaining all functionality.

The heavy lifting is now done by:
- lib/core: Configuration, rate limiting, models
- lib/data_sources: API clients (FMP, Yahoo, Alpha Vantage)
- lib/discovery: Symbol discovery and validation
- lib/processors: Price, dividend, and company data processing
"""

import argparse
import sys
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

# Import our modular library
from lib.core.config import Config
from lib.discovery.symbol_discovery import SymbolDiscovery
from lib.discovery.symbol_validator import SymbolValidator
from lib.discovery.portfolio_helper import get_portfolio_symbols
from lib.processors.price_processor import PriceProcessor
from lib.processors.dividend_processor import DividendProcessor
from lib.processors.company_processor import CompanyProcessor
from lib.processors.holdings_processor import HoldingsProcessor
from lib.processors.etf_classifier import ETFClassifier

# Import Supabase helpers
from supabase_helpers import (
    test_supabase_connection,
    supabase_select,
    supabase_insert
)

# Setup logger
logger = Config.setup()


class StockDataPipeline:
    """
    Main data pipeline orchestrator.

    Coordinates symbol discovery, validation, and data processing.
    """

    def __init__(self):
        """Initialize pipeline with all processors."""
        # Get portfolio symbols for validation bypass
        logger.info("📋 Loading portfolio symbols for validation bypass...")
        self.portfolio_symbols = get_portfolio_symbols()
        if self.portfolio_symbols:
            logger.info(f"✅ Loaded {len(self.portfolio_symbols)} portfolio symbols")
            logger.debug(f"   Portfolio symbols: {', '.join(sorted(list(self.portfolio_symbols)[:10]))}...")
        else:
            logger.info("⚠️  No portfolio symbols found")

        # Initialize processors with portfolio symbols
        self.discovery = SymbolDiscovery()
        self.validator = SymbolValidator(portfolio_symbols=self.portfolio_symbols)
        self.price_processor = PriceProcessor()
        self.dividend_processor = DividendProcessor()
        self.company_processor = CompanyProcessor()
        self.holdings_processor = HoldingsProcessor()
        self.etf_classifier = ETFClassifier()

    def run_discovery_mode(self, limit: int = None, validate: bool = True) -> Dict[str, Any]:
        """
        Discovery mode: Find new symbols and optionally validate them.

        Args:
            limit: Optional limit per discovery source
            validate: Whether to validate discovered symbols

        Returns:
            Dictionary with discovery results
        """
        logger.info("=" * 60)
        logger.info("DISCOVERY MODE")
        logger.info("=" * 60)

        # 1. Discover symbols from all sources
        logger.info("🔍 Step 1: Discovering symbols from all sources...")
        symbols = self.discovery.discover_comprehensive(
            include_etfs=True,
            include_dividend_stocks=True,
            limit_per_source=limit
        )

        logger.info(f"✅ Discovered {len(symbols)} unique symbols")

        if not symbols:
            logger.warning("⚠️  No symbols discovered")
            return {'discovered': 0, 'valid': 0, 'invalid': 0}

        # 2. Filter out existing and excluded symbols to only validate new ones
        logger.info("🔍 Step 2: Checking which symbols are new...")
        existing_symbols = set()
        excluded_symbols = set()

        # Get existing symbols from raw_stocks
        try:
            existing_records = supabase_select('raw_stocks', 'symbol', limit=None)
            if existing_records:
                existing_symbols = {r['symbol'] for r in existing_records}
                logger.info(f"📊 Found {len(existing_symbols)} existing symbols in database")
        except Exception as e:
            logger.warning(f"⚠️  Could not fetch existing symbols: {e}")

        # Get excluded symbols from raw_stocks_excluded
        try:
            excluded_records = supabase_select('raw_stocks_excluded', 'symbol', limit=None)
            if excluded_records:
                excluded_symbols = {r['symbol'] for r in excluded_records}
                logger.info(f"📊 Found {len(excluded_symbols)} previously excluded symbols")
        except Exception as e:
            logger.warning(f"⚠️  Could not fetch excluded symbols: {e}")

        # Filter out both existing and excluded symbols
        skip_symbols = existing_symbols | excluded_symbols
        symbol_strings = [s['symbol'] if isinstance(s, dict) else s for s in symbols]
        new_symbols = [s for s in symbols if (s['symbol'] if isinstance(s, dict) else s) not in skip_symbols]
        existing_count = len(symbols) - len(new_symbols)

        logger.info(
            f"📊 Symbol breakdown: {len(new_symbols)} new, "
            f"{len(existing_symbols)} in database, {len(excluded_symbols)} previously excluded"
        )

        # 3. Validate only new symbols if requested
        if validate and new_symbols:
            logger.info(
                f"🔍 Step 3: Validating {len(new_symbols)} new symbols "
                f"(skipping {len(existing_symbols)} existing + {len(excluded_symbols)} excluded)..."
            )
            validation_results = self.validator.validate_batch(new_symbols)

            valid_symbols = [s for s, r in validation_results.items() if r.is_valid]
            invalid_symbols = [s for s, r in validation_results.items() if not r.is_valid]

            logger.info(f"✅ Validation complete: {len(valid_symbols)} valid, {len(invalid_symbols)} invalid")

            # 4. Store excluded symbols
            if invalid_symbols:
                logger.info("💾 Step 4: Storing excluded symbols...")
                excluded_records = []
                for symbol in invalid_symbols:
                    result = validation_results[symbol]
                    excluded_records.append({
                        'symbol': symbol,
                        'reason': result.exclusion_reason,
                        'validation_attempts': 1
                    })

                try:
                    supabase_insert('raw_stocks_excluded', excluded_records, batch_size=100)
                    logger.info(f"✅ Stored {len(excluded_records)} excluded symbols")
                except Exception as e:
                    logger.error(f"❌ Failed to store excluded symbols: {e}")

            # 5. Store valid symbols to database so update mode can process them
            if valid_symbols:
                logger.info("💾 Step 5: Adding valid symbols to database...")
                valid_records = []

                # Build records with metadata from original discovery
                symbol_dict = {s['symbol'] if isinstance(s, dict) else s: s for s in symbols}

                for symbol in valid_symbols:
                    # Get original discovery data if available
                    symbol_data = symbol_dict.get(symbol, {})
                    if isinstance(symbol_data, str):
                        symbol_data = {'symbol': symbol_data}

                    record = {
                        'symbol': symbol,
                        'exchange': symbol_data.get('exchangeShortName') or symbol_data.get('exchange'),
                        # name, sector, industry, etc. will be filled by update mode
                    }
                    valid_records.append(record)

                try:
                    supabase_insert('raw_stocks', valid_records, batch_size=500)
                    logger.info(f"✅ Added {len(valid_records)} valid symbols to database")
                except Exception as e:
                    logger.error(f"❌ Failed to add valid symbols: {e}")
                    logger.info("⚠️  Symbols may need to be added manually or via update mode with symbol list")

            return {
                'discovered': len(symbols),
                'new': len(new_symbols),
                'existing': existing_count,
                'valid': len(valid_symbols),
                'invalid': len(invalid_symbols),
                'valid_symbols': valid_symbols
            }
        elif validate and not new_symbols:
            logger.info("✅ No new symbols to validate - all discovered symbols already exist")
            return {
                'discovered': len(symbols),
                'new': 0,
                'existing': existing_count,
                'valid': 0,
                'invalid': 0,
                'valid_symbols': []
            }
        else:
            return {
                'discovered': len(symbols),
                'new': len(new_symbols),
                'existing': existing_count,
                'symbols': [s['symbol'] if isinstance(s, dict) else s for s in symbols]
            }

    def run_update_mode(self, symbols: List[str] = None,
                       update_prices: bool = True,
                       update_dividends: bool = True,
                       update_companies: bool = True,
                       from_date: date = None) -> Dict[str, Any]:
        """
        Update mode: Fetch and store data for symbols.

        Args:
            symbols: List of symbols to update (if None, uses database)
            update_prices: Whether to update prices
            update_dividends: Whether to update dividends
            update_companies: Whether to update company info
            from_date: Start date for historical data

        Returns:
            Dictionary with update results
        """
        logger.info("=" * 60)
        logger.info("UPDATE MODE")
        logger.info("=" * 60)

        # Get symbols from database if not provided
        if symbols is None:
            logger.info("📊 Fetching symbols from database...")
            db_symbols = supabase_select('raw_stocks', 'symbol', limit=None)
            symbols = [s['symbol'] for s in db_symbols] if db_symbols else []
            logger.info(f"✅ Found {len(symbols)} symbols in database")

        if not symbols:
            logger.warning("⚠️  No symbols to update")
            return {'prices': 0, 'dividends': 0, 'companies': 0}

        results = {}

        # 1. Update prices
        if update_prices:
            logger.info(f"📊 Step 1: Updating prices for {len(symbols)} symbols...")
            self.price_processor.process_batch(symbols, from_date=from_date)
            results['prices'] = {
                'successful': self.price_processor.stats.successful,
                'failed': self.price_processor.stats.failed,
                'total': len(symbols)
            }
            logger.info(
                f"✅ Prices complete: {results['prices']['successful']} successful, "
                f"{results['prices']['failed']} failed"
            )

        # 2. Update dividends
        if update_dividends:
            logger.info(f"💰 Step 2: Updating dividends for {len(symbols)} symbols...")
            self.dividend_processor.process_batch(symbols, from_date=from_date)
            results['dividends'] = {
                'successful': self.dividend_processor.stats.successful,
                'skipped': self.dividend_processor.stats.skipped,
                'failed': self.dividend_processor.stats.failed,
                'total': len(symbols)
            }
            logger.info(
                f"✅ Dividends complete: {results['dividends']['successful']} successful, "
                f"{results['dividends']['skipped']} skipped (no dividends), "
                f"{results['dividends']['failed']} failed"
            )

        # 3. Update company info
        if update_companies:
            logger.info(f"🏢 Step 3: Updating company info for {len(symbols)} symbols...")
            self.company_processor.process_batch(symbols)
            results['companies'] = {
                'successful': self.company_processor.stats.successful,
                'failed': self.company_processor.stats.failed,
                'total': len(symbols)
            }
            logger.info(
                f"✅ Companies complete: {results['companies']['successful']} successful, "
                f"{results['companies']['failed']} failed"
            )

        return results

    def run_refresh_null_companies(self, limit: int = None) -> Dict[str, Any]:
        """
        Refresh mode: Fix NULL company names.

        Args:
            limit: Optional limit on symbols to process

        Returns:
            Summary dictionary
        """
        logger.info("=" * 60)
        logger.info("REFRESH NULL COMPANIES MODE")
        logger.info("=" * 60)

        summary = self.company_processor.refresh_null_company_names(limit=limit)

        logger.info(
            f"✅ Refresh complete: {summary['successful']} successful, "
            f"{summary['failed']} failed, {summary['success_rate']} success rate"
        )

        return summary

    def run_future_dividends(self, days_ahead: int = 90) -> bool:
        """
        Fetch and store future dividend calendar.

        Args:
            days_ahead: Number of days to look ahead (default: 90)

        Returns:
            True if successful
        """
        logger.info("=" * 60)
        logger.info("FUTURE DIVIDENDS MODE")
        logger.info("=" * 60)

        from_date = datetime.now().date()
        to_date = from_date + timedelta(days=days_ahead)

        logger.info(f"🔮 Fetching dividend calendar from {from_date} to {to_date}...")

        success = self.dividend_processor.store_future_dividends(
            from_date=from_date,
            to_date=to_date
        )

        if success:
            logger.info("✅ Future dividends updated successfully")
        else:
            logger.error("❌ Failed to update future dividends")

        return success

    def run_update_holdings(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Update ETF holdings for all ETFs in the database.

        Args:
            limit: Optional limit on number of ETFs to process

        Returns:
            Summary dictionary
        """
        logger.info("=" * 60)
        logger.info("UPDATE ETF HOLDINGS MODE")
        logger.info("=" * 60)

        summary = self.holdings_processor.update_all_etfs(limit=limit)

        logger.info(
            f"✅ Holdings update complete: {summary['successful']} successful, "
            f"{summary['skipped']} skipped, {summary['failed']} failed, "
            f"{summary['success_rate']} success rate"
        )

        return summary

    def run_classify_etfs(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Classify unclassified ETFs (set investment_strategy and related_stock).

        Args:
            limit: Optional limit on number of ETFs to classify

        Returns:
            Summary dictionary
        """
        logger.info("=" * 60)
        logger.info("CLASSIFY ETFs MODE")
        logger.info("=" * 60)

        summary = self.etf_classifier.classify_unclassified_etfs(limit=limit)

        logger.info(
            f"✅ Classification complete: {summary['successful']} classified, "
            f"{summary['skipped']} skipped (not ETFs), {summary['failed']} failed, "
            f"{summary['success_rate']} success rate"
        )

        return summary


def main():
    """Main entry point with command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Simplified Stock Data Update Script (Version 2)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discovery mode (find new symbols)
  python update_stock_v2.py --mode discover --limit 100

  # Discovery with validation
  python update_stock_v2.py --mode discover --validate

  # Update all symbols
  python update_stock_v2.py --mode update

  # Update prices only
  python update_stock_v2.py --mode update --prices-only

  # Refresh NULL company names
  python update_stock_v2.py --mode refresh-companies --limit 1000

  # Fetch future dividends
  python update_stock_v2.py --mode future-dividends
        """
    )

    parser.add_argument('--mode', type=str, required=True,
                       choices=['discover', 'update', 'refresh-companies', 'future-dividends', 'update-holdings', 'classify-etfs'],
                       help='Operation mode')

    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of symbols to process')

    parser.add_argument('--validate', action='store_true',
                       help='Validate discovered symbols (discovery mode)')

    parser.add_argument('--prices-only', action='store_true',
                       help='Update prices only (update mode)')

    parser.add_argument('--dividends-only', action='store_true',
                       help='Update dividends only (update mode)')

    parser.add_argument('--companies-only', action='store_true',
                       help='Update companies only (update mode)')

    parser.add_argument('--from-date', type=str, default=None,
                       help='Start date for historical data (YYYY-MM-DD)')

    parser.add_argument('--days-ahead', type=int, default=90,
                       help='Days ahead for future dividends (default: 90)')

    args = parser.parse_args()

    # Test Supabase connection
    logger.info("🔌 Testing Supabase connection...")
    if not test_supabase_connection():
        logger.error("❌ Supabase connection failed - exiting")
        sys.exit(1)
    logger.info("✅ Supabase connection successful")

    # Parse from_date if provided
    from_date = None
    if args.from_date:
        try:
            from_date = datetime.strptime(args.from_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"❌ Invalid date format: {args.from_date}. Use YYYY-MM-DD")
            sys.exit(1)

    # Initialize pipeline
    pipeline = StockDataPipeline()

    # Execute based on mode
    try:
        if args.mode == 'discover':
            results = pipeline.run_discovery_mode(
                limit=args.limit,
                validate=args.validate
            )
            logger.info(f"📊 Discovery Results: {results}")

        elif args.mode == 'update':
            # Check if today is a weekend (Saturday=5, Sunday=6 in weekday())
            from datetime import datetime
            is_weekend = datetime.now().weekday() in [5, 6]

            # Determine what to update
            update_prices = not (args.dividends_only or args.companies_only) or args.prices_only
            update_dividends = not (args.prices_only or args.companies_only) or args.dividends_only
            update_companies = not (args.prices_only or args.dividends_only) or args.companies_only

            # Skip price updates on weekends (markets closed)
            if is_weekend and update_prices:
                day_name = datetime.now().strftime('%A')
                logger.info(f"⏭️  Skipping price updates - markets closed on {day_name}")
                update_prices = False

            results = pipeline.run_update_mode(
                update_prices=update_prices,
                update_dividends=update_dividends,
                update_companies=update_companies,
                from_date=from_date
            )
            logger.info(f"📊 Update Results: {results}")

        elif args.mode == 'refresh-companies':
            summary = pipeline.run_refresh_null_companies(limit=args.limit)
            logger.info(f"📊 Refresh Summary: {summary}")

        elif args.mode == 'future-dividends':
            success = pipeline.run_future_dividends(days_ahead=args.days_ahead)
            sys.exit(0 if success else 1)

        elif args.mode == 'update-holdings':
            summary = pipeline.run_update_holdings(limit=args.limit)
            logger.info(f"📊 Holdings Update Summary: {summary}")

        elif args.mode == 'classify-etfs':
            summary = pipeline.run_classify_etfs(limit=args.limit)
            logger.info(f"📊 Classification Summary: {summary}")

        logger.info("=" * 60)
        logger.info("✅ PIPELINE COMPLETE")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
