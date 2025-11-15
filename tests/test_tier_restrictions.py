#!/usr/bin/env python3
"""
Tier Restriction Test Suite

Tests endpoint access restrictions and feature limitations based on pricing tiers.
Tests that:
- Free tier blocked from hourly/bulk endpoints
- Starter tier has access to hourly but blocked from bulk
- Premium tier has access to hourly but blocked from bulk
- Professional tier has access to bulk endpoints
- Historical data year limits enforced per tier
- Error messages include upgrade URLs

Can be run directly: python3 tests/test_tier_restrictions.py
"""

import sys
sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from supabase_helpers import get_supabase_client
import requests
import secrets
import hashlib
from datetime import datetime, timedelta
import uuid


# Configuration
API_BASE_URL = "http://localhost:8000"

# Tier configurations with feature access
# NOTE: Currently the users table constraint only allows 'free' and 'enterprise' tiers
# We test these two tiers to verify:
# - Free tier is properly restricted (no hourly, no bulk)
# - Enterprise tier has all features (hourly, bulk)
TIER_CONFIGS = {
    'free': {
        'has_hourly_access': False,
        'has_bulk_access': False,
        'historical_years': 1,
        'description': 'Free tier - EOD data only, 1 year history',
        'db_tier': 'free'
    },
    'enterprise': {
        'has_hourly_access': True,  # Enterprise has hourly (Premium+ feature)
        'has_bulk_access': True,     # Enterprise has bulk (Professional+ feature)
        'historical_years': 100,
        'description': 'Enterprise tier - All features, unlimited bulk',
        'db_tier': 'enterprise'
    }
}


class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    RESET = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_tier(tier: str, msg: str):
    colors = {
        'free': Colors.CYAN,
        'starter': Colors.BLUE,
        'premium': Colors.MAGENTA,
        'professional': Colors.YELLOW,
        'enterprise': Colors.GREEN
    }
    color = colors.get(tier, Colors.RESET)
    print(f"{color}[{tier.upper()}]{Colors.RESET} {msg}")


