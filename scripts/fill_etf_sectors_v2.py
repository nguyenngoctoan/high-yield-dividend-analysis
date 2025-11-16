#!/usr/bin/env python3
"""
Fill missing sector data for ETFs
ETFs are financial products, so they get sector="Financial Services"
and industry=category from Yahoo Finance to preserve investment focus
"""

import os
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import yfinance as yf

def get_etf_info(symbol):
    """Get ETF info from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        category = info.get('category', None)
        quote_type = info.get('quoteType', None)
        long_name = info.get('longName', None)

        # For ETFs, use category as industry
        if quote_type == 'ETF':
            return 'Financial Services', category, True
        # For mutual funds, also use Financial Services
        elif quote_type == 'MUTUALFUND':
            return 'Financial Services', category, False
        else:
            # Try to get regular sector/industry
            sector = info.get('sector', None)
            industry = info.get('industry', category)
            return sector, industry, False

    except Exception as e:
        print(f"      Yahoo error: {e}")
        return None, None, None

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
    print("🔧 FILLING MISSING ETF/FUND SECTORS")
    print("=" * 80)
    print()
    print("Strategy: ETFs/Funds are financial products, so:")
    print("  • sector = 'Financial Services'")
    print("  • industry = Yahoo Finance 'category' (investment focus)")
    print("  • is_etf = true (for ETFs only)")
    print()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get ETFs/Funds with missing sectors
    print("📋 Finding ETFs/Funds with missing sectors...")
    cursor.execute("""
        SELECT symbol, name, exchange
        FROM raw_stocks
        WHERE (name ILIKE '%ETF%' OR name ILIKE '%Fund%' OR name ILIKE '%Trust%')
        AND sector IS NULL
        ORDER BY symbol;
    """)
    symbols_missing_sector = cursor.fetchall()

    print(f"   Found {len(symbols_missing_sector)} symbols with missing sectors")
    print()

    if not symbols_missing_sector:
        print("✅ No symbols with missing sectors found!")
        cursor.close()
        conn.close()
        return 0

    # Process each symbol
    updated_count = 0
    failed_symbols = []

    for i, record in enumerate(symbols_missing_sector, 1):
        symbol = record['symbol']
        name = record['name'] if record['name'] else 'N/A'

        print(f"[{i}/{len(symbols_missing_sector)}] {symbol:8s} - {name[:60]:60s}")

        # Get info from Yahoo
        print("      Fetching from Yahoo Finance...")
        sector, industry, is_etf = get_etf_info(symbol)

        if sector:
            try:
                update_cursor = conn.cursor()

                # Build update query
                if industry:
                    update_cursor.execute(
                        "UPDATE raw_stocks SET sector = %s, industry = %s, is_etf = %s WHERE symbol = %s",
                        (sector, industry, is_etf, symbol)
                    )
                else:
                    update_cursor.execute(
                        "UPDATE raw_stocks SET sector = %s, is_etf = %s WHERE symbol = %s",
                        (sector, is_etf, symbol)
                    )

                conn.commit()
                update_cursor.close()

                etf_flag = "✓ ETF" if is_etf else "  Fund"
                ind_display = industry if industry else "N/A"
                print(f"      ✅ Updated: sector='{sector}' | industry='{ind_display}' | {etf_flag}")
                updated_count += 1

            except Exception as e:
                print(f"      ❌ Database update failed: {e}")
                conn.rollback()
                failed_symbols.append(symbol)
        else:
            print(f"      ⚠️  No data found - setting to Financial Services by default")
            # Set to Financial Services even if we can't get category
            try:
                update_cursor = conn.cursor()
                update_cursor.execute(
                    "UPDATE raw_stocks SET sector = %s WHERE symbol = %s",
                    ('Financial Services', symbol)
                )
                conn.commit()
                update_cursor.close()
                print(f"      ✅ Updated: sector='Financial Services' (default)")
                updated_count += 1
            except Exception as e:
                print(f"      ❌ Database update failed: {e}")
                conn.rollback()
                failed_symbols.append(symbol)

        # Rate limiting
        time.sleep(0.5)
        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"   Total symbols processed: {len(symbols_missing_sector)}")
    print(f"   Successfully updated: {updated_count}")
    print(f"   Failed to update: {len(failed_symbols)}")

    if failed_symbols:
        print(f"\n   Symbols that failed to update:")
        for sym in failed_symbols[:20]:
            print(f"      - {sym}")
        if len(failed_symbols) > 20:
            print(f"      ... and {len(failed_symbols) - 20} more")

    # Verify final state
    print()
    print("📋 Verifying final state...")
    cursor.execute("""
        SELECT
            COUNT(*) as total_etf_like,
            COUNT(sector) as with_sector,
            COUNT(*) - COUNT(sector) as without_sector
        FROM raw_stocks
        WHERE name ILIKE '%ETF%' OR name ILIKE '%Fund%' OR name ILIKE '%Trust%';
    """)
    final_stats = cursor.fetchone()

    print(f"   Total ETF/Fund-like symbols: {final_stats['total_etf_like']:,}")
    print(f"   With sector: {final_stats['with_sector']:,}")
    print(f"   Without sector: {final_stats['without_sector']:,}")

    if final_stats['without_sector'] == 0:
        print()
        print("🎉 SUCCESS! All ETF/Fund-like symbols now have sectors assigned!")
    print()

    cursor.close()
    conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
