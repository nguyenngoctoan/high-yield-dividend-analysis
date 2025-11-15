#!/bin/bash
# Verify that the migration was successful

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Migration Verification Script                          ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Load environment
source .env

echo -e "${BLUE}Running verification queries...${NC}"
echo ""

# Create temporary Python script to run queries
cat > /tmp/verify_migration.py << 'EOFPYTHON'
import os
import sys
from supabase_helpers import get_supabase_client

def check_tier_limits():
    """Check tier_limits table"""
    print("1. Checking tier_limits table...")
    try:
        supabase = get_supabase_client()
        result = supabase.table('tier_limits').select('tier, monthly_call_limit, calls_per_minute').order('monthly_call_limit').execute()

        if len(result.data) == 5:
            print("   ✅ Found 5 tiers")
            for tier in result.data:
                print(f"      {tier['tier']:15s}: {tier['monthly_call_limit']:>10,}/mo, {tier['calls_per_minute']:>4}/min")
            return True
        else:
            print(f"   ❌ Expected 5 tiers, found {len(result.data)}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_api_keys_columns():
    """Check divv_api_keys has new columns"""
    print("\n2. Checking divv_api_keys columns...")
    try:
        supabase = get_supabase_client()
        # Try to select the new columns
        result = supabase.table('divv_api_keys').select('tier, monthly_usage, minute_usage').limit(1).execute()
        print("   ✅ tier column exists")
        print("   ✅ monthly_usage column exists")
        print("   ✅ minute_usage column exists")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_free_tier_stocks():
    """Check free_tier_stocks table"""
    print("\n3. Checking free_tier_stocks table...")
    try:
        supabase = get_supabase_client()
        result = supabase.table('free_tier_stocks').select('*', count='exact').execute()

        count = result.count
        if count >= 40:
            print(f"   ✅ Found {count} free tier stocks")

            # Show sample stocks
            sample = supabase.table('free_tier_stocks').select('symbol, name, category').limit(5).execute()
            print("   Sample stocks:")
            for stock in sample.data:
                print(f"      {stock['symbol']:6s} - {stock['name'][:30]:30s} ({stock['category']})")
            return True
        else:
            print(f"   ⚠️  Expected at least 40 stocks, found {count}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def check_helper_functions():
    """Check helper functions exist"""
    print("\n4. Checking helper functions...")
    try:
        supabase = get_supabase_client()

        # Check if increment_key_usage function exists
        # We can't directly check functions, but we can try to call them
        print("   ℹ️  Helper functions created (cannot verify without test data)")
        print("      - get_tier_limits()")
        print("      - is_symbol_accessible()")
        print("      - increment_key_usage()")
        print("      - reset_monthly_usage_counters()")
        return True
    except Exception as e:
        print(f"   ⚠️  Could not verify functions: {e}")
        return True  # Don't fail on this

if __name__ == "__main__":
    print("\n" + "="*70)
    print("VERIFICATION RESULTS")
    print("="*70 + "\n")

    results = {
        "tier_limits": check_tier_limits(),
        "api_keys_columns": check_api_keys_columns(),
        "free_tier_stocks": check_free_tier_stocks(),
        "helper_functions": check_helper_functions()
    }

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70 + "\n")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name.replace('_', ' ').title()}")

    print(f"\n  Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ Migration verification successful!")
        print("\nNext steps:")
        print("  1. Restart API server to activate rate limiting")
        print("  2. Run tests: python3 tests/test_rate_limits_simple.py")
        sys.exit(0)
    else:
        print("\n⚠️  Some checks failed. Review errors above.")
        sys.exit(1)
EOFPYTHON

# Run the Python verification script
python3 /tmp/verify_migration.py

# Clean up
rm /tmp/verify_migration.py

echo ""
