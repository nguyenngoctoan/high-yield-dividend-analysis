# API Key Management with User Authentication

This document describes how the `divv_api_keys` table links API keys to authenticated users.

## Overview

The `divv_api_keys` table now supports user authentication with the following key features:

- **User Linking**: Each API key is associated with a `user_id`
- **Subscription Tiers**: Free, Pro, and Enterprise tiers with different rate limits
- **Automatic Tracking**: Last used timestamp and request count
- **Expiration Support**: Optional key expiration dates
- **Metadata Storage**: Additional user information (email, company, etc.)

## Database Schema

### New Columns in `divv_api_keys`

```sql
user_id VARCHAR(255)              -- User identifier
tier VARCHAR(50) DEFAULT 'free'   -- Subscription tier (free/pro/enterprise)
updated_at TIMESTAMP              -- Last update timestamp
```

### Subscription Tiers

| Tier       | Requests/Min | Requests/Hour | Requests/Day |
|------------|-------------|---------------|--------------|
| Free       | 60          | 1,000         | 10,000       |
| Pro        | 600         | 20,000        | 500,000      |
| Enterprise | 6,000       | 200,000       | 10,000,000   |

## Using the Management Script

### Create a New API Key

```bash
# Basic creation
python scripts/manage_api_keys.py create \
  --user-id "user_123" \
  --name "Production API Key"

# With subscription tier and expiration
python scripts/manage_api_keys.py create \
  --user-id "user_123" \
  --name "Pro Account Key" \
  --tier pro \
  --expires-in-days 365 \
  --email "user@example.com" \
  --company "Example Corp"
```

### List API Keys

```bash
# List all active keys
python scripts/manage_api_keys.py list

# List keys for specific user
python scripts/manage_api_keys.py list --user-id "user_123"

# Include revoked keys
python scripts/manage_api_keys.py list --include-inactive
```

### Revoke an API Key

```bash
python scripts/manage_api_keys.py revoke <key-id>
```

### Migrate from Old api_keys Table

```bash
python scripts/manage_api_keys.py migrate
```

## API Endpoints

### Create API Key
```http
POST /api/keys
X-API-Key: sk_live_existing_key

{
  "name": "My API Key",
  "tier": "free",
  "expires_in_days": 365,
  "metadata": {
    "email": "user@example.com",
    "company": "Example Corp"
  }
}
```

### List Your API Keys
```http
GET /api/keys?include_inactive=false
X-API-Key: sk_live_your_key
```

### Revoke an API Key
```http
DELETE /api/keys/{key_id}
X-API-Key: sk_live_your_key
```

### Get Key Usage Statistics
```http
GET /api/keys/{key_id}/usage?days=30
X-API-Key: sk_live_your_key
```

## Using API Keys in Requests

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: sk_live_abc123..." \
     https://api.example.com/v1/stocks/AAPL
```

```python
import requests

headers = {
    'X-API-Key': 'sk_live_abc123...'
}

response = requests.get(
    'https://api.example.com/v1/stocks/AAPL',
    headers=headers
)
```

## Authentication Flow

1. **Request arrives** with `X-API-Key` header
2. **Hash the key** using SHA-256
3. **Look up** the key_hash in `divv_api_keys`
4. **Validate**:
   - Key exists
   - `is_active` is true
   - Not expired (if `expires_at` is set)
5. **Update** `last_used_at` and increment `request_count`
6. **Return** user context including:
   - `user_id`
   - `api_key_id`
   - `tier`
   - `rate_limit` settings

## Database View

A convenient view `v_user_api_keys` provides computed status:

```sql
SELECT * FROM v_user_api_keys WHERE user_id = 'user_123';
```

Includes computed fields:
- `is_valid`: Whether the key is not expired
- `status`: 'active', 'disabled', or 'expired'

## Security Best Practices

1. **Never log full API keys** - only log the key_prefix
2. **Store hashes only** - never store plaintext keys
3. **Use HTTPS** - always transmit keys over secure connections
4. **Rotate keys** - encourage users to rotate keys periodically
5. **Rate limit** - enforce tier-based rate limits
6. **Monitor usage** - track suspicious patterns

## Integration with Existing Code

The following files have been updated to use `divv_api_keys`:

- `api/auth.py` - Authentication validation
- `api/routers/api_keys.py` - API key management endpoints

All references to the old `api_keys` table have been replaced with `divv_api_keys`.

## Migration Path

If you have existing data in the `api_keys` table:

1. Run the migration SQL:
   ```bash
   psql -d dividend_db -f migrations/add_user_to_divv_api_keys.sql
   ```

2. Migrate the data:
   ```bash
   python scripts/manage_api_keys.py migrate
   ```

3. Verify the migration:
   ```bash
   python scripts/manage_api_keys.py list
   ```

## Example Usage

### Complete Flow

```python
# 1. Create a key for a new user
from scripts.manage_api_keys import create_api_key

key_info = create_api_key(
    user_id="user_456",
    name="Development Key",
    tier="pro",
    expires_in_days=30,
    metadata={"email": "dev@example.com"}
)

print(f"Your API key: {key_info['api_key']}")
# Output: Your API key: sk_live_Xyz789...

# 2. User makes API requests
# Their requests include: X-API-Key: sk_live_Xyz789...

# 3. System validates and tracks usage automatically
# - Checks validity
# - Enforces rate limits based on tier (pro = 600 req/min)
# - Updates last_used_at
# - Increments request_count

# 4. User can check their usage
# GET /api/keys/{key_id}/usage
# Returns statistics for the last 30 days
```

## Troubleshooting

### Key not found error
- Verify the key format starts with `sk_live_` or `sk_test_`
- Check if the key has been revoked
- Ensure the key hash matches in the database

### Key expired error
- Check the `expires_at` field
- Create a new key if needed

### Rate limit exceeded
- Check the user's tier and rate limits
- Consider upgrading to a higher tier
- Implement retry logic with exponential backoff

## Future Enhancements

Potential improvements to consider:

1. **JWT-based authentication** - In addition to API keys
2. **Scoped permissions** - Fine-grained access control
3. **Key rotation** - Automatic key rotation policies
4. **Usage alerts** - Notify users when approaching limits
5. **Webhook support** - Real-time event notifications
6. **API analytics dashboard** - Visual usage statistics
