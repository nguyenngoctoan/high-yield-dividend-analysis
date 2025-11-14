#!/usr/bin/env python3
"""
Test Yahoo Finance Rate Limiting

Tests the improved rate limiting and adaptive backoff for Yahoo Finance API.
"""

import logging
import time
from lib.data_sources.yahoo_client import YahooClient
from lib.core.config import Config

# Set up logging to see rate limiting messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_yahoo_rate_limiting():
    """Test Yahoo Finance rate limiting with multiple requests."""

    logger.info("=" * 80)
    logger.info("Testing Yahoo Finance Rate Limiting")
    logger.info("=" * 80)

    # Initialize Yahoo client
    yahoo_client = YahooClient()

    # Test symbols (mix of stocks and ETFs)
    test_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',  # Tech stocks
        'VOO', 'SPY', 'QQQ', 'VTI', 'IWM',        # ETFs
        'T', 'VZ', 'IBM', 'INTC', 'CSCO'          # More stocks
    ]

    logger.info(f"Testing with {len(test_symbols)} symbols")
    logger.info(f"Yahoo concurrent requests: {Config.API.YAHOO_CONCURRENT_REQUESTS}")
    logger.info(f"Min delay: 0.5s between requests")
    logger.info("")

    start_time = time.time()
    success_count = 0
    fail_count = 0
    rate_limit_count = 0

    for i, symbol in enumerate(test_symbols, 1):
        logger.info(f"[{i}/{len(test_symbols)}] Fetching dividends for {symbol}...")

        try:
            result = yahoo_client.fetch_dividends(symbol)

            if result and result.get('data'):
                success_count += 1
                logger.info(f"  ✅ Success: {result['count']} dividends")
            else:
                fail_count += 1
                logger.info(f"  ℹ️  No dividend data (may not pay dividends)")

        except Exception as e:
            error_msg = str(e)
            if 'Too Many Requests' in error_msg or 'Rate limited' in error_msg:
                rate_limit_count += 1
                logger.error(f"  ⚠️  Rate limited: {e}")
            else:
                fail_count += 1
                logger.error(f"  ❌ Error: {e}")

    elapsed_time = time.time() - start_time

    logger.info("")
    logger.info("=" * 80)
    logger.info("Test Results")
    logger.info("=" * 80)
    logger.info(f"Total symbols: {len(test_symbols)}")
    logger.info(f"Successful: {success_count}")
    logger.info(f"Failed: {fail_count}")
    logger.info(f"Rate limited: {rate_limit_count}")
    logger.info(f"Elapsed time: {elapsed_time:.2f}s")
    logger.info(f"Avg time per symbol: {elapsed_time / len(test_symbols):.2f}s")
    logger.info("")

    if rate_limit_count > 0:
        logger.warning("⚠️  Rate limiting detected! The adaptive rate limiter should have backed off.")
        logger.warning("   If you see consecutive rate limit errors, consider:")
        logger.warning("   - Increasing min_delay in GlobalRateLimiters.get_yahoo_limiter()")
        logger.warning("   - Reducing YAHOO_CONCURRENT_REQUESTS in config.py")
    else:
        logger.info("✅ No rate limiting detected! Rate limiter is working correctly.")

    logger.info("=" * 80)


if __name__ == '__main__':
    test_yahoo_rate_limiting()
