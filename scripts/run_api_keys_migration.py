#!/usr/bin/env python3
"""
Run API Keys Database Migration

This script creates the necessary tables for API key authentication and rate limiting.
"""

import sys
import os
import psycopg2
from psycopg2 import sql

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db_connection():
    """Get database connection from environment variables."""
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    db_url = os.getenv('SUPABASE_DB_URL_DIRECT')
    if not db_url:
        # Fallback to constructed URL
        host = os.getenv('DB_HOST', 'aws-0-us-east-1.pooler.supabase.com')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('SUPABASE_DB_PASSWORD')
        database = os.getenv('DB_NAME', 'postgres')

        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    return psycopg2.connect(db_url)

def run_migration():
    """Run the API keys migration."""

    # Read the migration SQL
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations',
        'create_api_keys.sql'
    )

    with open(migration_file, 'r') as f:
        sql_content = f.read()

    print("Running API keys migration...")
    print("=" * 70)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Execute the entire SQL file
        cursor.execute(sql_content)
        conn.commit()

        print("\n✅ Migration completed successfully!")
        print("\nCreated tables:")
        print("  - api_keys")
        print("  - api_usage")
        print("  - rate_limit_state")
        print("  - mv_api_usage_daily (materialized view)")
        print("\nYou can now use API key authentication!")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nThis is normal if tables already exist.")
        print("You can manually run the migration using the Supabase SQL Editor:")
        print("  migrations/create_api_keys.sql")
        sys.exit(1)

if __name__ == '__main__':
    run_migration()
