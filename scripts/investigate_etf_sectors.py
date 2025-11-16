#!/usr/bin/env python3
"""
Investigate ETF sector fields in raw_stocks table
Check all data sources (FMP, AlphaVantage, Yahoo, Nasdaq) for missing sector data
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    # Load environment
    load_dotenv()

    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    if not db_password:
        print("❌ SUPABASE_DB_PASSWORD not found in .env")
        return 1

    # Database connection
    conn = psycopg2.connect(
        host="db.uykxgbrzpfswbdxtyzlv.supabase.co",
        port=6543,
        user="postgres",
        password=db_password,
        database="postgres"
    )

    print("=" * 80)
    print("🔍 ETF SECTOR INVESTIGATION")
    print("=" * 80)
    print()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Step 1: Check table schema
    print("📋 Step 1: Checking raw_stocks table schema...")
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'raw_stocks'
        AND table_schema = 'public'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print(f"   Found {len(columns)} columns:")
    for col in columns[:10]:  # Show first 10
        print(f"   - {col['column_name']}: {col['data_type']}")
    if len(columns) > 10:
        print(f"   ... and {len(columns) - 10} more")
    print()

    # Step 2: Check for ETF-related fields
    print("📋 Step 2: Checking for ETF identification fields...")
    etf_related_cols = [col['column_name'] for col in columns if 'etf' in col['column_name'].lower() or 'asset' in col['column_name'].lower() or 'type' in col['column_name'].lower()]
    if etf_related_cols:
        print(f"   Found ETF-related columns: {', '.join(etf_related_cols)}")
    else:
        print("   ❌ No obvious ETF-related columns found")
    print()

    # Step 3: Check type values
    print("📋 Step 3: Checking distinct type values...")
    cursor.execute("SELECT DISTINCT type, COUNT(*) as count FROM raw_stocks WHERE type IS NOT NULL GROUP BY type ORDER BY count DESC;")
    types = cursor.fetchall()
    if types:
        print(f"   Found {len(types)} distinct types:")
        for t in types[:20]:
            print(f"   - {t['type']}: {t['count']:,} symbols")
    else:
        print("   ❌ No type values found")
    print()

    # Step 4: Find ETFs (try multiple methods)
    print("📋 Step 4: Finding ETFs using multiple methods...")

    # Method 1: Check for is_etf field
    cursor.execute("SELECT COUNT(*) as count FROM raw_stocks WHERE is_etf = true;")
    result = cursor.fetchone()
    print(f"   Method 1 (is_etf = true): {result['count']:,} ETFs")

    # Method 2: Check type = 'etf'
    cursor.execute("SELECT COUNT(*) as count FROM raw_stocks WHERE type = 'etf';")
    result = cursor.fetchone()
    print(f"   Method 2 (type = 'etf'): {result['count']:,} ETFs")

    # Method 3: Check type ILIKE '%etf%'
    cursor.execute("SELECT COUNT(*) as count FROM raw_stocks WHERE type ILIKE '%etf%';")
    result = cursor.fetchone()
    print(f"   Method 3 (type contains 'etf'): {result['count']:,} ETFs")
    print()

    # Step 5: Check sector field for ETFs
    print("📋 Step 5: Analyzing sector field for ETFs...")

    # Try all methods to find ETFs and check their sectors
    methods = [
        ("is_etf = true", "is_etf = true"),
        ("type = 'etf'", "type = 'etf'"),
        ("type ILIKE '%etf%'", "type contains 'etf'"),
    ]

    for condition, description in methods:
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_etfs,
                COUNT(sector) as with_sector,
                COUNT(*) - COUNT(sector) as without_sector,
                COUNT(CASE WHEN sector = 'Unknown' THEN 1 END) as unknown_sector,
                COUNT(CASE WHEN sector IS NULL OR sector = 'Unknown' THEN 1 END) as needs_update
            FROM raw_stocks
            WHERE {condition};
        """)
        stats = cursor.fetchone()

        if stats['total_etfs'] > 0:
            print(f"   {description}:")
            print(f"      Total ETFs: {stats['total_etfs']:,}")
            print(f"      With sector: {stats['with_sector']:,}")
            print(f"      Without sector (NULL): {stats['without_sector']:,}")
            print(f"      With 'Unknown' sector: {stats['unknown_sector']:,}")
            print(f"      ⚠️  Needs update: {stats['needs_update']:,}")
            print()

    # Step 6: Sample ETFs with missing sectors
    print("📋 Step 6: Sample ETFs with missing or unknown sectors...")
    cursor.execute("""
        SELECT symbol, name, sector, type, exchange
        FROM raw_stocks
        WHERE (type ILIKE '%etf%' OR is_etf = true)
        AND (sector IS NULL OR sector = 'Unknown')
        ORDER BY symbol
        LIMIT 20;
    """)
    samples = cursor.fetchall()

    if samples:
        print(f"   Found {len(samples)} sample ETFs needing sector updates:")
        for s in samples:
            print(f"      {s['symbol']:6s} - {s['name'][:50]:50s} | sector: {s['sector']} | type: {s['type']}")
    else:
        print("   ✅ No ETFs found with missing sectors (or no ETFs found)")
    print()

    # Step 7: Check if there are ANY records with sector data
    print("📋 Step 7: Overall sector field statistics...")
    cursor.execute("""
        SELECT
            COUNT(*) as total_records,
            COUNT(sector) as with_sector,
            COUNT(*) - COUNT(sector) as without_sector,
            COUNT(CASE WHEN sector = 'Unknown' THEN 1 END) as unknown_sector
        FROM raw_stocks;
    """)
    overall = cursor.fetchone()
    print(f"   Total records: {overall['total_records']:,}")
    print(f"   With sector: {overall['with_sector']:,} ({100*overall['with_sector']/overall['total_records']:.1f}%)")
    print(f"   Without sector: {overall['without_sector']:,} ({100*overall['without_sector']/overall['total_records']:.1f}%)")
    print(f"   'Unknown' sector: {overall['unknown_sector']:,} ({100*overall['unknown_sector']/overall['total_records']:.1f}%)")
    print()

    cursor.close()
    conn.close()

    print("=" * 80)
    print("✅ Investigation complete")
    print("=" * 80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
