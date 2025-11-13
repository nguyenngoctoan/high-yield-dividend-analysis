# API Authentication & Rate Limiting Implementation

## Overview

Complete implementation of API key-based authentication and token bucket rate limiting for the Dividend API.

## What Was Implemented

### 1. Authentication Module (`api/auth.py`)

**Features**:
- API key generation with secure random tokens
- SHA-256 hashing for secure storage
- API key validation middleware
- User tier management (free, pro, enterprise)
- Optional authentication for public endpoints

**Key Functions**:
```python
generate_api_key()          # Generate secure API keys (sk_live_xxx)
hash_api_key(key)          # Hash keys with SHA-256
validate_api_key()         # FastAPI dependency for authentication
optional_api_key()         # Optional auth for public endpoints
get_rate_limit_for_tier()  # Get rate limits by subscription tier
```

**API Key Format**:
- Production: `sk_live_[32-char-random]`
- Test: `sk_test_[32-char-random]`

### 2. Rate Limiting Module (`api/rate_limit.py`)

**Features**:
- Token bucket algorithm with multiple time windows
- Per-minute, per-hour, and per-day limits
- Different limits for authenticated vs unauthenticated requests
- Tier-based rate limits
- Thread-safe in-memory storage (can be upgraded to Redis)

**Rate Limits by Tier**:

| Tier | Per Minute | Per Hour | Per Day |
|------|------------|----------|---------|
| **Free** | 60 | 1,000 | 10,000 |
| **Pro** | 600 | 20,000 | 500,000 |
| **Enterprise** | 6,000 | 200,000 | 10,000,000 |
| **Unauthenticated** | 20 | 200 | 1,000 |

**Response Headers**:
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp when limit resets
- `Retry-After`: Seconds to wait (on 429 errors)

### 3. API Key Management Endpoints (`api/routers/api_keys.py`)

**Endpoints**:

#### POST `/v1/keys` - Create API Key
Create a new API key (requires existing API key for auth).

**Request**:
```json
{
  "name": "Production Key",
  "tier": "free",
  "expires_in_days": 365,
  "metadata": {
    "email": "user@example.com",
    "company": "Acme Corp"
  }
}
```

**Response** (includes full key - shown only once!):
```json
{
  "id": "uuid",
  "api_key": "sk_live_abc123...",
  "key_prefix": "sk_live_abc12345",
  "name": "Production Key",
  "tier": "free",
  "expires_at": "2025-11-13T12:00:00Z",
  "created_at": "2024-11-13T12:00:00Z",
  "message": "API key created successfully. Save this key securely - it won't be shown again!"
}
```

#### GET `/v1/keys` - List API Keys
List all API keys for the authenticated user.

**Query Parameters**:
- `include_inactive`: Include revoked keys (default: false)

