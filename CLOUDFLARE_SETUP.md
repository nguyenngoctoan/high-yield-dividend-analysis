# Cloudflare CDN Setup for Divv API

Add a free global CDN to your Railway deployment for faster performance worldwide.

## 🎯 Why Cloudflare?

- ✅ **FREE tier** with generous limits
- ✅ **200+ global locations** for fast content delivery
- ✅ **DDoS protection** included
- ✅ **Free SSL certificates**
- ✅ **Analytics dashboard**
- ✅ **Caching for static assets**
- ✅ **Works seamlessly with Railway**

---

## 📋 Prerequisites

1. Custom domain (e.g., `divv.yourdomain.com` or `yourdomain.com`)
2. Access to domain registrar (GoDaddy, Namecheap, etc.)
3. Railway app deployed and working

---

## 🚀 Setup Steps

### Step 1: Add Site to Cloudflare

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com)
2. Click **Add a Site**
3. Enter your domain: `yourdomain.com`
4. Select **Free plan**
5. Click **Continue**

### Step 2: Update Nameservers

Cloudflare will show you 2 nameservers like:
```
ns1.cloudflare.com
ns2.cloudflare.com
```

**At your domain registrar:**
1. Go to DNS settings
2. Replace existing nameservers with Cloudflare's
3. Save changes

**Wait 5-60 minutes** for DNS propagation.

### Step 3: Configure DNS Records

In Cloudflare DNS settings:

**For root domain:**
```
Type:  CNAME
Name:  @
Target: your-app.railway.app
Proxy:  ☁️ Proxied (orange cloud)
```

**For www subdomain:**
```
Type:  CNAME
Name:  www
Target: your-app.railway.app
Proxy:  ☁️ Proxied (orange cloud)
```

**For API subdomain (optional):**
```
Type:  CNAME
Name:  api
Target: your-app.railway.app
Proxy:  ☁️ Proxied (orange cloud)
```

---

## ⚙️ Optimize Caching Rules

### Cache Static Assets

**Cloudflare Dashboard** → **Rules** → **Page Rules**

#### Rule 1: Cache Next.js Static Files
```
URL Pattern: *yourdomain.com/_next/static/*

Settings:
  ✅ Cache Level: Cache Everything
  ✅ Edge Cache TTL: 1 month
  ✅ Browser Cache TTL: 1 year
```

#### Rule 2: Cache Images
```
URL Pattern: *yourdomain.com/_next/image*

Settings:
  ✅ Cache Level: Cache Everything
  ✅ Edge Cache TTL: 7 days
```

#### Rule 3: Bypass Cache for API
```
URL Pattern: *yourdomain.com/api/*

Settings:
  ✅ Cache Level: Bypass
```

#### Rule 4: Bypass Cache for API v1
```
URL Pattern: *yourdomain.com/v1/*

Settings:
  ✅ Cache Level: Bypass
```

**Free tier includes 3 page rules**, so prioritize:
1. Static files caching
2. API bypass
3. Image caching (if you have 3 rules)

---

## 🔒 Security Settings

### SSL/TLS Configuration

**Cloudflare** → **SSL/TLS** → **Overview**

Select: **Full (strict)**

This ensures end-to-end encryption:
- Browser ← HTTPS → Cloudflare ← HTTPS → Railway

### Enable Security Features

**Cloudflare** → **Security** → **Settings**

- ✅ **Security Level**: Medium
- ✅ **Challenge Passage**: 30 minutes
- ✅ **Browser Integrity Check**: On
- ✅ **Always Use HTTPS**: On

### Bot Protection

**Cloudflare** → **Security** → **Bots**

- ✅ **Bot Fight Mode**: On (Free tier)

---

## 🚀 Performance Optimization

### Auto Minify

**Cloudflare** → **Speed** → **Optimization**

Enable:
- ✅ Auto Minify JavaScript
- ✅ Auto Minify CSS
- ✅ Auto Minify HTML

### Brotli Compression

**Speed** → **Optimization**
- ✅ Brotli: On (better than gzip)

### Early Hints

**Speed** → **Optimization**
- ✅ Early Hints: On (faster page loads)

---

## 📊 Analytics & Monitoring

### View Traffic Analytics

