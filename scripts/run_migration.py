#!/usr/bin/env python3
"""
Run Database Migration

Executes SQL migration files against the Supabase database.
"""

import sys
from pathlib import Path
from supabase_helpers import get_supabase_client

def run_migration(migration_file: str):
    """Run a SQL migration file"""
    print(f"Running migration: {migration_file}")

    # Read migration file
    migration_path = Path(migration_file)
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_file}")
        sys.exit(1)

    with open(migration_path, 'r') as f:
        sql = f.read()

    print(f"Migration size: {len(sql)} bytes")
    print("\nExecuting migration...")

    # Get Supabase client
    supabase = get_supabase_client()

    try:
        # Execute the migration SQL
        # Note: Supabase client's .rpc() method can execute SQL
        result = supabase.rpc('exec_sql', {'sql': sql}).execute()

        print("✅ Migration executed successfully!")
        return True

    except Exception as e:
        # If exec_sql doesn't exist, we need to execute manually
        print(f"⚠️  RPC method not available, trying direct execution...")
        print(f"Error: {e}")

        # For complex migrations, we need to use psql or direct postgres connection
        print("\n" + "="*80)
        print("ALTERNATIVE: Run migration using psql")
        print("="*80)
        print("\nYou can run this migration manually using:")
        print(f"\npsql -U postgres -d dividend_analysis -f {migration_file}")
        print("\nOr copy the SQL to Supabase SQL Editor:")
        print("https://app.supabase.com/project/_/sql")
        return False

if __name__ == "__main__":
    migration_file = "migrations/update_pricing_tiers_v2.sql"

    if len(sys.argv) > 1:
        migration_file = sys.argv[1]

    run_migration(migration_file)
