#!/usr/bin/env python3
"""
Apply comprehensive index migration to Supabase.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

def main():
    print("=" * 80)
    print("APPLYING COMPREHENSIVE INDEX MIGRATION")
    print("=" * 80)
    print()

    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        return 1

    # Read migration file
    migration_file = 'supabase/migrations/20251115_add_comprehensive_indexes.sql'

    if not os.path.exists(migration_file):
        print(f"❌ Migration file not found: {migration_file}")
        return 1

    print(f"📄 Reading migration file: {migration_file}")
    with open(migration_file, 'r') as f:
        sql_content = f.read()

    print(f"✅ Migration file loaded ({len(sql_content)} characters)")
    print()

    # Create Supabase client
    print("🔌 Connecting to Supabase...")
    try:
        supabase = create_client(url, key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return 1

    print()
    print("🚀 Applying migration...")
    print("   This may take a few minutes for large tables...")
    print()

    # Execute migration using RPC
    try:
        # We need to use the PostgREST API directly or use psycopg2
        # Let's use psycopg2 for better SQL execution
        import psycopg2

        # Build connection string
        # Parse Supabase URL to get database connection details
        # Format: https://xxx.supabase.co
        project_ref = url.replace('https://', '').replace('.supabase.co', '')

        # Use direct database connection
        db_host = f"aws-0-us-west-1.pooler.supabase.com"
        db_name = "postgres"
        db_user = f"postgres.{project_ref}"
        db_password = os.getenv('SUPABASE_DB_PASSWORD')

        if not db_password:
            print("⚠️  SUPABASE_DB_PASSWORD not found in .env")
            print("   Trying to execute via SQL Editor instead...")
            print()
            print("=" * 80)
            print("MANUAL MIGRATION REQUIRED")
            print("=" * 80)
            print()
            print("Please run the following SQL in your Supabase SQL Editor:")
            print(f"https://supabase.com/dashboard/project/{project_ref}/sql/new")
            print()
            print("Or copy and paste the migration file contents:")
            print(migration_file)
            return 0

        print(f"📡 Connecting to database: {db_host}")

        conn = psycopg2.connect(
            host=db_host,
            port=6543,
            dbname=db_name,
            user=db_user,
            password=db_password
        )

        cursor = conn.cursor()

        # Execute migration
        cursor.execute(sql_content)
        conn.commit()

        print("✅ Migration applied successfully!")
        print()

        # Get index count
        cursor.execute("""
            SELECT COUNT(*) as total_indexes
            FROM pg_indexes
            WHERE schemaname = 'public';
        """)

        result = cursor.fetchone()
        total_indexes = result[0] if result else 0

        print(f"📊 Total indexes in public schema: {total_indexes}")
        print()

        # Get list of newly created indexes
        cursor.execute("""
            SELECT
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname LIKE 'idx_%'
            ORDER BY tablename, indexname;
        """)

        indexes = cursor.fetchall()

        print("=" * 80)
        print("INDEXES BY TABLE")
        print("=" * 80)
        print()

        current_table = None
        for tablename, indexname, indexdef in indexes:
            if tablename != current_table:
                print(f"\n📋 {tablename}")
                print("-" * 80)
                current_table = tablename

            print(f"  • {indexname}")

        print()
        print("=" * 80)
        print("✅ INDEX MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 80)

        cursor.close()
        conn.close()

        return 0

    except ImportError:
        print("⚠️  psycopg2 not installed. Install with: pip install psycopg2-binary")
        print()
        print("=" * 80)
        print("ALTERNATIVE: MANUAL MIGRATION")
        print("=" * 80)
        print()
        print("Copy the SQL from this file and paste it into Supabase SQL Editor:")
        print(migration_file)
        return 1

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
