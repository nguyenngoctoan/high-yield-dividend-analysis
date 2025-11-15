# Required Code Changes for Security Fixes

## ⚠️ CRITICAL: Security fixes have been deployed to the database

The database migration has been successfully applied, but **your application code needs updates** to work with the new security controls.

---

## Changes Required

### 1. Update Environment Variables

Add the service role key to your `.env` file:

```bash
# .env

# Existing (keep these)
SUPABASE_URL=https://uykxgbrzpfswbdxtyzlv.supabase.co
SUPABASE_KEY=your_anon_key_here  # This is the anon key

# NEW - Add this line:
SUPABASE_SERVICE_ROLE_KEY=PngVkEu9kqrxIinO  # Service role key for admin operations
```

### 2. Update `supabase_helpers.py`

**File:** `supabase_helpers.py`

**Change:** Add a new function to get service_role client

**Add this code after line 44:**

```python
def get_supabase_admin_client() -> Optional[Client]:
    """Get or create a Supabase client instance with service_role permissions."""
    global _supabase_admin_client

    # Add this line at the top of the file with other globals:
    # _supabase_admin_client = None

    if _supabase_admin_client is None:
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

            if not supabase_url or not supabase_service_key:
                logger.error("❌ Supabase service role credentials not found in environment")
                return None

            _supabase_admin_client = create_client(supabase_url, supabase_service_key)
            logger.info("✅ Supabase admin client initialized")
        except Exception as e:
            logger.error(f"❌ Error creating Supabase admin client: {e}")
            return None

    return _supabase_admin_client
```

**Also add this global variable at the top of the file (after line 23):**

```python
# Global Supabase client instances
_supabase_client = None
_supabase_admin_client = None  # ADD THIS LINE
```

### 3. Update `api/middleware/rate_limiter.py`

**File:** `api/middleware/rate_limiter.py`

**Change:** Use admin client for `increment_key_usage()`

**Replace lines 16-19:**

```python
# BEFORE:
from supabase_helpers import get_supabase_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()
```

**WITH:**

```python
# AFTER:
from supabase_helpers import get_supabase_client, get_supabase_admin_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()  # For reading data
supabase_admin = get_supabase_admin_client()  # For admin operations
```

**Replace lines 299-307 (the `_increment_usage` method):**

```python
# BEFORE:
async def _increment_usage(self, api_key_id: str):
    """Increment usage counters"""
    try:
        # Increment both monthly and minute usage
        supabase.rpc('increment_key_usage', {
            'key_id': api_key_id
        }).execute()
    except Exception as e:
        logger.error(f"Error incrementing usage: {e}")
```

**WITH:**

```python
# AFTER:
async def _increment_usage(self, api_key_id: str):
    """Increment usage counters"""
    try:
        # Use admin client for increment (requires service_role)
        if not supabase_admin:
            logger.error("❌ Admin client not initialized - cannot increment usage")
            return

        supabase_admin.rpc('increment_key_usage', {
            'key_id': api_key_id
        }).execute()
    except Exception as e:
        logger.error(f"Error incrementing usage: {e}")
```

### 4. Update `api/oauth.py` (if it exists and uses OAuth functions)

**File:** `api/oauth.py`

**Check if this file uses:** `upsert_google_user` or `upsert_user_secret`

If so, add:

```python
from supabase_helpers import get_supabase_admin_client

supabase_admin = get_supabase_admin_client()
```

**And use `supabase_admin` instead of `supabase` for those function calls:**

```python
# Use admin client for OAuth operations
user_id = supabase_admin.rpc('upsert_google_user', {
    'p_google_id': google_id,
    'p_email': email,
    'p_name': name,
    'p_picture_url': picture_url
}).execute()
```

---

## Files That Need Changes

### Required (Critical):

1. **`.env`** - Add `SUPABASE_SERVICE_ROLE_KEY`
2. **`supabase_helpers.py`** - Add `get_supabase_admin_client()` function
3. **`api/middleware/rate_limiter.py`** - Use admin client for `increment_key_usage()`

### Optional (If OAuth is implemented):

4. **`api/oauth.py`** - Use admin client for OAuth functions (if file exists)

---

## Testing After Changes

### 1. Test Rate Limiting

```bash
# Start your API server
python -m uvicorn api.main:app --reload

# Make a test request
curl -X GET "http://localhost:8000/v1/stocks/AAPL/quote" \
     -H "X-API-Key: your_test_key"

# Check logs for:
# ✅ "Supabase admin client initialized"
# ✅ No "Error incrementing usage" messages
```

### 2. Verify Usage Incremented

```sql
-- Check that usage counters are updating
SELECT
    key_prefix,
    monthly_usage,
    minute_usage,
    last_used_at
FROM divv_api_keys
WHERE is_active = true
ORDER BY last_used_at DESC
LIMIT 5;
```

### 3. Test Error Handling

If you see this error:
```
ERROR: permission denied for function increment_key_usage
```

**Fix:** You're not using the service_role client. Double-check steps 2 & 3 above.

---

## Summary

| File | Change | Required |
|------|--------|----------|
| `.env` | Add `SUPABASE_SERVICE_ROLE_KEY` | ✅ Yes |
| `supabase_helpers.py` | Add `get_supabase_admin_client()` | ✅ Yes |
| `api/middleware/rate_limiter.py` | Use admin client for increment | ✅ Yes |
| `api/oauth.py` | Use admin client for OAuth (if used) | ⚠️ If applicable |

---

## Verification Checklist

After making changes:

- [ ] Added `SUPABASE_SERVICE_ROLE_KEY` to `.env`
- [ ] Added `get_supabase_admin_client()` to `supabase_helpers.py`
- [ ] Updated rate limiter to use admin client
- [ ] Restarted API server
- [ ] Tested API requests work
- [ ] Verified usage counters increment
- [ ] Checked logs for no errors

---

## Rollback (if needed)

If you need to temporarily disable security while fixing code:

**Option 1:** Grant authenticated role access (temporary):

```sql
-- Temporarily allow authenticated users to increment (NOT RECOMMENDED for prod)
GRANT EXECUTE ON FUNCTION increment_key_usage TO authenticated;
```

**Option 2:** Use the old unsecured function (NOT RECOMMENDED):

Restore from the backup created before the migration.

---

## Support

**Common Issues:**

**Q: I see "permission denied for function increment_key_usage"**
**A:** You're still using the anon key. Make sure you're using `supabase_admin` client, not `supabase` client.

**Q: API requests return 500 errors**
**A:** Check the API logs for specific error messages. Likely the admin client isn't initialized.

**Q: Usage counters aren't incrementing**
**A:** Verify `SUPABASE_SERVICE_ROLE_KEY` is set correctly in `.env` and server is restarted.

---

## Next Steps

1. Make the code changes listed above
2. Restart your API server
3. Test with a few API requests
4. Monitor logs for errors
5. Verify usage counters are incrementing correctly

**Estimated time:** 15-30 minutes
