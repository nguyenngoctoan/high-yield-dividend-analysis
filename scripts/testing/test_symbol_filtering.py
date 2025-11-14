#!/usr/bin/env python3
"""
Test Symbol Filtering

Verifies that international symbols are properly filtered out.
"""

import sys
sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from lib.core.config import Config

# Test symbols
test_cases = [
    # International symbols that SHOULD be blocked
    ('0700.HK', 'Hong Kong', False),
    ('005930.KS', 'Korea', False),
    ('7203.T', 'Tokyo', False),
    ('VOD.L', 'London', False),
    ('SAP.DE', 'Germany', False),
    ('AAPL.AX', 'Australia', False),
    ('TSLA.PA', 'Paris', False),
    ('GOOGL.SW', 'Switzerland', False),
    ('AMZN.TW', 'Taiwan', False),
    ('MSFT.SI', 'Singapore', False),
    ('FB.BR', 'Brussels', False),
    ('NFLX.KQ', 'KOSDAQ', False),

    # US symbols that SHOULD be allowed
    ('AAPL', 'Apple', True),
    ('MSFT', 'Microsoft', True),
    ('GOOGL', 'Google', True),
    ('TSLA', 'Tesla', True),
    ('SPY', 'S&P 500 ETF', True),
    ('QQQ', 'Nasdaq ETF', True),
    ('VOO', 'Vanguard ETF', True),

    # Canadian symbols that SHOULD be allowed
    ('TD.TO', 'TD Bank', True),
    ('RY.TO', 'Royal Bank', True),
    ('SHOP.TO', 'Shopify', True),
    ('ENB.TO', 'Enbridge', True),
]

def test_symbol_filtering():
    """Test that symbol filtering works correctly."""
    print("=" * 80)
    print("Symbol Filtering Test")
    print("=" * 80)
    print()

    passed = 0
    failed = 0

    for symbol, description, should_allow in test_cases:
        is_international = Config.EXCHANGE.is_international_symbol(symbol)
        is_allowed = Config.EXCHANGE.is_allowed_symbol(symbol)

        # Determine if test passed
        test_passed = (is_allowed == should_allow)

        if test_passed:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        expected = "ALLOW" if should_allow else "BLOCK"
        actual = "ALLOW" if is_allowed else "BLOCK"

        print(f"{status} | {symbol:15} | {description:20} | Expected: {expected:5} | Actual: {actual:5}")

    print()
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    print()

    if failed > 0:
        print("❌ FILTERING NOT WORKING CORRECTLY")
        print("Some symbols are not being filtered as expected.")
        return 1
    else:
        print("✅ ALL TESTS PASSED")
        print("Symbol filtering is working correctly.")
        print()
        print("Summary:")
        print(f"  - {len(Config.EXCHANGE.BLOCKED_SUFFIXES)} international suffixes blocked")
        print(f"  - {len(Config.EXCHANGE.ALLOWED_EXCHANGES)} exchanges allowed")
        print("  - US and Canadian symbols: ALLOWED")
        print("  - International symbols: BLOCKED")
        return 0

if __name__ == '__main__':
    sys.exit(test_symbol_filtering())
