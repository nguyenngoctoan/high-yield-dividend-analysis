## Google OAuth Authentication Setup

This guide walks you through setting up Google OAuth authentication for the Dividend API, allowing users to log in with their Google accounts and manage API keys.

## Overview

The authentication system uses:
- **Google OAuth 2.0** for user authentication
- **JWT tokens** for session management
- **PostgreSQL users table** to store user profiles
- **divv_api_keys table** linked to authenticated users

## Architecture

```
User → Google Login → OAuth Callback → Create/Update User → Create Session → Dashboard
                                              ↓
                                         users table
                                              ↓
                                      divv_api_keys table
```

## Setup Steps

### 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Configure the OAuth consent screen if prompted:
   - **User Type**: External
   - **App name**: Dividend API
   - **User support email**: Your email
   - **Developer contact**: Your email
6. Select **Application type**: Web application
7. Configure **Authorized redirect URIs**:
   - Development: `http://localhost:8000/auth/callback`
   - Production: `https://yourdomain.com/auth/callback`
8. Save and copy your **Client ID** and **Client Secret**

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `authlib>=1.3.0` - OAuth client library
- `python-jose[cryptography]>=3.3.0` - JWT token handling
- `itsdangerous>=2.1.2` - Session security

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your Google OAuth credentials:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# Session and Security (generate secure random strings)
SECRET_KEY=your-secure-secret-key-change-this
SESSION_SECRET=your-secure-session-secret-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application URLs
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# CORS Origins
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Generate secure keys:**

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate SESSION_SECRET
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Setup Database

Run the migration to create the users table:

```bash
psql -d dividend_db -f migrations/create_users_table.sql
```

This creates:
- `users` table for storing Google user profiles
- Foreign key constraint linking `divv_api_keys.user_id` to `users.id`
- Views and functions for user management
- `upsert_google_user` function for OAuth login

### 5. Update Existing API Keys (Optional)

If you have existing API keys without user IDs, you'll need to:

1. **Option A**: Delete old keys and recreate through OAuth
   ```sql
   DELETE FROM divv_api_keys WHERE user_id IS NULL;
   ```

2. **Option B**: Manually assign to a user
   ```sql
   -- First create a user via OAuth login
   -- Then update existing keys
   UPDATE divv_api_keys
   SET user_id = 'user-uuid-here'
   WHERE user_id IS NULL;
   ```

### 6. Start the Application

```bash
# From the project root
cd api
uvicorn main:app --reload --port 8000
```

The application will be available at:
- API: http://localhost:8000
- Login page: http://localhost:8000/login
- Dashboard: http://localhost:8000/dashboard

## Authentication Flow

### 1. User Login

```
GET http://localhost:8000/login
```

Displays login page with "Sign in with Google" button.

### 2. OAuth Authorization

User clicks "Sign in with Google" → Redirected to:

```
GET http://localhost:8000/auth/login
```

Server redirects to Google OAuth consent screen.

### 3. OAuth Callback

After user authorizes, Google redirects back to:

```
GET http://localhost:8000/auth/callback?code=...
```

Server:
1. Exchanges authorization code for access token
2. Fetches user info from Google
3. Creates or updates user in `users` table
4. Creates JWT session token
5. Sets secure HTTP-only cookies
6. Redirects to dashboard

### 4. Dashboard Access

```
GET http://localhost:8000/dashboard
```

User can now:
- View their profile
- Create API keys
- List existing API keys
- Revoke API keys
- View usage statistics

## API Endpoints

### Authentication Endpoints

#### Login
```http
GET /auth/login
```
Initiates Google OAuth flow.

#### Callback
```http
GET /auth/callback?code=...
```
Handles OAuth callback from Google.

#### Logout
```http
POST /auth/logout
```
Clears session cookies and logs out the user.

#### Get Current User
```http
GET /auth/me
Cookie: access_token=<jwt>
```

Response:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "picture_url": "https://...",
  "tier": "free",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login_at": "2025-01-14T00:00:00Z"
}
```

#### Check Auth Status
```http
GET /auth/status
Cookie: access_token=<jwt>
```

Response:
```json
{
  "authenticated": true,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "picture_url": "https://...",
    "tier": "free"
  }
}
```

### API Key Management (Requires Auth)

#### Create API Key
```http
POST /v1/keys
Cookie: access_token=<jwt>
Content-Type: application/json

