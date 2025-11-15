#!/usr/bin/env python3
"""
Verify TTM calculation for weekly dividend stocks.

The key question: Does weekly dividend frequency require different TTM calculation?

Answer: NO - TTM is period-agnostic. We sum ALL dividends in the period regardless of frequency.
"""

import sys
from pathlib import Path
import psycopg2
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent))

symbol = 'LFGY'

print("=" * 80)
print(f"VERIFYING WEEKLY DIVIDEND TTM CALCULATION FOR {symbol}")
print("=" * 80)

conn = psycopg2.connect(
    host='localhost',
    port=5434,
    database='postgres',
    user='postgres',
    password=os.getenv('PGPASSWORD', 'postgres')
)
cursor = conn.cursor()

# Get price data range
cursor.execute("""
    SELECT MIN(date) as first_date, MAX(date) as last_date
    FROM raw_stock_prices
    WHERE symbol = %s
""", (symbol,))
first_date, last_date = cursor.fetchone()

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

days_of_data = (last_date - first_date).days

print(f"\n📅 DATA RANGE:")
print(f"Start: {first_date}")
print(f"End: {last_date}")
print(f"Days: {days_of_data} ({days_of_data/30.44:.1f} months)")

print(f"\n💵 PRICE DATA:")
print(f"Starting price: ${first_price:.2f}")
print(f"Ending price: ${last_price:.2f}")
print(f"Price change: ${last_price - first_price:.2f} ({(last_price/first_price - 1)*100:.2f}%)")

# Get all dividends in period (deduplicated)
cursor.execute("""
    SELECT ex_date, amount
    FROM raw_dividends
    WHERE symbol = %s
    AND ex_date >= %s
    AND ex_date <= %s
    ORDER BY ex_date
""", (symbol, first_date, last_date))

all_divs = cursor.fetchall()

# Deduplicate
unique_divs = {}
for ex_date, amount in all_divs:
    amount = float(amount)
    if ex_date not in unique_divs or amount > unique_divs[ex_date]:
        unique_divs[ex_date] = amount

total_dividends = sum(unique_divs.values())
num_dividends = len(unique_divs)

print(f"\n💰 DIVIDENDS (ACTUAL PERIOD):")
print(f"Number of dividends: {num_dividends}")
print(f"Total dividends: ${total_dividends:.2f}")
print(f"Average per dividend: ${total_dividends/num_dividends:.2f}")

# Show weekly pattern
if num_dividends >= 2:
    dates = sorted(unique_divs.keys())
    intervals = []
    for i in range(1, len(dates)):
        days_between = (dates[i] - dates[i-1]).days
        intervals.append(days_between)

    avg_interval = sum(intervals) / len(intervals)
    print(f"Average days between dividends: {avg_interval:.1f} days")
    print(f"Frequency: {'Weekly' if 4 <= avg_interval <= 13 else 'Unknown'}")

print(f"\n📊 ACTUAL PERIOD RETURN:")
period_return = (last_price - first_price + total_dividends) / first_price
print(f"Total return ({days_of_data} days): {period_return*100:.2f}%")

print(f"\n🎯 ANNUALIZATION TO 12 MONTHS:")
print(f"Method: Compound annualization (works for ANY frequency)")
print(f"Formula: ((1 + period_return) ^ (365/days)) - 1")

annualization_factor = 365.0 / days_of_data
annualized_return = ((1 + period_return) ** annualization_factor) - 1

print(f"\nPeriod return: {period_return*100:.2f}%")
print(f"Annualization factor: {annualization_factor:.4f}x")
print(f"Annualized return (TTM): {annualized_return*100:.2f}%")

print(f"\n✅ DIVIDEND FREQUENCY DOESN'T MATTER FOR TTM!")
print(f"Whether weekly, monthly, or quarterly:")
print(f"1. Sum ALL dividends in the period")
print(f"2. Calculate period return")
print(f"3. Annualize using compound formula")
print(f"\nThe frequency only affects:")
print(f"- The 'frequency' field (for user information)")
print(f"- How many dividends appear in the period")
print(f"- NOT the calculation method")

# Verify with dividend yield
annualized_dividends = total_dividends * (365.0 / days_of_data)
dividend_yield = annualized_dividends / last_price

print(f"\n💵 DIVIDEND YIELD VERIFICATION:")
print(f"Actual dividends: ${total_dividends:.2f}")
print(f"Annualized dividends: ${annualized_dividends:.2f}")
print(f"Current price: ${last_price:.2f}")
print(f"Dividend yield: {dividend_yield*100:.2f}%")

print(f"\n🔍 KEY INSIGHT:")
print(f"For weekly dividends:")
print(f"- {num_dividends} dividends in {days_of_data} days = ~{num_dividends*365/days_of_data:.0f} dividends/year")
print(f"- Average ${total_dividends/num_dividends:.2f} per dividend")
print(f"- Annualized: ~{num_dividends*365/days_of_data:.0f} × ${total_dividends/num_dividends:.2f} = ${annualized_dividends:.2f}/year")

cursor.close()
conn.close()