**Response**:
```json
[
  {
    "id": "uuid",
    "user_id": "user_001",
    "name": "Production Key",
    "key_prefix": "sk_live_abc12345",
    "tier": "free",
    "is_active": true,
    "request_count": 1523,
    "last_used_at": "2025-11-13T10:30:00Z",
    "expires_at": null,
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

#### DELETE `/v1/keys/{key_id}` - Revoke API Key
Revoke an API key (marks as inactive).

**Response**:
```json
{
  "id": "uuid",
  "revoked": true,
  "message": "API key has been revoked successfully"
}
```

#### GET `/v1/keys/{key_id}/usage` - Get Usage Statistics
Get usage statistics for an API key.

**Query Parameters**:
- `days`: Number of days of history (default: 30)

**Response**:
```json
{
  "api_key_id": "uuid",
  "period_days": 30,
  "total_requests": 15234,
  "successful_requests": 14998,
  "error_requests": 236,
  "error_rate": 1.55,
  "avg_response_time_ms": 45.3,
  "daily_usage": [
    {
      "request_date": "2025-11-13",
      "total_requests": 523,
      "successful_requests": 518,
      "error_requests": 5,
      "avg_response_time_ms": 43.2,
      "p95_response_time_ms": 98.5,
      "unique_ips": 3,
      "endpoints_used": ["/v1/stocks", "/v1/dividends"]
    }
  ]
}
```

### 4. Database Schema (`migrations/create_api_keys.sql`)

**Tables Created**:

#### `api_keys`
Stores API key information.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | VARCHAR(255) | User identifier |
| key_name | VARCHAR(255) | Friendly name |
| key_hash | VARCHAR(64) | SHA-256 hash (unique) |
| key_prefix | VARCHAR(20) | First 16 chars for identification |
| tier | VARCHAR(50) | Subscription tier |
| is_active | BOOLEAN | Active status |
| request_count | BIGINT | Total requests made |
| last_used_at | TIMESTAMP | Last usage timestamp |
| expires_at | TIMESTAMP | Expiration date (nullable) |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| metadata | JSONB | Additional metadata |

**Indexes**:
- `idx_api_keys_key_hash` (unique lookup)
- `idx_api_keys_user_id` (user queries)
- `idx_api_keys_is_active` (filtering)
- `idx_api_keys_created_at` (sorting)

#### `api_usage`
Tracks individual API requests for analytics.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| api_key_id | UUID | Reference to api_keys |
| endpoint | VARCHAR(255) | API endpoint |
| method | VARCHAR(10) | HTTP method |
| status_code | INTEGER | Response status |
| response_time_ms | INTEGER | Response time |
| request_size | BIGINT | Request size in bytes |
| response_size | BIGINT | Response size in bytes |
| ip_address | INET | Client IP |
| user_agent | TEXT | User agent string |
| error_message | TEXT | Error message (if any) |
| created_at | TIMESTAMP | Request timestamp |
| request_date | DATE | Date (generated column) |

**Indexes**:
- `idx_api_usage_api_key_id`
- `idx_api_usage_created_at`
- `idx_api_usage_request_date`
- `idx_api_usage_endpoint`
- `idx_api_usage_status_code`

#### `rate_limit_state`
Persistent storage for rate limiting (optional, for Redis replacement).

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| identifier | VARCHAR(255) | api_key:id or ip:address |
| window_type | VARCHAR(20) | minute, hour, day |
| tokens_remaining | DECIMAL | Tokens left in window |
| window_start | TIMESTAMP | Window start time |
| window_end | TIMESTAMP | Window end time |
| updated_at | TIMESTAMP | Last update |

#### `mv_api_usage_daily`
Materialized view for daily usage statistics (fast aggregation).

**Columns**:
- `api_key_id`, `request_date`
- `total_requests`, `successful_requests`, `error_requests`
- `avg_response_time_ms`, `p95_response_time_ms`
- `total_request_size`, `total_response_size`
- `unique_ips`, `endpoints_used`

**Functions**:
- `refresh_api_usage_stats()` - Refresh materialized view (run daily)
- `cleanup_expired_rate_limits()` - Clean old rate limit data (run hourly)

## Installation

### Step 1: Run Database Migration

**Option A: Manual (Recommended)**
1. Open Supabase SQL Editor
2. Copy contents of `migrations/create_api_keys.sql`
3. Execute the SQL

**Option B: Using Python Script** (if database connection works)
```bash
python3 scripts/run_api_keys_migration.py
```

### Step 2: Restart API Server

The API server needs to be restarted to load the new modules:

```bash
# Stop current server
pkill -f "uvicorn api.main:app"

# Start new server
cd /Users/toan/dev/high-yield-dividend-analysis
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3: Create Your First API Key

Since API key creation requires authentication, you need to bootstrap the first key manually:

```python
from api.auth import generate_api_key, hash_api_key
import uuid

# Generate a key
api_key = generate_api_key()
key_hash = hash_api_key(api_key)
key_prefix = api_key[:16]

print(f"API Key: {api_key}")
print(f"Hash: {key_hash}")
print(f"Prefix: {key_prefix}")

# Insert into database manually
"""
INSERT INTO api_keys (id, user_id, key_name, key_hash, key_prefix, tier, is_active, metadata)
VALUES (
    gen_random_uuid(),
    'admin_user',
    'Bootstrap Admin Key',
    '{key_hash}',
    '{key_prefix}',
    'enterprise',
    true,
    '{"email": "admin@example.com", "purpose": "Initial setup"}'::jsonb
);
"""
```

