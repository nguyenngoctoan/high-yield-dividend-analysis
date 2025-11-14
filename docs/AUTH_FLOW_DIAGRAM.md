# Authentication Flow Diagrams

Visual representation of the login and logout flows.

## Login Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │
     │ 1. Visits /login
     ▼
┌─────────────────────┐
│   Login Page        │
│  (web/login.html)   │
│                     │
│  [Sign in with      │
│   Google Button]    │
└──────────┬──────────┘
           │
           │ 2. Click button → GET /auth/login
           ▼
┌─────────────────────┐
│  FastAPI Server     │
│  (auth.router)      │
│                     │
│  def login():       │
│    redirect to      │
│    Google OAuth     │
└──────────┬──────────┘
           │
           │ 3. Redirect with client_id, scopes
           ▼
┌─────────────────────┐
│  Google OAuth       │
│  accounts.google... │
│                     │
│  - Select account   │
│  - Grant permission │
│  - Authorize app    │
└──────────┬──────────┘
           │
           │ 4. Redirect back with code
           │    GET /auth/callback?code=abc123
           ▼
┌─────────────────────┐
│  FastAPI Server     │
│  (auth.router)      │
│                     │
│  def callback():    │
└──────────┬──────────┘
           │
           │ 5. Exchange code for token
           ▼
┌─────────────────────┐
│  Google OAuth API   │
│  oauth2.google...   │
│                     │
│  Returns:           │
│  - access_token     │
│  - id_token         │
│  - user_info        │
└──────────┬──────────┘
           │
           │ 6. User info (email, name, picture)
           ▼
┌─────────────────────┐
│  Database Function  │
│  upsert_google_user │
│                     │
│  INSERT/UPDATE      │
│  users table        │
└──────────┬──────────┘
           │
           │ 7. User record created/updated
           ▼
┌─────────────────────┐
│  JWT Creation       │
│  (api/oauth.py)     │
│                     │
│  create_access_     │
│  token()            │
└──────────┬──────────┘
           │
           │ 8. JWT token + session token
           ▼
┌─────────────────────┐
│  Set Cookies        │
│                     │
│  access_token=JWT   │
│  session_token=...  │
│  (HttpOnly, Secure) │
└──────────┬──────────┘
           │
           │ 9. Redirect to /dashboard
           ▼
