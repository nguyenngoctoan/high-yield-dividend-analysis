#!/usr/bin/env python3
"""
Run the adj_close migration using Supabase SQL function.

Note: This requires direct database access. If you're using Supabase hosted,
you should run the migration through the Supabase Studio SQL Editor.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Run the adj_close migration SQL."""

    # Read the migration file
    migration_file = '/Users/toan/dev/high-yield-dividend-analysis/migrations/002_add_adj_close.sql'

    with open(migration_file, 'r') as f:
        sql = f.read()

    print("=" * 80)
    print("RUNNING ADJ_CLOSE MIGRATION")
    print("=" * 80)
    print("\nMigration SQL:")
    print("-" * 80)
    print(sql)
    print("-" * 80)

    # Get Supabase URL
    supabase_url = os.getenv('SUPABASE_URL')

    if 'localhost' in supabase_url or '127.0.0.1' in supabase_url:
        print("\n📝 LOCAL SUPABASE DETECTED")
        print("\nTo run this migration on local Supabase, you have two options:\n")

        print("OPTION 1: Use Supabase Studio SQL Editor")
        print("  1. Open: http://localhost:3004 (or your Supabase Studio URL)")
        print("  2. Navigate to SQL Editor")
        print("  3. Copy and paste the SQL from migrations/002_add_adj_close.sql")
        print("  4. Run the query\n")

        print("OPTION 2: Use psql directly (if you have database port exposed)")
        print("  Find your database port with:")
        print("    docker ps | grep supabase")
        print("  Then run:")
        print("    PGPASSWORD=postgres psql -h localhost -p [DB_PORT] -U postgres -d postgres \\")
        print("      -f migrations/002_add_adj_close.sql\n")

        print("OPTION 3: Use Docker exec (recommended)")
        print("  docker exec -i [CONTAINER_NAME] psql -U postgres -d postgres < migrations/002_add_adj_close.sql\n")

    else:
        print("\n📝 REMOTE SUPABASE DETECTED")
        print("\nTo run this migration on remote Supabase:")
        print("  1. Open your Supabase Dashboard")
        print("  2. Navigate to SQL Editor")
        print("  3. Copy and paste the SQL from migrations/002_add_adj_close.sql")
        print("  4. Run the query\n")

    print("\n✅ After running the migration, you can:")
    print("  1. Test with: python backfill_adj_close.py 5")
    print("  2. Run full backfill: python backfill_adj_close.py")
    print("  3. Verify: Check stock_prices table has adj_close column")
    print("=" * 80)

if __name__ == "__main__":
    run_migration()
