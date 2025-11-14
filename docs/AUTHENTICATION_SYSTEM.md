# Authentication System Overview

The Dividend API now features a complete Google OAuth authentication system that integrates with the existing API key management.

## System Components

### 1. User Authentication (Google OAuth)
- Users log in with their Google account
- User profiles stored in `users` table
- Session management with JWT tokens
- Secure HTTP-only cookies

### 2. API Key Management
- Users can create multiple API keys
- Each key is linked to a user account
- Keys have tiers (free, pro, enterprise)
- Optional expiration dates
- Usage tracking and statistics

### 3. Web Interface
- **Login page** (`/login`) - Google OAuth sign-in
- **Dashboard** (`/dashboard`) - Manage API keys, view usage

## Quick Start

### 1. Run Setup Script

```bash
./scripts/setup_oauth.sh
```

This will:
- Create `.env` file from template
- Generate secure secrets
- Install OAuth dependencies
- Run database migrations

### 2. Configure Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add redirect URI: `http://localhost:8000/auth/callback`
4. Copy Client ID and Secret to `.env`

### 3. Start the Application

```bash
uvicorn api.main:app --reload
```

### 4. Access the Application

- Login: http://localhost:8000/login
- Dashboard: http://localhost:8000/dashboard
- API: http://localhost:8000/v1/

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. Click "Sign in with Google"
       ▼
┌─────────────────┐
│  /auth/login    │
└────────┬────────┘
         │
         │ 2. Redirect to Google
         ▼
┌─────────────────┐
│  Google OAuth   │
└────────┬────────┘
         │
         │ 3. User authorizes
         ▼
┌─────────────────┐
│ /auth/callback  │
└────────┬────────┘
         │
         │ 4. Create/update user
         ▼
┌─────────────────┐
│  users table    │
└────────┬────────┘
         │
         │ 5. Create session
         ▼
┌─────────────────┐
│  Set JWT cookie │
└────────┬────────┘
         │
         │ 6. Redirect to dashboard
         ▼
┌─────────────────┐
│   /dashboard    │
└────────┬────────┘
         │
         │ 7. Create API keys
         ▼
┌──────────────────┐
│ divv_api_keys    │
│   (user_id FK)   │
└──────────────────┘
```

## Database Schema

### users Table

Stores Google OAuth user profiles:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    google_id VARCHAR(255) UNIQUE,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    picture_url TEXT,
    tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_login_at TIMESTAMP,
    metadata JSONB
);
```

### divv_api_keys Table (Updated)

Now includes `user_id` foreign key:

```sql
ALTER TABLE divv_api_keys
ADD COLUMN user_id VARCHAR(255);

ALTER TABLE divv_api_keys
ADD COLUMN tier VARCHAR(50) DEFAULT 'free';

ALTER TABLE divv_api_keys
ADD CONSTRAINT divv_api_keys_user_id_fkey
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

## API Endpoints

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | GET | Initiate Google OAuth |
| `/auth/callback` | GET | Handle OAuth callback |
| `/auth/logout` | POST | Clear session |
| `/auth/me` | GET | Get current user |
| `/auth/status` | GET | Check auth status |

### API Keys (Require OAuth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/keys` | POST | Create API key |
| `/v1/keys` | GET | List user's keys |
| `/v1/keys/{id}` | DELETE | Revoke key |
| `/v1/keys/{id}/usage` | GET | Get usage stats |

## Authentication Methods

### 1. Web Browser (Cookie-based)

For dashboard and web interface:

```javascript
// Automatic cookie handling
fetch('/v1/keys', {
    credentials: 'include'
})
```

### 2. API Requests (Header-based)

For programmatic access:

```bash
curl -H "X-API-Key: sk_live_abc123..." \
     http://localhost:8000/v1/stocks/AAPL
```

### 3. Hybrid (JWT + API Key)

Dashboard uses JWT for user authentication, but displays API keys for external use.

## User Flow

### First Time User

1. Visit `/login`
2. Click "Sign in with Google"
3. Authorize application
4. Redirected to `/dashboard`
5. Create first API key
6. Copy key and use in applications

### Returning User

1. Visit `/login` (or any protected page)
2. Redirected to Google (if not logged in)
3. Auto-redirected to dashboard (if already logged in)
4. Manage existing keys or create new ones

## Security Features

### 1. Secure Session Management

- JWT tokens signed with `SECRET_KEY`
- 30-minute token expiration (configurable)
- HTTP-only cookies (not accessible via JavaScript)
- SameSite protection against CSRF
- Secure flag in production (HTTPS only)

### 2. API Key Security

- SHA-256 hashed storage (never store plaintext)
- One-time display (key shown only on creation)
- Per-user isolation (users only see their own keys)
- Soft delete (revoke instead of delete for audit trail)

### 3. OAuth Security

- State parameter validation
- Redirect URI validation
- Token verification
- Scope limitation (only openid, email, profile)

### 4. Database Security

