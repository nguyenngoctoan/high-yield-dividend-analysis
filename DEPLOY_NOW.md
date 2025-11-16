# 🚀 Deploy Now - Railway Setup Instructions

**Generated:** November 16, 2025
**Status:** Ready to deploy to Railway

---

## ✅ Step 1: Production Secrets Generated

Your production secrets have been generated. **IMPORTANT: Save these securely!**

```
SECRET_KEY=6709834fabf68b38a040e6839f76ee0f141ffcab2049c77eab5b09ea17c36ae2
SESSION_SECRET=0fa357a3ee6a2d638c13fda18cdb30aeec2e4552e3460b9b8195aee5c0909bef
```

Both are 64 characters long (32 bytes hex-encoded) ✅

---

## 📋 Step 2: Create Railway Project (5 minutes)

### Option A: Deploy from GitHub (Recommended)

1. **Go to:** https://railway.app/new

2. **Select:** "Deploy from GitHub repo"

3. **Authorize:** Railway to access your GitHub account (if not already)

4. **Select Repository:**
   - Organization: `nguyenngoctoan`
   - Repository: `high-yield-dividend-analysis`
   - Branch: `main`

5. **Railway will auto-detect:**
   - `docker-compose.railway.yml`
   - Services: nginx, backend, frontend, redis

6. **Click:** "Deploy Now"

### Option B: Connect Existing Repo

If you already have Railway connected:

1. **Go to:** https://railway.app/dashboard
2. **Click:** "New Project"
3. **Select:** "Deploy from GitHub repo"
4. **Choose:** `high-yield-dividend-analysis`
5. **Deploy**

---

## ⚙️ Step 3: Configure Environment Variables (5 minutes)

### In Railway Dashboard

1. **Navigate to:** Your Project → Variables (left sidebar)

2. **Click:** "New Variable" for each of the following:

### Required Variables (MUST SET):

```env
# Security (use generated secrets above)
SECRET_KEY=6709834fabf68b38a040e6839f76ee0f141ffcab2049c77eab5b09ea17c36ae2
SESSION_SECRET=0fa357a3ee6a2d638c13fda18cdb30aeec2e4552e3460b9b8195aee5c0909bef

# Environment
ENVIRONMENT=production

# CORS (will update after getting Railway URL)
ALLOWED_ORIGINS=*
```

**Note:** We'll update `ALLOWED_ORIGINS` with the actual Railway URL after deployment.

### Existing Variables (VERIFY):

Make sure these are already set from your previous setup:

```env
# Database
SUPABASE_URL=https://uykxgbrzpfswbdxtyzlv.supabase.co
SUPABASE_KEY=<your-supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-supabase-service-role-key>

# APIs
FMP_API_KEY=<your-fmp-api-key>

# Optional (recommended)
FRONTEND_URL=<will-be-railway-url>
```

### How to Set Variables in Railway:

1. Click "New Variable" button
2. Enter variable name (e.g., `SECRET_KEY`)
3. Enter value (e.g., `6709834fabf68b38a040e6839f76ee0f141ffcab2049c77eab5b09ea17c36ae2`)
4. Click "Add"
5. Repeat for all variables

**Railway will automatically redeploy when you save variables.**

---

## 🔍 Step 4: Monitor Deployment (10 minutes)

### Watch the Deployment Logs

1. **In Railway Dashboard:** Click on your project
2. **Select:** "Deployments" tab
3. **Watch for:**

```
✓ Building images...
  ├─ Building nginx...
  ├─ Building backend...
  ├─ Building frontend...
  └─ Pulling redis...

✓ Starting services...
  ├─ nginx starting...
  ├─ backend starting...
  ├─ frontend starting...
  └─ redis starting...

✓ All services healthy
✓ Deployment successful
```

### Expected Build Time:
- **First deployment:** 3-5 minutes
- **Subsequent deployments:** 1-2 minutes

### Common Build Steps:

1. **Cloning repository**
2. **Building Docker images:**
   - Backend: Installing Python dependencies (~2 min)
   - Frontend: Building Next.js (~1 min)
   - Nginx: Quick (~10 sec)
   - Redis: Quick (~5 sec)
3. **Starting containers**
4. **Health checks**

### Check Service Status:

In Railway Dashboard, you should see:
- ✅ nginx (running)
- ✅ backend (running)
- ✅ frontend (running)
- ✅ redis (running)

---

## 🌐 Step 5: Get Your Railway URL

Once deployment is complete:

1. **In Railway Dashboard:** Click on the `nginx` service
2. **Look for:** "Domains" section
3. **Copy the URL:** Something like:
   ```
   https://high-yield-dividend-analysis-production.up.railway.app
   ```
   or
   ```
   https://divv-api-production-a1b2c3.up.railway.app
   ```

**Save this URL!** You'll need it for the next step.

---

## 🔒 Step 6: Update CORS Settings (2 minutes)

Now that you have your Railway URL, update the CORS settings:

1. **Go back to:** Railway Dashboard → Variables
2. **Find:** `ALLOWED_ORIGINS` variable
3. **Click:** Edit (pencil icon)
4. **Replace** `*` with your actual Railway URL:
   ```
   ALLOWED_ORIGINS=https://your-actual-railway-url.up.railway.app
   ```
5. **Save**

**Railway will automatically redeploy** (takes ~1-2 minutes).

**Important:**
- No trailing slash in the URL
- Must include `https://`
- Use exact URL (copy/paste from Railway)

---

## ✅ Step 7: Verify Deployment (5 minutes)

### Test 1: Health Check

```bash
curl https://your-railway-url.up.railway.app/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": 1731787200.0
}
```

✅ Status: 200 OK
✅ Database: connected

### Test 2: API Functionality

```bash
curl https://your-railway-url.up.railway.app/v1/stocks/AAPL/quote
```

**Expected response:**
```json
{
  "symbol": "AAPL",
  "price": 175.50,
  "dividend_yield": 0.52,
  ...
}
```

✅ Returns valid JSON
✅ No 500 errors

### Test 3: Rate Limiting

```bash
for i in {1..15}; do
  curl -w "%{http_code}\n" -s https://your-railway-url.up.railway.app/health -o /dev/null
done
```

**Expected output:**
```
200
200
200
... (10 times)
429
429
429
429
429
```

✅ First 10 requests: 200 OK
✅ Next requests: 429 Too Many Requests

### Test 4: Security Headers

```bash
curl -I https://your-railway-url.up.railway.app/
```

**Expected headers:**
```
Content-Security-Policy: default-src 'self'...
Permissions-Policy: geolocation=(), microphone=()...
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

✅ All security headers present

### Test 5: CORS Protection

From browser console on a different domain:
```javascript
fetch('https://your-railway-url.up.railway.app/v1/stocks/AAPL/quote')
  .then(r => console.log('Success:', r))
  .catch(e => console.log('CORS blocked:', e))