**Cloudflare Dashboard** → **Analytics & Logs** → **Traffic**

Monitor:
- Total requests
- Cached vs uncached ratio
- Bandwidth saved
- Top countries
- Threat analytics

### Performance Insights

**Speed** → **Performance**

Check:
- Time to First Byte (TTFB)
- Page load times
- Cache hit ratio (aim for >80% for static assets)

---

## 🎨 Custom Error Pages (Optional)

**Cloudflare** → **Custom Pages**

Customize error pages for:
- 500 errors (server down)
- 1000 errors (DNS issues)
- Always Online mode

---

## 🔧 Advanced Configuration

### Transform Rules (Pro plan+)

Modify headers, URLs, and responses on the fly.

**Free alternative:** Use nginx config in your Railway deployment

### Rate Limiting

**Security** → **WAF** → **Rate Limiting Rules**

Example:
```
Rule: API Rate Limit
If: URL Path contains "/v1/"
Then: Block when > 60 requests/minute
```

**Cost:** $0.05 per 10,000 requests above free tier

---

## ✅ Verification

### 1. Check DNS Propagation

```bash
# Check if Cloudflare is working
dig yourdomain.com

# Should show Cloudflare IPs (104.x.x.x or 172.x.x.x)
```

### 2. Test CDN Caching

```bash
# Check response headers
curl -I https://yourdomain.com/_next/static/chunks/main.js

# Look for:
# cf-cache-status: HIT (cached by Cloudflare)
# cf-ray: xxx-YYY (Cloudflare serving)
```

### 3. Verify SSL

```bash
# Check SSL certificate
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Should show Cloudflare's certificate
```

---

## 🎯 Expected Performance Gains

### Before Cloudflare
- TTFB: 200-500ms (depending on user location)
- Static asset load: Direct from Railway
- Bandwidth: All from Railway

### After Cloudflare
- TTFB: 50-150ms (CDN edge locations)
- Static asset load: From nearest Cloudflare POP
- Bandwidth saved: 60-80% (cached at edge)
- DDoS protection: Automatic

---

## 💰 Cost

**Cloudflare Free Tier Includes:**
- Unlimited bandwidth
- Global CDN
- DDoS protection
- Free SSL certificates
- 3 page rules
- Basic analytics
- **Cost: $0/month**

**Railway + Cloudflare Total:**
- Railway: $10-15/month
- Cloudflare: $0/month
- **Total: $10-15/month** for global, fast, secure API

---

## 🔄 Update Railway Environment

After setting up Cloudflare, update Railway variables:

```bash
railway variables set ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

---

## 🆘 Troubleshooting

### 1. "Too Many Redirects" Error

**Cause:** SSL mode mismatch

**Fix:** Cloudflare → SSL/TLS → Change to **Full (strict)**

### 2. Cache Not Working

**Check:**
```bash
curl -I https://yourdomain.com/_next/static/main.js
```

Look for `cf-cache-status: MISS` → wait a few requests, should become `HIT`

### 3. API Requests Cached (shouldn't be)

**Fix:** Ensure page rule exists:
```
*yourdomain.com/api/*
Cache Level: Bypass
```

### 4. Orange Cloud vs Gray Cloud

- **Orange ☁️**: Traffic routed through Cloudflare (CDN + protection)
- **Gray ☁️**: Direct to Railway (no caching)

For best performance: Keep orange cloud enabled

---

## 📈 Monitoring

### Weekly Checks

1. **Cache Hit Ratio**: Should be >70% for static assets
2. **Bandwidth Saved**: Should be >50%
3. **Security Threats Blocked**: Review blocked threats
4. **Top Countries**: See where users are from

### Set Up Alerts (Pro plan)

Or use free webhooks:
- Downtime notifications
- Traffic spike alerts
- Security threat alerts

---

## 🎉 Done!

Your Divv API is now:
- ✅ Globally distributed (200+ locations)
- ✅ Protected from DDoS
- ✅ Faster for all users
- ✅ Cost: $0 extra

**Next:** Monitor analytics and optimize based on real traffic patterns.

---

**Questions?** Check [Cloudflare's documentation](https://developers.cloudflare.com/) or Railway's [custom domain guide](https://docs.railway.app/deploy/exposing-your-app#custom-domains).