{
  "name": "Production API Key",
  "expires_in_days": 365
}
```

Response:
```json
{
  "id": "uuid",
  "api_key": "sk_live_abc123...",
  "key_prefix": "sk_live_abc123",
  "name": "Production API Key",
  "tier": "free",
  "expires_at": "2026-01-14T00:00:00Z",
  "created_at": "2025-01-14T00:00:00Z",
  "message": "API key created successfully..."
}
```

#### List API Keys
```http
GET /v1/keys?include_inactive=false
Cookie: access_token=<jwt>
```

#### Revoke API Key
```http
DELETE /v1/keys/{key_id}
Cookie: access_token=<jwt>
```

#### Get API Key Usage
```http
GET /v1/keys/{key_id}/usage?days=30
Cookie: access_token=<jwt>
```

## Using API Keys

Once created, API keys can be used to access the API:

```bash
curl -H "X-API-Key: sk_live_abc123..." \
     http://localhost:8000/v1/stocks/AAPL
```

```python
import requests

headers = {
    'X-API-Key': 'sk_live_abc123...'
}

response = requests.get(
    'http://localhost:8000/v1/stocks/AAPL',
    headers=headers
)
```

## Security Best Practices

### Production Deployment

1. **Use HTTPS only**
   ```bash
   COOKIE_SECURE=true
   ```

2. **Set proper CORS origins**
   ```bash
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

3. **Use strong secrets**
   - Generate 32+ character random strings
   - Never commit secrets to version control

4. **Configure session security**
   ```bash
   COOKIE_SAMESITE=strict
   COOKIE_DOMAIN=yourdomain.com
   ```

5. **Update Google OAuth redirect URI**
   ```bash
   GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback
   ```

### Cookie Security

The application sets two HTTP-only cookies:
- `access_token`: JWT for API authentication
- `session_token`: Additional session identifier

Both cookies are:
- HTTP-only (not accessible via JavaScript)
- Secure (HTTPS only in production)
- SameSite protected
- Auto-expire after 30 minutes (configurable)

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "tier": "free",
  "type": "access",
  "exp": 1736822400,
  "iat": 1736820600
}
```

## Database Schema

### users table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    picture_url TEXT,
    tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);
```

### divv_api_keys updates

```sql
ALTER TABLE divv_api_keys
ADD COLUMN user_id VARCHAR(255);

ALTER TABLE divv_api_keys
ADD CONSTRAINT divv_api_keys_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

## Troubleshooting

### "Redirect URI mismatch" error

Make sure the redirect URI in Google Cloud Console exactly matches your `.env` file:
- Development: `http://localhost:8000/auth/callback`
- Production: `https://yourdomain.com/auth/callback`

### "Invalid token" errors

- Check that `SECRET_KEY` matches across app instances
- Verify token hasn't expired (check `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Ensure cookies are being sent with requests

### "User not found" errors

- Verify database migration ran successfully
- Check `users` table exists and has data
- Ensure foreign key constraint is properly set

### OAuth consent screen not working

1. Publish OAuth app (Google Cloud Console)
2. Add test users if app is in testing mode
3. Verify OAuth scopes: `openid email profile`

## Testing

### Test OAuth Flow Locally

1. Start the server:
   ```bash
   uvicorn api.main:app --reload
   ```

2. Visit: http://localhost:8000/login

3. Click "Sign in with Google"

4. Authorize the application

5. You should be redirected to: http://localhost:8000/dashboard

### Test API Key Creation

1. Log in via OAuth
2. Go to dashboard
3. Click "Create New Key"
4. Copy the generated API key
5. Test with curl:
   ```bash
   curl -H "X-API-Key: sk_live_..." \
        http://localhost:8000/v1/stocks/AAPL
   ```

## Migration from Old System

If you're migrating from the old `api_keys` table:

```bash
# Run migration
python scripts/manage_api_keys.py migrate

# Verify migration
python scripts/manage_api_keys.py list
```

All users will need to:
1. Log in with Google OAuth
2. Create new API keys through the dashboard
3. Update their applications with new keys

## Support

For issues or questions:
- Check the [API documentation](./API_KEY_MANAGEMENT.md)
- Review the [troubleshooting](#troubleshooting) section
- Check application logs for detailed error messages