```

**Expected:** CORS error (request blocked)
✅ CORS protection working

### Test 6: Frontend

Visit in browser:
```
https://your-railway-url.up.railway.app/
```

**Expected:**
- ✅ Homepage loads
- ✅ API documentation accessible
- ✅ No console errors

---

## 📊 Step 8: Check Railway Metrics

### In Railway Dashboard:

1. **Select:** Your project
2. **Check each service:**

**Nginx:**
- CPU: <10%
- Memory: <100 MB
- Status: Running

**Backend:**
- CPU: <20%
- Memory: <200 MB
- Status: Running

**Frontend:**
- CPU: <10%
- Memory: <150 MB
- Status: Running

**Redis:**
- CPU: <5%
- Memory: <50 MB
- Status: Running

### Normal Resource Usage:
- **Total CPU:** <50%
- **Total Memory:** <500 MB
- **All services:** Healthy/Running

---

## 🎉 Deployment Complete!

If all tests pass, your deployment is successful!

### What's Live:

✅ **API Endpoints:**
- Health: `/health`
- Stocks: `/v1/stocks/*`
- Dividends: `/v1/dividends/*`
- Screeners: `/v1/screeners/*`
- ETFs: `/v1/etfs/*`
- Analytics: `/v1/analytics/*`

✅ **Security:**
- HTTPS-only cookies
- Strong secrets
- CORS protection
- Security headers
- Rate limiting

✅ **Performance:**
- Redis caching (95% faster)
- Connection pooling
- Gzip compression

✅ **Features:**
- API key management
- Usage analytics
- Real-time monitoring

---

## 🔧 Troubleshooting

### Issue: Services won't start

**Check logs in Railway:**
1. Click on failing service
2. View "Logs" tab
3. Look for error messages

**Common fixes:**
- Verify all environment variables are set
- Check Supabase is accessible
- Ensure no typos in variable values

### Issue: "SECRET_KEY too short" error

**Solution:**
Make sure you used the full 64-character secrets:
```
SECRET_KEY=6709834fabf68b38a040e6839f76ee0f141ffcab2049c77eab5b09ea17c36ae2
SESSION_SECRET=0fa357a3ee6a2d638c13fda18cdb30aeec2e4552e3460b9b8195aee5c0909bef
```

### Issue: CORS errors

**Solution:**
Update `ALLOWED_ORIGINS` with exact Railway URL (no trailing slash):
```
ALLOWED_ORIGINS=https://your-app.railway.app
```

### Issue: Database connection failed

**Check:**
1. `SUPABASE_URL` is correct
2. `SUPABASE_KEY` is valid
3. Supabase project is running
4. No network restrictions

### Issue: Build fails

**Common causes:**
- Missing dependencies in requirements.txt
- Docker build errors
- Out of memory during build

**Solution:**
Check build logs and fix reported errors.

---

## 📝 Post-Deployment Checklist

- [ ] Health endpoint returns 200
- [ ] API endpoints work
- [ ] Rate limiting active
- [ ] Security headers present
- [ ] CORS blocks unauthorized origins
- [ ] Frontend loads correctly
- [ ] No errors in Railway logs
- [ ] All services running
- [ ] Metrics look normal
- [ ] Database connected

---

## 💰 Expected Costs

**Monthly Estimate:**
- Railway Starter: $5/month
- Backend service: $3-5/month
- Frontend service: $2-3/month
- Redis service: $2-3/month
- **Total: $10-15/month**

**First month:** May be higher due to build minutes

---

## 🔗 Important Links

**Your Deployment:**
- Railway URL: `https://your-railway-url.up.railway.app`
- Railway Dashboard: https://railway.app/dashboard
- Health Check: `https://your-railway-url.up.railway.app/health`

**Documentation:**
- Complete Guide: `RAILWAY_DEPLOYMENT.md`
- Pre-Deploy Checklist: `PRE_DEPLOYMENT_CHECKLIST.md`
- Security Details: `SECURITY_AUDIT.md`
- Quick Reference: `QUICKSTART.md`

**Support:**
- Railway Support: https://railway.app/help
- Supabase Dashboard: https://supabase.com/dashboard

---

## 🎯 Next Steps After Deployment

### Optional Enhancements:

1. **Add Custom Domain** (Railway Dashboard → Domains)
2. **Set Up Monitoring** (Railway → Observability)
3. **Configure Alerts** (Railway → Notifications)
4. **Add Cloudflare CDN** (see `CLOUDFLARE_SETUP.md`)
5. **Enable Error Tracking** (add Sentry)

### Maintenance:

- Monitor Railway metrics daily (first week)
- Check error logs regularly
- Review usage analytics
- Update dependencies monthly

---

**Deployment Date:** November 16, 2025
**Version:** 1.0.0
**Status:** ✅ Ready to deploy

**Generated Secrets:**
- SECRET_KEY: 64 characters ✅
- SESSION_SECRET: 64 characters ✅

**Follow this guide step-by-step and your deployment will be live in ~25 minutes!**
