# Rate Limiting Tests

This directory contains tests for the API rate limiting and tier enforcement systems.

## Test Files

### `test_rate_limiting.py`
Comprehensive pytest-based test suite for rate limiting. Tests:
- Monthly usage limits
- Per-minute rate limits with burst support
- Rate limit headers
- Reset behavior
- Concurrent request handling
- Different tier limits
- Tier enforcement (stock access, bulk limits)

**Run with pytest:**
```bash
pytest tests/test_rate_limiting.py -v -s
```

### `test_rate_limits_simple.py`
Standalone test script that can be run without pytest. More user-friendly for manual testing.

**Run directly:**
```bash
python3 tests/test_rate_limits_simple.py
```

## Setup

### Prerequisites

1. **API server running:**
   ```bash
   python3 -m uvicorn api.main:app --reload --port 8000
   ```

2. **Database migration applied:**
   ```bash
   psql -U postgres -d dividend_analysis -f migrations/update_pricing_tiers_v2.sql
   ```

3. **Test API key:**
   - Option 1: Use an existing API key
   - Option 2: Create one via OAuth:
     - Go to http://localhost:8000/login
     - Login with Google
     - Create API key in dashboard

### Install Test Dependencies

```bash
pip3 install pytest requests
```

## Running Tests

### Quick Test (Simple Script)

```bash
python3 tests/test_rate_limits_simple.py
```

You'll be prompted to enter an API key. The script will then run 7 tests:

1. ✅ Valid Request with Rate Limit Headers
2. ✅ Per-Minute Rate Limit Enforcement
3. ✅ Rate Limit Headers Validation
4. ✅ Invalid API Key (401 response)
5. ✅ No API Key (non-429 response)
6. ✅ Health Endpoint (bypasses rate limiting)
7. ✅ Concurrent Requests

### Full Test Suite (pytest)

```bash
# Run all tests
pytest tests/test_rate_limiting.py -v

# Run specific test
pytest tests/test_rate_limiting.py::TestRateLimiting::test_per_minute_rate_limit_exceeded -v

# Run with output
pytest tests/test_rate_limiting.py -v -s
```

## What Gets Tested

### Rate Limiting Behavior

1. **Monthly Limits:**
   - Free tier: 10,000 calls/month
   - Starter: 50,000 calls/month
   - Premium: 250,000 calls/month
   - Professional: 1M calls/month

2. **Per-Minute Limits:**
   - Free: 10 calls/min (20 burst)
   - Starter: 30 calls/min (60 burst)
   - Premium: 100 calls/min (200 burst)
   - Professional: 300 calls/min (600 burst)

3. **429 Response Format:**
   ```json
   {
     "error": "Rate limit exceeded",
     "message": "Per-minute limit of 10 calls (burst: 20) exceeded. Try again in 45 seconds.",
     "limit_type": "minute",
     "retry_after": 45
   }
   ```

4. **Response Headers:**
   - `X-RateLimit-Tier`: User's pricing tier
   - `X-RateLimit-Limit-Month`: Monthly limit
   - `X-RateLimit-Remaining-Month`: Remaining monthly calls
   - `X-RateLimit-Reset-Month`: Unix timestamp when monthly limit resets
   - `X-RateLimit-Limit-Minute`: Per-minute limit
   - `X-RateLimit-Remaining-Minute`: Remaining calls this minute
   - `X-RateLimit-Reset-Minute`: Unix timestamp when minute window resets
   - `Retry-After`: Seconds until retry (on 429 only)
   - `X-RateLimit-Type`: "monthly" or "minute" (on 429 only)

### Tier Enforcement

1. **Stock Access:**
   - Free: Sample dataset only (~150 stocks)
   - Starter: US stocks (~3,000)
   - Premium: US + International (~4,600)
   - Professional: All stocks (~8,000+)

2. **Bulk Limits:**
   - Free: Not available
   - Starter: 50 symbols per request
   - Premium: 200 symbols per request
   - Professional: 1,000 symbols per request

3. **Features:**
   - Webhooks: Premium+
   - Custom screeners: Professional+
   - White-label API: Professional+

## Expected Behavior

### ✅ Successful Request (200)
```
Status: 200 OK
Headers:
  X-RateLimit-Tier: free
  X-RateLimit-Limit-Month: 10000
  X-RateLimit-Remaining-Month: 9998
  X-RateLimit-Limit-Minute: 10
  X-RateLimit-Remaining-Minute: 8
```

### ⚠️ Rate Limited (429)
```
Status: 429 Too Many Requests
Headers:
  Retry-After: 45
  X-RateLimit-Type: minute
Body:
{
  "error": "Rate limit exceeded",
  "limit_type": "minute",
  "retry_after": 45
}
```

### ❌ Unauthorized (401)
```
Status: 401 Unauthorized
Body:
{
  "detail": "Invalid API key"
}
```

### 🚫 Forbidden (403)
```
Status: 403 Forbidden
Body:
{
  "error": "access_denied",
  "message": "Symbol TSLA is not accessible on the free tier",
  "upgrade_url": "http://localhost:3000/pricing"
}
```

## Troubleshooting

### Tests Fail with Connection Error
**Problem:** `requests.exceptions.ConnectionError`

**Solution:** Ensure API server is running:
```bash
python3 -m uvicorn api.main:app --reload --port 8000
```

### No Rate Limiting Occurs
**Problem:** Making many requests but never getting 429

**Possible causes:**
1. Rate limiting middleware not enabled in `api/main.py`
2. API key has high-tier limits
3. Database tier limits not configured

**Solution:**
```bash
# Check middleware is registered
grep -A 5 "RateLimiterMiddleware" api/main.py

# Check tier limits in database
psql -U postgres -d dividend_analysis -c "SELECT * FROM tier_limits WHERE tier='free';"
```

### 401 Instead of 429
**Problem:** Getting 401 Unauthorized instead of 429 when exceeding limits

**Solution:** Check API key is valid and active:
```bash
psql -U postgres -d dividend_analysis -c "SELECT tier, is_active, monthly_usage FROM divv_api_keys WHERE key_prefix='your_prefix';"
```

### Import Errors
**Problem:** `ModuleNotFoundError: No module named 'supabase_helpers'`

**Solution:** Run tests from project root:
```bash
cd /Users/toan/dev/high-yield-dividend-analysis
python3 tests/test_rate_limits_simple.py
```

## Database Queries for Manual Testing

```sql
-- Check current usage for an API key
SELECT
    key_prefix,
    tier,
    monthly_usage,
    minute_usage,
    monthly_usage_reset_at,
    minute_window_start
FROM divv_api_keys
WHERE key_prefix = 'your_prefix';

-- Reset usage for testing
UPDATE divv_api_keys
SET monthly_usage = 0, minute_usage = 0
WHERE key_prefix = 'your_prefix';

-- Set usage near limit
UPDATE divv_api_keys
SET monthly_usage = 9999
WHERE key_prefix = 'your_prefix';

-- Check tier configuration
SELECT * FROM tier_limits ORDER BY monthly_call_limit;

-- View all active API keys
SELECT
    key_prefix,
    tier,
    monthly_usage,
    request_count,
    last_used_at
FROM divv_api_keys
WHERE is_active = true;
```

## Next Steps

After running tests successfully:

1. ✅ Verify rate limiting works correctly
2. ✅ Test with different tier API keys
3. ✅ Implement Stripe integration for tier upgrades
4. ✅ Add monitoring/alerting for rate limit violations
5. ✅ Document rate limits in API documentation
