#!/usr/bin/env python3
"""Create stock_prices_hourly table via Supabase."""

from supabase_helpers import get_supabase_client

def create_table():
    """Execute the table creation SQL."""
    print("Creating stock_prices_hourly table...")

    # Read the SQL file
    with open('migrations/create_stock_prices_hourly.sql', 'r') as f:
        sql = f.read()

    print("\nPlease run this SQL in Supabase Studio SQL Editor:")
    print("=" * 80)
    print(sql)
    print("=" * 80)
    print("\nOr use psql:")
    print("cd /Users/toan/dev/ai-dividend-tracker && npx supabase db execute --local < /Users/toan/dev/high-yield-dividend-analysis/migrations/create_stock_prices_hourly.sql")

if __name__ == "__main__":
    create_table()