┌─────────────────────┐
│   Dashboard Page    │
│  (web/dashboard.html│
│                     │
│  - Shows user info  │
│  - List API keys    │
│  - Create new keys  │
└─────────────────────┘
```

## Logout Flow

```
┌─────────┐
│  User   │
└────┬────┘
     │
     │ On dashboard
     ▼
┌─────────────────────┐
│   Dashboard         │
│  (web/dashboard.html│
│                     │
│  [Logout Button]    │
└──────────┬──────────┘
           │
           │ 1. Click logout
           │    onclick="logout()"
           ▼
┌─────────────────────┐
│  JavaScript         │
│                     │
│  function logout() {│
│    window.location= │
│    '/auth/logout'   │
│  }                  │
└──────────┬──────────┘
           │
           │ 2. GET /auth/logout
           ▼
┌─────────────────────┐
│  FastAPI Server     │
│  (auth.router)      │
│                     │
│  def logout():      │
│    clear cookies    │
│    redirect login   │
└──────────┬──────────┘
           │
           │ 3. Delete cookies
           │    Set-Cookie: access_token=; Max-Age=0
           │    Set-Cookie: session_token=; Max-Age=0
           ▼
┌─────────────────────┐
│  Browser            │
│                     │
│  Cookies cleared:   │
│  ❌ access_token    │
│  ❌ session_token   │
└──────────┬──────────┘
           │
           │ 4. Redirect to /login
           ▼
┌─────────────────────┐
│   Login Page        │
│  (web/login.html)   │
│                     │
│  Ready to sign in   │
│  again              │
└─────────────────────┘
```

## API Key Creation Flow (After Login)

```
┌─────────┐
│  User   │
│ (Logged │
│   in)   │
└────┬────┘
     │
     │ On dashboard
     ▼
┌─────────────────────┐
│   Dashboard         │
│                     │
│  [Create New Key]   │
└──────────┬──────────┘
           │
           │ 1. Click button
           │    showCreateKeyModal()
           ▼
┌─────────────────────┐
│   Modal Dialog      │
│                     │
│  Name: [________]   │
│  Expiration: [▼]    │
│                     │
│  [Cancel] [Create]  │
└──────────┬──────────┘
           │
           │ 2. Submit form
           │    POST /v1/keys
           │    Cookie: access_token=JWT
           ▼
┌─────────────────────┐
│  FastAPI Server     │
│  (api_keys.router)  │
│                     │
│  @Depends(require_  │
│   authentication)   │
└──────────┬──────────┘
           │
           │ 3. Validate JWT from cookie
           ▼
┌─────────────────────┐
│  JWT Verification   │
│  (api/oauth.py)     │
│                     │
│  verify_access_     │
│  token()            │
└──────────┬──────────┘
           │
           │ 4. Extract user_id from JWT
           ▼
┌─────────────────────┐
│  Generate API Key   │
│  (api/auth.py)      │
│                     │
│  key = generate_    │
│        api_key()    │
│  hash = sha256(key) │
└──────────┬──────────┘
           │
           │ 5. Store in database
           ▼
┌─────────────────────┐
│  Database           │
│  divv_api_keys      │
│                     │
│  INSERT:            │
│  - user_id (FK)     │
│  - key_hash         │
│  - key_prefix       │
│  - tier             │
└──────────┬──────────┘
           │
           │ 6. Return full key (ONLY ONCE!)
           ▼
┌─────────────────────┐
│  Response           │
│                     │
│  {                  │
│   "api_key":        │
│   "sk_live_abc..."  │
│  }                  │
└──────────┬──────────┘
           │
           │ 7. Display key to user
           ▼
┌─────────────────────┐
│  Success Modal      │
│                     │
│  Your API Key:      │
│  sk_live_abc123...  │
│                     │
│  ⚠️ Copy now!       │
│                     │
│  [Copy & Close]     │
└─────────────────────┘
```

## Using API Key Flow

```
┌─────────────┐
│ Application │
│ (curl, etc) │
└──────┬──────┘
       │
       │ GET /v1/stocks/AAPL
       │ X-API-Key: sk_live_abc123...
       ▼
┌─────────────────────┐
│  FastAPI Server     │
│  Middleware         │
│                     │
│  Extract X-API-Key  │
│  header             │
└──────────┬──────────┘
           │
           │ Hash the key
           │ sha256(sk_live_abc123...)
           ▼
┌─────────────────────┐
│  Database Lookup    │
│  divv_api_keys      │
│                     │
│  SELECT * WHERE     │
│  key_hash = ?       │
└──────────┬──────────┘
           │
           ├─ Not found → 401 Unauthorized
           │
           ├─ is_active = false → 401 Key revoked
           │
           ├─ expires_at < now → 401 Key expired
           │
           └─ Valid ✓
           │
           │ Update usage stats
           ▼
┌─────────────────────┐
│  Update Tracking    │
│                     │
│  UPDATE:            │
│  - last_used_at     │
│  - request_count++  │
└──────────┬──────────┘
           │
           │ Get tier & rate limits
           ▼
┌─────────────────────┐
│  Rate Limiting      │
│                     │
│  Check tier limits: │
│  - free: 60/min     │
│  - pro: 600/min     │
│  - ent: 6000/min    │
└──────────┬──────────┘
           │
           ├─ Over limit → 429 Too Many Requests
           │
           └─ Within limit ✓
           │
           │ Process request
           ▼
┌─────────────────────┐
│  API Endpoint       │
│  (stocks.router)    │
│                     │
│  Return stock data  │
└──────────┬──────────┘
           │
           │ 200 OK + data
           ▼
┌─────────────┐
│ Application │
│  (receives  │
│    data)    │
└─────────────┘
```

## Session Expiration Flow

```
┌─────────┐
│  User   │
│ (Logged │
│   in)   │
└────┬────┘
     │
     │ Active session (JWT in cookie)
     ▼
┌─────────────────────┐
│   Dashboard         │
│  Active for         │
│  29 minutes         │
└──────────┬──────────┘
           │
           │ Time passes...
           ▼
┌─────────────────────┐
│  30 Minutes Later   │
│  JWT expired        │
│  (exp claim < now)  │
└──────────┬──────────┘
           │
           │ User tries to create API key
           │ POST /v1/keys
           ▼
┌─────────────────────┐
│  JWT Verification   │
│  (api/oauth.py)     │
│                     │
│  verify_access_     │
│  token()            │
│                     │
│  ❌ Token expired!  │
└──────────┬──────────┘
           │
           │ 401 Unauthorized
           ▼
┌─────────────────────┐
│  Frontend JS        │
│  (dashboard.html)   │
│                     │
│  catch (401) {      │
│    redirect login   │
│  }                  │
└──────────┬──────────┘
           │
           │ Redirect to /login
           ▼
┌─────────────────────┐
│   Login Page        │
│                     │
│  Session expired    │
│  Please login again │
└─────────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────┐
│         User's Browser              │
│                                     │
│  HTTP-only Cookies (JS can't read)  │
│  ├─ access_token (JWT)              │
│  └─ session_token                   │
│                                     │
│  SameSite: Lax (CSRF protection)    │
│  Secure: true (HTTPS only in prod)  │
└───────────────┬─────────────────────┘
                │
                │ HTTPS (in production)
                ▼
┌─────────────────────────────────────┐
│         FastAPI Server              │
│                                     │
│  1. CORS Middleware                 │
│     ├─ Check origin                 │
│     └─ Allow credentials            │
│                                     │
│  2. JWT Validation                  │
│     ├─ Verify signature (SECRET_KEY)│
│     ├─ Check expiration             │
│     └─ Extract user_id              │
│                                     │
│  3. Rate Limiting                   │
│     ├─ Check tier limits            │
│     └─ Block if exceeded            │
│                                     │
│  4. Database Validation             │
│     ├─ User exists & active         │
│     ├─ API key valid                │
│     └─ Foreign key constraints      │
└───────────────┬─────────────────────┘
                │
                │ Encrypted connection
                ▼
┌─────────────────────────────────────┐
│         PostgreSQL                  │
│                                     │
│  users table:                       │
│  ├─ Indexed on google_id, email     │
│  └─ Unique constraints              │
│                                     │
│  divv_api_keys table:               │
│  ├─ SHA-256 hashed keys (not plain) │
│  ├─ Foreign key to users (CASCADE)  │
│  └─ Indexed on key_hash, user_id    │
└─────────────────────────────────────┘
```

## Technology Stack

```
┌─────────────────────────────────────┐
│           Frontend                  │
│                                     │
│  - Vanilla HTML/CSS/JavaScript      │
│  - Fetch API for requests           │
│  - Cookie-based auth                │
│  - Responsive design                │
└───────────────┬─────────────────────┘
                │
                │ REST API
                ▼
┌─────────────────────────────────────┐
│           Backend                   │
│                                     │
│  FastAPI (Python)                   │
│  ├─ Authlib (OAuth client)          │
│  ├─ python-jose (JWT)               │
│  ├─ Pydantic (validation)           │
│  └─ Starlette (ASGI)                │
└───────────────┬─────────────────────┘
                │
                │ SQL queries
                ▼
┌─────────────────────────────────────┐
│          Database                   │
│                                     │
│  PostgreSQL                         │
│  ├─ users table                     │
│  ├─ divv_api_keys table             │
│  ├─ Views & functions               │
│  └─ Supabase client                 │
└───────────────┬─────────────────────┘
                │
                │ OAuth flow
                ▼
┌─────────────────────────────────────┐
│       External Service              │
│                                     │
│  Google OAuth 2.0                   │
│  ├─ User authentication             │
│  ├─ Profile information             │
│  └─ Email verification              │
└─────────────────────────────────────┘
```

---

These diagrams show the complete authentication flow from login to API key usage!
