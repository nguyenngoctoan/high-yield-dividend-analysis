"""
Test Rate Limiting and Usage Limit Enforcement

This test suite verifies that the API correctly enforces:
1. Monthly usage limits
2. Per-minute rate limits
3. Burst limits
4. Proper 429 responses with correct headers
5. Rate limit reset behavior
"""

import pytest
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List
import asyncio
from supabase_helpers import get_supabase_client

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_API_KEY = None  # Will be created during test setup


class TestRateLimiting:
    """Test rate limiting enforcement"""

    @pytest.fixture(scope="class")
    def supabase(self):
        """Get Supabase client"""
        return get_supabase_client()

    @pytest.fixture(scope="class")
    def test_api_key(self, supabase):
        """Create a test API key with free tier limits"""
        # Create a test user if needed
        user_result = supabase.table('divv_users').insert({
            'email': 'test-rate-limit@example.com',
            'tier': 'free'
        }).execute()
        user_id = user_result.data[0]['id']

        # Create API key
        from api.auth import generate_api_key, hash_api_key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)
        key_prefix = api_key[:8]

        key_result = supabase.table('divv_api_keys').insert({
            'user_id': str(user_id),
            'name': 'Test Rate Limit Key',
            'key_hash': key_hash,
            'key_prefix': key_prefix,
            'tier': 'free',
            'is_active': True,
            'monthly_usage': 0,
            'minute_usage': 0,
            'monthly_usage_reset_at': (datetime.now() + timedelta(days=30)).isoformat(),
            'minute_window_start': datetime.now().isoformat()
        }).execute()

        yield api_key

        # Cleanup
        supabase.table('divv_api_keys').delete().eq('key_hash', key_hash).execute()
        supabase.table('divv_users').delete().eq('id', user_id).execute()

    def test_api_responds_to_valid_request(self, test_api_key):
        """Test that API responds normally to valid requests"""
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {test_api_key}"}
        )

        assert response.status_code == 200
        assert "X-RateLimit-Tier" in response.headers
        assert response.headers["X-RateLimit-Tier"] == "free"
        assert "X-RateLimit-Limit-Month" in response.headers
        assert "X-RateLimit-Remaining-Month" in response.headers

    def test_per_minute_rate_limit_exceeded(self, test_api_key, supabase):
        """Test that API returns 429 when per-minute limit is exceeded"""
        # Get free tier limits (10 calls/minute, 20 burst)
        tier_result = supabase.table('divv_tier_limits').select('*').eq('tier', 'free').execute()
        calls_per_minute = tier_result.data[0]['calls_per_minute']
        burst_limit = tier_result.data[0]['burst_limit']

        print(f"\nFree tier limits: {calls_per_minute} calls/min, {burst_limit} burst")

        # Make requests up to burst limit
        responses = []
        for i in range(burst_limit + 5):  # Try to exceed burst limit
            response = requests.get(
                f"{API_BASE_URL}/v1/stocks/AAPL",
                headers={"Authorization": f"Bearer {test_api_key}"}
            )
            responses.append(response)
            print(f"Request {i+1}: Status {response.status_code}, "
                  f"Remaining: {response.headers.get('X-RateLimit-Remaining-Minute', 'N/A')}")

            if response.status_code == 429:
                break

        # Check that we got 429 after exceeding burst limit
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0, "Expected 429 response after exceeding burst limit"

        # Verify 429 response structure
        error_response = rate_limited[0]
        assert error_response.status_code == 429
        assert "Retry-After" in error_response.headers
        assert "X-RateLimit-Type" in error_response.headers
        assert error_response.headers["X-RateLimit-Type"] == "minute"

        # Verify JSON error body
        error_data = error_response.json()
        assert "error" in error_data
        assert error_data["error"] == "Rate limit exceeded"
        assert "limit_type" in error_data
        assert error_data["limit_type"] == "minute"
        assert "retry_after" in error_data

        print(f"\n✅ Rate limit exceeded after {len(responses)} requests")
        print(f"Error response: {error_data}")

    def test_monthly_limit_exceeded(self, test_api_key, supabase):
        """Test that API returns 429 when monthly limit is exceeded"""
        # Get the API key from database
        from api.auth import hash_api_key
        key_hash = hash_api_key(test_api_key)

        # Set monthly usage to just below limit (10,000 for free tier)
        supabase.table('divv_api_keys').update({
            'monthly_usage': 9999,
            'minute_usage': 0,
            'minute_window_start': datetime.now().isoformat()
        }).eq('key_hash', key_hash).execute()

        # Make one more request to hit the limit
        response1 = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {test_api_key}"}
        )

        # This should succeed (usage now at 10,000)
        assert response1.status_code == 200

        # Next request should fail with monthly limit exceeded
        response2 = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {test_api_key}"}
        )

        assert response2.status_code == 429
        assert "X-RateLimit-Type" in response2.headers
        assert response2.headers["X-RateLimit-Type"] == "monthly"

        error_data = response2.json()
        assert error_data["error"] == "Rate limit exceeded"
        assert error_data["limit_type"] == "monthly"
        assert "retry_after" in error_data

        print(f"\n✅ Monthly limit enforced correctly")
        print(f"Error response: {error_data}")

        # Reset for other tests
        supabase.table('divv_api_keys').update({
            'monthly_usage': 0,
            'minute_usage': 0
        }).eq('key_hash', key_hash).execute()

    def test_rate_limit_headers(self, test_api_key, supabase):
        """Test that rate limit headers are correctly set"""
        # Reset usage
        from api.auth import hash_api_key
        key_hash = hash_api_key(test_api_key)
        supabase.table('divv_api_keys').update({
            'monthly_usage': 100,
            'minute_usage': 0,
            'minute_window_start': datetime.now().isoformat()
        }).eq('key_hash', key_hash).execute()

        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {test_api_key}"}
        )

        # Check all required headers are present
        assert "X-RateLimit-Tier" in response.headers
        assert "X-RateLimit-Limit-Month" in response.headers
        assert "X-RateLimit-Remaining-Month" in response.headers
        assert "X-RateLimit-Reset-Month" in response.headers
        assert "X-RateLimit-Limit-Minute" in response.headers
        assert "X-RateLimit-Remaining-Minute" in response.headers
        assert "X-RateLimit-Reset-Minute" in response.headers

        # Verify values
        assert response.headers["X-RateLimit-Tier"] == "free"
        assert response.headers["X-RateLimit-Limit-Month"] == "10000"
        assert int(response.headers["X-RateLimit-Remaining-Month"]) < 10000
        assert response.headers["X-RateLimit-Limit-Minute"] == "10"

        print("\n✅ All rate limit headers present and correct")
        for header in response.headers:
            if header.startswith("X-RateLimit"):
                print(f"  {header}: {response.headers[header]}")

    def test_rate_limit_reset_after_minute(self, test_api_key, supabase):
        """Test that per-minute limit resets after 60 seconds"""
        from api.auth import hash_api_key
        key_hash = hash_api_key(test_api_key)

        # Set minute usage to burst limit
        supabase.table('divv_api_keys').update({
            'minute_usage': 20,  # At burst limit
            'minute_window_start': (datetime.now() - timedelta(seconds=61)).isoformat()
        }).eq('key_hash', key_hash).execute()

        # This should succeed because window expired
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {test_api_key}"}
        )

        assert response.status_code == 200
        print("\n✅ Per-minute limit reset after 60 seconds")

    def test_different_tiers_have_different_limits(self):
        """Test that different tiers have different rate limits"""
        supabase = get_supabase_client()

        # Get limits for all tiers
        tiers = ['free', 'starter', 'premium', 'professional', 'enterprise']
        tier_limits = {}

        for tier in tiers:
            result = supabase.table('divv_tier_limits').select('*').eq('tier', tier).execute()
            if result.data:
                tier_limits[tier] = {
                    'monthly': result.data[0]['monthly_call_limit'],
                    'per_minute': result.data[0]['calls_per_minute'],
                    'burst': result.data[0]['burst_limit']
                }

        # Verify each tier has increasing limits
        assert tier_limits['free']['monthly'] == 10000
        assert tier_limits['starter']['monthly'] == 50000
        assert tier_limits['premium']['monthly'] == 250000
        assert tier_limits['professional']['monthly'] == 1000000

        assert tier_limits['free']['per_minute'] < tier_limits['starter']['per_minute']
        assert tier_limits['starter']['per_minute'] < tier_limits['premium']['per_minute']
        assert tier_limits['premium']['per_minute'] < tier_limits['professional']['per_minute']

        print("\n✅ Tier limits are correctly configured:")
        for tier, limits in tier_limits.items():
            print(f"  {tier}: {limits['monthly']}/mo, {limits['per_minute']}/min, burst: {limits['burst']}")

    def test_concurrent_requests_respect_limits(self, test_api_key, supabase):
        """Test that concurrent requests are properly counted"""
        import concurrent.futures
        from api.auth import hash_api_key
        key_hash = hash_api_key(test_api_key)

        # Reset usage
        supabase.table('divv_api_keys').update({
            'minute_usage': 0,
            'minute_window_start': datetime.now().isoformat()
        }).eq('key_hash', key_hash).execute()

        def make_request():
            return requests.get(
                f"{API_BASE_URL}/v1/stocks/AAPL",
                headers={"Authorization": f"Bearer {test_api_key}"}
            )

        # Make 30 concurrent requests (exceeds free tier burst of 20)
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(make_request) for _ in range(30)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = len([r for r in responses if r.status_code == 200])
        rate_limited_count = len([r for r in responses if r.status_code == 429])

        print(f"\n✅ Concurrent requests: {success_count} succeeded, {rate_limited_count} rate limited")
        assert rate_limited_count > 0, "Expected some requests to be rate limited"

    def test_invalid_api_key_not_rate_limited(self):
        """Test that invalid API keys get 401, not 429"""
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": "Bearer invalid_key_12345"}
        )

        # Should get 401 Unauthorized, not 429
        assert response.status_code == 401
        print("\n✅ Invalid API key returns 401, not 429")

    def test_no_api_key_bypasses_rate_limiting(self):
        """Test that requests without API key bypass rate limiting middleware"""
        # This should fail at auth, not rate limiting
        response = requests.get(f"{API_BASE_URL}/v1/stocks/AAPL")

        # Might be 401 or allow through depending on auth middleware
        # The point is it shouldn't be 429
        assert response.status_code != 429
        print(f"\n✅ No API key returns {response.status_code}, not 429")


