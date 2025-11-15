#!/usr/bin/env python3
"""
Simple Rate Limiting Test Script

Tests API behavior when usage limits are exceeded.
Can be run directly without pytest: python3 tests/test_rate_limits_simple.py
"""

import requests
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = None  # Set this to your test API key


class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def setup_test_api_key() -> Optional[str]:
    """Get test API key from environment, file, or user input"""
    print_info("Setting up test API key...")

    # Check environment variable first
    test_key = os.getenv('TEST_API_KEY')
    if test_key:
        print_info(f"Using API key from TEST_API_KEY environment variable")
        return test_key

    # Check if test key file exists
    test_key_file = '/tmp/test_api_key.txt'
    if os.path.exists(test_key_file):
        with open(test_key_file, 'r') as f:
            test_key = f.read().strip()
        if test_key:
            print_info(f"Using API key from {test_key_file}")
            return test_key

    # Only ask for input if stdin is a TTY (interactive terminal)
    if sys.stdin.isatty():
        test_key = input("\nEnter a test API key (or press Enter to skip setup): ").strip()
        if test_key:
            return test_key

    print_warning("No API key provided. Some tests will be skipped.")
    return None


def test_valid_request(api_key: str):
    """Test that API responds normally to valid requests"""
    print("\n" + "="*80)
    print("TEST 1: Valid Request with Rate Limit Headers")
    print("="*80)

    response = requests.get(
        f"{API_BASE_URL}/v1/stocks/AAPL",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Tier: {response.headers.get('X-RateLimit-Tier', 'N/A')}")
    print(f"Monthly Limit: {response.headers.get('X-RateLimit-Limit-Month', 'N/A')}")
    print(f"Monthly Remaining: {response.headers.get('X-RateLimit-Remaining-Month', 'N/A')}")
    print(f"Per-Minute Limit: {response.headers.get('X-RateLimit-Limit-Minute', 'N/A')}")
    print(f"Per-Minute Remaining: {response.headers.get('X-RateLimit-Remaining-Minute', 'N/A')}")

    if response.status_code == 200:
        print_success("Valid request succeeded with rate limit headers")
        return True
    else:
        print_error(f"Expected 200, got {response.status_code}")
        return False


def test_per_minute_limit(api_key: str):
    """Test per-minute rate limit by making rapid requests"""
    print("\n" + "="*80)
    print("TEST 2: Per-Minute Rate Limit Enforcement")
    print("="*80)

    print_info("Making rapid requests to test per-minute limit...")

    # Get initial rate limit info
    initial = requests.get(
        f"{API_BASE_URL}/v1/stocks/AAPL",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    per_minute_limit = int(initial.headers.get('X-RateLimit-Limit-Minute', '10'))
    print(f"Per-minute limit: {per_minute_limit}")
    print(f"Attempting to make {per_minute_limit + 25} requests rapidly...\n")

    responses = []
    rate_limited = False

    for i in range(per_minute_limit + 25):
        response = requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        responses.append(response)

        remaining = response.headers.get('X-RateLimit-Remaining-Minute', 'N/A')

        if response.status_code == 429:
            rate_limited = True
            print(f"Request {i+1}: {Colors.RED}429 RATE LIMITED{Colors.RESET}")
            print(f"  Error: {response.json().get('error', 'N/A')}")
            print(f"  Limit Type: {response.json().get('limit_type', 'N/A')}")
            print(f"  Retry After: {response.json().get('retry_after', 'N/A')} seconds")
            print(f"  Headers: Retry-After={response.headers.get('Retry-After', 'N/A')}, "
                  f"X-RateLimit-Type={response.headers.get('X-RateLimit-Type', 'N/A')}")
            break
        else:
            status_color = Colors.GREEN if response.status_code == 200 else Colors.YELLOW
            print(f"Request {i+1}: {status_color}{response.status_code}{Colors.RESET} "
                  f"(Remaining: {remaining})")

    print(f"\nTotal requests made: {len(responses)}")
    success_count = len([r for r in responses if r.status_code == 200])
    rate_limited_count = len([r for r in responses if r.status_code == 429])

    print(f"Successful: {success_count}")
    print(f"Rate Limited: {rate_limited_count}")

    if rate_limited:
        print_success("Per-minute rate limit was enforced (got 429 response)")

        # Verify response structure
        last_response = responses[-1]
        error_data = last_response.json()

        required_fields = ['error', 'limit_type', 'retry_after']
        if all(field in error_data for field in required_fields):
            print_success("429 response has all required fields")
        else:
            print_error(f"429 response missing fields. Got: {error_data.keys()}")

        return True
    else:
        print_warning("Did not hit rate limit (might have high tier or limits not enforced)")
        return False


def test_rate_limit_headers(api_key: str):
    """Test that all rate limit headers are present"""
    print("\n" + "="*80)
    print("TEST 3: Rate Limit Headers Validation")
    print("="*80)

    response = requests.get(
        f"{API_BASE_URL}/v1/stocks/AAPL",
        headers={"Authorization": f"Bearer {api_key}"}
    )

    required_headers = [
        'X-RateLimit-Tier',
        'X-RateLimit-Limit-Month',
        'X-RateLimit-Remaining-Month',
        'X-RateLimit-Reset-Month',
        'X-RateLimit-Limit-Minute',
        'X-RateLimit-Remaining-Minute',
        'X-RateLimit-Reset-Minute'
    ]

    missing_headers = []
    for header in required_headers:
        if header in response.headers:
            print_success(f"{header}: {response.headers[header]}")
        else:
            print_error(f"{header}: MISSING")
            missing_headers.append(header)

    if not missing_headers:
        print_success("All required rate limit headers are present")
        return True
    else:
        print_error(f"Missing headers: {', '.join(missing_headers)}")
        return False


def test_invalid_api_key():
    """Test that invalid API key returns 401, not 429"""
    print("\n" + "="*80)
    print("TEST 4: Invalid API Key (should get 401, not 429)")
    print("="*80)

    response = requests.get(
        f"{API_BASE_URL}/v1/stocks/AAPL",
        headers={"Authorization": "Bearer invalid_key_12345"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 401:
        print_success("Invalid API key correctly returns 401 Unauthorized")
        return True
    elif response.status_code == 429:
        print_error("Invalid API key incorrectly returns 429 (should be 401)")
        return False
    else:
        print_warning(f"Unexpected status code: {response.status_code}")
        return False


def test_no_api_key():
    """Test behavior when no API key is provided"""
    print("\n" + "="*80)
    print("TEST 5: No API Key Provided")
    print("="*80)

    response = requests.get(f"{API_BASE_URL}/v1/stocks/AAPL")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 429:
        print_error("No API key should not trigger rate limiting (should be 401 or allow through)")
        return False
    else:
        print_success(f"No API key returns {response.status_code} (not 429)")
        return True


def test_health_endpoint_not_rate_limited(api_key: str):
    """Test that health endpoint bypasses rate limiting"""
    print("\n" + "="*80)
    print("TEST 6: Health Endpoint (should bypass rate limiting)")
    print("="*80)

    response = requests.get(f"{API_BASE_URL}/health")

    print(f"Status Code: {response.status_code}")

    # Health endpoint should not have rate limit headers
    has_rate_limit_headers = 'X-RateLimit-Tier' in response.headers

    if response.status_code == 200 and not has_rate_limit_headers:
        print_success("Health endpoint bypasses rate limiting")
        return True
    else:
        print_warning("Health endpoint might be rate limited")
        return False


def test_concurrent_requests(api_key: str):
    """Test concurrent requests respect rate limits"""
    print("\n" + "="*80)
    print("TEST 7: Concurrent Requests")
    print("="*80)

    import concurrent.futures

    def make_request():
        return requests.get(
            f"{API_BASE_URL}/v1/stocks/AAPL",
            headers={"Authorization": f"Bearer {api_key}"}
        )

    print_info("Making 30 concurrent requests...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(make_request) for _ in range(30)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = len([r for r in responses if r.status_code == 200])
    rate_limited_count = len([r for r in responses if r.status_code == 429])

    print(f"Successful: {success_count}")
    print(f"Rate Limited: {rate_limited_count}")

    if rate_limited_count > 0:
        print_success("Concurrent requests properly rate limited")
        return True
    else:
        print_warning("No concurrent requests were rate limited")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RATE LIMITING TEST SUITE")
    print("="*80)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*80)

    # Setup
    api_key = setup_test_api_key()

    if not api_key:
        print_error("No API key provided. Cannot run tests.")
        print_info("To get an API key:")
        print_info("1. Go to http://localhost:8000/login")
        print_info("2. Login with Google OAuth")
        print_info("3. Navigate to dashboard and create an API key")
        sys.exit(1)

    # Run tests
    results = {}

    # Tests that require API key
    if api_key:
        results['Valid Request'] = test_valid_request(api_key)
        results['Per-Minute Limit'] = test_per_minute_limit(api_key)
        results['Rate Limit Headers'] = test_rate_limit_headers(api_key)
        results['Health Endpoint'] = test_health_endpoint_not_rate_limited(api_key)
        results['Concurrent Requests'] = test_concurrent_requests(api_key)

    # Tests that don't require API key
    results['Invalid API Key'] = test_invalid_api_key()
    results['No API Key'] = test_no_api_key()

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.RESET} - {test_name}")

    print("="*80)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print_success("All tests passed!")
        sys.exit(0)
    else:
        print_error(f"{total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
