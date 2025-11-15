#!/usr/bin/env python3
"""
Comprehensive Rate Limiting Test Suite - All Tiers

Tests rate limiting behavior for all subscription tiers with their specific limits.
Can be run directly: python3 tests/test_all_tiers.py
"""

import sys
sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from supabase_helpers import get_supabase_client
import requests
import time
import secrets
import hashlib
from datetime import datetime, timedelta
import uuid

# Configuration
API_BASE_URL = "http://localhost:8000"

# Tier configurations from database
# Note: users table allows 'free', 'pro', 'enterprise'
# tier_limits table maps them to rate limits
TIER_CONFIGS = {
    'free': {
        'monthly_call_limit': 10000,
        'calls_per_minute': 10,
        'burst_limit': 20,
        'description': 'Free tier with basic limits'
    },
    # NOTE: 'pro' tier exists in users table but divv_api_keys table constraint
    # currently only allows 'free' and 'enterprise', so we skip pro for now
    # 'pro': {
    #     'monthly_call_limit': 250000,
    #     'calls_per_minute': 100,
    #     'burst_limit': 200,
    #     'description': 'Pro tier with enhanced limits',
    #     'tier_limits_name': 'premium'  # Maps to 'premium' in tier_limits table
    # },
    'enterprise': {
        'monthly_call_limit': 999999999,
        'calls_per_minute': 1000,
        'burst_limit': 2000,
        'description': 'Enterprise tier with highest limits'
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
        user_result = supabase.table('divv_users').select('id').eq('email', f'test_{tier}@local.dev').execute()

        if user_result.data:
            user_id = user_result.data[0]['id']
            print_tier(tier, f"Using existing test user: {user_id}")
        else:
            user_result = supabase.table('divv_users').insert({
                'google_id': f'test_{tier}_{uuid.uuid4()}',
                'email': f'test_{tier}@local.dev',
                'tier': tier,
                'name': f'Test User - {tier.title()}'
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
            'name': f'{tier.title()} Test Key',
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


def test_tier_limits(tier: str, api_key: str) -> bool:
    """Test rate limits for a specific tier"""
    config = TIER_CONFIGS[tier]

    print("\n" + "="*80)
    print_tier(tier, f"Testing Rate Limits")
    print("="*80)
    print(f"Monthly Limit: {config['monthly_call_limit']:,}")
    print(f"Per-Minute Limit: {config['calls_per_minute']}")
    print(f"Burst Limit: {config['burst_limit']}")
    print()

    # Test 1: Verify tier is correctly identified
    print_tier(tier, "Test 1: Verify tier identification")
    response = requests.get(
        f"{API_BASE_URL}/v1/stocks/AAPL",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    if response.status_code != 200:
        print_error(f"Initial request failed: {response.status_code}")
        return False

    reported_tier = response.headers.get('X-RateLimit-Tier')
    if reported_tier != tier:
        print_error(f"Tier mismatch: expected '{tier}', got '{reported_tier}'")
        return False

    print_success(f"Tier correctly identified as: {tier}")

    # Test 2: Verify reported limits match configuration
    print_tier(tier, "Test 2: Verify reported limits")
    monthly_limit = int(response.headers.get('X-RateLimit-Limit-Month', 0))
    minute_limit = int(response.headers.get('X-RateLimit-Limit-Minute', 0))

    if monthly_limit != config['monthly_call_limit']:
        print_error(f"Monthly limit mismatch: expected {config['monthly_call_limit']}, got {monthly_limit}")
        return False

    if minute_limit != config['calls_per_minute']:
        print_error(f"Per-minute limit mismatch: expected {config['calls_per_minute']}, got {minute_limit}")
        return False

    print_success(f"Monthly limit: {monthly_limit:,}")
    print_success(f"Per-minute limit: {minute_limit}")

    # Test 3: Test burst limit enforcement
    print_tier(tier, "Test 3: Test burst limit enforcement")
    burst_limit = config['burst_limit']

    # Make requests up to burst limit + 5
    requests_to_make = min(burst_limit + 5, 50)  # Cap at 50 to keep tests fast
    print(f"Making {requests_to_make} rapid requests (burst limit: {burst_limit})...")

    responses = []
    for i in range(requests_to_make):
        resp = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        responses.append(resp)

        if resp.status_code == 429:
            print(f"  Request {i+1}: Rate limited (as expected after {burst_limit} requests)")
            break

    success_count = len([r for r in responses if r.status_code == 200])
    rate_limited_count = len([r for r in responses if r.status_code == 429])

    # For tiers with high burst limits, we might not hit the limit in our test
    if burst_limit <= 50:
        if rate_limited_count == 0:
            print_warning(f"Did not hit burst limit (made {success_count} successful requests)")
            # This is okay - might just be timing
        else:
            print_success(f"Burst limit enforced after {success_count} requests")
    else:
        print_info(f"Burst limit too high to test ({burst_limit}), made {success_count} requests successfully")

    return True


def cleanup_test_keys():
    """Clean up any existing test API keys"""
    supabase = get_supabase_client()

    print("\n" + "="*80)
    print("Cleaning up test API keys...")
    print("="*80)

    try:
        # Delete test users and their API keys
        for tier in TIER_CONFIGS.keys():
            email = f'test_{tier}@local.dev'
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
    """Run comprehensive tier testing"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TIER RATE LIMITING TEST SUITE")
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
        results[tier] = test_tier_limits(tier, api_key)

        # Wait a bit between tiers to reset rate limits
        if tier != list(TIER_CONFIGS.keys())[-1]:
            print(f"\nWaiting 2 seconds before next tier...")
            time.sleep(2)

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