- Foreign key constraints
- CASCADE delete (removing user removes keys)
- Indexed lookups
- Prepared statements (SQL injection prevention)

## Tier System

Users and their API keys have tiers that determine rate limits:

| Tier | Req/Min | Req/Hour | Req/Day |
|------|---------|----------|---------|
| Free | 60 | 1,000 | 10,000 |
| Pro | 600 | 20,000 | 500,000 |
| Enterprise | 6,000 | 200,000 | 10,000,000 |

Tiers can be set:
- At user level (`users.tier`)
- At key level (`divv_api_keys.tier`)
- Key tier inherits from user tier by default

## Usage Tracking

Every API request updates:
- `last_used_at` - Timestamp of last use
- `request_count` - Total number of requests

View detailed statistics:
```bash
GET /v1/keys/{key_id}/usage?days=30
```

Returns:
- Total requests
- Successful vs error requests
- Average response time
- Daily breakdown

## File Structure

```
├── api/
│   ├── config.py                 # Configuration management
│   ├── oauth.py                  # OAuth utilities & JWT
│   ├── routers/
│   │   ├── auth.py              # Auth endpoints
│   │   └── api_keys.py          # Key management (updated)
│   └── main.py                   # Main app (updated)
│
├── migrations/
│   ├── create_users_table.sql   # User table migration
│   └── add_user_to_divv_api_keys.sql  # FK migration
│
├── web/
│   ├── login.html               # Login page
│   └── dashboard.html           # Dashboard
│
├── scripts/
│   ├── setup_oauth.sh           # Setup script
│   └── manage_api_keys.py       # CLI management
│
├── docs/
│   ├── GOOGLE_OAUTH_SETUP.md    # Setup guide
│   ├── API_KEY_MANAGEMENT.md    # Key management docs
│   └── AUTHENTICATION_SYSTEM.md # This file
│
├── .env.example                 # Environment template
└── requirements.txt             # Updated dependencies
```

## Environment Variables

Required variables in `.env`:

```bash
# Google OAuth
GOOGLE_CLIENT_ID=your-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret

# Security
SECRET_KEY=generated-secret
SESSION_SECRET=generated-secret

# URLs
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Development vs Production

### Development

```bash
ENVIRONMENT=development
COOKIE_SECURE=false
COOKIE_DOMAIN=localhost
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
```

### Production

```bash
ENVIRONMENT=production
COOKIE_SECURE=true
COOKIE_DOMAIN=yourdomain.com
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback
ALLOWED_ORIGINS=https://yourdomain.com
```

## Testing

### Test Authentication

```bash
# Start server
uvicorn api.main:app --reload

# Visit login
open http://localhost:8000/login

# Check API
curl http://localhost:8000/auth/status
```

### Test API Key Creation

```python
import requests

# Login via browser first, then:
session = requests.Session()

# Create key (uses cookies from browser)
response = session.post('http://localhost:8000/v1/keys', json={
    'name': 'Test Key',
    'expires_in_days': 30
})

key_data = response.json()
api_key = key_data['api_key']

# Use the key
response = requests.get(
    'http://localhost:8000/v1/stocks/AAPL',
    headers={'X-API-Key': api_key}
)
```

## Troubleshooting

### "Redirect URI mismatch"
- Check Google Cloud Console redirect URIs match `.env`
- Include protocol (http:// or https://)
- No trailing slash

### "Invalid token"
- Verify `SECRET_KEY` is consistent
- Check token expiration
- Clear cookies and login again

### "User not found"
- Run database migration
- Check `users` table exists
- Verify foreign key constraint

### Keys not appearing
- Check user is logged in (`/auth/status`)
- Verify `user_id` is set on keys
- Check foreign key relationship

## Migration from Old System

If migrating from `api_keys` table:

```bash
# 1. Backup existing keys
pg_dump -t api_keys dividend_db > backup_api_keys.sql

# 2. Run migrations
psql -d dividend_db -f migrations/create_users_table.sql
psql -d dividend_db -f migrations/add_user_to_divv_api_keys.sql

# 3. Migrate data
python scripts/manage_api_keys.py migrate

# 4. Verify
python scripts/manage_api_keys.py list
```

## Best Practices

1. **Rotate keys regularly** - Set expiration dates
2. **Use different keys per environment** - Dev, staging, prod
3. **Monitor usage** - Check `/keys/{id}/usage` regularly
4. **Revoke compromised keys immediately**
5. **Use HTTPS in production**
6. **Keep secrets out of version control**
7. **Backup database regularly**
8. **Implement rate limiting** - Already built-in by tier

## Resources

- [Google OAuth Setup Guide](./GOOGLE_OAUTH_SETUP.md)
- [API Key Management](./API_KEY_MANAGEMENT.md)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Documentation](https://oauth.net/2/)
- [JWT.io](https://jwt.io/)

## Support

For issues:
1. Check application logs
2. Review troubleshooting section
3. Verify environment variables
4. Test with curl/Postman
5. Check database state
