"""
Stock Data Pipeline

High-level orchestration pipeline for stock data workflows including:
- Symbol discovery and validation
- Company data refresh
- Dividend data updates
- ETF classification

This pipeline coordinates multiple processors and data sources to provide
complete workflows for the update.py script.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from lib.discovery.symbol_discovery import SymbolDiscovery
from lib.discovery.symbol_validator import SymbolValidator
from lib.processors.company_processor import CompanyProcessor
from lib.processors.dividend_processor import DividendProcessor
from lib.processors.etf_classifier import ETFClassifier
from supabase_helpers import supabase_select, supabase_upsert

logger = logging.getLogger(__name__)


class StockDataPipeline:
    """
    High-level pipeline for orchestrating stock data workflows.

    Coordinates symbol discovery, validation, company data refresh,
    dividend updates, and ETF classification.
    """

    def __init__(self):
        """Initialize the pipeline with required processors."""
        self.symbol_discovery = SymbolDiscovery()
        self.symbol_validator = SymbolValidator()
        self.company_processor = CompanyProcessor()
        self.dividend_processor = DividendProcessor()
        self.etf_classifier = ETFClassifier()

    def run_discovery_mode(self, limit: Optional[int] = None,
                          validate: bool = False) -> Dict[str, Any]:
        """
        Run symbol discovery mode to find new symbols.

        Args:
            limit: Optional limit on number of symbols to discover
            validate: Whether to validate discovered symbols

        Returns:
            Dictionary with discovery results
        """
        start_time = datetime.now()
        logger.info("=" * 70)
        logger.info("🔍 SYMBOL DISCOVERY MODE")
        logger.info("=" * 70)
        logger.info(f"Limit: {limit or 'None'}")
        logger.info(f"Validation: {'Enabled' if validate else 'Disabled'}")
        logger.info("=" * 70)
        logger.info("")

        # Discover symbols from all available sources
        logger.info("📊 Discovering symbols from data sources...")
        discovered_symbols = self.symbol_discovery.discover_all_symbols(limit=limit)
        logger.info(f"✅ Discovered {len(discovered_symbols)} symbols")

        results = {
            'discovered_count': len(discovered_symbols),
            'validated_count': 0,
            'added_count': 0,
            'excluded_count': 0,
            'duration_seconds': 0
        }

        if not discovered_symbols:
            logger.warning("⚠️ No symbols discovered")
            return results

        # Optionally validate symbols
        if validate:
            logger.info("")
            logger.info("🔍 Validating discovered symbols...")

            # Get existing symbols from database
            existing = supabase_select('raw_stocks', 'symbol', limit=None)
            existing_symbols = {s['symbol'] for s in existing} if existing else set()

            # Filter out already-existing symbols
            new_symbols = [s for s in discovered_symbols
                          if s.get('symbol') not in existing_symbols]
            logger.info(f"📊 Found {len(new_symbols)} new symbols (not in database)")

            if new_symbols:
                # Validate new symbols
                validated = []
                excluded = []

                for i, symbol_data in enumerate(new_symbols, 1):
                    symbol = symbol_data.get('symbol')
                    if not symbol:
                        continue

                    if i % 100 == 0:
                        logger.info(f"   Progress: {i}/{len(new_symbols)}")

                    # Validate symbol
                    is_valid = self.symbol_validator.validate_symbol(symbol)

                    if is_valid:
                        validated.append(symbol_data)
                    else:
                        excluded.append(symbol)

                logger.info(f"✅ Validated: {len(validated)} symbols")
                logger.info(f"❌ Excluded: {len(excluded)} invalid symbols")

                # Add validated symbols to database
                if validated:
                    logger.info("")
                    logger.info("💾 Adding validated symbols to database...")
                    records = [{
                        'symbol': s.get('symbol'),
                        'name': s.get('name', s.get('symbol')),
                        'exchange': s.get('exchange'),
                        'type': s.get('type', 'stock'),
                        'data_source': s.get('source', 'discovery')
                    } for s in validated]

                    success = supabase_upsert('raw_stocks', records,
                                             conflict_columns=['symbol'])
                    if success:
                        logger.info(f"✅ Added {len(validated)} symbols to database")
                        results['added_count'] = len(validated)
                    else:
                        logger.error("❌ Failed to add symbols to database")

                # Add excluded symbols to exclusion table
                if excluded:
                    logger.info(f"💾 Adding {len(excluded)} excluded symbols...")
                    excluded_records = [{
                        'symbol': s,
                        'reason': 'validation_failed',
                        'excluded_at': datetime.now().isoformat()
                    } for s in excluded]

                    supabase_upsert('raw_excluded_symbols', excluded_records,
                                   conflict_columns=['symbol'])
                    results['excluded_count'] = len(excluded)

                results['validated_count'] = len(validated)

        duration = (datetime.now() - start_time).total_seconds()
        results['duration_seconds'] = duration

        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ DISCOVERY COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Discovered: {results['discovered_count']}")
        logger.info(f"Validated: {results['validated_count']}")
        logger.info(f"Added: {results['added_count']}")
        logger.info(f"Excluded: {results['excluded_count']}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info("=" * 70)

        return results

    def run_refresh_companies_mode(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Refresh company data (names, exchange, type, etc).

        Args:
            limit: Optional limit on number of companies to refresh

        Returns:
            Dictionary with refresh results
        """
        start_time = datetime.now()
        logger.info("=" * 70)
        logger.info("🏢 COMPANY DATA REFRESH MODE")
        logger.info("=" * 70)
        logger.info(f"Limit: {limit or 'All symbols'}")
        logger.info("=" * 70)
        logger.info("")

        # Get symbols from database
        logger.info("📊 Fetching symbols from database...")
        symbols_data = supabase_select('raw_stocks', 'symbol', limit=limit)
        symbols = [s['symbol'] for s in symbols_data] if symbols_data else []
        logger.info(f"✅ Found {len(symbols)} symbols to refresh")

        if not symbols:
            logger.warning("⚠️ No symbols to refresh")
            return {'refreshed_count': 0, 'duration_seconds': 0}

        # Refresh company data
        logger.info("")
        logger.info("🔄 Refreshing company data...")
        refreshed_count = 0

        for i, symbol in enumerate(symbols, 1):
            if i % 100 == 0:
                logger.info(f"   Progress: {i}/{len(symbols)}")

            # Fetch and update company info
            company_info = self.company_processor.fetch_company_info(symbol)
            if company_info:
                refreshed_count += 1

        duration = (datetime.now() - start_time).total_seconds()

        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ COMPANY REFRESH COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Refreshed: {refreshed_count}/{len(symbols)}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info("=" * 70)

        return {
            'total_symbols': len(symbols),
            'refreshed_count': refreshed_count,
            'duration_seconds': duration
        }

    def run_future_dividends_mode(self, days_ahead: int = 90) -> Dict[str, Any]:
        """
        Fetch future dividend payments.

        Args:
            days_ahead: Number of days ahead to fetch dividends

        Returns:
            Dictionary with dividend fetch results
        """
        start_time = datetime.now()
        logger.info("=" * 70)
        logger.info("💰 FUTURE DIVIDENDS MODE")
        logger.info("=" * 70)
        logger.info(f"Days ahead: {days_ahead}")
        logger.info("=" * 70)
        logger.info("")

        # Get symbols with dividend history
        logger.info("📊 Fetching dividend-paying symbols...")
        cutoff_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        # Query for symbols with recent dividends
        dividend_symbols = supabase_select(
            'raw_dividends',
            'symbol',
            filters={'ex_date': f'gte.{cutoff_date}'},
            limit=None
        )

        unique_symbols = list(set(s['symbol'] for s in dividend_symbols)) if dividend_symbols else []
        logger.info(f"✅ Found {len(unique_symbols)} dividend-paying symbols")

        if not unique_symbols:
            logger.warning("⚠️ No dividend-paying symbols found")
            return {'fetched_count': 0, 'duration_seconds': 0}

        # Fetch future dividends
        logger.info("")
        logger.info(f"🔄 Fetching future dividends ({days_ahead} days ahead)...")
        fetched_count = 0

        for i, symbol in enumerate(unique_symbols, 1):
            if i % 100 == 0:
                logger.info(f"   Progress: {i}/{len(unique_symbols)}")

            # Fetch future dividends for symbol
            dividends = self.dividend_processor.fetch_future_dividends(
                symbol,
                days_ahead=days_ahead
            )
            if dividends:
                fetched_count += len(dividends)

        duration = (datetime.now() - start_time).total_seconds()

        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ DIVIDEND FETCH COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Symbols processed: {len(unique_symbols)}")
        logger.info(f"Dividends fetched: {fetched_count}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info("=" * 70)

        return {
            'symbols_processed': len(unique_symbols),
            'fetched_count': fetched_count,
            'duration_seconds': duration
        }

    def run_classify_etfs_mode(self) -> Dict[str, Any]:
        """
        Classify ETFs in the database.

        Returns:
            Dictionary with classification results
        """
        start_time = datetime.now()
        logger.info("=" * 70)
        logger.info("📊 ETF CLASSIFICATION MODE")
        logger.info("=" * 70)
        logger.info("")

        # Get all symbols
        logger.info("📊 Fetching symbols from database...")
        symbols_data = supabase_select('raw_stocks', 'symbol,type', limit=None)
        symbols = [s['symbol'] for s in symbols_data] if symbols_data else []
        logger.info(f"✅ Found {len(symbols)} symbols to classify")

        if not symbols:
            logger.warning("⚠️ No symbols to classify")
            return {'classified_count': 0, 'duration_seconds': 0}

        # Classify ETFs
        logger.info("")
        logger.info("🔄 Classifying ETFs...")
        classified_count = 0

        results = self.etf_classifier.classify_batch(symbols)
        classified_count = results.get('classified_count', 0)

        duration = (datetime.now() - start_time).total_seconds()

        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ ETF CLASSIFICATION COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Symbols processed: {len(symbols)}")
        logger.info(f"ETFs classified: {classified_count}")
        logger.info(f"Duration: {duration:.1f}s")
        logger.info("=" * 70)

        return {
            'total_symbols': len(symbols),
            'classified_count': classified_count,
            'duration_seconds': duration
        }
