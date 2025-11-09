#!/usr/bin/env python3
"""
Comprehensive investigation of symbols with NULL exchange values.

This script analyzes why certain symbols still have NULL exchanges after FMP backfill:
1. Samples NULL symbols and examines their characteristics
2. Queries FMP API to see what data is actually returned
3. Checks for patterns and determines root causes
4. Provides recommendations for handling these symbols
"""

import os
import sys
import requests
from time import sleep
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client
from collections import defaultdict
import json

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')

def get_null_exchange_symbols(limit=None):
    """Get all symbols with NULL exchange."""
    print("📊 Fetching NULL exchange symbols...")
    supabase = get_supabase_client()

    query = supabase.table('stocks').select('symbol, company, dividend_yield, last_updated').is_('exchange', 'null')

    if limit:
        query = query.limit(limit)

    result = query.execute()
    print(f"   Found {len(result.data)} NULL exchange symbols")
    return result.data

def analyze_symbol_patterns(symbols):
    """Analyze patterns in NULL symbols."""
    print("\n🔍 ANALYZING SYMBOL PATTERNS")
    print("=" * 80)

    patterns = {
        'has_dot': [],
        'has_hyphen': [],
        'has_caret': [],
        'has_slash': [],
        'numeric': [],
        'very_long': [],
        'special_chars': [],
        'normal': []
    }

    for stock in symbols:
        symbol = stock['symbol']

        if '.' in symbol:
            patterns['has_dot'].append(symbol)
        elif '-' in symbol:
            patterns['has_hyphen'].append(symbol)
        elif '^' in symbol:
            patterns['has_caret'].append(symbol)
        elif '/' in symbol:
            patterns['has_slash'].append(symbol)
        elif any(char.isdigit() for char in symbol):
            patterns['numeric'].append(symbol)
        elif len(symbol) > 10:
            patterns['very_long'].append(symbol)
        elif not symbol.replace('-', '').replace('.', '').isalnum():
            patterns['special_chars'].append(symbol)
        else:
            patterns['normal'].append(symbol)

    print("\n📋 Pattern Distribution:")
    for pattern, syms in patterns.items():
        if syms:
            print(f"   {pattern:20} {len(syms):,} symbols")
            # Show first 5 examples
            examples = syms[:5]
            print(f"      Examples: {', '.join(examples)}")

    return patterns