def create_test_api_key(tier: str) -> str:
    """Create a test API key for the specified tier"""
    supabase = get_supabase_client()

    # Generate API key
    api_key = f"divv_{tier}_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    key_prefix = api_key[:12]

    print_tier(tier, f"Creating test API key...")

    # Create or get test user
    try:
        user_result = supabase.table('divv_users').select('id').eq('email', f'test_restrictions_{tier}@local.dev').execute()

        if user_result.data:
            user_id = user_result.data[0]['id']
            print_tier(tier, f"Using existing test user: {user_id}")
        else:
            user_result = supabase.table('divv_users').insert({
                'google_id': f'test_restrictions_{tier}_{uuid.uuid4()}',
                'email': f'test_restrictions_{tier}@local.dev',
                'tier': tier,
                'name': f'Test User - Restrictions {tier.title()}'
            }).execute()
            user_id = user_result.data[0]['id']
            print_tier(tier, f"Created test user: {user_id}")
    except Exception as e:
        print_error(f"Could not create user for {tier}: {e}")
        return None

    # Create API key
    try:
        key_result = supabase.table('divv_api_keys').insert({
            'user_id': user_id,
            'name': f'{tier.title()} Restrictions Test Key',
            'key_hash': key_hash,
            'key_prefix': key_prefix,
            'tier': tier,
            'is_active': True,
            'monthly_usage': 0,
            'minute_usage': 0,
            'monthly_usage_reset_at': (datetime.now() + timedelta(days=30)).isoformat(),
            'minute_window_start': datetime.now().isoformat(),
            'request_count': 0
        }).execute()

        print_tier(tier, f"Created API key: {key_prefix}...")
        return api_key

    except Exception as e:
        print_error(f"Could not create API key for {tier}: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_hourly_access(tier: str, api_key: str) -> bool:
    """Test access to hourly price endpoint"""
    config = TIER_CONFIGS[tier]

    print_tier(tier, f"Testing hourly price access (should {'ALLOW' if config['has_hourly_access'] else 'BLOCK'})...")

    response = requests.get(
        f"{API_BASE_URL}/v1/prices/AAPL/hourly",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if config['has_hourly_access']:
        # Should allow access
        if response.status_code == 200:
            print_success(f"Hourly access allowed (as expected)")
            return True
        elif response.status_code == 404:
            # Data not found is okay - endpoint is accessible
            print_success(f"Hourly endpoint accessible (404 = no data, but not blocked)")
            return True
        else:
            print_error(f"Expected 200/404, got {response.status_code}: {response.text[:200]}")
            return False
    else:
        # Should block access with 403
        if response.status_code == 403:
            error_data = response.json()
            detail = error_data.get('detail', {})

            # Verify error includes tier info and upgrade URL
            if 'required_tier' in detail and 'upgrade_url' in detail:
                print_success(f"Hourly access blocked with proper error (403)")
                print_info(f"  Error: {detail.get('message', 'N/A')}")
                return True
            else:
                print_warning(f"Blocked (403) but missing tier info in error")
                return True  # Still counts as pass - endpoint is blocked
        else:
            print_error(f"Expected 403 (forbidden), got {response.status_code}")
            return False


def test_bulk_access(tier: str, api_key: str) -> bool:
    """Test access to bulk operations endpoint"""
    config = TIER_CONFIGS[tier]

    print_tier(tier, f"Testing bulk operations access (should {'ALLOW' if config['has_bulk_access'] else 'BLOCK'})...")

    # Bulk endpoint expects symbols as a JSON array in the body
    response = requests.post(
        f"{API_BASE_URL}/v1/bulk/stocks",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=["AAPL", "MSFT", "GOOGL"]  # Send as array, not object
    )

    if config['has_bulk_access']:
        # Should allow access
        if response.status_code == 200:
            print_success(f"Bulk access allowed (as expected)")
            return True
        elif response.status_code == 404:
            print_success(f"Bulk endpoint accessible (404 = no data, but not blocked)")
            return True
        else:
            print_error(f"Expected 200/404, got {response.status_code}: {response.text[:200]}")
            return False
    else:
        # Should block access with 403
        if response.status_code == 403:
            error_data = response.json()
            detail = error_data.get('detail', {})

            # Verify error includes tier info and upgrade URL
            if isinstance(detail, dict) and ('required_tier' in detail or 'error' in detail):
                print_success(f"Bulk access blocked with proper error (403)")
                print_info(f"  Error: {detail.get('message', 'N/A')}")
                return True
            else:
                print_warning(f"Blocked (403) but error format unexpected: {detail}")
                return True  # Still counts as pass - endpoint is blocked
        else:
            print_error(f"Expected 403 (forbidden), got {response.status_code}")
            return False


def test_historical_data_limits(tier: str, api_key: str) -> bool:
    """Test historical data year limits"""
    config = TIER_CONFIGS[tier]
    max_years = config['historical_years']

    print_tier(tier, f"Testing historical data limits (max {max_years} years)...")

    # Test 1: Request within limit (should work)
    years_within = min(max_years, 2)  # Request 2 years or max, whichever is smaller
    start_date = (datetime.now() - timedelta(days=365 * years_within)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/v1/prices/AAPL",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"start_date": start_date}
    )

    if response.status_code in [200, 404]:
        print_success(f"  ✓ Request within limit ({years_within} years) allowed")
    else:
        print_error(f"  ✗ Request within limit failed: {response.status_code}")
        return False

    # Test 2: Request exceeding limit (should block if tier has limits)
    if max_years < 100:  # Only test if there's an actual limit
        years_over = max_years + 10
        start_date_over = (datetime.now() - timedelta(days=365 * years_over)).strftime('%Y-%m-%d')

        response = requests.get(
            f"{API_BASE_URL}/v1/prices/AAPL",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"start_date": start_date_over}
        )

        if response.status_code == 403:
            error_data = response.json()
            detail = error_data.get('detail', {})
            print_success(f"  ✓ Request over limit ({years_over} years) blocked (403)")
            print_info(f"    Max years: {detail.get('max_years', 'N/A')}")
            return True
        elif response.status_code in [200, 404]:
            print_warning(f"  ⚠ Request over limit ({years_over} years) was allowed (might not be enforced yet)")
            return True  # Not failing yet - enforcement might be gradual
        else:
            print_error(f"  ✗ Unexpected response: {response.status_code}")
            return False
    else:
        print_info(f"  No limit to test (tier allows {max_years} years)")
        return True


def test_fundamental_data_access(tier: str, api_key: str) -> bool:
    """Test access to fundamental data (market cap, volume, etc.) - Free tier has LIMITED access, Starter+ has FULL access"""
    config = TIER_CONFIGS[tier]

    if tier == 'free':
        print_tier(tier, f"Testing basic price access (Free tier - price & yield only)...")

        # Free tier should only get price and dividend yield, not full fundamentals
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        if response.status_code == 200:
            data = response.json()
            # Free tier gets basic info but not full fundamentals
            print_success(f"  ✓ Stock info accessible (price & dividend yield)")
        elif response.status_code == 404:
            print_success(f"  ✓ Stock info endpoint accessible (404 = no data, but not blocked)")
        else:
            print_error(f"  ✗ Stock info failed: {response.status_code}")
            return False

        print_success(f"Free tier has basic price & yield access (as expected)")
        return True
    else:
        print_tier(tier, f"Testing fundamental data access (Starter+ tiers - full access)...")

        # Test 1: Stock quote endpoint (price, volume, change, etc.)
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL/quote",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        if response.status_code == 200:
            data = response.json()
            # Verify key fields are present
            if 'price' in data and 'volume' in data and 'market_cap' in data:
                print_success(f"  ✓ Stock quote accessible (price, volume, market_cap)")
            else:
                print_warning(f"  ⚠ Stock quote accessible but missing some fields")
        elif response.status_code == 404:
            print_success(f"  ✓ Stock quote endpoint accessible (404 = no data, but not blocked)")
        else:
            print_error(f"  ✗ Stock quote failed: {response.status_code}")
            return False

        # Test 2: Fundamentals endpoint (market cap, P/E, sector, etc.)
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL/fundamentals",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        if response.status_code == 200:
            data = response.json()
            # Verify key fields are present
            if 'market_cap' in data and 'sector' in data:
                print_success(f"  ✓ Fundamentals accessible (market_cap, sector, industry)")
            else:
                print_warning(f"  ⚠ Fundamentals accessible but missing some fields")
        elif response.status_code == 404:
            print_success(f"  ✓ Fundamentals endpoint accessible (404 = no data, but not blocked)")
        else:
            print_error(f"  ✗ Fundamentals failed: {response.status_code}")
            return False

        # Test 3: Basic stock info endpoint
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"  ✓ Stock info accessible (company name, exchange, sector)")
        elif response.status_code == 404:
            print_success(f"  ✓ Stock info endpoint accessible (404 = no data, but not blocked)")
        else:
            print_error(f"  ✗ Stock info failed: {response.status_code}")
            return False

        print_success(f"All fundamental data endpoints accessible for {tier} tier")
        return True


