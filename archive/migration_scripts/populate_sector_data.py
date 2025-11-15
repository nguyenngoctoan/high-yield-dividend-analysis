#!/usr/bin/env python3
"""
Populate sector data for all stocks from FMP API.

For individual stocks: Single sector from company profile
For ETFs: Multiple sectors with percentages (e.g., "Technology (45%), Healthcare (30%), Financial (25%)")
"""

import os
import sys
import requests
from time import sleep
from dotenv import load_dotenv
from supabase_helpers import get_supabase_client, supabase_update
from threading import Semaphore
from collections import defaultdict

load_dotenv()

FMP_API_KEY = os.getenv('FMP_API_KEY')
fmp_limiter = Semaphore(10)  # Conservative rate limit

def get_etf_sector_weightings(symbol):
    """Get sector weightings for an ETF from FMP."""
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/etf-sector-weightings/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            # FMP returns sector weightings as list of dicts
            # Example: [{"sector": "Technology", "weightPercentage": "45.23"}, ...]
            sector_data = {}
            for item in data:
                sector = item.get('sector', '').strip()
                weight = item.get('weightPercentage', 0)

                if sector and weight:
                    try:
                        weight_float = float(weight) if isinstance(weight, (int, float, str)) else 0
                        if weight_float > 0:
                            sector_data[sector] = weight_float
                    except (ValueError, TypeError):
                        pass

            return sector_data

        return None
    except Exception as e:
        # ETF sector weightings may not exist for all symbols
        return None
    finally:
        fmp_limiter.release()
        sleep(0.1)

def get_company_sector(symbol):
    """Get sector for a regular stock from company profile."""
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            sector = data[0].get('sector', '').strip()
            return sector if sector else None

        return None
    except Exception as e:
        print(f"  ⚠️  Error fetching {symbol}: {e}")
        return None
    finally:
        fmp_limiter.release()
        sleep(0.1)

def format_sector_string(sector_data):
    """
    Format sector data as a string.

    Args:
        sector_data: Either a dict of {sector: percentage} or a single sector string

    Returns:
        Formatted string like "Technology (45%), Healthcare (30%)" or just "Technology"
    """
    if isinstance(sector_data, dict):
        # Multiple sectors with percentages (ETF)
        # Sort by percentage descending
        sorted_sectors = sorted(sector_data.items(), key=lambda x: -x[1])

        # Format as "Sector1 (X%), Sector2 (Y%)"
        # Only include sectors with >1% weight
        significant_sectors = [(sector, pct) for sector, pct in sorted_sectors if pct >= 1.0]

        if not significant_sectors:
            # If no significant sectors, take top 3
            significant_sectors = sorted_sectors[:3]

        if significant_sectors:
            formatted_parts = [f"{sector} ({pct:.1f}%)" for sector, pct in significant_sectors]
            return ", ".join(formatted_parts)

        return None

    elif isinstance(sector_data, str) and sector_data:
        # Single sector (regular stock)
        return sector_data

    return None

def populate_sectors(batch_size=1000):
    """
    Populate sector data for all stocks.

    Strategy:
    1. Try ETF sector weightings first (works for ETFs, fails gracefully for stocks)
    2. Fall back to company profile sector (works for stocks)
    3. Format appropriately and update database
    """
    print("=" * 80)
    print("📊 POPULATING SECTOR DATA FROM FMP API")
    print("=" * 80)

    supabase = get_supabase_client()

    # Get all stocks without sector data
    print("\n📊 Fetching stocks to update...")
    result = supabase.table('raw_stocks').select('symbol, sector').execute()

    stocks_to_update = []
    for stock in result.data:
        sector = stock.get('sector')
        # Update if sector is NULL or empty
        if not sector or sector.strip() == '':
            stocks_to_update.append(stock)

    print(f"✅ Found {len(stocks_to_update):,} stocks without sector data")

    if not stocks_to_update:
        print("\n✅ All stocks already have sector data!")
        return

    # Process in batches
    total_updated = 0
    total_checked = 0
    sector_type_counts = defaultdict(int)

    print(f"\n🚀 Processing {len(stocks_to_update):,} stocks in batches of {batch_size}...")

    for i in range(0, len(stocks_to_update), batch_size):
        batch = stocks_to_update[i:i + batch_size]
        print(f"\n📦 Batch {i // batch_size + 1} ({i + 1} to {i + len(batch)})")

        for stock in batch:
            symbol = stock['symbol']

            # Strategy: Try ETF sector weightings first, then fall back to company profile
            sector_string = None

            # 1. Try ETF sector weightings
            etf_sectors = get_etf_sector_weightings(symbol)
            if etf_sectors:
                sector_string = format_sector_string(etf_sectors)
                sector_type_counts['ETF (multi-sector)'] += 1

            # 2. Fall back to company profile
            if not sector_string:
                company_sector = get_company_sector(symbol)
                if company_sector:
                    sector_string = format_sector_string(company_sector)
                    sector_type_counts['Stock (single sector)'] += 1

            # 3. Update database if we got sector data
            if sector_string:
                try:
                    supabase_update('stocks',
                                  {'sector': sector_string},
                                  where_clause={'condition': 'symbol = %s', 'params': [symbol]})
                    total_updated += 1

                    if total_updated % 50 == 0:
                        print(f"  ✅ Updated {total_updated} stocks so far...")

                    # Show examples
                    if total_updated <= 10:
                        print(f"  📊 {symbol:10} -> {sector_string}")

                except Exception as e:
                    print(f"  ❌ Error updating {symbol}: {e}")
            else:
                print(f"  ⚠️  No sector data found for {symbol}")

            total_checked += 1

            # Progress update every 100 symbols
            if total_checked % 100 == 0:
                print(f"  📊 Checked {total_checked:,} / {len(stocks_to_update):,} symbols...")

    # Summary
    print("\n" + "=" * 80)
    print("✅ SECTOR POPULATION COMPLETE")
    print("=" * 80)
    print(f"Total checked: {total_checked:,}")
    print(f"Total updated: {total_updated:,}")
    print(f"Not updated: {total_checked - total_updated:,}")

    if sector_type_counts:
        print("\n📊 Updates by type:")
        for sector_type, count in sorted(sector_type_counts.items(), key=lambda x: -x[1]):
            print(f"   {sector_type:30} {count:,} symbols")

    # Show final statistics
    print("\n📈 Final Sector Coverage:")
    print("=" * 60)
    result = supabase.table('raw_stocks').select('sector', count='exact').execute()

    total_stocks = len(result.data)
    stocks_with_sector = sum(1 for s in result.data if s.get('sector') and s.get('sector').strip())
    stocks_without_sector = total_stocks - stocks_with_sector

    coverage_pct = (stocks_with_sector / total_stocks * 100) if total_stocks > 0 else 0

    print(f"Total stocks:        {total_stocks:,}")
    print(f"With sector data:    {stocks_with_sector:,} ({coverage_pct:.1f}%)")
    print(f"Without sector data: {stocks_without_sector:,}")
    print("=" * 60)

    # Show some example sector distributions
    print("\n📊 Sample Sector Strings (first 20):")
    result = supabase.table('raw_stocks').select('symbol, sector').not_.is_('sector', 'null').limit(20).execute()

    for stock in result.data:
        sector = stock.get('sector', '')
        if sector:
            print(f"   {stock['symbol']:10} {sector}")

if __name__ == "__main__":
    try:
        populate_sectors()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