def query_fmp_profile(symbol):
    """Query FMP profile API for a symbol."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        sleep(0.15)  # Rate limiting
        return data
    except Exception as e:
        return {'error': str(e)}

def query_fmp_quote(symbol):
    """Query FMP quote API for a symbol."""
    try:
        url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        sleep(0.15)  # Rate limiting
        return data
    except Exception as e:
        return {'error': str(e)}

def deep_dive_sample(symbols, sample_size=50):
    """Deep dive into a sample of NULL symbols."""
    print(f"\n🔬 DEEP DIVE ANALYSIS ({sample_size} sample symbols)")
    print("=" * 80)

    # Take a diverse sample
    sample = symbols[:sample_size]

    results = {
        'profile_empty': [],
        'profile_error': [],
        'profile_no_exchange': [],
        'profile_international': [],
        'profile_has_exchange': [],
        'quote_has_exchange': []
    }

    for i, stock in enumerate(sample, 1):
        symbol = stock['symbol']
        print(f"\n[{i}/{sample_size}] Investigating {symbol}...")

        # Try profile endpoint
        profile_data = query_fmp_profile(symbol)

        if 'error' in profile_data:
            results['profile_error'].append({
                'symbol': symbol,
                'error': profile_data['error']
            })
            print(f"   ❌ Profile API error: {profile_data['error']}")
        elif not profile_data or len(profile_data) == 0:
            results['profile_empty'].append(symbol)
            print(f"   ⚠️  Profile returned empty data")
        elif isinstance(profile_data, list) and len(profile_data) > 0:
            exchange = profile_data[0].get('exchangeShortName', '').strip()
            country = profile_data[0].get('country', '').strip()
            currency = profile_data[0].get('currency', '').strip()

            if not exchange:
                results['profile_no_exchange'].append({
                    'symbol': symbol,
                    'country': country,
                    'currency': currency
                })
                print(f"   ⚠️  Profile has NO exchange field (country: {country}, currency: {currency})")
            else:
                # Check if it's an allowed exchange
                ALLOWED_EXCHANGES = [
                    "NYSE", "NASDAQ", "AMEX", "BATS", "BTS", "BYX", "BZX", "CBOE",
                    "EDGA", "EDGX", "PCX", "NGM", "OTCM", "OTCX", "OTC",
                    "TSX", "TSXV", "CSE", "TSE", "NEO"
                ]

                if exchange in ALLOWED_EXCHANGES:
                    results['profile_has_exchange'].append({
                        'symbol': symbol,
                        'exchange': exchange,
                        'country': country
                    })
                    print(f"   ✅ Profile HAS exchange: {exchange} (country: {country})")
                else:
                    results['profile_international'].append({
                        'symbol': symbol,
                        'exchange': exchange,
                        'country': country
                    })
                    print(f"   🌍 Profile has INTERNATIONAL exchange: {exchange} (country: {country})")

        # Also try quote endpoint
        quote_data = query_fmp_quote(symbol)
        if isinstance(quote_data, list) and len(quote_data) > 0:
            quote_exchange = quote_data[0].get('exchange', '').strip()
            if quote_exchange:
                results['quote_has_exchange'].append({
                    'symbol': symbol,
                    'exchange': quote_exchange
                })
                print(f"   📊 Quote API has exchange: {quote_exchange}")

    # Summary
    print("\n" + "=" * 80)
    print("📊 DEEP DIVE RESULTS SUMMARY")
    print("=" * 80)
    print(f"Profile API errors:           {len(results['profile_error'])} symbols")
    print(f"Profile returned empty:       {len(results['profile_empty'])} symbols")
    print(f"Profile has NO exchange:      {len(results['profile_no_exchange'])} symbols")
    print(f"Profile has VALID exchange:   {len(results['profile_has_exchange'])} symbols ⚠️ SHOULD BE UPDATED!")
    print(f"Profile has INTL exchange:    {len(results['profile_international'])} symbols")
    print(f"Quote API has exchange:       {len(results['quote_has_exchange'])} symbols")

    # Show symbols that SHOULD have been updated
    if results['profile_has_exchange']:
        print("\n⚠️  SYMBOLS THAT SHOULD HAVE VALID EXCHANGES:")
        print("=" * 60)
        for item in results['profile_has_exchange']:
            print(f"   {item['symbol']:15} -> {item['exchange']:10} (country: {item['country']})")

    return results

def check_recent_activity(symbols, sample_size=100):
    """Check if NULL symbols have recent price/dividend activity."""
    print(f"\n📈 CHECKING RECENT ACTIVITY ({sample_size} sample)")
    print("=" * 80)

    supabase = get_supabase_client()
    sample_symbols = [s['symbol'] for s in symbols[:sample_size]]

    # Check for recent prices
    price_result = supabase.table('stock_prices').select('symbol', count='exact').in_('symbol', sample_symbols).execute()

    # Check for dividends
    div_result = supabase.table('dividend_history').select('symbol', count='exact').in_('symbol', sample_symbols).execute()

    print(f"   Symbols with price data:     {len(price_result.data):,} / {sample_size}")
    print(f"   Symbols with dividend data:  {len(div_result.data):,} / {sample_size}")

    return {
        'has_prices': len(price_result.data),
        'has_dividends': len(div_result.data)
    }

def main():
    print("=" * 80)
    print("🔍 NULL EXCHANGE INVESTIGATION")
    print("=" * 80)

    # Get all NULL symbols
    null_symbols = get_null_exchange_symbols()

    if not null_symbols:
        print("\n✅ No NULL exchange symbols found!")
        return

    print(f"\n📊 Total NULL exchange symbols: {len(null_symbols):,}")

    # Analyze patterns
    patterns = analyze_symbol_patterns(null_symbols)

    # Deep dive into sample
    deep_results = deep_dive_sample(null_symbols, sample_size=100)

    # Check activity
    activity = check_recent_activity(null_symbols, sample_size=100)

    # Recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)

    if deep_results['profile_has_exchange']:
        print(f"\n1. 🔄 RE-RUN BACKFILL: {len(deep_results['profile_has_exchange'])} symbols")
        print("   These symbols DO have valid exchanges in FMP but weren't updated.")
        print("   Likely due to API errors during the first backfill run.")
        print("   → ACTION: Run backfill_exchange_from_fmp.py again")

    if deep_results['profile_international']:
        print(f"\n2. 🗑️  DELETE INTERNATIONAL: {len(deep_results['profile_international'])} symbols")
        print("   These are international symbols that should be removed.")
        print("   → ACTION: Run cleanup_international_symbols.py again")

    if deep_results['profile_empty'] or deep_results['profile_error']:
        total_invalid = len(deep_results['profile_empty']) + len(deep_results['profile_error'])
        print(f"\n3. 🗑️  DELETE INVALID: ~{total_invalid} symbols (from sample)")
        print("   These symbols don't exist in FMP or return errors.")
        print("   → ACTION: Create script to delete symbols with no FMP data")

    if deep_results['profile_no_exchange']:
        print(f"\n4. 🔍 MANUAL REVIEW: {len(deep_results['profile_no_exchange'])} symbols")
        print("   FMP has data but no exchange field.")
        print("   → ACTION: Try alternative data sources or manual mapping")

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
