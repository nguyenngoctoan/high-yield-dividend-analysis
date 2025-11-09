#!/usr/bin/env python3
"""Debug script to investigate YMAG frequency calculation."""

import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from supabase_helpers import supabase_select

# Get YMAG dividends
dividends = supabase_select(
    'raw_dividends',
    columns='ex_date,amount',
    where_clause={'symbol': 'YMAG'},
    order_by='ex_date.desc',
    limit=100
)

print(f"🔍 Debugging Frequency Calculation for YMAG")
print(f"Found {len(dividends)} dividends")
print()

if dividends and len(dividends) >= 2:
    # Sort by ex_date
    sorted_divs = sorted(dividends, key=lambda d: d['ex_date'])

    print("First 20 dividends (oldest to newest):")
    for i, div in enumerate(sorted_divs[:20], 1):
        print(f"  {i}. {div['ex_date']}: ${div['amount']}")
    print()

    # Calculate intervals
    intervals = []
    for i in range(1, len(sorted_divs)):
        prev_date = datetime.strptime(sorted_divs[i-1]['ex_date'], '%Y-%m-%d').date()
        curr_date = datetime.strptime(sorted_divs[i]['ex_date'], '%Y-%m-%d').date()
        days_between = (curr_date - prev_date).days
        intervals.append(days_between)

    print(f"Calculated {len(intervals)} intervals")
    print()

    # Show interval distribution
    interval_counts = Counter(intervals)
    print("Interval distribution (top 10):")
    for days, count in interval_counts.most_common(10):
        print(f"  {days} days: {count} occurrences")
    print()

    # Calculate average
    avg_interval = sum(intervals) / len(intervals)
    print(f"Average interval: {avg_interval:.2f} days")
    print()

    # Check against frequency ranges
    print("Frequency detection:")
    print(f"  Monthly (25-40 days): {'✅' if 25 <= avg_interval <= 40 else '❌'}")
    print(f"  Quarterly (75-110 days): {'✅' if 75 <= avg_interval <= 110 else '❌'}")
    print(f"  Semi-Annual (150-210 days): {'✅' if 150 <= avg_interval <= 210 else '❌'}")
    print(f"  Annual (330-400 days): {'✅' if 330 <= avg_interval <= 400 else '❌'}")
    print()

    # Check most common interval
    most_common_interval = interval_counts.most_common(1)[0][0]
    print(f"Most common interval: {most_common_interval} days")
    print(f"  Monthly (25-40 days): {'✅' if 25 <= most_common_interval <= 40 else '❌'}")
    print(f"  Quarterly (75-110 days): {'✅' if 75 <= most_common_interval <= 110 else '❌'}")
    print(f"  Semi-Annual (150-210 days): {'✅' if 150 <= most_common_interval <= 210 else '❌'}")
    print(f"  Annual (330-400 days): {'✅' if 330 <= most_common_interval <= 400 else '❌'}")
    print()

    print("❌ YMAG pays WEEKLY dividends (~7 days), which is not in our frequency categories!")
    print("   We need to add 'Weekly' as a frequency option.")
else:
    print("❌ Not enough dividend data to calculate frequency")
