#!/usr/bin/env python3
"""Test that dividend upsert works correctly (no duplicates)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from supabase_helpers import supabase_upsert, supabase_select

print("=" * 80)
print("TESTING DIVIDEND UPSERT (No Duplicates)")
print("=" * 80)

# Test data - LFGY dividend from 2025-10-09
test_dividend = {
    'symbol': 'LFGY',
    'ex_date': '2025-10-09',
    'amount': 0.5102,
    'payment_date': '2025-10-10',
    'record_date': '2025-10-09'
}

print("\n1️⃣  Count before upsert:")
result = supabase_select(
    'raw_dividends',
    columns='id,symbol,ex_date,amount',
    where_clause={'symbol': 'LFGY'}
)
print(f"   LFGY has {len(result)} dividend records")

lfgy_oct9 = [r for r in result if r['ex_date'] == '2025-10-09']
print(f"   Records for 2025-10-09: {len(lfgy_oct9)}")
if lfgy_oct9:
    print(f"   Amount: ${lfgy_oct9[0]['amount']}")

print("\n2️⃣  Attempting to insert the SAME dividend (should update, not duplicate):")
print(f"   Symbol: {test_dividend['symbol']}")
print(f"   Ex-date: {test_dividend['ex_date']}")
print(f"   Amount: ${test_dividend['amount']}")

upsert_result = supabase_upsert('raw_dividends', test_dividend)
print(f"   ✅ Upsert completed")

print("\n3️⃣  Count after upsert:")
result_after = supabase_select(
    'raw_dividends',
    columns='id,symbol,ex_date,amount',
    where_clause={'symbol': 'LFGY'}
)
print(f"   LFGY has {len(result_after)} dividend records")

lfgy_oct9_after = [r for r in result_after if r['ex_date'] == '2025-10-09']
print(f"   Records for 2025-10-09: {len(lfgy_oct9_after)}")

print("\n" + "=" * 80)
print("RESULT:")
print("=" * 80)
if len(result) == len(result_after):
    print("✅ SUCCESS: No duplicates created!")
    print(f"   Record count stayed at {len(result)}")
    print("   Upsert correctly updated the existing record")
else:
    print("❌ FAILURE: Duplicate was created!")
    print(f"   Before: {len(result)} records")
    print(f"   After: {len(result_after)} records")

if len(lfgy_oct9_after) == 1:
    print("✅ Only 1 record for 2025-10-09 (correct)")
else:
    print(f"❌ {len(lfgy_oct9_after)} records for 2025-10-09 (should be 1)")
