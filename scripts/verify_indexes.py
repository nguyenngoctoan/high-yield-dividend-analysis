#!/usr/bin/env python3
"""
Verify that all indexes have been created successfully.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    load_dotenv()

    print("=" * 80)
    print("INDEX VERIFICATION REPORT")
    print("=" * 80)
    print()

    # Try to connect and verify
    try:
        import psycopg2

        url = os.getenv('SUPABASE_URL')
        db_password = os.getenv('SUPABASE_DB_PASSWORD')

        if not url or not db_password:
            print("❌ Missing SUPABASE_URL or SUPABASE_DB_PASSWORD")
            print()
            print("Please add these to your .env file:")
            print("  SUPABASE_URL=https://your-project.supabase.co")
            print("  SUPABASE_DB_PASSWORD=your_db_password")
            return 1

        project_ref = url.replace('https://', '').replace('.supabase.co', '')
        db_host = "aws-0-us-west-1.pooler.supabase.com"
        db_name = "postgres"
        db_user = f"postgres.{project_ref}"

        print(f"🔌 Connecting to Supabase database...")

        conn = psycopg2.connect(
            host=db_host,
            port=6543,
            dbname=db_name,
            user=db_user,
            password=db_password
        )

        cursor = conn.cursor()

        # Get all indexes
        cursor.execute("""
            SELECT
                t.tablename,
                i.indexname,
                i.indexdef
            FROM pg_indexes i
            JOIN pg_tables t ON i.tablename = t.tablename
            WHERE t.schemaname = 'public'
            ORDER BY t.tablename, i.indexname;
        """)

        indexes = cursor.fetchall()

        # Group by table
        tables = {}
        for tablename, indexname, indexdef in indexes:
            if tablename not in tables:
                tables[tablename] = []
            tables[tablename].append((indexname, indexdef))

        print(f"✅ Connected successfully")
        print()
        print(f"📊 Found {len(indexes)} indexes across {len(tables)} tables")
        print()

        # Display indexes by table
        for table in sorted(tables.keys()):
            print(f"📋 {table}")
            print("-" * 80)

            for indexname, indexdef in tables[table]:
                # Extract key parts of index definition
                if 'UNIQUE' in indexdef:
                    index_type = "UNIQUE"
                elif 'PRIMARY KEY' in indexdef:
                    index_type = "PRIMARY"
                else:
                    index_type = "INDEX"

                # Check if it's a partial index (has WHERE clause)
                is_partial = "WHERE" in indexdef

                # Check if it includes columns
                has_include = "INCLUDE" in indexdef

                badges = []
                if is_partial:
                    badges.append("PARTIAL")
                if has_include:
                    badges.append("COVERING")

                badge_str = f" [{', '.join(badges)}]" if badges else ""

                print(f"  {index_type:8} {indexname}{badge_str}")

            print()

        # Check for critical indexes
        print("=" * 80)
        print("CRITICAL INDEX VERIFICATION")
        print("=" * 80)
        print()

        critical_indexes = [
            ('raw_stocks', 'idx_raw_stocks_dividend_yield', 'Dividend yield filtering'),
            ('raw_stocks', 'idx_raw_stocks_sector', 'Sector filtering'),
            ('raw_stock_prices', 'idx_raw_stock_prices_symbol_date', 'Price lookups'),
            ('raw_dividends', 'idx_raw_dividends_symbol_ex_date', 'Dividend lookups'),
            ('divv_api_keys', 'idx_divv_api_keys_key_hash', 'API key validation'),
            ('users', 'idx_users_email', 'User email lookup'),
        ]

        all_found = True
        for table, index_name, description in critical_indexes:
            if table in tables:
                index_names = [idx[0] for idx in tables[table]]
                if index_name in index_names:
                    print(f"  ✅ {table:30} {index_name:40} - {description}")
                else:
                    print(f"  ❌ {table:30} {index_name:40} - {description} [MISSING]")
                    all_found = False
            else:
                print(f"  ⚠️  {table:30} {index_name:40} - Table not found")
                all_found = False

        print()

        if all_found:
            print("✅ All critical indexes are present!")
        else:
            print("⚠️  Some critical indexes are missing. Please run the migration.")

        print()

        # Get table sizes and index usage stats
        cursor.execute("""
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
                pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
        """)

        sizes = cursor.fetchall()

        print("=" * 80)
        print("TABLE SIZES (Including Indexes)")
        print("=" * 80)
        print()
        print(f"{'Table':<30} {'Total Size':<15} {'Table Size':<15} {'Indexes Size':<15}")
        print("-" * 80)

        for schema, table, total_size, table_size, indexes_size in sizes:
            print(f"{table:<30} {total_size:<15} {table_size:<15} {indexes_size:<15}")

        print()
        print("=" * 80)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 80)

        cursor.close()
        conn.close()

        return 0

    except ImportError:
        print("❌ psycopg2 not installed")
        print("   Install with: pip install psycopg2-binary")
        return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
