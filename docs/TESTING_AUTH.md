# Testing Authentication - Login & Logout

This guide shows you how to test the complete login and logout functionality.

## Prerequisites

1. **Run the setup script:**
   ```bash
   ./scripts/setup_oauth.sh
   ```

2. **Get Google OAuth credentials:**
   - Go to https://console.cloud.google.com/
   - Create OAuth 2.0 Client ID
   - Add redirect URI: `http://localhost:8000/auth/callback`

3. **Update .env file:**
   ```bash
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```

4. **Run database migration:**
   ```bash
   psql -d dividend_db -f migrations/create_users_table.sql
   ```

5. **Start the server:**
   ```bash
   uvicorn api.main:app --reload
   ```

## Testing Login Flow

### Step 1: Visit Login Page

Open your browser to:
```
http://localhost:8000/login
```

You should see:
- Beautiful login page
- "Sign in with Google" button
- Feature list (API keys, dividend data, etc.)

### Step 2: Click "Sign in with Google"

This will:
1. Redirect to `/auth/login`
2. Which redirects to Google's OAuth consent screen
3. You'll see a Google login page

### Step 3: Authorize the Application

1. Select your Google account
2. Review permissions (email, profile)
3. Click "Allow" or "Continue"

### Step 4: Redirected to Dashboard

After authorization:
1. Google redirects to `/auth/callback`
2. Server creates/updates user in database
3. Sets secure cookies
4. Redirects to `/dashboard`

You should see:
- Your name and profile picture in header
- "API Keys" section
- "Create New Key" button
- "Logout" button

## Testing Logout Flow

### Method 1: Click Logout Button

On the dashboard, click the "Logout" button in the header.

This will:
1. Call `/auth/logout`
2. Clear `session_token` and `access_token` cookies
3. Redirect to `/login`

### Method 2: Direct URL

Navigate to:
```
http://localhost:8000/auth/logout
```

Same result - cookies cleared and redirected to login.

### Method 3: API Call

```bash
curl -X POST http://localhost:8000/auth/logout \
     -H "Cookie: access_token=your-token" \
     -v
```

You'll see the cookies being deleted in the response headers.

## Verification Tests

### Test 1: Check Authentication Status

**Before Login:**
```bash
curl http://localhost:8000/auth/status
```

Response:
```json
{
  "authenticated": false,
  "user": null
}
```

**After Login:**
```bash
curl -b cookies.txt http://localhost:8000/auth/status
```

Response:
```json
{
  "authenticated": true,
  "user": {
    "id": "uuid-here",
    "email": "you@gmail.com",
    "name": "Your Name",
    "picture_url": "https://...",
    "tier": "free"
  }
}
```

### Test 2: Get Current User Profile

```bash
curl http://localhost:8000/auth/me \
     -H "Cookie: access_token=your-token"
```

Response:
```json
{
  "id": "uuid",
  "email": "you@gmail.com",
  "name": "Your Name",
  "picture_url": "https://lh3.googleusercontent.com/...",
  "tier": "free",
  "is_active": true,
  "created_at": "2025-01-14T12:00:00Z",
  "last_login_at": "2025-01-14T12:30:00Z"
}
```

### Test 3: Access Protected Routes

**Without Authentication:**
```bash
curl http://localhost:8000/v1/keys
```

Response:
```json
{
  "detail": "Not authenticated. Please log in."
}
```

**With Authentication (using cookies from browser):**
```bash
# Export cookies from browser dev tools, then:
curl http://localhost:8000/v1/keys \
     -H "Cookie: access_token=eyJ0eXAiOiJKV1Q..."
```

Response:
```json
[
  {
    "id": "key-uuid",
    "user_id": "user-uuid",
    "name": "My API Key",
    "key_prefix": "sk_live_abc123",
    "tier": "free",
    "is_active": true,
    "request_count": 0,
    "last_used_at": null,
    "expires_at": null,
    "created_at": "2025-01-14T12:00:00Z"
  }
]
```

### Test 4: Database Verification

Check that user was created:

```sql
-- Connect to database
psql -d dividend_db

-- Check users table
SELECT id, email, name, tier, created_at, last_login_at
FROM users
ORDER BY created_at DESC
LIMIT 5;

-- Check API keys for a user
SELECT dak.*, u.email
FROM divv_api_keys dak
JOIN users u ON dak.user_id = u.id
WHERE u.email = 'your@gmail.com';
```

## Complete User Journey Test

### 1. First Time User

```bash
# 1. Visit login page
open http://localhost:8000/login

# 2. Click "Sign in with Google"
# 3. Authorize application
# 4. Should arrive at dashboard

# 5. Create an API key
# (Click "Create New Key" button)
# Name: "Test Key"
# Expiration: "Never"

# 6. Copy the displayed API key
# Example: sk_live_xyz789abc123...

# 7. Test the API key
curl -H "X-API-Key: sk_live_xyz789abc123..." \
     http://localhost:8000/v1/stocks/AAPL

# 8. Should return stock data

# 9. Logout
# (Click "Logout" button)

# 10. Should redirect to login page
```

### 2. Returning User

```bash
# 1. Visit any protected page
open http://localhost:8000/dashboard

# 2. Should redirect to login (if not logged in)
# 3. Click "Sign in with Google"
# 4. Should auto-login (if recently authorized)
# 5. Redirected back to dashboard
# 6. See existing API keys
```

### 3. Session Expiration

