#!/usr/bin/env python3
"""
Backfill exchange metadata from FMP API for symbols with NULL or potentially incorrect exchanges.

This script queries FMP's profile endpoint to get the correct exchange for each symbol.
"""

import os
import sys
import requests
from time import sleep
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client, supabase_update
from threading import Semaphore

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')
fmp_limiter = Semaphore(10)  # Conservative rate limit

# US and Canadian exchanges we want to keep
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "BATS", "BTS", "BYX", "BZX", "CBOE",
    "EDGA", "EDGX", "PCX", "NGM",
    "OTCM", "OTCX", "OTC",
    "TSX", "TSXV", "CSE", "TSE", "NEO"
]

def get_exchange_from_fmp(symbol):
    """Get exchange for a symbol from FMP profile API."""
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            exchange = data[0].get('exchangeShortName', '').strip()
            return exchange if exchange else None
        return None
    except Exception as e:
        print(f"  ⚠️  Error fetching {symbol}: {e}")
        return None
    finally:
        fmp_limiter.release()
        sleep(0.1)  # Small delay between requests

def backfill_exchanges(target_exchange=None, batch_size=1000):
    """
    Backfill exchange metadata from FMP API.

    Args:
        target_exchange: If specified, only update symbols with this exchange (or NULL)
        batch_size: Number of symbols to process per batch
    """
    print("=" * 80)
    print("🔄 EXCHANGE METADATA BACKFILL FROM FMP API")
    print("=" * 80)

    supabase = get_supabase_client()

    # Get symbols that need exchange data
    print("\n📊 Fetching symbols to update...")

    if target_exchange:
        # Get symbols with NULL or specific exchange
        print(f"   Target: NULL or {target_exchange} exchanges")
        result1 = supabase.table('stocks').select('symbol, exchange').is_('exchange', 'null').execute()
        result2 = supabase.table('stocks').select('symbol, exchange').eq('exchange', target_exchange).execute()
        symbols_to_check = result1.data + result2.data
    else:
        # Get ALL symbols with NULL exchange
        print("   Target: NULL exchanges only")
        result = supabase.table('stocks').select('symbol, exchange').is_('exchange', 'null').execute()
        symbols_to_check = result.data

    print(f"✅ Found {len(symbols_to_check):,} symbols to check")

    if not symbols_to_check:
        print("\n✅ No symbols need updating!")
        return

    # Process in batches
    total_updated = 0
    total_checked = 0
    exchange_counts = {}

    for i in range(0, len(symbols_to_check), batch_size):
        batch = symbols_to_check[i:i + batch_size]
        print(f"\n📦 Processing batch {i // batch_size + 1} ({i + 1} to {i + len(batch)})")

        for stock in batch:
            symbol = stock['symbol']
            current_exchange = stock.get('exchange')

            # Get exchange from FMP
            fmp_exchange = get_exchange_from_fmp(symbol)

            if fmp_exchange:
                # Only update if it's an allowed exchange
                if fmp_exchange in ALLOWED_EXCHANGES:
                    try:
                        supabase_update('stocks',
                                      {'exchange': fmp_exchange},
                                      where_clause={'condition': 'symbol = %s', 'params': [symbol]})
                        total_updated += 1
                        exchange_counts[fmp_exchange] = exchange_counts.get(fmp_exchange, 0) + 1

                        if total_updated % 50 == 0:
                            print(f"  ✅ Updated {total_updated} symbols so far...")
                    except Exception as e:
                        print(f"  ❌ Error updating {symbol}: {e}")
                else:
                    print(f"  ⏭️  Skipping {symbol} - exchange {fmp_exchange} not in allowed list")

            total_checked += 1

            # Progress update every 100 symbols
            if total_checked % 100 == 0:
                print(f"  📊 Checked {total_checked:,} / {len(symbols_to_check):,} symbols...")

    # Summary
    print("\n" + "=" * 80)
    print("✅ BACKFILL COMPLETE")
    print("=" * 80)
    print(f"Total checked: {total_checked:,}")
    print(f"Total updated: {total_updated:,}")
    print(f"Not updated: {total_checked - total_updated:,}")

    if exchange_counts:
        print("\n📊 Updates by exchange:")
        for exchange, count in sorted(exchange_counts.items(), key=lambda x: -x[1]):
            print(f"   {exchange:15} {count:,} symbols")

    # Show final distribution
    print("\n📈 Final Exchange Distribution:")
    print("=" * 60)
    result = supabase.table('stocks').select('exchange', count='exact').execute()

    exchanges = {}
    for stock in result.data:
        ex = stock.get('exchange') or 'NULL'
        exchanges[ex] = exchanges.get(ex, 0) + 1

    for exchange, count in sorted(exchanges.items(), key=lambda x: -x[1]):
        marker = "✅" if exchange in ALLOWED_EXCHANGES or exchange == 'NULL' else "❌"
        print(f"{marker} {exchange:15} {count:,} stocks")
    print("=" * 60)
    print(f"Total: {sum(exchanges.values()):,} stocks")

if __name__ == "__main__":
    try:
        # By default, backfill NULL exchanges
        # To also check specific exchange, pass as argument
        target = sys.argv[1] if len(sys.argv) > 1 else None
        backfill_exchanges(target_exchange=target)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
