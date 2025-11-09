#!/usr/bin/env python3
"""
Delete NULL exchange symbols that are actually international stocks.

Based on investigation, 98%+ of NULL exchange symbols are international stocks
with suffixes like .L (LSE), .AX (ASX), .DE (XETRA), .AS (AMS), etc.

This script will:
1. Delete symbols with common international suffixes
2. Optionally verify remaining NULL symbols via FMP API
"""

import sys
import os
import requests
from time import sleep
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')

# Common international exchange suffixes
INTERNATIONAL_SUFFIXES = [
    '.L',     # London Stock Exchange (LSE)
    '.AX',    # Australian Securities Exchange (ASX)
    '.DE',    # Deutsche Börse XETRA
    '.AS',    # Euronext Amsterdam (AMS)
    '.MI',    # Borsa Italiana (MIL)
    '.PA',    # Euronext Paris
    '.SW',    # Swiss Exchange (SIX)
    '.HK',    # Hong Kong Stock Exchange (HKSE)
    '.BR',    # Euronext Brussels
    '.LS',    # Euronext Lisbon
    '.MC',    # Bolsa de Madrid
    '.CO',    # OMX Copenhagen
    '.ST',    # OMX Stockholm
    '.OL',    # Oslo Børs
    '.HE',    # Helsinki Stock Exchange
    '.IC',    # NASDAQ Iceland
    '.VI',    # Vienna Stock Exchange
    '.AT',    # Athens Stock Exchange
    '.WA',    # Warsaw Stock Exchange
    '.PR',    # Prague Stock Exchange
    '.BD',    # Budapest Stock Exchange
    '.SA',    # Bovespa (Brazil)
    '.MX',    # Mexican Stock Exchange
    '.JK',    # Jakarta Stock Exchange
    '.KL',    # Bursa Malaysia
    '.SI',    # Singapore Exchange
    '.BK',    # Stock Exchange of Thailand
    '.TW',    # Taiwan Stock Exchange
    '.KS',    # Korea Stock Exchange
    '.KQ',    # KOSDAQ
    '.T',     # Tokyo Stock Exchange
]

# US and Canadian exchanges to KEEP
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "BATS", "BTS", "BYX", "BZX", "CBOE",
    "EDGA", "EDGX", "PCX", "NGM",
    "OTCM", "OTCX", "OTC",
    "TSX", "TSXV", "CSE", "TSE", "NEO"
]

def get_symbols_with_international_suffixes():
    """Get NULL exchange symbols with international suffixes."""
    print("🔍 Finding NULL exchange symbols with international suffixes...")

    supabase = get_supabase_client()
    result = supabase.table('stocks').select('symbol, exchange').is_('exchange', 'null').execute()

    international_symbols = []
    normal_symbols = []

    for stock in result.data:
        symbol = stock['symbol']
        # Check if symbol has any international suffix
        is_international = any(symbol.endswith(suffix) for suffix in INTERNATIONAL_SUFFIXES)

        if is_international:
            international_symbols.append(symbol)
        else:
            normal_symbols.append(symbol)

    print(f"   International (with suffix): {len(international_symbols):,} symbols")
    print(f"   Unknown (no suffix):         {len(normal_symbols):,} symbols")

    return international_symbols, normal_symbols

def verify_via_fmp(symbols, sample_size=50):
    """Verify symbols via FMP API to check if they're international."""
    print(f"\n🔬 Verifying sample via FMP API ({sample_size} symbols)...")

    sample = symbols[:sample_size]
    international_count = 0
    us_canadian_count = 0
    error_count = 0

    for i, symbol in enumerate(sample, 1):
        try:
            url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data and isinstance(data, list) and len(data) > 0:
                exchange = data[0].get('exchangeShortName', '').strip()

                if exchange in ALLOWED_EXCHANGES:
                    us_canadian_count += 1
                    print(f"   [{i}/{sample_size}] {symbol:15} -> {exchange} (US/CANADIAN!) ⚠️")
                else:
                    international_count += 1

            sleep(0.15)  # Rate limiting
        except Exception as e:
            error_count += 1

    print(f"\n   Results: {international_count} international, {us_canadian_count} US/Canadian, {error_count} errors")
    return us_canadian_count == 0  # Safe to delete if none are US/Canadian

