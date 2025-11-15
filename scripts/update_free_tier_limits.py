#!/usr/bin/env python3
"""
Update Free Tier Limits to Half

Reduces free tier from:
- 10,000 calls/month -> 5,000 calls/month
- 10 calls/minute -> 5 calls/minute
- Burst 20 -> Burst 10
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_helpers import get_supabase_client

def main():
    print("=" * 80)
    print("Updating Free Tier Limits")
    print("=" * 80)
    print()

    # Get Supabase client
    supabase = get_supabase_client()

    # Update free tier limits
    print("Updating free tier limits in tier_limits table...")

    try:
        result = supabase.table('divv_tier_limits').update({
            'monthly_call_limit': 5000,
            'calls_per_minute': 5,
            'burst_limit': 10,
            'updated_at': 'NOW()'
        }).eq('tier', 'free').execute()

        if result.data:
            print("✅ Successfully updated free tier limits:")
            print(f"   - Monthly calls: 10,000 -> 5,000")
            print(f"   - Calls/minute: 10 -> 5")
            print(f"   - Burst limit: 20 -> 10")
            print()
            print("Updated record:", result.data[0])
        else:
            print("❌ No records updated. Free tier may not exist in database.")

    except Exception as e:
        print(f"❌ Error updating tier limits: {e}")
        sys.exit(1)

    print()
    print("=" * 80)
    print("Migration Complete")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Restart API server to pick up new limits")
    print("2. Verify limits with: curl http://localhost:8000/health")
    print()

if __name__ == "__main__":
    main()
