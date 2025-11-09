#!/usr/bin/env python3
"""
Cleanup All International Symbols

Removes all stocks with international exchange suffixes from all database tables.
Only keeps US and Canadian stocks (NASDAQ, NYSE, AMEX, TSX).
"""

import logging
import sys

sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from supabase_helpers import get_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# International exchange suffixes to remove
# Note: .TO (TSX) and .V (TSXV) are Canadian exchanges and will be KEPT
INTERNATIONAL_SUFFIXES = [
    '.L',     # London Stock Exchange (LSE)
    '.AX',    # Australian Securities Exchange (ASX)
    '.DE',    # Deutsche Börse XETRA
    '.AS',    # Euronext Amsterdam (AMS)
    '.MI',    # Borsa Italiana (MIL)
    '.PA',    # Euronext Paris
    '.SW',    # Swiss Exchange (SIX)
    '.HK',    # Hong Kong Stock Exchange (HKSE)
    '.BR',    # Euronext Brussels
    '.LS',    # Euronext Lisbon
    '.MC',    # Bolsa de Madrid
    '.CO',    # OMX Copenhagen
    '.ST',    # OMX Stockholm
    '.OL',    # Oslo Børs
    '.HE',    # Helsinki Stock Exchange
    '.IC',    # NASDAQ Iceland
    '.VI',    # Vienna Stock Exchange
    '.AT',    # Athens Stock Exchange
    '.WA',    # Warsaw Stock Exchange
    '.PR',    # Prague Stock Exchange
    '.BD',    # Budapest Stock Exchange
    '.SA',    # Bovespa (Brazil)
    '.MX',    # Mexican Stock Exchange
    '.JK',    # Jakarta Stock Exchange
    '.KL',    # Bursa Malaysia
    '.SI',    # Singapore Exchange
    '.BK',    # Stock Exchange of Thailand
    '.TW',    # Taiwan Stock Exchange
    '.KS',    # Korea Stock Exchange
    '.KQ',    # KOSDAQ
    '.T',     # Tokyo Stock Exchange
    '.F',     # Frankfurt Stock Exchange
    '.NZ',    # New Zealand Stock Exchange
    '.JO',    # Johannesburg Stock Exchange
    '.SG',    # Singapore (alternative)
    '.BO',    # Bombay Stock Exchange
    '.NS',    # National Stock Exchange of India
    '.NE',    # NYSE Euronext
    '.ME',    # Moscow Exchange
]

# Tables that contain stock symbols
TABLES_TO_CLEAN = [
    'raw_stocks',
    'raw_stock_prices',
    'raw_stock_prices_hourly',
    'raw_dividends',
    'raw_stock_splits',
    'dim_stocks',
    'holdings',
    'raw_holdings_history',
]


def count_international_symbols(supabase, table_name: str) -> int:
    """Count international symbols in a table."""
    try:
        # Build filter for any international suffix
        response = supabase.table(table_name).select('symbol', count='exact').execute()

        if not response.data:
            return 0

        # Count symbols with international suffixes
        count = 0
        for row in response.data:
            symbol = row.get('symbol', '')
            if any(symbol.endswith(suffix) for suffix in INTERNATIONAL_SUFFIXES):
                count += 1

        return count
    except Exception as e:
        logger.error(f"Error counting symbols in {table_name}: {e}")
        return 0


def delete_international_symbols_from_table(supabase, table_name: str) -> int:
    """Delete all international symbols from a table."""
    deleted_count = 0

    logger.info(f"\nCleaning {table_name}...")

    try:
        # For each suffix, delete in batches
        for suffix in INTERNATIONAL_SUFFIXES:
            batch_size = 1000

            while True:
                # Get batch of symbols to delete
                response = supabase.table(table_name).select('symbol').like(
                    'symbol', f'%{suffix}'
                ).limit(batch_size).execute()

                if not response.data or len(response.data) == 0:
                    break

                symbols_to_delete = [row['symbol'] for row in response.data]

                # Delete this batch
                for symbol in symbols_to_delete:
                    try:
                        supabase.table(table_name).delete().eq('symbol', symbol).execute()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"  Failed to delete {symbol} from {table_name}: {e}")

                logger.info(f"  Deleted {len(symbols_to_delete)} {suffix} symbols from {table_name}")

                if len(response.data) < batch_size:
                    break

        logger.info(f"✅ Cleaned {table_name}: {deleted_count} symbols deleted")
        return deleted_count

    except Exception as e:
        logger.error(f"❌ Error cleaning {table_name}: {e}")
        return deleted_count


def main():
    """Main execution."""
    logger.info("="*80)
    logger.info("International Symbols Cleanup Script")
    logger.info("="*80)
    logger.info("")
    logger.info("This will DELETE all stocks with international exchange suffixes")
    logger.info("from ALL database tables.")
    logger.info("")
    logger.info("Stocks that will be KEPT:")
    logger.info("  - US: NASDAQ, NYSE, AMEX, BATS, OTC (no suffix)")
    logger.info("  - Canadian: .TO (TSX), .V (TSXV)")
    logger.info("")
    logger.info("Stocks that will be DELETED:")
    logger.info("  - All other international exchanges (.L, .DE, .KS, .T, .HK, etc.)")
    logger.info("")

    # Get Supabase client
    supabase = get_supabase_client()

    # Show current counts
    logger.info("Current international symbol counts:")
    total_before = 0
    for table in TABLES_TO_CLEAN:
        try:
            count = count_international_symbols(supabase, table)
            total_before += count
            logger.info(f"  {table}: {count:,} international symbols")
        except Exception as e:
            logger.warning(f"  {table}: Could not count - {e}")

    logger.info(f"\nTotal international symbols to delete: {total_before:,}")
    logger.info("")

    # Confirm
    response = input("Do you want to DELETE all these international symbols? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        logger.info("Operation cancelled")
        return 0

    # Clean each table
    logger.info("\nStarting cleanup...")
    total_deleted = 0

    for table in TABLES_TO_CLEAN:
        try:
            deleted = delete_international_symbols_from_table(supabase, table)
            total_deleted += deleted
        except Exception as e:
            logger.error(f"Failed to clean {table}: {e}")

    logger.info("")
    logger.info("="*80)
    logger.info(f"✅ CLEANUP COMPLETE")
    logger.info(f"   Total deleted: {total_deleted:,} symbols across all tables")
    logger.info("="*80)

    return 0


if __name__ == '__main__':
    sys.exit(main())
