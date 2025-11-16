# Railway Deployment Guide - Divv API

Complete guide to deploy your entire Divv stack (Frontend + Backend + Redis) on Railway.

## 🎯 Architecture Overview

**What you're deploying:**
- **Single Railway Service** running all components
- **Nginx** reverse proxy for unified routing
- **FastAPI** backend (Python)
- **Next.js** frontend (Node.js)
- **Redis** for caching and rate limiting
- **Supabase** database (external, already configured)

**Routing:**
```
your-app.railway.app/        → Next.js frontend
your-app.railway.app/v1/     → FastAPI backend
your-app.railway.app/api/    → FastAPI backend
your-app.railway.app/docs    → API documentation
```

---

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Account**: Railway deploys from GitHub
3. **Supabase Project**: Already set up ✅
4. **Environment Variables**: Ready from `.env.railway.example`

---

## 🚀 Deployment Steps

### Step 1: Push Code to GitHub

```bash
# Ensure your code is committed
git add .
git commit -m "feat: railway deployment configuration"
git push origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"**
3. Select your repository: `high-yield-dividend-analysis`
4. Railway will detect the project automatically

### Step 3: Configure Deployment Settings

Railway should auto-detect Docker Compose. If not:

1. Click **Settings** → **Deploy**
2. **Build Method**: Docker Compose
3. **Docker Compose File**: `docker-compose.railway.yml`
4. **Port**: Railway auto-detects from nginx (port 80)

### Step 4: Add Environment Variables

Click **Variables** → **Raw Editor** and paste:

```env
# Supabase
SUPABASE_URL=https://uykxgbrzpfswbdxtyzlv.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
NEXT_PUBLIC_SUPABASE_URL=https://uykxgbrzpfswbdxtyzlv.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# API Keys
FMP_API_KEY=your-fmp-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key

# Security
SECRET_KEY=your-secret-key-here
SESSION_SECRET=your-session-secret

# App Settings
ENVIRONMENT=production
ALLOWED_ORIGINS=*
```

**Generate SECRET_KEY:**
```bash
openssl rand -hex 32
```

### Step 5: Deploy

1. Click **Deploy**
2. Watch the build logs (takes 3-5 minutes first time)
3. Railway will assign you a URL: `your-app.railway.app`

### Step 6: Verify Deployment

Test the endpoints:

```bash
# Health check
curl https://your-app.railway.app/health

# API endpoint
curl https://your-app.railway.app/v1/stocks/AAPL/quote

# Frontend
open https://your-app.railway.app
```

---

## 🔧 Post-Deployment Configuration

### 1. Update Supabase CORS

Add Railway URL to allowed origins in Supabase dashboard:
- Settings → API → CORS
- Add: `https://your-app.railway.app`

### 2. Add Custom Domain (Optional)

In Railway:
1. **Settings** → **Domains**
2. Click **Add Domain**
3. Enter your domain: `divv.yourdomain.com`
4. Add CNAME record in your DNS:
   ```
   CNAME divv → your-app.railway.app
   ```

### 3. Enable Metrics (Included Free)

Railway provides built-in metrics:
- CPU usage
- Memory usage
- Network traffic
- Request logs

Access from: **Metrics** tab in Railway dashboard

---

## 💰 Cost Estimation

### Starter Plan ($5/month usage-based)

**Your stack needs:**
- **Backend**: 512MB-1GB RAM (Python + Chrome for scrapers)
- **Frontend**: 256MB RAM (Next.js)
- **Redis**: 128MB RAM
- **Nginx**: 64MB RAM
- **Total**: ~1GB RAM

**Monthly cost:**
```
Base:        Free tier includes $5 credit
RAM usage:   1GB × $0.000231/GB/hour = ~$7/month
CPU usage:   ~$3/month
Total:       ~$10-15/month
```

### Growing Usage
```
2GB RAM:     ~$20/month
4GB RAM:     ~$40/month
8GB RAM:     ~$80/month
```

---

## 🔍 Monitoring & Debugging

### View Logs

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs

# View specific service logs
railway logs backend
railway logs frontend
railway logs nginx
```

### Access Metrics

Railway Dashboard → **Metrics** tab:
- Request volume
- Response times
- Error rates
- Resource usage

### Common Issues

**1. Build fails:**
```bash
# Check Docker Compose syntax
docker-compose -f docker-compose.railway.yml config

# Test locally first
docker-compose -f docker-compose.railway.yml up
```

**2. Service not responding:**
```bash
# Check health endpoint
railway logs nginx