```bash
# 1. Login and go to dashboard
# 2. Wait 30 minutes (or change ACCESS_TOKEN_EXPIRE_MINUTES to 1)
# 3. Try to create an API key
# 4. Should get 401 Unauthorized
# 5. Frontend should detect and redirect to login
```

## Testing with Different Browsers

### Chrome/Edge

1. Open DevTools (F12)
2. Go to Application tab
3. Check Cookies → http://localhost:8000
4. Should see:
   - `access_token` (JWT)
   - `session_token` (random string)
5. Both should be:
   - HttpOnly: ✓
   - Secure: ✗ (dev) or ✓ (prod)
   - SameSite: Lax

### Firefox

1. Open DevTools (F12)
2. Go to Storage tab
3. Click Cookies → http://localhost:8000
4. Verify same cookies as above

### Safari

1. Develop → Show Web Inspector
2. Storage tab
3. Cookies
4. Verify cookies

## Testing Logout Thoroughly

### Scenario 1: Normal Logout

```bash
# 1. Login and verify cookies exist
# 2. Click logout button
# 3. Check Application → Cookies
# 4. Cookies should be gone
# 5. Try to access /v1/keys
# 6. Should get 401 Unauthorized
```

### Scenario 2: Logout from Multiple Tabs

```bash
# 1. Login
# 2. Open dashboard in 3 different tabs
# 3. Logout from one tab
# 4. Refresh other tabs
# 5. All should redirect to login (cookies cleared globally)
```

### Scenario 3: Manual Cookie Deletion

```bash
# 1. Login
# 2. Manually delete access_token cookie in DevTools
# 3. Try to access protected route
# 4. Should get 401
# 5. Frontend redirects to login
```

## Common Issues & Solutions

### Issue: "Redirect URI mismatch"

**Solution:**
- In Google Cloud Console, verify redirect URI is exactly:
  `http://localhost:8000/auth/callback`
- No trailing slash
- Include http://

### Issue: Cookies not being set

**Solution:**
- Check browser console for errors
- Verify `ALLOWED_ORIGINS` includes your domain
- Check `credentials: 'include'` in fetch calls
- In production, ensure HTTPS

### Issue: Login works but logout doesn't clear cookies

**Solution:**
- Check `COOKIE_DOMAIN` matches your domain
- In development, should be `localhost`
- Clear browser cache and try again

### Issue: "User not found" after login

**Solution:**
```bash
# Check database
psql -d dividend_db -c "SELECT * FROM users ORDER BY created_at DESC LIMIT 1;"

# If empty, check server logs
tail -f logs/app.log

# Verify upsert_google_user function exists
psql -d dividend_db -c "\df upsert_google_user"
```

## Automated Testing

Create a test script:

```python
# test_auth.py
import requests
from http.cookiejar import CookieJar

# Test login flow
session = requests.Session()

# 1. Test unauthenticated access
response = session.get('http://localhost:8000/auth/status')
assert response.json()['authenticated'] == False

# 2. Login via OAuth (manual - open browser)
print("Please login at: http://localhost:8000/login")
input("Press Enter after logging in...")

# 3. Test authenticated access
response = session.get('http://localhost:8000/auth/status')
assert response.json()['authenticated'] == True
print(f"Logged in as: {response.json()['user']['email']}")

# 4. Create API key
response = session.post('http://localhost:8000/v1/keys', json={
    'name': 'Test Key',
    'expires_in_days': 30
})
assert response.status_code == 201
api_key = response.json()['api_key']
print(f"Created API key: {api_key[:20]}...")

# 5. Test API key
response = requests.get(
    'http://localhost:8000/v1/stocks/AAPL',
    headers={'X-API-Key': api_key}
)
assert response.status_code == 200
print("API key works!")

# 6. Logout
response = session.get('http://localhost:8000/auth/logout', allow_redirects=False)
assert response.status_code == 302
print("Logged out successfully")

# 7. Verify logout
response = session.get('http://localhost:8000/auth/status')
assert response.json()['authenticated'] == False
print("Logout verified")

print("\n✅ All tests passed!")
```

Run it:
```bash
python test_auth.py
```

## Production Testing Checklist

Before deploying to production:

- [ ] HTTPS enabled
- [ ] `COOKIE_SECURE=true` in .env
- [ ] `ENVIRONMENT=production` in .env
- [ ] Strong `SECRET_KEY` and `SESSION_SECRET`
- [ ] Google OAuth redirect URI updated to production domain
- [ ] `ALLOWED_ORIGINS` set to production domains only
- [ ] Database migrations run on production DB
- [ ] Test login/logout on production URL
- [ ] Verify cookies are Secure and HttpOnly
- [ ] Test API keys work with production API
- [ ] Check SSL certificate is valid
- [ ] Test session expiration
- [ ] Monitor logs for errors

## Success Criteria

Login/Logout is working correctly if:

✅ User can login with Google account
✅ User profile is saved to database
✅ JWT cookies are set securely
✅ Dashboard loads with user info
✅ User can create API keys
✅ API keys work for API requests
✅ Logout clears all cookies
✅ After logout, protected routes return 401
✅ User can login again successfully
✅ Session expires after configured time

## Next Steps

After verifying login/logout:

1. Test API key creation and usage
2. Test rate limiting per tier
3. Test key revocation
4. Set up monitoring and logging
5. Configure production environment
6. Deploy to production
7. Update documentation with production URLs
