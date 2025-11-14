# Quick Start - Login & Logout

Get the authentication system running in 5 minutes!

## 1. Run Setup (30 seconds)

```bash
./scripts/setup_oauth.sh
```

This creates `.env`, generates secrets, and installs dependencies.

## 2. Get Google OAuth Credentials (2 minutes)

1. Visit: https://console.cloud.google.com/apis/credentials
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Application type: **Web application**
4. Authorized redirect URIs: `http://localhost:8000/auth/callback`
5. Copy **Client ID** and **Client Secret**

## 3. Update .env (30 seconds)

Edit `.env` file:

```bash
GOOGLE_CLIENT_ID=your-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret-here
```

## 4. Setup Database (30 seconds)

```bash
psql -d dividend_db -f migrations/create_users_table.sql
```

## 5. Start Server (10 seconds)

```bash
uvicorn api.main:app --reload
```

## 6. Test It! (1 minute)

### Login:

1. Open browser: http://localhost:8000/login
2. Click **"Sign in with Google"**
3. Choose your Google account
4. Click **"Allow"**
5. You should see the dashboard! 🎉

### Logout:

1. Click the **"Logout"** button in the header
2. You should be back at the login page

### Create an API Key:

1. Login again
2. Click **"Create New Key"**
3. Enter a name (e.g., "My First Key")
4. Click **"Create Key"**
5. **Copy the key** (you won't see it again!)

### Test the API Key:

```bash
curl -H "X-API-Key: YOUR_KEY_HERE" \
     http://localhost:8000/v1/stocks/AAPL
```

## Complete! 🚀

You now have:
- ✅ Google OAuth login
- ✅ Secure session management
- ✅ User dashboard
- ✅ API key creation
- ✅ Working API access

## What You Can Do Now

### On the Dashboard:

- **View your profile** (name, email, picture from Google)
- **Create API keys** with optional expiration
- **List all your keys** with usage statistics
- **Revoke keys** you no longer need
- **Copy keys** to use in your applications

### With API Keys:

```python
import requests

headers = {'X-API-Key': 'sk_live_your_key_here'}

# Get stock info
response = requests.get(
    'http://localhost:8000/v1/stocks/AAPL',
    headers=headers
)
print(response.json())

# Get dividend data
response = requests.get(
    'http://localhost:8000/v1/dividends/AAPL',
    headers=headers
)
print(response.json())
```

## URLs to Remember

| Page | URL |
|------|-----|
| Login | http://localhost:8000/login |
| Dashboard | http://localhost:8000/dashboard |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

## Troubleshooting

### "Redirect URI mismatch"
- Go back to Google Cloud Console
- Make sure redirect URI is exactly: `http://localhost:8000/auth/callback`
- No trailing slash!

### "Cannot connect to database"
- Make sure PostgreSQL is running
- Check your database name is `dividend_db`
- Run: `psql -d dividend_db -c "SELECT 1"`

### "Module not found"
- Install dependencies: `pip install -r requirements.txt`

### Still stuck?
- Check the logs in your terminal
- See full guide: `docs/TESTING_AUTH.md`
- Review setup: `docs/GOOGLE_OAUTH_SETUP.md`

## Next Steps

1. **Read the docs**: Check `docs/AUTHENTICATION_SYSTEM.md`
2. **Test API**: Try different endpoints with your key
3. **Invite users**: Share the login page
4. **Deploy**: Set up production with HTTPS
5. **Monitor**: Check usage statistics on dashboard

---

**Questions?** Check `docs/GOOGLE_OAUTH_SETUP.md` for detailed instructions.