# Verify nginx config
railway run cat /etc/nginx/nginx.conf
```

**3. CORS errors:**
```bash
# Add Railway URL to ALLOWED_ORIGINS
railway variables set ALLOWED_ORIGINS="https://your-app.railway.app"
```

---

## 📈 Scaling

### Vertical Scaling (Increase Resources)

Railway auto-scales memory, but you can set limits:

1. **Settings** → **Resources**
2. Set **Memory Limit**: 1GB → 2GB → 4GB
3. Restart service

### Horizontal Scaling (Multiple Instances)

For high traffic:

1. **Settings** → **Deploy**
2. **Replicas**: 1 → 2 → 3
3. Railway auto-load balances

**Note**: Redis won't work with multiple replicas (needs Redis Cloud or Upstash)

---

## 🔐 Security Checklist

- [ ] SECRET_KEY is randomly generated (not default)
- [ ] SUPABASE_SERVICE_ROLE_KEY is set (for admin operations)
- [ ] ALLOWED_ORIGINS restricts to your domain
- [ ] API keys are in Railway variables (not in code)
- [ ] HTTPS enabled (Railway does this automatically)
- [ ] Rate limiting configured (nginx handles this)

---

## 🎨 Adding Cloudflare CDN (Optional - FREE)

For faster global performance:

### Step 1: Add Site to Cloudflare

1. Go to [cloudflare.com](https://cloudflare.com)
2. Add your domain
3. Update nameservers at your registrar

### Step 2: Configure DNS

In Cloudflare DNS:
```
CNAME  @     your-app.railway.app  (Proxied ☁️)
CNAME  www   your-app.railway.app  (Proxied ☁️)
```

### Step 3: Configure Cache Rules

Cloudflare → **Rules** → **Page Rules**:

```
Pattern: *yourdomain.com/_next/static/*
Settings:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 1 month

Pattern: *yourdomain.com/api/*
Settings:
  - Cache Level: Bypass
```

### Result

- ✅ Global CDN (200+ locations)
- ✅ DDoS protection
- ✅ Free SSL
- ✅ Analytics
- ✅ Cost: $0/month

**Total Stack Cost: $10-15/month Railway + $0 Cloudflare = $10-15/month**

---

## 🔄 CI/CD (Automatic Deployments)

Railway auto-deploys on every `git push`:

1. Push to GitHub: `git push origin main`
2. Railway detects changes
3. Builds new Docker images
4. Zero-downtime deployment
5. Live in ~3-5 minutes

### Deployment Notifications

Railway → **Settings** → **Webhooks**:
- Slack notifications
- Discord webhooks
- Custom webhooks

---

## 📊 Performance Optimization

### 1. Enable Redis Caching

Already configured in `docker-compose.railway.yml` ✅

### 2. Monitor Slow Queries

Check Railway logs for slow database queries:
```bash
railway logs | grep "slow query"
```

### 3. Optimize Images

In Next.js, images are auto-optimized. Ensure you're using:
```jsx
import Image from 'next/image'

<Image src="/logo.png" width={100} height={100} />
```

### 4. Database Connection Pooling

Already configured in FastAPI with Supabase ✅

---

## 🆘 Support & Help

### Railway Support
- [Railway Docs](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- Help button in dashboard

### Debugging Commands

```bash
# SSH into running container (Railway CLI)
railway run bash

# Check service status
railway status

# View environment variables
railway variables

# Restart service
railway up --detach
```

---

## ✅ Deployment Checklist

Before going live:

- [ ] Environment variables set in Railway
- [ ] `.env.railway.example` documented for team
- [ ] Test all API endpoints
- [ ] Test frontend loads correctly
- [ ] Verify Supabase connection works
- [ ] Check health endpoint: `/health`
- [ ] Verify API docs: `/docs`
- [ ] Test rate limiting works
- [ ] Monitor logs for errors
- [ ] Set up custom domain (optional)
- [ ] Add Cloudflare CDN (optional)
- [ ] Configure monitoring/alerts

---

## 🎉 Next Steps

After deployment:

1. **Monitor**: Check Railway metrics daily for first week
2. **Optimize**: Identify slow endpoints and optimize
3. **Scale**: Increase resources as traffic grows
4. **Backup**: Supabase handles backups automatically
5. **Marketing**: Share your API! 🚀

---

**Deployed with ❤️ on Railway**

Questions? Check the Railway docs or your deployment logs.
