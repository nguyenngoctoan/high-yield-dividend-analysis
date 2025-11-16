#!/usr/bin/env python3
"""
Find potential ETFs in the database by checking symbols and names
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
    print("🔎 FINDING POTENTIAL ETFs IN DATABASE")
    print("=" * 80)
    print()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Strategy 1: Check for common ETF name patterns
    print("📋 Strategy 1: Finding symbols with ETF-related names...")
    cursor.execute("""
        SELECT symbol, name, sector, exchange
        FROM raw_stocks
        WHERE name ILIKE '%ETF%'
        OR name ILIKE '%Fund%'
        OR name ILIKE '%Trust%'
        OR name ILIKE '%Index%'
        ORDER BY symbol
        LIMIT 30;
    """)
    name_matches = cursor.fetchall()

    if name_matches:
        print(f"   Found {len(name_matches)} potential ETFs by name pattern:")
        for m in name_matches[:30]:
            sector_display = m['sector'] if m['sector'] else '❌ NULL'
            print(f"      {m['symbol']:6s} - {m['name'][:60]:60s} | sector: {sector_display}")
    print()

    # Strategy 2: Check exchange patterns (ETFs often trade on specific exchanges)
    print("📋 Strategy 2: Checking records without sectors by exchange...")
    cursor.execute("""
        SELECT exchange, COUNT(*) as count
        FROM raw_stocks
        WHERE sector IS NULL
        GROUP BY exchange
        ORDER BY count DESC
        LIMIT 15;
    """)
    exchanges = cursor.fetchall()

    if exchanges:
        print("   Records without sector by exchange:")
        for e in exchanges:
            exch_name = e['exchange'] if e['exchange'] else 'NULL'
            print(f"      {exch_name:25s}: {e['count']:,} records")
    print()

    # Strategy 3: Sample records without sectors
    print("📋 Strategy 3: Sample of records without sectors...")
    cursor.execute("""
        SELECT symbol, name, exchange, price, market_cap
        FROM raw_stocks
        WHERE sector IS NULL
        ORDER BY market_cap DESC NULLS LAST
        LIMIT 30;
    """)
    no_sector_samples = cursor.fetchall()

    if no_sector_samples:
        print(f"   Sample of {len(no_sector_samples)} records without sectors (by market cap):")
        for s in no_sector_samples:
            mc_display = f"${s['market_cap']:,}" if s['market_cap'] else "N/A"
            name_display = (s['name'][:50] if s['name'] else 'N/A')
            exch_display = (s['exchange'][:10] if s['exchange'] else 'NULL')
            print(f"      {s['symbol']:6s} - {name_display:50s} | {exch_display:10s} | MC: {mc_display}")
    print()

    # Strategy 4: Check for KNOWN major ETFs
    print("📋 Strategy 4: Checking for known major ETFs...")
    known_etfs = ['SPY', 'QQQ', 'VOO', 'VTI', 'IWM', 'EEM', 'GLD', 'SLV', 'TLT',
                   'IVV', 'VEA', 'AGG', 'BND', 'VWO', 'LQD', 'XLF', 'XLE', 'XLK',
                   'VTV', 'VUG', 'IJH', 'IJR', 'EFA', 'DIA', 'IEMG']

    placeholders = ','.join(['%s'] * len(known_etfs))
    cursor.execute(f"""
        SELECT symbol, name, sector, is_etf, type, market_cap
        FROM raw_stocks
        WHERE symbol IN ({placeholders})
        ORDER BY symbol;
    """, known_etfs)

    found_etfs = cursor.fetchall()

    if found_etfs:
        print(f"   Found {len(found_etfs)}/{len(known_etfs)} known major ETFs in database:")
        for etf in found_etfs:
            sector_display = etf['sector'] if etf['sector'] else '❌ NULL'
            is_etf_flag = '✓' if etf['is_etf'] else '✗'
            mc_display = f"${etf['market_cap']:,}" if etf['market_cap'] else "N/A"
            print(f"      {etf['symbol']:6s} - {etf['name'][:45]:45s} | sector: {sector_display:20s} | is_etf: {is_etf_flag} | MC: {mc_display}")
    else:
        print("   ❌ None of the known major ETFs found in database")
    print()

    # Strategy 5: Count total ETF-like names and how many lack sectors
    print("📋 Strategy 5: Counting all ETF-like names...")
    cursor.execute("""
        SELECT
            COUNT(*) as total_etf_like,
            COUNT(sector) as with_sector,
            COUNT(*) - COUNT(sector) as without_sector,
            COUNT(*) FILTER (WHERE is_etf = true) as marked_as_etf
        FROM raw_stocks
        WHERE name ILIKE '%ETF%'
        OR name ILIKE '%Fund%'
        OR name ILIKE '%Trust%'
        OR symbol IN ('SPY', 'QQQ', 'VOO', 'VTI', 'IWM', 'EEM', 'GLD', 'SLV', 'TLT',
                      'IVV', 'VEA', 'AGG', 'BND', 'VWO', 'LQD', 'XLF', 'XLE', 'XLK',
                      'VTV', 'VUG', 'IJH', 'IJR', 'EFA', 'DIA', 'IEMG');
    """)
    stats = cursor.fetchone()

    print(f"   Total ETF-like names: {stats['total_etf_like']:,}")
    print(f"   With sector: {stats['with_sector']:,}")
    print(f"   Without sector: {stats['without_sector']:,} ⚠️")
    print(f"   Marked as is_etf=true: {stats['marked_as_etf']:,}")
    print()

    cursor.close()
    conn.close()

    print("=" * 80)
    print("✅ ETF search complete")
    print("=" * 80)
    print()
    print("SUMMARY:")
    print(f"  • Found {stats['total_etf_like']:,} ETF-like symbols in database")
    print(f"  • {stats['without_sector']:,} of them are missing sector data")
    print(f"  • Currently {stats['marked_as_etf']:,} are marked as is_etf=true")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
