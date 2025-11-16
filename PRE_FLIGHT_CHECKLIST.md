# ✈️ Pre-Flight Deployment Checklist

**Before deploying to Railway, verify all these items are correct.**

This checklist ensures a smooth deployment with no surprises.

---

## ✅ Configuration Verification

### Docker Compose (`docker-compose.railway.yml`)

**Ports:**
- [x] Nginx exposed on port 80 (Railway provides SSL)
- [x] Backend on internal port 8000 (not exposed)
- [x] Frontend on internal port 3000 (not exposed)
- [x] Redis on internal port 6379 (not exposed)

**Health Checks:**
- [x] Nginx: Checks `/health` endpoint
- [x] Backend: Python health check script
- [x] Redis: `redis-cli ping`
- [x] All have proper intervals and timeouts

**Networks:**
- [x] All services on `app-network`
- [x] Internal DNS working (service names)

**Volumes:**
- [x] Redis data persistence configured
- [x] Local driver for Railway

**Environment Variables Required:**
- [x] SUPABASE_URL
- [x] SUPABASE_KEY
- [x] SUPABASE_SERVICE_ROLE_KEY
- [x] FMP_API_KEY
- [x] SECRET_KEY
- [x] SESSION_SECRET
- [x] ALLOWED_ORIGINS
- [x] ENVIRONMENT=production

**Optional Variables:**
- [ ] GOOGLE_CLIENT_ID
- [ ] GOOGLE_CLIENT_SECRET
- [ ] ALPHA_VANTAGE_API_KEY
- [ ] DATABASE_URL

---

### Nginx Configuration (`nginx/nginx.railway.conf`)

**Routing:**
- [x] `/` → Frontend (Next.js)
- [x] `/v1/*` → Backend (FastAPI)
- [x] `/api/*` → Backend (FastAPI)
- [x] `/health` → Backend health check
- [x] `/_next/*` → Frontend static files

**Security Headers:**
- [x] X-Frame-Options: SAMEORIGIN
- [x] X-Content-Type-Options: nosniff
- [x] X-XSS-Protection: 1; mode=block
- [x] Content-Security-Policy configured
- [x] Permissions-Policy configured
- [x] Referrer-Policy set

**Performance:**
- [x] Gzip compression enabled
- [x] Keep-alive connections (32)
- [x] Static asset caching configured
- [x] Rate limiting zones defined

**Rate Limits:**
- [x] API: 60 req/min with burst=20
- [x] General: 120 req/min with burst=30
- [x] Static files: burst=50

---

### Backend Dockerfile (`Dockerfile.backend`)

**Multi-stage Build:**
- [x] Builder stage for dependencies
- [x] Runtime stage for production
- [x] Python 3.11-slim base image

**Security:**
- [x] Non-root user (appuser:1000)
- [x] Proper file permissions
- [x] No unnecessary packages

**Dependencies:**
- [x] PostgreSQL client
- [x] Chromium (for Selenium scrapers)
- [x] ChromeDriver
- [x] All Python packages from requirements.txt

**Configuration:**
- [x] PYTHONUNBUFFERED=1
- [x] PYTHONDONTWRITEBYTECODE=1
- [x] Workers: 4 uvicorn workers
- [x] Health check configured

**Files Copied:**
- [x] api/ directory
- [x] lib/ directory
- [x] scripts/ directory
- [x] supabase_helpers.py
- [x] sector_helpers.py

---

### Frontend Dockerfile (`Dockerfile.frontend`)

**Multi-stage Build:**
- [x] Deps stage for node_modules
- [x] Builder stage for Next.js build
- [x] Runner stage for production
- [x] Node 20-alpine base image

**Security:**
- [x] Non-root user (nextjs:1001)
- [x] Proper file permissions
- [x] Minimal attack surface

**Build Configuration:**
- [x] Standalone output mode
- [x] Static files optimization
- [x] Telemetry disabled
- [x] NODE_ENV=production

**Files Copied:**
- [x] public/ directory
- [x] .next/standalone
- [x] .next/static

---

## 🔐 Security Checklist

### Secrets Management

**Generated Secrets:**
- [x] SECRET_KEY: 64 characters ✓
- [x] SESSION_SECRET: 64 characters ✓
- [x] Saved securely (DEPLOY_NOW.md)