def delete_from_table(table_name, symbols, batch_size=100):
    """Delete symbols from a table in batches."""
    print(f"\n🗑️  Deleting from {table_name}...")

    supabase = get_supabase_client()
    total_deleted = 0

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]

        try:
            result = supabase.table(table_name).delete().in_('symbol', batch).execute()
            deleted_count = len(result.data) if result.data else 0
            total_deleted += deleted_count

            if (i // batch_size + 1) % 10 == 0:
                print(f"  Processed {i + len(batch):,} / {len(symbols):,} symbols...")
        except Exception as e:
            print(f"  ⚠️  Error deleting batch {i // batch_size + 1}: {e}")

    print(f"  ✅ Deleted {total_deleted:,} records from {table_name}")
    return total_deleted

def main():
    print("=" * 80)
    print("🌍 DELETE NULL INTERNATIONAL SYMBOLS")
    print("=" * 80)

    # Get symbols with international suffixes
    intl_symbols, unknown_symbols = get_symbols_with_international_suffixes()

    if not intl_symbols and not unknown_symbols:
        print("\n✅ No NULL exchange symbols found!")
        return

    # Verify international symbols
    if intl_symbols:
        print(f"\n📊 Found {len(intl_symbols):,} symbols with international suffixes")
        print("\n   Examples:")
        for symbol in intl_symbols[:10]:
            print(f"      {symbol}")

        # Verify via FMP
        safe_to_delete = verify_via_fmp(intl_symbols, sample_size=100)

        if not safe_to_delete:
            print("\n⚠️  WARNING: Some symbols appear to be US/Canadian!")
            print("   Manual review required before deletion.")
            return

    # Handle unknown symbols
    if unknown_symbols:
        print(f"\n📋 Found {len(unknown_symbols):,} NULL symbols without clear suffixes")
        print("\n   Examples:")
        for symbol in unknown_symbols[:20]:
            print(f"      {symbol}")

        # Verify these too
        print("\n🔬 Checking if these are international or invalid...")
        verify_via_fmp(unknown_symbols, sample_size=min(50, len(unknown_symbols)))

    # Get confirmation
    total_to_delete = len(intl_symbols) + len(unknown_symbols)
    print(f"\n⚠️  WARNING: About to delete {total_to_delete:,} symbols!")
    print("   This will remove data from all tables (stocks, stock_prices, dividend_history, dividend_calendar)")
    response = input("\n❓ Proceed with deletion? (type 'yes' to confirm): ")

    if response.lower() != 'yes':
        print("❌ Deletion cancelled.")
        return

    # Delete
    print("\n🚀 Starting deletion process...")
    print("=" * 80)

    all_symbols = intl_symbols + unknown_symbols
    tables = ['dividend_calendar', 'dividend_history', 'stock_prices', 'stocks']

    results = {}
    for table in tables:
        results[table] = delete_from_table(table, all_symbols)

    # Summary
    print("\n" + "=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)
    print("\nDeletion Summary:")
    for table, count in results.items():
        print(f"  {table:20} {count:,} records deleted")

    # Final stats
    print("\n📊 Final database stats...")
    supabase = get_supabase_client()

    # Check for any remaining NULL exchanges
    result = supabase.table('stocks').select('symbol', count='exact').is_('exchange', 'null').execute()
    null_count = len(result.data)

    # Get exchange distribution
    result = supabase.table('stocks').select('exchange', count='exact').execute()
    exchanges = {}
    for stock in result.data:
        ex = stock.get('exchange') or 'NULL'
        exchanges[ex] = exchanges.get(ex, 0) + 1

    print("\n📈 Final Exchange Distribution:")
    print("=" * 60)
    for exchange, count in sorted(exchanges.items(), key=lambda x: -x[1]):
        marker = "✅" if exchange in ALLOWED_EXCHANGES or exchange == 'NULL' else "❌"
        print(f"{marker} {exchange:15} {count:,} stocks")
    print("=" * 60)
    print(f"Total remaining: {sum(exchanges.values()):,} stocks")

    if null_count > 0:
        print(f"\n⚠️  {null_count:,} NULL exchange symbols still remain")
    else:
        print("\n✅ All NULL international symbols successfully removed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