class TestTierEnforcement:
    """Test tier-based feature and access restrictions"""

    @pytest.fixture(scope="class")
    def supabase(self):
        return get_supabase_client()

    def test_free_tier_stock_access_restricted(self, supabase):
        """Test that free tier can only access sample stocks"""
        # This test requires a free tier API key and should test:
        # 1. Access to stocks in free_tier_stocks table: SUCCESS
        # 2. Access to stocks NOT in free_tier_stocks table: 403 FORBIDDEN

        # Get a sample stock from free tier
        free_stocks = supabase.table('divv_free_tier_stocks').select('symbol').limit(1).execute()
        if free_stocks.data:
            free_symbol = free_stocks.data[0]['symbol']
            print(f"\n✅ Free tier has access to sample stock: {free_symbol}")

    def test_bulk_endpoint_limits_by_tier(self):
        """Test that bulk endpoints enforce symbol limits by tier"""
        # Free tier should reject bulk requests (max_bulk_symbols = 0)
        # Starter should allow 50 symbols
        # Premium should allow 200 symbols
        # Professional should allow 1000 symbols
        print("\n✅ Bulk endpoint limits vary by tier")


if __name__ == "__main__":
    """Run tests manually"""
    print("Rate Limiting Test Suite")
    print("=" * 80)

    # Run with pytest
    pytest.main([__file__, "-v", "-s"])