Or use this SQL directly in Supabase SQL Editor:

```sql
-- Generate a bootstrap API key
-- API key: sk_live_admin_bootstrap_key_12345 (example - use your own!)

INSERT INTO api_keys (
    user_id,
    key_name,
    key_hash,
    key_prefix,
    tier,
    is_active,
    metadata
) VALUES (
    'admin_user',
    'Bootstrap Admin Key',
    encode(sha256('sk_live_admin_bootstrap_key_12345'::bytea), 'hex'),
    'sk_live_admin_bo',
    'enterprise',
    true,
    '{"email": "admin@example.com", "purpose": "Initial setup"}'::jsonb
);
```

Then use `sk_live_admin_bootstrap_key_12345` as your first API key to create more keys via the API.

## Usage Examples

### Authenticated Request

```bash
curl -H "X-API-Key: sk_live_abc123..." \
  "http://localhost:8000/v1/stocks?limit=10"
```

### Create New API Key

```bash
curl -X POST "http://localhost:8000/v1/keys" \
  -H "X-API-Key: sk_live_admin_bootstrap_key_12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Production Key",
    "tier": "pro",
    "expires_in_days": 365
  }'
```

### List Your API Keys

```bash
curl -H "X-API-Key: sk_live_abc123..." \
  "http://localhost:8000/v1/keys"
```

### Get Usage Statistics

```bash
curl -H "X-API-Key: sk_live_abc123..." \
  "http://localhost:8000/v1/keys/{key_id}/usage?days=7"
```

### Revoke API Key

```bash
curl -X DELETE \
  -H "X-API-Key: sk_live_abc123..." \
  "http://localhost:8000/v1/keys/{key_id}"
```

## Error Responses

### 401 Unauthorized - Missing API Key

```json
{
  "error": {
    "type": "authentication_error",
    "message": "No API key provided. Include your API key in the X-API-Key header.",
    "code": "api_key_missing"
  }
}
```

### 401 Unauthorized - Invalid API Key

```json
{
  "error": {
    "type": "authentication_error",
    "message": "Invalid API key. Your API key may be revoked or incorrect.",
    "code": "invalid_api_key"
  }
}
```

### 429 Too Many Requests - Rate Limit Exceeded

```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Rate limit exceeded for minute window. Limit: 60 requests per minute.",
    "code": "rate_limit_exceeded"
  }
}
```

**Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699876543
Retry-After: 45
```

## Security Features

### 1. Secure Key Storage
- API keys are hashed with SHA-256 before storage
- Only the hash is stored in the database
- Full key is shown only once during creation

### 2. Key Validation
- Format validation (must start with sk_live_ or sk_test_)
- Hash-based lookup (constant-time comparison)
- Active status check
- Expiration check

### 3. Rate Limiting
- Multi-window protection (minute/hour/day)
- Per-key and per-IP tracking
- Thread-safe token bucket implementation
- Graceful degradation

### 4. Audit Trail
- Request logging (api_usage table)
- Daily statistics (materialized view)
- Usage analytics per key
- Error tracking

## Upgrade Path

### Current Implementation
- In-memory rate limiting (single server)
- PostgreSQL for API keys and usage
- Basic tier system

### Future Enhancements

#### 1. Redis Rate Limiting
For distributed systems:
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

# Store rate limit tokens in Redis
redis_client.setex(
    f"rate_limit:{identifier}:{window}",
    window_seconds,
    tokens_remaining
)
```

#### 2. Webhook Support
Notify on key events:
- Key created/revoked
- Rate limit exceeded
- Unusual usage patterns

#### 3. Usage-Based Billing
Track usage for billing:
```python
# Calculate monthly usage
monthly_usage = supabase.table('api_usage') \
    .select('api_key_id', count='exact') \
    .gte('created_at', start_of_month) \
    .execute()
```

#### 4. IP Allowlisting
Restrict keys to specific IPs:
```python
allowed_ips = key_data.get('allowed_ips', [])
if allowed_ips and request.client.host not in allowed_ips:
    raise HTTPException(403, "IP not allowed")
```

## Files Created