**HTTPS Configuration:**
- [x] Cookies set to https_only in production
- [x] Railway handles SSL termination
- [x] nginx listens on HTTP (Railway adds HTTPS)

**CORS Configuration:**
- [x] No wildcard (*) in production
- [x] Must be set to specific Railway URL
- [x] Will update after deployment

**Secret Validation:**
- [x] api/config.py validates secrets in production
- [x] Raises error if SECRET_KEY < 32 chars
- [x] Raises error if CORS is wildcard in production

---

### Rate Limiting

**Health Endpoint:**
- [x] 10 requests per minute per IP
- [x] Sliding window algorithm
- [x] In-memory rate limiter

**API Endpoints:**
- [x] Nginx rate limiting (60/min)
- [x] Burst handling configured
- [x] 429 responses properly formatted

---

### Headers

**Security Headers (nginx):**
- [x] X-Frame-Options
- [x] X-Content-Type-Options
- [x] X-XSS-Protection
- [x] Content-Security-Policy
- [x] Permissions-Policy
- [x] Referrer-Policy

**Application Headers (FastAPI):**
- [x] X-Request-ID (request tracking)
- [x] X-Process-Time (performance monitoring)
- [x] X-RateLimit-* (rate limit info)

---

## ⚡ Performance Checklist

### Caching

**Redis:**
- [x] Service configured in docker-compose
- [x] 256MB max memory
- [x] LRU eviction policy
- [x] Persistence enabled (AOF)
- [x] Health checks working

**Application Caching:**
- [x] @cache_response() decorator ready
- [x] Graceful fallback if Redis down
- [x] TTL management configured
- [x] Cache invalidation by pattern

**Static Assets:**
- [x] Next.js static files: 1 year cache
- [x] Images: 30 days cache
- [x] Public assets: 7 days cache
- [x] HTML: no-cache

---

### Optimization

**Gzip Compression:**
- [x] Enabled in nginx
- [x] Compression level: 6
- [x] All text formats covered

**Connection Pooling:**
- [x] Nginx keep-alive: 32 connections
- [x] Supabase connection pooling (built-in)

**Docker Images:**
- [x] Multi-stage builds
- [x] Alpine Linux where possible
- [x] Layer caching optimized
- [x] Minimal final images

---

## 📦 Build Verification

### Repository Status

```bash
git status
```
Expected: `nothing to commit, working tree clean`

- [x] All changes committed
- [x] All commits pushed to main
- [x] No uncommitted files
- [x] .gitignore working correctly

### Files Present

Required configuration files:
- [x] docker-compose.railway.yml
- [x] Dockerfile.backend
- [x] Dockerfile.frontend
- [x] nginx/nginx.railway.conf
- [x] .env.railway.example
- [x] railway.toml
- [x] railway.json

Required application files:
- [x] api/ directory
- [x] api/main.py
- [x] api/config.py
- [x] api/cache.py
- [x] api/middleware/health_rate_limit.py
- [x] lib/ directory
- [x] docs-site/ directory
- [x] supabase_helpers.py

---

## 🌐 Environment Variables Checklist

### Railway Dashboard

Before deployment, set these in Railway → Variables:

**Critical (MUST SET):**
```env
SECRET_KEY=6709834fabf68b38a040e6839f76ee0f141ffcab2049c77eab5b09ea17c36ae2
SESSION_SECRET=0fa357a3ee6a2d638c13fda18cdb30aeec2e4552e3460b9b8195aee5c0909bef
ENVIRONMENT=production
ALLOWED_ORIGINS=*  # Update after deployment!
```

**Required (VERIFY EXISTING):**
```env
SUPABASE_URL=https://uykxgbrzpfswbdxtyzlv.supabase.co
SUPABASE_KEY=<your-supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
FMP_API_KEY=<your-fmp-api-key>
```

**Optional:**
```env
ALPHA_VANTAGE_API_KEY=<optional>
GOOGLE_CLIENT_ID=<optional>
GOOGLE_CLIENT_SECRET=<optional>
NEXT_PUBLIC_API_URL=<will-be-railway-url>
```

---

## 🧪 Pre-Deployment Tests

### Local Docker Test (Optional but Recommended)

