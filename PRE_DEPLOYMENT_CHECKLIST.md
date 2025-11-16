# Pre-Deployment Checklist

Complete this checklist before deploying to production.

## ✅ Critical Security (Must Complete)

### 1. Generate Production Secrets
```bash
# Generate SECRET_KEY (save this!)
openssl rand -hex 32

# Generate SESSION_SECRET (save this!)
openssl rand -hex 32
```

- [ ] SECRET_KEY generated (64 characters)
- [ ] SESSION_SECRET generated (64 characters)
- [ ] Both secrets saved securely (password manager)

### 2. Railway Environment Variables
Go to Railway Dashboard → Your Project → Variables:

**Required:**
- [ ] `SECRET_KEY=<your-64-char-key>`
- [ ] `SESSION_SECRET=<your-64-char-key>`
- [ ] `ENVIRONMENT=production`
- [ ] `ALLOWED_ORIGINS=https://your-app.railway.app`

**Already Set (verify):**
- [ ] `SUPABASE_URL=https://uykxgbrzpfswbdxtyzlv.supabase.co`
- [ ] `SUPABASE_KEY=<your-key>`
- [ ] `SUPABASE_SERVICE_ROLE_KEY=<your-key>`
- [ ] `FMP_API_KEY=<your-key>`

### 3. Code Changes Committed
```bash
git status
# Should show these files modified:
#   api/main.py
#   api/config.py
#   docker-compose.railway.yml
#   nginx/nginx.railway.conf
#   .env.railway.example
#   api/middleware/health_rate_limit.py (new)
#   api/cache.py (new)
```

- [ ] All changes committed
- [ ] Pushed to GitHub (`git push origin main`)

---

## 🧪 Local Testing (Recommended)

### Test 1: Environment Validation
```bash
# This should FAIL with development environment
ENVIRONMENT=production python3 -c "from api.config import settings"
# Expected: ValueError about SECRET_KEY

# This should SUCCEED
export SECRET_KEY=$(openssl rand -hex 32)
export SESSION_SECRET=$(openssl rand -hex 32)
export ALLOWED_ORIGINS="http://localhost:3000"
ENVIRONMENT=production python3 -c "from api.config import settings; print('✅ Config valid')"
```

- [ ] Validation rejects missing secrets
- [ ] Validation accepts valid secrets

### Test 2: Docker Build
```bash
# Build backend
docker build -f Dockerfile.backend -t divv-backend .

# Build frontend
docker build -f Dockerfile.frontend -t divv-frontend .
```

- [ ] Backend builds successfully
- [ ] Frontend builds successfully
- [ ] No critical warnings

### Test 3: Local Railway Stack
```bash
# Set environment variables
export SECRET_KEY=$(openssl rand -hex 32)
export SESSION_SECRET=$(openssl rand -hex 32)
export ALLOWED_ORIGINS="http://localhost"
export ENVIRONMENT=production

# Start stack
docker-compose -f docker-compose.railway.yml up

# In another terminal, test endpoints
curl http://localhost/health
curl http://localhost/v1/stocks/AAPL/quote
```

- [ ] All services start without errors
- [ ] Health endpoint responds
- [ ] API endpoints work
- [ ] Nginx routing works

---

## 🔒 Security Verification

### Security Headers Test
```bash
curl -I http://localhost/ | grep -E "Content-Security-Policy|Permissions-Policy|X-Frame-Options"
```

Expected output:
```
Content-Security-Policy: default-src 'self'; ...
Permissions-Policy: geolocation=(), microphone=(), camera=(), ...
X-Frame-Options: SAMEORIGIN
```

- [ ] Content-Security-Policy present
- [ ] Permissions-Policy present
- [ ] X-Frame-Options present
- [ ] X-Content-Type-Options present

### Rate Limiting Test
```bash
# Should get 429 after 10 requests
for i in {1..15}; do curl -w "%{http_code}\n" http://localhost/health; done | tail -5
```

Expected: Last 5 responses should be `429`

- [ ] Rate limiting activates after 10 requests
- [ ] Returns 429 status code
- [ ] Error message mentions rate limit

### CORS Test
```bash
# Should be rejected
curl -H "Origin: https://evil.com" http://localhost/v1/stocks/AAPL/quote -v
```

Expected: No `Access-Control-Allow-Origin` header

- [ ] CORS rejects unauthorized origins
- [ ] Allows configured origins only

---