| File | Purpose |
|------|---------|
| `api/auth.py` | Authentication middleware |
| `api/rate_limit.py` | Rate limiting logic |
| `api/routers/api_keys.py` | API key management endpoints |
| `migrations/create_api_keys.sql` | Database schema |
| `scripts/run_api_keys_migration.py` | Migration script |
| `docs/AUTH_RATE_LIMIT_IMPLEMENTATION.md` | This file |

## Testing

### Test Rate Limiting

```bash
# Make 70 requests in 1 minute (should hit limit at 61st request)
for i in {1..70}; do
  echo "Request $i"
  curl -H "X-API-Key: sk_live_test..." \
    "http://localhost:8000/v1/stocks?limit=1"
  sleep 0.8
done
```

### Test Authentication

```bash
# Valid key
curl -H "X-API-Key: sk_live_valid..." \
  "http://localhost:8000/v1/stocks"
# Returns: 200 OK

# Invalid key
curl -H "X-API-Key: sk_live_invalid..." \
  "http://localhost:8000/v1/stocks"
# Returns: 401 Unauthorized

# No key
curl "http://localhost:8000/v1/stocks"
# Returns: 401 Unauthorized
```

### Test Key Management

```bash
# Create key
KEY_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/keys" \
  -H "X-API-Key: sk_live_admin..." \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Key", "tier": "free"}')

# Extract new key
NEW_KEY=$(echo $KEY_RESPONSE | jq -r '.api_key')

# Use new key
curl -H "X-API-Key: $NEW_KEY" \
  "http://localhost:8000/v1/stocks?limit=5"

# List keys
curl -H "X-API-Key: sk_live_admin..." \
  "http://localhost:8000/v1/keys"

# Revoke key
KEY_ID=$(echo $KEY_RESPONSE | jq -r '.id')
curl -X DELETE \
  -H "X-API-Key: sk_live_admin..." \
  "http://localhost:8000/v1/keys/$KEY_ID"
```

## Monitoring & Analytics

### Daily Usage Report

```sql
SELECT
    ak.user_id,
    ak.key_name,
    ak.tier,
    SUM(ud.total_requests) as total_requests,
    AVG(ud.avg_response_time_ms) as avg_response_time,
    SUM(ud.error_requests) as errors
FROM api_keys ak
JOIN mv_api_usage_daily ud ON ak.id = ud.api_key_id
WHERE ud.request_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY ak.user_id, ak.key_name, ak.tier
ORDER BY total_requests DESC;
```

### Top Endpoints

```sql
SELECT
    endpoint,
    COUNT(*) as request_count,
    AVG(response_time_ms) as avg_response_time,
    COUNT(*) FILTER (WHERE status_code >= 400) as error_count
FROM api_usage
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY endpoint
ORDER BY request_count DESC
LIMIT 20;
```

### Error Analysis

```sql
SELECT
    endpoint,
    status_code,
    error_message,
    COUNT(*) as occurrence_count
FROM api_usage
WHERE status_code >= 400
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY endpoint, status_code, error_message
ORDER BY occurrence_count DESC
LIMIT 50;
```

## Production Considerations

### 1. Database Indexes
All necessary indexes are created by the migration.

### 2. Materialized View Refresh
Schedule daily refresh:
```sql
-- Run daily at 2 AM
SELECT refresh_api_usage_stats();
```

### 3. Cleanup Old Data
Schedule hourly cleanup:
```sql
-- Run hourly
SELECT cleanup_expired_rate_limits();
```

### 4. Connection Pooling
Use connection pooling for high traffic:
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)
```

### 5. Monitoring
Monitor these metrics:
- Rate limit hit rate
- Authentication failures
- Average response times
- Error rates by endpoint
- Active keys count

## Conclusion

The authentication and rate limiting system is now fully implemented and ready for use. The system provides:

✅ Secure API key authentication
✅ Multi-tier rate limiting
✅ Usage tracking and analytics
✅ Key management API
✅ Comprehensive error handling
✅ Audit trail

**Next Steps**:
1. Run database migration
2. Create bootstrap API key
3. Test authentication and rate limiting
4. Update documentation site with auth examples
5. Deploy to production

---

*Implementation Date: November 13, 2025*
*Status: Complete - Ready for Database Setup*
