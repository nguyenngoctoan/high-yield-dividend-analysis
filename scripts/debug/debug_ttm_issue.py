#!/usr/bin/env python3
"""Debug high TTM values for HOOY and WNTR."""

import sys
from pathlib import Path
import psycopg2
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

symbols = ['HOOY', 'WNTR']

conn = psycopg2.connect(
    host='localhost',
    port=5434,
    database='postgres',
    user='postgres',
    password=os.getenv('PGPASSWORD', 'postgres')
)
cursor = conn.cursor()

for symbol in symbols:
    print("=" * 80)
    print(f"🔍 INVESTIGATING {symbol} - HIGH TTM")
    print("=" * 80)

    # Get current metrics from database
    cursor.execute("""
        SELECT total_return_ttm, price_change_ttm, dividend_yield, price, frequency
        FROM raw_stocks
        WHERE symbol = %s
    """, (symbol,))

    result = cursor.fetchone()
    if result:
        ttm, price_chg_ttm, div_yield, price, frequency = result
        print(f"\n📊 CURRENT METRICS IN DATABASE:")
        print(f"Total Return TTM: {ttm*100 if ttm else 0:.2f}%")
        print(f"Price Change TTM: {price_chg_ttm*100 if price_chg_ttm else 0:.2f}%")
        print(f"Dividend Yield: {div_yield*100 if div_yield else 0:.2f}%")
        print(f"Current Price: ${price}")
        print(f"Frequency: {frequency}")

    # Check price history
    print(f"\n📈 PRICE HISTORY:")
    cursor.execute("""
        SELECT MIN(date) as first_date,
               MAX(date) as last_date,
               COUNT(*) as total_records
        FROM raw_stock_prices
        WHERE symbol = %s
    """, (symbol,))

    first_date, last_date, total_records = cursor.fetchone()
    print(f"First price: {first_date}")
    print(f"Last price: {last_date}")
    print(f"Total records: {total_records}")

    days_of_data = (last_date - first_date).days
    print(f"Days of data: {days_of_data} ({days_of_data/30.44:.1f} months)")

    # Check for data gaps
    print(f"\n🕳️  CHECKING FOR DATA GAPS:")
    cursor.execute("""
        WITH date_diffs AS (
            SELECT
                date,
                LAG(date) OVER (ORDER BY date) as prev_date,
                date - LAG(date) OVER (ORDER BY date) as gap_days
            FROM raw_stock_prices
            WHERE symbol = %s
            ORDER BY date
        )
        SELECT date, prev_date, gap_days
        FROM date_diffs
        WHERE gap_days > 30
        ORDER BY gap_days DESC
        LIMIT 10;
    """, (symbol,))

    gaps = cursor.fetchall()
    if gaps:
        print(f"Found {len(gaps)} gaps > 30 days:")
        for dt, prev_dt, gap in gaps:
            print(f"  Gap of {gap} days: {prev_dt} → {dt}")
    else:
        print("No significant gaps found")

    # Get price at first date and last date
    cursor.execute("""
        SELECT adj_close FROM raw_stock_prices
        WHERE symbol = %s AND date = %s
    """, (symbol, first_date))
    first_price = float(cursor.fetchone()[0])

    cursor.execute("""
        SELECT adj_close FROM raw_stock_prices
        WHERE symbol = %s AND date = %s
    """, (symbol, last_date))
    last_price = float(cursor.fetchone()[0])

    print(f"\n💵 PRICE DATA:")
    print(f"First price ({first_date}): ${first_price:.2f}")
    print(f"Last price ({last_date}): ${last_price:.2f}")
    print(f"Price change: ${last_price - first_price:.2f} ({(last_price/first_price - 1)*100:.2f}%)")

    # Check what price would be used for 12-month TTM
    today = date.today()
    twelve_months_ago = today - timedelta(days=365)
    twelve_mo_start = twelve_months_ago - timedelta(days=15)
    twelve_mo_end = twelve_months_ago + timedelta(days=15)

    print(f"\n🎯 TTM CALCULATION (12 months ago = {twelve_months_ago}):")

    # Check if we have price in 30-day window
    cursor.execute("""
        SELECT adj_close, date,
               ABS(EXTRACT(EPOCH FROM (date::timestamp - %s::timestamp))) as seconds_diff
        FROM raw_stock_prices
        WHERE symbol = %s
          AND date >= %s
          AND date <= %s
        ORDER BY ABS(EXTRACT(EPOCH FROM (date::timestamp - %s::timestamp)))
        LIMIT 1
    """, (twelve_months_ago, symbol, twelve_mo_start, twelve_mo_end, twelve_months_ago))

    ttm_price = cursor.fetchone()
    if ttm_price:
        ttm_close, ttm_date, diff = ttm_price
        ttm_close = float(ttm_close)
        days_off = diff / 86400
        print(f"✅ Found price near 12mo ago: ${ttm_close:.2f} on {ttm_date} (±{days_off:.1f} days)")
        print(f"   Period return: {(last_price - ttm_close)/ttm_close*100:.2f}%")
        print(f"   Days: {(last_date - ttm_date).days}")
    else:
        print(f"❌ NO price found in 30-day window around {twelve_months_ago}")
        print(f"   Script will use EARLIEST price for projection: ${first_price:.2f} on {first_date}")
        print(f"   Days of data: {days_of_data}")

        # Calculate annualization
        period_return = (last_price - first_price) / first_price
        annualization_factor = 365.0 / days_of_data
        annualized_return = ((1 + period_return) ** annualization_factor) - 1

        print(f"\n⚠️  PROJECTED TTM (ANNUALIZED):")
        print(f"   Period return ({days_of_data} days): {period_return*100:.2f}%")
        print(f"   Annualization factor: {annualization_factor:.4f}x")
        print(f"   Formula: ((1 + {period_return:.4f}) ^ {annualization_factor:.4f}) - 1")
        print(f"   Annualized return: {annualized_return*100:.2f}%")

        print(f"\n🔍 ISSUE IDENTIFIED:")
        if days_of_data < 365 and period_return > 0.5:
            print(f"   ⚠️  SHORT PERIOD ({days_of_data} days) + HIGH RETURN ({period_return*100:.2f}%)")
            print(f"   ⚠️  Annualization amplifies the return significantly!")
            print(f"   ⚠️  This may not be realistic for annual projection")
        if first_date > twelve_months_ago:
            print(f"   ⚠️  Using earliest price ({first_date}) which is AFTER 12mo target!")
            print(f"   ⚠️  This is NOT a true 12-month return")

    # Check dividends
    print(f"\n💰 DIVIDENDS:")
    cursor.execute("""
        SELECT COUNT(*), SUM(amount)
        FROM raw_dividends
        WHERE symbol = %s
        AND ex_date >= %s
    """, (symbol, first_date))

    div_count, div_total = cursor.fetchone()
    div_total = float(div_total) if div_total else 0

    print(f"Dividends since {first_date}: {div_count} payments = ${div_total:.2f}")

    if days_of_data < 365:
        annualized_divs = div_total * (365.0 / days_of_data)
        print(f"Annualized dividends: ${annualized_divs:.2f}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("💡 CONCLUSION:")
print("=" * 80)
print("The issue is likely:")
print("1. Stock has < 12 months of data (recent IPO/listing)")
print("2. Had large price gains in short period")
print("3. Annualization formula amplifies short-term gains")
print("4. Result: Unrealistic projected annual return")
print("\nPossible solutions:")
print("- Set minimum data threshold (e.g., 180 days) for projection")
print("- Cap maximum annualized return (e.g., 500%)")
print("- Flag projected returns as estimates")
print("- Use simpler linear projection for short periods")
