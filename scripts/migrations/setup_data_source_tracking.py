#!/usr/bin/env python3
"""
Setup Data Source Tracking System

This script:
1. Runs the database migration
2. Tests the tracking system
3. Optionally discovers data for a sample of symbols
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.core.config import Config
from lib.utils.data_source_tracker import (
    DataSourceTracker, DataType, DataSource, get_tracker
)
from lib.processors.aum_discovery_processor import AUMDiscoveryProcessor
from lib.processors.data_discovery_processor import DataDiscoveryProcessor
from supabase_helpers import supabase_raw_query

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the data source tracking migration."""
    logger.info("=" * 80)
    logger.info("STEP 1: Running Database Migration")
    logger.info("=" * 80)

    migration_file = Path(__file__).parent.parent / 'migrations' / 'create_data_source_tracking.sql'

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        # Execute migration
        logger.info("Executing migration SQL...")
        supabase_raw_query(migration_sql, params=None, allow_multi=True)

        logger.info("✅ Migration completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


def verify_migration():
    """Verify the migration was successful."""
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Verifying Migration")
    logger.info("=" * 80)

    try:
        # Check if table exists
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'raw_data_source_tracking'
            ) as table_exists
        """
        result = supabase_raw_query(query)

        if not result or not result[0].get('table_exists'):
            logger.error("❌ Table 'raw_data_source_tracking' not found")
            return False

        logger.info("✅ Table 'raw_data_source_tracking' exists")

        # Check if view exists
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.views
                WHERE table_name = 'v_data_source_preferences'
            ) as view_exists
        """
        result = supabase_raw_query(query)

        if not result or not result[0].get('view_exists'):
            logger.error("❌ View 'v_data_source_preferences' not found")
            return False

        logger.info("✅ View 'v_data_source_preferences' exists")

        # Check if functions exist
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.routines
                WHERE routine_name = 'get_preferred_source'
            ) as function_exists
        """
        result = supabase_raw_query(query)

        if not result or not result[0].get('function_exists'):
            logger.error("❌ Function 'get_preferred_source' not found")
            return False

        logger.info("✅ Function 'get_preferred_source' exists")

        logger.info("\n✅ All migration components verified successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


def test_tracker():
    """Test the data source tracker."""
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: Testing Data Source Tracker")
    logger.info("=" * 80)

    try:
        tracker = get_tracker()

        # Test recording a check
        logger.info("\nTest 1: Recording a check...")
        success = tracker.record_check(
            symbol='TEST',
            data_type=DataType.AUM,
            source=DataSource.FMP,
            has_data=True,
            notes='Test record'
        )

        if success:
            logger.info("✅ Successfully recorded check")
        else:
            logger.error("❌ Failed to record check")
            return False

        # Test getting preferred source
        logger.info("\nTest 2: Getting preferred source...")
        preferred = tracker.get_preferred_source('TEST', DataType.AUM)

        if preferred == DataSource.FMP:
            logger.info(f"✅ Retrieved preferred source: {preferred.value}")
        else:
            logger.error("❌ Failed to retrieve preferred source")
            return False

        # Test getting available sources
        logger.info("\nTest 3: Getting available sources...")
        sources = tracker.get_available_sources('TEST', DataType.AUM)

        if DataSource.FMP in sources:
            logger.info(f"✅ Retrieved available sources: {[s.value for s in sources]}")
        else:
            logger.error("❌ Failed to retrieve available sources")
            return False

        logger.info("\n✅ All tracker tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Tracker test failed: {e}")
        return False


def discover_sample_data(sample_size: int = 5):
    """Discover data for a sample of symbols."""
    logger.info("\n" + "=" * 80)
    logger.info(f"STEP 4: Discovering Data for {sample_size} Sample Symbols")
    logger.info("=" * 80)

    try:
        from supabase_helpers import supabase_select

        # Get sample ETFs for AUM discovery
        logger.info("\n📊 Finding sample ETFs for AUM discovery...")
        etfs = supabase_select(
            'raw_stocks',
            'symbol,name',
            where_clause={'is_etf': True},
            limit=sample_size
        )

        if etfs:
            logger.info(f"Found {len(etfs)} ETFs")
            logger.info("\n💰 Discovering AUM...")

            processor = AUMDiscoveryProcessor()
            for etf in etfs:
                symbol = etf['symbol']
                logger.info(f"\n  Discovering AUM for {symbol}...")
                result = processor.discover_aum(symbol, force_rediscover=False)

                if result['success']:
                    logger.info(
                        f"    ✅ {symbol}: ${result['aum']:,.0f} from {result['source']}"
                    )
                else:
                    logger.info(f"    ⚠️  {symbol}: No AUM data available")

        # Get sample stocks for dividend/volume discovery
        logger.info("\n📊 Finding sample stocks for dividend/volume discovery...")
        stocks = supabase_select(
            'raw_stocks',
            'symbol,name',
            limit=sample_size
        )

        if stocks:
            logger.info(f"Found {len(stocks)} stocks")
            logger.info("\n📈 Discovering dividends and volume...")

            processor = DataDiscoveryProcessor()
            for stock in stocks:
                symbol = stock['symbol']
                logger.info(f"\n  Discovering data for {symbol}...")

                results = processor.discover_all_data_types(
                    symbol,
                    data_types=[DataType.DIVIDENDS, DataType.VOLUME],
                    force_rediscover=False
                )

                for data_type, result in results.items():
                    if result.get('success'):
                        if data_type == 'dividends':
                            logger.info(
                                f"    ✅ {data_type}: {result.get('count', 0)} records "
                                f"from {result.get('source')}"
                            )
                        else:
                            logger.info(
                                f"    ✅ {data_type}: available from {result.get('source')}"
                            )
                    else:
                        logger.info(f"    ⚠️  {data_type}: not available")

        logger.info("\n✅ Sample data discovery completed!")
        return True

    except Exception as e:
        logger.error(f"❌ Sample discovery failed: {e}")
        return False


def show_statistics():
    """Show tracking statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("STEP 5: Tracking Statistics")
    logger.info("=" * 80)

    try:
        tracker = get_tracker()

        # Get overall statistics
        logger.info("\n📊 Overall Statistics:")
        stats = tracker.get_statistics()

        if stats.get('stats'):
            for stat in stats['stats']:
                logger.info(
                    f"\n  {stat['data_type']} / {stat['source']}:"
                    f"\n    Total checks: {stat['total_checks']}"
                    f"\n    Successful: {stat['successful']}"
                    f"\n    Unsuccessful: {stat['unsuccessful']}"
                    f"\n    Unique symbols: {stat['unique_symbols']}"
                    f"\n    Success rate: "
                    f"{(stat['successful'] / stat['total_checks'] * 100):.1f}%"
                )
        else:
            logger.info("  No statistics available yet")

        # Get AUM statistics
        logger.info("\n💰 AUM Statistics:")
        aum_stats = tracker.get_statistics(DataType.AUM)

        if aum_stats.get('stats'):
            for stat in aum_stats['stats']:
                logger.info(
                    f"\n  {stat['source']}:"
                    f"\n    Total checks: {stat['total_checks']}"
                    f"\n    Successful: {stat['successful']}"
                    f"\n    Success rate: "
                    f"{(stat['successful'] / stat['total_checks'] * 100):.1f}%"
                )
        else:
            logger.info("  No AUM statistics available yet")

        return True

    except Exception as e:
        logger.error(f"❌ Statistics failed: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("\n" + "=" * 80)
    logger.info("DATA SOURCE TRACKING SYSTEM - SETUP")
    logger.info("=" * 80)

    # Initialize config
    try:
        Config.setup()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return False

    # Step 1: Run migration
    if not run_migration():
        logger.error("\n❌ Setup failed at migration step")
        return False

    # Step 2: Verify migration
    if not verify_migration():
        logger.error("\n❌ Setup failed at verification step")
        return False

    # Step 3: Test tracker
    if not test_tracker():
        logger.error("\n❌ Setup failed at tracker test step")
        return False

    # Step 4: Discover sample data (optional)
    try:
        discover_sample = input(
            "\n🔍 Discover data for sample symbols? (y/n): "
        ).lower().strip() == 'y'

        if discover_sample:
            sample_size = input("How many symbols? (default: 5): ").strip()
            sample_size = int(sample_size) if sample_size else 5
            discover_sample_data(sample_size)
    except KeyboardInterrupt:
        logger.info("\n\nSkipping sample discovery")
    except Exception as e:
        logger.warning(f"\n⚠️  Sample discovery error (non-fatal): {e}")

    # Step 5: Show statistics
    show_statistics()

    # Success message
    logger.info("\n" + "=" * 80)
    logger.info("✅ SETUP COMPLETED SUCCESSFULLY!")
    logger.info("=" * 80)
    logger.info("""
The Data Source Tracking System is now ready to use!

Next steps:
1. Review the documentation: docs/DATA_SOURCE_TRACKING.md
2. Run discovery for all symbols:
   python -c "from lib.processors.aum_discovery_processor import discover_all_etf_aum; discover_all_etf_aum()"
3. Integrate with existing processors
4. Monitor statistics regularly

For more information, see: docs/DATA_SOURCE_TRACKING.md
""")

    return True


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Setup failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