## 📝 Railway Deployment

### Pre-Deployment
- [ ] All code changes committed and pushed
- [ ] Railway project created and linked
- [ ] Environment variables set in Railway
- [ ] Docker Compose file selected in Railway settings

### During Deployment
- [ ] Watch Railway logs for errors
- [ ] Deployment completes successfully
- [ ] No build errors
- [ ] No runtime errors on startup

### Post-Deployment
- [ ] Health endpoint accessible
- [ ] API endpoints respond correctly
- [ ] Frontend loads
- [ ] No errors in Railway logs

---

## 🧪 Production Verification

### 1. Health Check
```bash
curl https://your-app.railway.app/health
```

Expected:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": 1731787200.0
}
```

- [ ] Returns 200 status
- [ ] Database connected
- [ ] Version correct

### 2. API Functionality
```bash
# Test stock quote endpoint
curl https://your-app.railway.app/v1/stocks/AAPL/quote

# Test dividends endpoint
curl https://your-app.railway.app/v1/dividends/AAPL
```

- [ ] Stock quotes work
- [ ] Dividends endpoint works
- [ ] No 500 errors
- [ ] Response times reasonable (<500ms)

### 3. Security Headers (Production)
```bash
curl -I https://your-app.railway.app/
```

Verify presence of:
- [ ] `Content-Security-Policy`
- [ ] `Permissions-Policy`
- [ ] `X-Frame-Options: SAMEORIGIN`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `X-XSS-Protection: 1; mode=block`
- [ ] `Referrer-Policy`

### 4. Rate Limiting (Production)
```bash
# Should get rate limited
for i in {1..15}; do curl https://your-app.railway.app/health; sleep 1; done
```

- [ ] First 10 requests succeed
- [ ] Next requests return 429
- [ ] Error message clear

### 5. CORS (Production)
```bash
# From browser console on different domain:
fetch('https://your-app.railway.app/v1/stocks/AAPL/quote', {
  headers: { 'Origin': 'https://evil.com' }
})
```

- [ ] Request blocked by CORS
- [ ] Browser shows CORS error
- [ ] Only your domain allowed

---

## 📊 Monitoring Setup

### Railway Metrics
- [ ] CPU usage normal (<50%)
- [ ] Memory usage normal (<70%)
- [ ] No error spikes
- [ ] Deployment successful

### Optional: External Monitoring
- [ ] UptimeRobot or similar configured
- [ ] Alerts set up for downtime
- [ ] Performance monitoring active

---

## 📚 Documentation

- [ ] README updated (if needed)
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Team notified of changes

---

## 🎯 Final Checklist

### Security
- [ ] ✅ All critical fixes applied
- [ ] ✅ Secrets generated and set
- [ ] ✅ CORS restricted
- [ ] ✅ Security headers added
- [ ] ✅ Rate limiting active

### Performance
- [ ] ✅ Redis caching ready
- [ ] ✅ Connection pooling active
- [ ] ✅ Compression enabled
- [ ] ✅ Health checks working

### Deployment
- [ ] ✅ Code committed and pushed
- [ ] ✅ Environment variables set
- [ ] ✅ Railway deployment successful
- [ ] ✅ All endpoints tested
- [ ] ✅ No errors in logs

---

## 🚨 Rollback Plan

If something goes wrong:

### Quick Rollback
```bash
# In Railway dashboard
Deployments → Select previous deployment → "Redeploy"
```

### Fix Environment Variables
```bash
railway variables set ENVIRONMENT=development
railway variables set ALLOWED_ORIGINS="*"
# Then redeploy
```

### Revert Code Changes
```bash
git revert HEAD
git push origin main
# Railway auto-deploys reverted code
```

---

## ✅ Sign-Off

**Deployment performed by:** ________________

**Date:** ________________

**Environment variables verified:** ☐ Yes ☐ No

**All tests passed:** ☐ Yes ☐ No

**Production ready:** ☐ Yes ☐ No

**Notes:**
```
_______________________________________________________
_______________________________________________________
_______________________________________________________
```

---

## 📞 Emergency Contacts

**Railway Support:** https://railway.app/help
**Supabase Support:** https://supabase.com/dashboard/support

**If critical issues arise:**
1. Check Railway logs first
2. Rollback to previous deployment
3. Review CHANGES_APPLIED.md
4. Check SECURITY_AUDIT.md for context

---

**Once all boxes are checked, you're ready to deploy! 🚀**
