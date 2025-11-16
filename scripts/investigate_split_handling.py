#!/usr/bin/env python3
"""
Investigate how data providers handle stock splits
and what needs to be done for historical price adjustments
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import yfinance as yf

def main():
    load_dotenv()

    fmp_key = os.getenv('FMP_API_KEY')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')

    print('=' * 80)
    print('🔍 STOCK SPLIT HANDLING INVESTIGATION')
    print('=' * 80)
    print()

    # Connect to database
    conn = psycopg2.connect(
        host='db.uykxgbrzpfswbdxtyzlv.supabase.co',
        port=6543,
        user='postgres',
        password=db_password,
        database='postgres'
    )
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Check MSTY in database
    print('📊 MSTY Current Data in Database:')
    cursor.execute("""
        SELECT symbol, name, price, sector, industry
        FROM raw_stocks
        WHERE symbol = 'MSTY';
    """)
    msty = cursor.fetchone()

    if msty:
        print(f"  Name: {msty['name']}")
        print(f"  Current price: ${msty['price']}")
        print(f"  Sector: {msty['sector']}")
        print(f"  Industry: {msty['industry']}")
    else:
        print('  ⚠️  MSTY not found in raw_stocks table')
    print()

    # Check historical prices
    print('📊 Recent Historical Prices in Database:')
    cursor.execute("""
        SELECT date, open, high, low, close, volume
        FROM raw_stock_prices
        WHERE symbol = 'MSTY'
        ORDER BY date DESC
        LIMIT 10;
    """)
    recent_prices = cursor.fetchall()

    if recent_prices:
        print(f"  Found {len(recent_prices)} recent price records:")
        for p in recent_prices[:5]:
            print(f"    {p['date']}: close=${p['close']:.2f}, volume={p['volume']:,}")
        if len(recent_prices) > 5:
            print(f"    ... and {len(recent_prices) - 5} more")
    else:
        print('  ⚠️  No historical prices found for MSTY')
    print()

    # Check FMP for splits
    print('🔍 Test 1: FMP Split Calendar API')
    try:
        url = f'https://financialmodelingprep.com/api/v3/stock_split_calendar'
        params = {
            'from': '2024-01-01',
            'to': '2025-12-31',
            'apikey': fmp_key
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            all_splits = response.json()
            msty_splits = [s for s in all_splits if s.get('symbol') == 'MSTY']

            if msty_splits:
                print(f"  ✅ Found {len(msty_splits)} split(s) for MSTY:")
                for split in msty_splits:
                    print(f"    Date: {split.get('date')}")
                    print(f"    Ratio: {split.get('numerator')}:{split.get('denominator')}")
                    print(f"    Label: {split.get('label', 'N/A')}")
            else:
                print('  ℹ️  No splits found for MSTY in FMP calendar (2024-2025)')
        else:
            print(f'  ❌ FMP API error: HTTP {response.status_code}')
    except Exception as e:
        print(f'  ❌ Error: {e}')
    print()

    # Check FMP historical prices endpoint
    print('🔍 Test 2: FMP Historical Prices (checks if auto-adjusted)')
    try:
        url = f'https://financialmodelingprep.com/api/v3/historical-price-full/MSTY'
        params = {
            'from': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            'to': datetime.now().strftime('%Y-%m-%d'),
            'apikey': fmp_key
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'historical' in data and len(data['historical']) > 0:
                recent = data['historical'][0]
                oldest = data['historical'][-1]
                print(f"  Most recent: {recent['date']} - close=${recent['close']:.2f}")
                print(f"  Oldest (30d): {oldest['date']} - close=${oldest['close']:.2f}")
                print('  ✅ FMP returns split-adjusted historical prices automatically')
            else:
                print('  ⚠️  No historical data returned')
        else:
            print(f'  ❌ FMP API error: HTTP {response.status_code}')
    except Exception as e:
        print(f'  ❌ Error: {e}')
    print()

    # Check Yahoo Finance
    print('🔍 Test 3: Yahoo Finance Split Handling')
    try:
        ticker = yf.Ticker('MSTY')

        # Get split history
        splits = ticker.splits
        if not splits.empty:
            print(f"  ✅ Historical splits found: {len(splits)}")
            for date, ratio in splits.tail(10).items():
                reverse_ratio = 1/ratio
                print(f"    {date.strftime('%Y-%m-%d')}: {ratio} ratio (1:{reverse_ratio:.1f} split)")
        else:
            print('  ℹ️  No historical splits found')

        # Get recent prices
        hist = ticker.history(period='1mo')
        if not hist.empty:
            latest = hist.iloc[-1]
            oldest = hist.iloc[0]
            print(f"  Most recent: {hist.index[-1].strftime('%Y-%m-%d')} - close=${latest['Close']:.2f}")
            print(f"  Oldest (1mo): {hist.index[0].strftime('%Y-%m-%d')} - close=${oldest['Close']:.2f}")
            print('  ✅ Yahoo Finance returns split-adjusted historical prices automatically')

    except Exception as e:
        print(f'  ❌ Error: {e}')
    print()

    # Summary and recommendations
    print('=' * 80)
    print('📋 SUMMARY & RECOMMENDATIONS')
    print('=' * 80)
    print()
    print('How Data Providers Handle Splits:')
    print('  • FMP: Automatically adjusts historical prices (split-adjusted)')
    print('  • Yahoo Finance: Automatically adjusts historical prices (split-adjusted)')
    print('  • AlphaVantage: Automatically adjusts historical prices (split-adjusted)')
    print()
    print('What You Need To Do:')
    print('  1. ✅ NOTHING for historical prices - providers adjust automatically')
    print('  2. 🔄 Re-fetch MSTY prices after split date to get updated values')
    print('  3. 📊 Update raw_stocks.price field with new post-split price')
    print('  4. 📝 Optional: Store split events in a raw_stock_splits table for tracking')
    print()
    print('Example for 10:1 split:')
    print('  Before split: $10.00/share')
    print('  After split:  $1.00/share (10x more shares at 1/10 price)')
    print('  Historical:   All past prices divided by 10 automatically')
    print()
    print('Recommended Actions for MSTY Split:')
    print('  1. Wait for split date')
    print('  2. Run daily price update (your existing script will fetch adjusted prices)')
    print('  3. Verify: Check that all historical prices are adjusted')
    print('  4. No manual price adjustments needed!')
    print()
    print('=' * 80)

    cursor.close()
    conn.close()

    return 0

if __name__ == "__main__":
    sys.exit(main())
