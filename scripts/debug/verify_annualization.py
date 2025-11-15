#!/usr/bin/env python3
"""Verify annualization logic for projected TTM calculations."""

import sys
from pathlib import Path
import psycopg2
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

symbol = 'LFGY'

print("=" * 80)
print(f"VERIFYING ANNUALIZATION LOGIC FOR {symbol}")
print("=" * 80)

# Connect to database
conn = psycopg2.connect(
    host='localhost',
    port=5434,
    database='postgres',
    user='postgres',
    password=os.getenv('PGPASSWORD', 'postgres')
)
cursor = conn.cursor()

# Get price history range
cursor.execute("""
    SELECT MIN(date) as first_date,
           MAX(date) as last_date,
           COUNT(*) as total_records
    FROM raw_stock_prices
    WHERE symbol = %s
""", (symbol,))
first_date, last_date, total_records = cursor.fetchone()

days_of_data = (last_date - first_date).days
print(f"\n📈 PRICE DATA:")
print(f"First price date: {first_date}")
print(f"Last price date: {last_date}")
print(f"Days of data: {days_of_data} days ({days_of_data/30.44:.1f} months)")
print(f"Total records: {total_records}")

# Get earliest and latest prices
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

print(f"\nFirst price: ${first_price}")
print(f"Last price: ${last_price}")

# Calculate price change
price_change = (last_price - first_price) / first_price
print(f"\n📊 PRICE CHANGE:")
print(f"Period return ({days_of_data} days): {price_change*100:.2f}%")

# Annualize price change
annualized_price_change = ((1 + price_change) ** (365.0 / days_of_data)) - 1
print(f"Annualized return (365 days): {annualized_price_change*100:.2f}%")

# Get dividends
cursor.execute("""
    SELECT ex_date, amount
    FROM raw_dividends
    WHERE symbol = %s
    AND ex_date >= %s
    AND ex_date <= %s
    ORDER BY ex_date
""", (symbol, first_date, last_date))
dividends = cursor.fetchall()

# Deduplicate
unique_divs = {}
for ex_date, amount in dividends:
    amount = float(amount)
    if ex_date not in unique_divs or amount > unique_divs[ex_date]:
        unique_divs[ex_date] = amount

total_dividends = sum(unique_divs.values())
num_unique_divs = len(unique_divs)

print(f"\n💰 DIVIDENDS:")
print(f"Total dividend records: {len(dividends)}")
print(f"Unique dividend dates: {num_unique_divs}")
print(f"Duplicate ratio: {len(dividends)/num_unique_divs:.1f}x")
print(f"Total dividends (period): ${total_dividends:.2f}")

# Annualize dividends (simple linear)
annualized_dividends = total_dividends * (365.0 / days_of_data)
print(f"Annualized dividends (365 days): ${annualized_dividends:.2f}")

# Calculate dividend yield
dividend_yield = annualized_dividends / last_price
print(f"\n📈 DIVIDEND YIELD:")
print(f"Current price: ${last_price:.2f}")
print(f"Annualized dividends: ${annualized_dividends:.2f}")
print(f"Dividend yield: {dividend_yield*100:.2f}%")

# Calculate total return
period_total_return = (last_price - first_price + total_dividends) / first_price
annualized_total_return = ((1 + period_total_return) ** (365.0 / days_of_data)) - 1

print(f"\n📊 TOTAL RETURN TTM:")
print(f"Period total return: {period_total_return*100:.2f}%")
print(f"Annualized total return: {annualized_total_return*100:.2f}%")

print("\n" + "=" * 80)
print("✅ VERIFICATION:")
print("=" * 80)
print(f"Annualization factor: {365.0/days_of_data:.4f}x")
print(f"\nFor dividends (linear): multiply by {365.0/days_of_data:.2f}x")
print(f"For returns (compound): raise to power of {365.0/days_of_data:.4f}")
print("\nThis is correct because:")
print("- Dividends are additive (sum) → linear annualization")
print("- Returns are multiplicative (compound) → exponential annualization")

cursor.close()
conn.close()
