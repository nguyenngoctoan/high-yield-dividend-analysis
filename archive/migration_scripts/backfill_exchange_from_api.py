#!/usr/bin/env python3
"""
Backfill exchange metadata using FMP API (primary) and Yahoo Finance (fallback).
Gets proper exchange names from APIs instead of inferring from symbol suffix.
"""

import sys
import os
import requests
import yfinance as yf
from supabase_helpers import get_supabase_client, supabase_update
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore

# API configuration
FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')

# Rate limiters
fmp_limiter = Semaphore(150)  # Ultimate plan: 3000/min
yahoo_limiter = Semaphore(10)  # Conservative rate limiting

def get_exchange_from_fmp(symbol):
    """Fetch exchange from FMP API."""
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0].get('exchangeShortName')
        return None
    except Exception as e:
        return None
    finally:
        fmp_limiter.release()

def get_exchange_from_yahoo(symbol):
    """Fetch exchange from Yahoo Finance API."""
    yahoo_limiter.acquire()
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info

        yahoo_exchange = info.get('exchange')
        if not yahoo_exchange:
            return None

        # Map Yahoo exchange codes to standard names
        yahoo_exchange_map = {
            'NMS': 'NASDAQ',      # NASDAQ Capital Market
            'NGM': 'NASDAQ',      # NASDAQ Global Market
            'NIM': 'NASDAQ',      # NASDAQ Integrated Market
            'NYQ': 'NYSE',        # New York Stock Exchange
            'PCX': 'ARCA',        # NYSE Arca (for ETFs)
            'TOR': 'TSX',         # Toronto Stock Exchange
            'LSE': 'LSE',         # London Stock Exchange
            'ASX': 'ASX',         # Australian Securities Exchange
            'FRA': 'FRA',         # Frankfurt
            'EPA': 'EPA',         # Euronext Paris
            'MIL': 'MIL',         # Milan
            'SWX': 'SWX',         # Swiss Exchange
            'HKG': 'HKEX',        # Hong Kong
            'KSC': 'KRX',         # Korea Exchange
            'JPX': 'TYO',         # Tokyo
            'TSE': 'TSX',         # Toronto (alternate code)
            'CVE': 'TSXV',        # TSX Venture
            'CNQ': 'CSE',         # Canadian Securities Exchange
            'AMEX': 'AMEX',       # American Stock Exchange
            'AMS': 'AMEX',        # AMEX alternate code
            'BTS': 'BATS',        # BATS Exchange
            'BYX': 'BYX',         # BATS BYX
            'BZX': 'BZX',         # BATS BZX
            'EDGA': 'EDGA',       # EDGA Exchange
            'EDGX': 'EDGX',       # EDGX Exchange
        }

        return yahoo_exchange_map.get(yahoo_exchange)
    except Exception as e:
        print(f"  ⚠️  Error fetching {symbol}: {e}")
        return None
    finally:
        yahoo_limiter.release()

def process_symbol(symbol):
    """Process a single symbol to get and update its exchange using FMP (primary) → Yahoo (fallback)."""
    # Try FMP first
    exchange = get_exchange_from_fmp(symbol)
    source = 'FMP'

    # Fallback to Yahoo if FMP didn't return exchange
    if not exchange:
        exchange = get_exchange_from_yahoo(symbol)
        source = 'Yahoo'

    if exchange:
        try:
            supabase_update('stocks',
                          {'exchange': exchange},
                          where_clause={'condition': 'symbol = %s', 'params': [symbol]})
            return {'symbol': symbol, 'exchange': exchange, 'source': source, 'status': 'updated'}
        except Exception as e:
            return {'symbol': symbol, 'error': str(e), 'status': 'failed'}
    else:
        return {'symbol': symbol, 'status': 'no_exchange'}

def backfill_exchanges(batch_size=1000, max_workers=50):
    """Backfill exchange metadata using FMP (primary) and Yahoo Finance (fallback)."""
    print("🔄 Starting exchange metadata backfill from FMP → Yahoo APIs...")

    supabase = get_supabase_client()

    # Get all stocks with NULL exchange
    result = supabase.table('raw_stocks').select('symbol, exchange').is_('exchange', 'null').execute()

    symbols_to_process = [stock['symbol'] for stock in result.data]
    total_symbols = len(symbols_to_process)

    print(f"📊 Found {total_symbols:,} stocks with NULL exchange")

    if total_symbols == 0:
        print("✅ All stocks already have exchange metadata!")
        return

    updated_count = 0
    failed_count = 0
    no_exchange_count = 0

    # Process in parallel with thread pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_symbol, symbol): symbol for symbol in symbols_to_process}

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()

            if result['status'] == 'updated':
                updated_count += 1
                source_label = f"[{result['source']}]" if result.get('source') else ""
                print(f"  ✅ {result['symbol']:15} → {result['exchange']:10} {source_label}")
            elif result['status'] == 'failed':
                failed_count += 1
                print(f"  ❌ {result['symbol']:15} → Error: {result.get('error', 'Unknown')}")
            else:  # no_exchange
                no_exchange_count += 1

            # Progress update every 100 symbols
            if i % 100 == 0:
                print(f"📈 Progress: {i}/{total_symbols} ({i/total_symbols*100:.1f}%)")

    print(f"\n" + "="*80)
    print(f"✅ Backfill complete!")
    print(f"   Total processed: {total_symbols:,}")
    print(f"   Updated: {updated_count:,}")
    print(f"   Failed: {failed_count:,}")
    print(f"   No exchange data: {no_exchange_count:,}")

    # Show exchange distribution
    print(f"\n📊 Exchange distribution after backfill:")
    result = supabase.table('raw_stocks').select('exchange').execute()

    exchange_counts = {}
    for stock in result.data:
        ex = stock.get('exchange') or '(null)'
        exchange_counts[ex] = exchange_counts.get(ex, 0) + 1

    for exchange, count in sorted(exchange_counts.items(), key=lambda x: -x[1]):
        print(f"   {exchange:15} {count:,}")

if __name__ == "__main__":
    try:
        backfill_exchanges()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