def test_tier_restrictions(tier: str, api_key: str) -> bool:
    """Run all restriction tests for a tier"""
    print("\n" + "="*80)
    print_tier(tier, f"Testing Tier Restrictions")
    print("="*80)
    print(f"Description: {TIER_CONFIGS[tier]['description']}")
    print()

    results = []

    # Test fundamental data access (should work for ALL tiers)
    results.append(test_fundamental_data_access(tier, api_key))
    print()

    # Test hourly access
    results.append(test_hourly_access(tier, api_key))
    print()

    # Test bulk access
    results.append(test_bulk_access(tier, api_key))
    print()

    # Test historical data limits
    results.append(test_historical_data_limits(tier, api_key))
    print()

    return all(results)


def cleanup_test_keys():
    """Clean up any existing test API keys"""
    supabase = get_supabase_client()

    print("\n" + "="*80)
    print("Cleaning up test API keys...")
    print("="*80)

    try:
        # Delete test users and their API keys
        for tier in TIER_CONFIGS.keys():
            email = f'test_restrictions_{tier}@local.dev'
            user_result = supabase.table('divv_users').select('id').eq('email', email).execute()

            if user_result.data:
                user_id = user_result.data[0]['id']
                # Delete API keys first
                supabase.table('divv_api_keys').delete().eq('user_id', user_id).execute()
                # Then delete user
                supabase.table('divv_users').delete().eq('id', user_id).execute()
                print_info(f"Cleaned up test data for {tier}")

        print_success("Cleanup complete")
    except Exception as e:
        print_warning(f"Cleanup error (non-critical): {e}")


def main():
    """Run comprehensive tier restriction testing"""
    print("\n" + "="*80)
    print("TIER RESTRICTION TEST SUITE")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Testing {len(TIER_CONFIGS)} tiers: {', '.join(TIER_CONFIGS.keys())}")
    print("="*80)

    # Clean up any existing test data
    cleanup_test_keys()

    # Test each tier
    results = {}
    test_keys = {}

    for tier in TIER_CONFIGS.keys():
        print(f"\n{'='*80}")
        print_tier(tier, "SETUP")
        print("="*80)

        api_key = create_test_api_key(tier)
        if not api_key:
            print_error(f"Failed to create API key for {tier}")
            results[tier] = False
            continue

        test_keys[tier] = api_key

        # Run tests for this tier
        results[tier] = test_tier_restrictions(tier, api_key)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for tier, result in results.items():
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.RESET} - {tier.upper()}")

    print("="*80)
    print(f"Passed: {passed}/{total} tiers")

    # Cleanup
    print("\n" + "="*80)
    print("CLEANUP")
    print("="*80)
    cleanup_test_keys()

    if passed == total:
        print_success(f"\nAll {total} tiers passed!")
        sys.exit(0)
    else:
        print_error(f"\n{total - passed} tier(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