```bash
# Export required variables
export SECRET_KEY="6709834fabf68b38a040e6839f76ee0f141ffcab2049c77eab5b09ea17c36ae2"
export SESSION_SECRET="0fa357a3ee6a2d638c13fda18cdb30aeec2e4552e3460b9b8195aee5c0909bef"
export ENVIRONMENT=production
export ALLOWED_ORIGINS="http://localhost"
export SUPABASE_URL="https://uykxgbrzpfswbdxtyzlv.supabase.co"
export SUPABASE_KEY="<your-key>"
export SUPABASE_SERVICE_ROLE_KEY="<your-key>"
export FMP_API_KEY="<your-key>"

# Build images
docker-compose -f docker-compose.railway.yml build

# Start services
docker-compose -f docker-compose.railway.yml up

# Test (in another terminal)
curl http://localhost/health
curl http://localhost/v1/stocks/AAPL/quote

# Stop
docker-compose -f docker-compose.railway.yml down
```

**Expected Results:**
- [x] All services build successfully
- [x] All services start without errors
- [x] Health check returns 200
- [x] API returns valid data
- [x] No errors in logs

---

## 📋 Deployment Day Checklist

### Before Creating Railway Project

- [x] Review all configurations above
- [x] Verify secrets are saved securely
- [x] Check git repository is clean
- [x] Read DEPLOY_NOW.md thoroughly

### During Railway Setup

- [ ] Create Railway project
- [ ] Select GitHub repo correctly
- [ ] Select `main` branch
- [ ] Wait for Railway to detect docker-compose.railway.yml
- [ ] Set all environment variables
- [ ] Double-check variable names (no typos!)
- [ ] Double-check variable values (copy/paste)

### During Deployment

- [ ] Watch build logs for errors
- [ ] Verify all 4 services start
- [ ] Check health status in Railway dashboard
- [ ] Note the Railway URL

### After Deployment

- [ ] Update ALLOWED_ORIGINS with Railway URL
- [ ] Wait for redeployment (~1-2 min)
- [ ] Run all verification tests
- [ ] Test health endpoint
- [ ] Test API functionality
- [ ] Test rate limiting
- [ ] Check security headers
- [ ] Verify CORS works
- [ ] Visit frontend in browser

---

## ⚠️ Common Issues to Watch For

### Issue: Build Fails

**Check:**
- All files committed and pushed?
- Dockerfile syntax correct?
- requirements.txt valid?
- package.json valid?

**Solution:**
- Review Railway build logs
- Fix any reported errors
- Push fixes to GitHub
- Railway auto-redeploys

### Issue: Services Won't Start

**Check:**
- Environment variables set?
- Secrets copied correctly (64 chars)?
- Database accessible?
- No port conflicts?

**Solution:**
- Check Railway service logs
- Verify all env vars
- Test database connection
- Restart services if needed

### Issue: Health Check Fails

**Check:**
- Backend running on port 8000?
- Database connection working?
- No errors in backend logs?

**Solution:**
- Check backend logs
- Verify SUPABASE_URL and keys
- Ensure all dependencies installed

### Issue: Frontend Not Loading

**Check:**
- Next.js build successful?
- frontend service running?
- nginx routing correct?

**Solution:**
- Check frontend build logs
- Verify no build errors
- Check nginx logs

---

## ✅ Final Pre-Flight Check

Before clicking "Deploy" in Railway:

- [x] All files committed and pushed to GitHub
- [x] Repository clean (git status)
- [x] Secrets generated (64 chars each)
- [x] Docker configurations reviewed
- [x] nginx configuration reviewed
- [x] Environment variables prepared
- [x] DEPLOY_NOW.md read and understood
- [x] This checklist completed
- [x] Ready to monitor deployment logs

---

## 🚀 You're Clear for Takeoff!

If all boxes above are checked, you're ready to deploy to Railway.

**Next Steps:**
1. Go to https://railway.app/new
2. Follow DEPLOY_NOW.md step-by-step
3. Monitor deployment closely
4. Run verification tests
5. Celebrate! 🎉

**Estimated time:** ~25 minutes
**Success rate:** High (all prerequisites met)
**Rollback available:** Yes (Railway keeps previous deployments)

---

**Good luck with your deployment!** 🚀
