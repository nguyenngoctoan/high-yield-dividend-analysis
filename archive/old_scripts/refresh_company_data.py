#!/usr/bin/env python3
"""
Refresh Company Data Script

This script identifies and fixes stocks with NULL company fields by:
1. Querying yfinance for fundFamily (ETFs) or companyName (stocks)
2. Updating the stocks table with the company data
3. Reporting statistics on what was fixed

Usage:
    python refresh_company_data.py                    # Dry run (show what would be fixed)
    python refresh_company_data.py --execute          # Actually fix the data
    python refresh_company_data.py --check-only       # Just show statistics
"""

import os
import sys
import logging
import argparse
import yfinance as yf
from datetime import datetime
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client, supabase_select, supabase_update

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('refresh_company_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_stocks_with_null_company():
    """Get all stocks with NULL or empty company fields."""
    try:
        supabase = get_supabase_client()

        # Query for NULL or empty company
        result = supabase.table('raw_stocks')\
            .select('symbol,name,company,exchange')\
            .or_('company.is.null,company.eq.')\
            .execute()

        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error fetching stocks with NULL company: {e}")
        return []

def fetch_company_name_from_yfinance(symbol):
    """Fetch company name from yfinance (fundFamily for ETFs, companyName for stocks)."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        # Try fundFamily first (for ETFs), then companyName (for stocks)
        company_name = info.get('fundFamily') or info.get('companyName') or None
        quote_type = info.get('quoteType')

        return {
            'company_name': company_name,
            'quote_type': quote_type,
            'long_name': info.get('longName')
        }
    except Exception as e:
        logger.debug(f"Error fetching {symbol} from yfinance: {e}")
        return None

def refresh_company_data(execute=False, limit=None):
    """
    Refresh company data for all stocks with NULL company fields.

    Args:
        execute: If True, actually update the database. If False, dry run.
        limit: Maximum number of symbols to process (None = all)
    """
    logger.info("=" * 80)
    logger.info("🔍 COMPANY DATA REFRESH")
    logger.info("=" * 80)
    logger.info(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")

    # Get stocks with NULL company
    stocks = get_stocks_with_null_company()

    if not stocks:
        logger.info("✅ No stocks with NULL company fields found!")
        return {
            'total': 0,
            'fixed': 0,
            'not_found': 0,
            'errors': 0
        }

    logger.info(f"📊 Found {len(stocks)} stocks with NULL/empty company fields")

    if limit:
        stocks = stocks[:limit]
        logger.info(f"⚠️  Processing limited to first {limit} symbols")

    # Statistics
    stats = {
        'total': len(stocks),
        'fixed': 0,
        'not_found': 0,
        'errors': 0,
        'etf_count': 0,
        'stock_count': 0
    }

    fixes = []  # Store fixes for reporting

    # Process each stock
    for i, stock in enumerate(stocks, 1):
        symbol = stock['symbol']
        name = stock['name']

        if i % 10 == 0:
            logger.info(f"Progress: {i}/{len(stocks)} ({i/len(stocks)*100:.1f}%)")

        try:
            # Fetch company name from yfinance
            data = fetch_company_name_from_yfinance(symbol)

            if not data or not data.get('company_name'):
                logger.debug(f"⏭️  {symbol}: No company name available")
                stats['not_found'] += 1
                continue

            company_name = data['company_name']
            quote_type = data['quote_type']

            # Track type
            if quote_type == 'ETF':
                stats['etf_count'] += 1
            elif quote_type in ['EQUITY', 'STOCK']:
                stats['stock_count'] += 1

            fixes.append({
                'symbol': symbol,
                'name': name,
                'company': company_name,
                'quote_type': quote_type
            })

            logger.info(f"✅ {symbol}: {company_name} ({quote_type})")

            # Update database if in execute mode
            if execute:
                try:
                    supabase = get_supabase_client()
                    supabase.table('raw_stocks')\
                        .update({'company': company_name})\
                        .eq('symbol', symbol)\
                        .execute()
                    stats['fixed'] += 1
                except Exception as e:
                    logger.error(f"❌ {symbol}: Failed to update - {e}")
                    stats['errors'] += 1
            else:
                stats['fixed'] += 1  # Count as "would be fixed" in dry run

        except Exception as e:
            logger.error(f"❌ {symbol}: Error - {e}")
            stats['errors'] += 1

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total symbols processed: {stats['total']}")
    logger.info(f"{'Fixed' if execute else 'Would fix'}: {stats['fixed']}")
    logger.info(f"Not found: {stats['not_found']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"\nBreakdown:")
    logger.info(f"  ETFs: {stats['etf_count']}")
    logger.info(f"  Stocks: {stats['stock_count']}")

    if not execute and stats['fixed'] > 0:
        logger.info("\n💡 Run with --execute to apply these changes to the database")

    # Show some examples
    if fixes and len(fixes) > 0:
        logger.info("\n📝 Sample Fixes:")
        for fix in fixes[:10]:  # Show first 10
            logger.info(f"  {fix['symbol']}: → {fix['company']} ({fix['quote_type']})")
        if len(fixes) > 10:
            logger.info(f"  ... and {len(fixes) - 10} more")

    logger.info("=" * 80)

    return stats

def check_statistics():
    """Just show statistics without fixing anything."""
    try:
        supabase = get_supabase_client()

        # Total stocks
        total_result = supabase.table('raw_stocks').select('symbol', count='exact').execute()
        total_count = total_result.count if hasattr(total_result, 'count') else 0

        # Stocks with NULL company
        null_result = supabase.table('raw_stocks')\
            .select('symbol', count='exact')\
            .or_('company.is.null,company.eq.')\
            .execute()
        null_count = null_result.count if hasattr(null_result, 'count') else 0

        # Stocks with company
        with_company = total_count - null_count

        logger.info("=" * 80)
        logger.info("📊 COMPANY DATA STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total stocks: {total_count:,}")
        logger.info(f"With company data: {with_company:,} ({with_company/total_count*100:.1f}%)")
        logger.info(f"NULL/empty company: {null_count:,} ({null_count/total_count*100:.1f}%)")
        logger.info("=" * 80)

        return {
            'total': total_count,
            'with_company': with_company,
            'null_company': null_count
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Refresh company data for stocks with NULL company fields')
    parser.add_argument('--execute', action='store_true', help='Actually update the database (default is dry run)')
    parser.add_argument('--check-only', action='store_true', help='Only show statistics, don\'t process')
    parser.add_argument('--limit', type=int, help='Limit number of symbols to process')

    args = parser.parse_args()

    try:
        if args.check_only:
            check_statistics()
        else:
            result = refresh_company_data(execute=args.execute, limit=args.limit)
            sys.exit(0 if result['errors'] == 0 else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
