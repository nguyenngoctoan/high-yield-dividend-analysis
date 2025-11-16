#!/usr/bin/env python3
"""
Fill missing sector data for ETFs using multiple data sources
FMP, AlphaVantage, Yahoo Finance, and Nasdaq
"""

import os
import sys
from pathlib import Path
import time
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

def get_sector_from_fmp(symbol, api_key):
    """Get sector from Financial Modeling Prep"""
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                sector = data[0].get('sector')
                industry = data[0].get('industry')
                return sector, industry, 'FMP'
    except Exception as e:
        print(f"      FMP error for {symbol}: {e}")
    return None, None, None

def get_sector_from_yahoo(symbol):
    """Get sector from Yahoo Finance (via yfinance)"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        info = ticker.info
        sector = info.get('sector')
        industry = info.get('industry')
        if sector:
            return sector, industry, 'Yahoo'
    except Exception as e:
        print(f"      Yahoo error for {symbol}: {e}")
    return None, None, None

def get_sector_from_alphavantage(symbol, api_key):
    """Get sector from AlphaVantage"""
    try:
        url = f"https://www.alphavantage.co/query"
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': api_key
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            sector = data.get('Sector')
            industry = data.get('Industry')
            if sector and sector != 'None':
                return sector, industry, 'AlphaVantage'
    except Exception as e:
        print(f"      AlphaVantage error for {symbol}: {e}")
    return None, None, None

def main():
    # Load environment
    load_dotenv()

    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    fmp_api_key = os.getenv('FMP_API_KEY')
    av_api_key = os.getenv('ALPHAVANTAGE_API_KEY')

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
    print("🔧 FILLING MISSING ETF SECTORS")
    print("=" * 80)
    print()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get ETFs with missing sectors
    print("📋 Finding ETFs with missing sectors...")
    cursor.execute("""
        SELECT symbol, name, exchange
        FROM raw_stocks
        WHERE (name ILIKE '%ETF%' OR name ILIKE '%Fund%' OR name ILIKE '%Trust%')
        AND sector IS NULL
        ORDER BY symbol;
    """)
    etfs_missing_sector = cursor.fetchall()

    print(f"   Found {len(etfs_missing_sector)} ETF-like symbols with missing sectors")
    print()

    if not etfs_missing_sector:
        print("✅ No ETFs with missing sectors found!")
        cursor.close()
        conn.close()
        return 0

    # Process each ETF
    updated_count = 0
    failed_symbols = []

    for i, etf in enumerate(etfs_missing_sector, 1):
        symbol = etf['symbol']
        name = etf['name'] if etf['name'] else 'N/A'

        print(f"[{i}/{len(etfs_missing_sector)}] {symbol:8s} - {name[:60]:60s}")

        sector = None
        industry = None
        source = None

        # Try FMP first
        if fmp_api_key and not sector:
            print("      Trying FMP...")
            sector, industry, source = get_sector_from_fmp(symbol, fmp_api_key)
            time.sleep(0.3)  # Rate limit

        # Try Yahoo Finance
        if not sector:
            print("      Trying Yahoo...")
            sector, industry, source = get_sector_from_yahoo(symbol)
            time.sleep(0.5)  # Rate limit

        # Try AlphaVantage
        if av_api_key and not sector:
            print("      Trying AlphaVantage...")
            sector, industry, source = get_sector_from_alphavantage(symbol, av_api_key)
            time.sleep(12)  # Free tier rate limit (5 calls/min)

        # Update database if we found sector data
        if sector:
            try:
                update_cursor = conn.cursor()
                if industry:
                    update_cursor.execute(
                        "UPDATE raw_stocks SET sector = %s, industry = %s WHERE symbol = %s",
                        (sector, industry, symbol)
                    )
                else:
                    update_cursor.execute(
                        "UPDATE raw_stocks SET sector = %s WHERE symbol = %s",
                        (sector, symbol)
                    )
                conn.commit()
                update_cursor.close()

                print(f"      ✅ Updated: sector='{sector}' from {source}")
                updated_count += 1
            except Exception as e:
                print(f"      ❌ Database update failed: {e}")
                conn.rollback()
                failed_symbols.append(symbol)
        else:
            print(f"      ⚠️  No sector data found from any source")
            failed_symbols.append(symbol)

        print()

    # Summary
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"   Total ETFs processed: {len(etfs_missing_sector)}")
    print(f"   Successfully updated: {updated_count}")
    print(f"   Failed to find data: {len(failed_symbols)}")

    if failed_symbols:
        print(f"\n   Symbols that still need sector data:")
        for sym in failed_symbols[:20]:
            print(f"      - {sym}")
        if len(failed_symbols) > 20:
            print(f"      ... and {len(failed_symbols) - 20} more")

    print()

    cursor.close()
    conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
