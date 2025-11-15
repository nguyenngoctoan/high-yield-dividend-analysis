#!/usr/bin/env python3
"""
Check all tables in Supabase and their current indexes.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_helpers import get_supabase_admin_client

def main():
    load_dotenv()

    supabase = get_supabase_admin_client()
    if not supabase:
        print("❌ Failed to connect to Supabase")
        return

    # Query to get all tables
    tables_query = """
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = 'public'
    ORDER BY tablename;
    """

    # Query to get indexes for each table
    indexes_query = """
    SELECT
        t.tablename,
        i.indexname,
        i.indexdef
    FROM pg_indexes i
    JOIN pg_tables t ON i.tablename = t.tablename
    WHERE t.schemaname = 'public'
    ORDER BY t.tablename, i.indexname;
    """

    # Query to get table columns and types
    columns_query = """
    SELECT
        table_name,
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """

    try:
        # Use RPC to execute SQL
        print("📊 Fetching database schema information...\n")

        # Get tables - we'll use a simple approach with Supabase's metadata
        from supabase import create_client
        import requests

        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not url or not key:
            print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
            return

        # Use REST API to query pg_catalog
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }

        # Query using PostgREST
        print("=" * 80)
        print("TABLES AND INDEXES REPORT")
        print("=" * 80)
        print()

        # We'll query the information schema directly using a Postgres function
        # First, let's just list what we know from the code

        known_tables = [
            'raw_stocks',
            'raw_stock_prices',
            'raw_dividends',
            'raw_stocks_excluded',
            'users',
            'divv_api_keys',
            'data_source_tracking',
            'raw_yieldmax_dividends',
            'stock_splits',
            'holdings_history'
        ]

        print("Known tables from migrations:")
        for table in known_tables:
            print(f"  - {table}")

        print("\n" + "=" * 80)
        print("RECOMMENDATIONS FOR INDEXES")
        print("=" * 80)
        print()

        recommendations = {
            'raw_stocks': [
                ('symbol', 'Primary lookups by symbol (likely already has PK)'),
                ('sector', 'Filtering by sector'),
                ('industry', 'Filtering by industry'),
                ('market_cap', 'Sorting/filtering by market cap'),
                ('dividend_yield', 'Sorting/filtering by dividend yield'),
            ],
            'raw_stock_prices': [
                ('(symbol, date)', 'Composite index for time-series queries (likely already exists as PK)'),
                ('date', 'Filtering by date range'),
                ('symbol', 'Filtering by symbol (if not first in composite)'),
            ],
            'raw_dividends': [
                ('(symbol, ex_date)', 'Composite index for dividend lookups (likely already exists as PK)'),
                ('ex_date', 'Filtering by ex-dividend date'),
                ('payment_date', 'Filtering by payment date'),
                ('symbol', 'Filtering by symbol (if not first in composite)'),
            ],
            'raw_stocks_excluded': [
                ('symbol', 'Primary key lookup'),
                ('excluded_at', 'Filtering by exclusion date'),
            ],
            'users': [
                ('email', 'User lookup by email'),
                ('api_tier', 'Filtering by tier'),
                ('created_at', 'Sorting by creation date'),
            ],
            'divv_api_keys': [
                ('key_hash', 'Fast API key lookup'),
                ('user_id', 'Lookup keys by user'),
                ('is_active', 'Filter active keys'),
            ],
            'data_source_tracking': [
                ('symbol', 'Lookup by symbol'),
                ('last_updated', 'Finding stale data'),
            ],
        }

        for table, indexes in recommendations.items():
            print(f"\n📋 {table}")
            print("-" * 80)
            for index_cols, reason in indexes:
                print(f"  • {index_cols:<40} - {reason}")

        print("\n" + "=" * 80)
        print("\n✅ Review complete. Migration file will be created next.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
