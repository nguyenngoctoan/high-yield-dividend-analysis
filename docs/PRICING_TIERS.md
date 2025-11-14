# Divv API Pricing Tiers & Implementation Plan

## Overview
This document outlines the pricing tier structure for the Divv API. Our pricing is designed to be **significantly more affordable** than competitors (Alpha Vantage, Polygon, Finnhub) while providing specialized dividend-focused features they don't offer.

## Competitive Positioning

### How We Compare to Competition

| Provider | Entry Price | Free Tier | Dividend Data Quality |
|----------|-------------|-----------|---------------------|
| **Divv API** | **$9/mo** | **10,000/mo** | **Specialized & Comprehensive** |
| Alpha Vantage | $49.99/mo | 25/day | Generic |
| Polygon (Massive) | $199/mo | 5/min | Limited, unreliable |
| Finnhub | $50/mo/market | 60/min (no dividends) | Requires paid plan |
| FMP | $22/mo | 250/day | Generic |

**Result: We're 2-20x cheaper with better dividend data!**

---

## Pricing Tiers Comparison

| Feature | Free | Starter | Premium | Professional | Enterprise |
|---------|------|---------|---------|--------------|------------|
| **Price** | $0 | $9/mo | $29/mo | $79/mo | Custom |
| **Monthly Calls** | 10,000 | 50,000 | 250,000 | 1,000,000 | Unlimited |
| **Per-Minute Limit** | 10/min | 30/min | 100/min | 300/min | 1,000+/min |
| **Daily Equivalent** | ~333/day | ~1,667/day | ~8,333/day | ~33,333/day | Unlimited |
| **Stock Coverage** | Sample (150) | US only | US+Intl | Global | Global+ |
| **Historical Data** | 1 year | 5 years | 30+ years | Full | Full |
| **Price Data** | EOD only | EOD + Hourly | 15-min | 1-min | Real-time |
| **Support** | Community | Email | Priority | 4hr SLA | Dedicated AM |
| **Portfolios** | 0 | 1 | 3 | Unlimited | Unlimited |

## Tier-Specific Features

### Free Tier
**Target Audience:** Hobbyists, students, personal projects
**Price:** $0/month

**Limits:**
- 10,000 API calls per month (~333/day)
- 10 calls per minute
- Burst: 20 calls (for 10 seconds)

**Included:**
- Sample dataset: 150 curated dividend stocks
  - Dividend Aristocrats (68 stocks)
  - Dividend Kings (32 stocks)
  - Top yielders (50 stocks, >4% yield, $1B+ market cap)
- 1-year dividend history
- End-of-day prices only
- Basic endpoints:
  - `/v1/search` - Search stocks
  - `/v1/dividends/calendar` - Upcoming dividends (limited to sample)
  - `/v1/dividends/history` - Historical dividends (1 year)
  - `/v1/stocks/{symbol}/dividends` - Stock dividend summary
  - `/v1/prices/{symbol}/latest` - Latest price

**Limitations:**
- No bulk exports
- No webhooks
- Community support only (Discord/GitHub)
- Response includes `X-Tier: free` header

**Perfect for:** Tracking 20-50 stocks, learning the API, building proof-of-concepts

---

### Starter Tier ($9/month)
**Target Audience:** Individual investors, small apps, bloggers, indie developers
**Price:** $9/month or $90/year (save $18)

**Why it's a steal:** 5x cheaper than Alpha Vantage, 2.4x cheaper than FMP

**Limits:**
- 50,000 API calls per month (~1,667/day)
- 30 calls per minute
- Burst: 60 calls

**Included:**
- All US dividend-paying stocks (~3,000 stocks)
- 5 years dividend history
- Hourly + EOD price data
- All Free tier endpoints plus:
  - `/v1/screeners/high-yield` - High-yield dividend screener
  - `/v1/screeners/monthly-payers` - Monthly dividend payers
  - `/v1/analytics/yield-analysis` - Dividend yield analytics
  - CSV export capability
  - Bulk endpoints (up to 50 symbols per call)

**Features:**
- Email support (48hr response time)
- 1 portfolio tracking (up to 100 stocks)
- Daily dividend alerts (email)
- Basic API analytics dashboard
- Caching recommendations

**Perfect for:** Small apps, bloggers tracking 100-200 stocks, financial advisors starting out

---

### Premium Tier ($29/month)
**Target Audience:** Active investors, fintech apps, financial bloggers, advisory firms
**Price:** $29/month or $299/year (save $49)

**Why it's a steal:** 40% cheaper than Alpha Vantage, 72% cheaper than Finnhub

**Limits:**
- 250,000 API calls per month (~8,333/day)
- 100 calls per minute
- Burst: 200 calls

**Included:**
- US + International stocks (~4,600 stocks)
  - US, Canada, UK, Germany, France, Australia
- Full historical dividend data (30+ years)
- 15-minute intraday price data
- All Starter tier endpoints plus:
  - `/v1/screeners/dividend-aristocrats` - Dividend aristocrats
  - `/v1/screeners/dividend-achievers` - Dividend achievers
  - `/v1/analytics/growth-rates` - Dividend growth analysis
  - `/v1/analytics/sustainability` - Dividend sustainability scores
  - `/v1/dividends/forecast` - AI-powered dividend forecasts
  - `/v1/etfs/{symbol}` - ETF dividend data
  - Bulk endpoints (up to 200 symbols per call)
  - Bulk export (JSON, CSV, Excel)

**Features:**
- Priority support (24hr response SLA)
- 3 portfolio tracking (up to 500 stocks each)
- Webhook notifications (dividend announcements, ex-dates)
- Advanced filtering & custom date ranges
- API usage analytics & insights
- Dedicated onboarding session (30 min)
- Historical data downloads

**Perfect for:** Platforms with 1,000+ users, fintech apps, investment newsletters

---

### Professional Tier ($79/month)
**Target Audience:** Financial advisors, fund managers, institutions, platforms
**Price:** $79/month or $799/year (save $149)

**Why it's a steal:** 60% cheaper than Polygon ($199), 47% cheaper than FMP Ultimate

**Limits:**
- 1,000,000 API calls per month (~33,333/day)
- 300 calls per minute
- Burst: 600 calls

**Included:**
- Global dividend stocks (8,000+ stocks, 30+ countries)
- Real-time dividend announcements (push notifications)
- 1-minute intraday price data
- All Premium tier endpoints plus:
  - `/v1/etfs/{symbol}/holdings` - ETF holdings & dividend contribution
  - `/v1/analytics/portfolio` - Full portfolio analysis (risk, diversification)
  - `/v1/analytics/tax` - Tax withholding rates by country
  - `/v1/analytics/forecasting` - ML-powered dividend forecasting
  - `/v1/dividends/special` - Special dividends & return of capital
  - `/v1/screeners/custom` - Custom screener builder (save & share)
  - `/v1/stocks/bulk` - Bulk endpoints (up to 1,000 symbols per call)
  - Bulk delivery (FTP, S3, Snowflake)

**Features:**
- Dedicated support (4hr response SLA, Slack channel)
- Unlimited portfolios (unlimited stocks)
- Real-time webhook notifications
- White-label API options (rebrand for clients)
- Custom report generation
- Historical data backfills on request
- SSO integration (SAML, OAuth)
- 99.5% uptime SLA
- Quarterly business review

**Perfect for:** Large platforms, RIAs managing $100M+, fund managers, institutional investors

---

### Enterprise Tier (Custom Pricing)
**Target Audience:** Large institutions, data vendors, platforms

**Included:**
- Custom rate limits (10,000+ calls/min)
- Full global coverage + alternative assets
- Real-time WebSocket feeds
- Custom data delivery schedules
- All Professional tier endpoints plus:
  - Custom endpoint development
  - Private data feeds
  - On-premise deployment options
  - Direct database access

**Features:**
- Dedicated account manager
- Custom SLA (up to 99.9% uptime)
- Priority feature development
- Training & workshops
- Integration consulting
- Volume-based pricing
- Multi-region deployment
- Audit logs & compliance reports

---

## Rate Limiting Structure

### Monthly + Per-Minute Limits (Dual Protection)
We use BOTH monthly and per-minute limits to ensure fair usage:

```
Free:         10,000/month,  10/minute  (burst: 20)
Starter:      50,000/month,  30/minute  (burst: 60)
Premium:     250,000/month, 100/minute  (burst: 200)
Professional: 1M/month,     300/minute  (burst: 600)
Enterprise:   Unlimited,   1,000+/min   (custom burst)
```

### Why This Matters for Dividend Data
Unlike real-time APIs that need constant polling, dividend data changes slowly:
- **Initial backfill**: Fetch historical data once (100-500 calls)
- **Daily sync**: Check for updates once daily (10-50 calls)
- **Screening**: Run dividend screens periodically (50-200 calls)
- **Portfolio tracking**: Update holdings daily (10-100 calls)

**Result**: Most users will use 1,000-5,000 calls/month, well within limits!

### Burst Allowance
Each tier gets burst allowance for traffic spikes (e.g., user batch operations):
- **Free**: 20 calls for 10 seconds
- **Starter**: 60 calls for 10 seconds
- **Premium**: 200 calls for 10 seconds
- **Professional**: 600 calls for 10 seconds

### Response Headers
Every API response includes rate limit info:
```http
X-RateLimit-Limit-Month: 50000
X-RateLimit-Remaining-Month: 48756
X-RateLimit-Reset-Month: 1638360000
X-RateLimit-Limit-Minute: 30
X-RateLimit-Remaining-Minute: 28
X-RateLimit-Reset-Minute: 1638356460
X-RateLimit-Tier: starter
```

---

## Stock Coverage by Tier

### Free Tier Sample Dataset (150 stocks)
- Dividend Aristocrats: 68 stocks
- Dividend Kings: 32 stocks
- Top yielders: 50 stocks (>4% yield, market cap > $1B)

### Starter Tier
- All US dividend-paying stocks: ~3,000 stocks
- Minimum criteria: Paid dividend in last 12 months

### Premium Tier
- US: ~3,000 stocks
- Canada (TSX): ~400 stocks
- UK (LSE): ~500 stocks
- Germany (XETRA): ~200 stocks
- France (Euronext): ~200 stocks
- Australia (ASX): ~300 stocks
- **Total: ~4,600 stocks**

### Professional Tier
- All Premium tier stocks
- Additional coverage:
  - Japan, Hong Kong, Singapore
  - Switzerland, Netherlands, Spain, Italy
  - REITs and MLPs (US & International)
  - ADRs
- **Total: ~8,000+ stocks**

### Enterprise Tier
- Full global coverage (30+ exchanges)
- Custom stock lists
- Private company data (available on request)

---

## Implementation Checklist

### Phase 1: Database Updates
- [ ] Update `divv_api_keys.tier` to include: 'free', 'starter', 'premium', 'professional', 'enterprise'
- [ ] Add `stock_coverage` JSONB column to track accessible symbols per tier
- [ ] Create `tier_limits` table to store rate limits and feature flags
- [ ] Add `bandwidth_usage` tracking for 30-day rolling limits

### Phase 2: Rate Limiting
- [ ] Implement sliding window rate limiter
- [ ] Add burst allowance logic
- [ ] Create rate limit middleware
- [ ] Add rate limit headers to all responses

### Phase 3: Feature Gating
- [ ] Create feature flag system per tier
- [ ] Implement stock coverage filters
- [ ] Add data retention limits (1yr, 5yr, full)
- [ ] Gate intraday data by tier

### Phase 4: Billing Integration
- [ ] Integrate Stripe for payment processing
- [ ] Create subscription management UI
- [ ] Build upgrade/downgrade flows
- [ ] Implement usage-based overage pricing (optional)

### Phase 5: Documentation & Marketing
- [ ] Update pricing page on docs site
- [ ] Create tier comparison widget
- [ ] Add tier badges to dashboard
- [ ] Build ROI calculator for each tier

---

## Competitive Positioning

### vs. Financial Modeling Prep
- **Lower prices** for comparable tiers ($19 vs $22, $49 vs $59)
- **Dividend-focused** dataset (curated, not general market)
- **Better support** for international dividends
- **Specialized features** (tax withholding, yield forecasting)

### vs. Alpha Vantage
- **More generous free tier** (250/day vs 25/day)
- **Better pricing** on paid tiers
- **Specialized dividend data** (not available in Alpha Vantage)

### vs. Polygon.io
- **More affordable** for dividend-specific use cases
- **Better dividend metadata** (sustainability scores, forecasts)
- **Simpler pricing** (no data credits system)

---

## Revenue Projections

### Year 1 Conservative Estimates (5% conversion)
```
Free users: 5,000
Paying users: 250 (5% conversion)

Tier breakdown:
- Starter (60%):      150 × $9   = $1,350/mo
- Premium (30%):       75 × $29  = $2,175/mo
- Professional (10%):  25 × $79  = $1,975/mo
- Enterprise:           0 × $499 = $0/mo

Total MRR: $5,500
Total ARR: $66,000
```

**Customer Acquisition Cost (CAC) assumptions:**
- Organic (SEO, content): $0-10 per signup
- Target CAC: < $20 (paid at 3:1 LTV:CAC ratio)
- Payback period: 3-4 months

### Year 2 Growth Targets (10x users, 7% conversion)
```
Free users: 50,000
Paying users: 3,500 (7% conversion - improved onboarding)

Tier breakdown:
- Starter (50%):        1,750 × $9   = $15,750/mo
- Premium (35%):        1,225 × $29  = $35,525/mo
- Professional (14%):     490 × $79  = $38,710/mo
- Enterprise (1%):         35 × $499 = $17,465/mo

Total MRR: $107,450
Total ARR: $1,289,400
```

### Year 3 Targets (Platform maturity)
```
Free users: 200,000
Paying users: 18,000 (9% conversion)

Tier breakdown:
- Starter (40%):        7,200 × $9   = $64,800/mo
- Premium (40%):        7,200 × $29  = $208,800/mo
- Professional (18%):   3,240 × $79  = $255,960/mo
- Enterprise (2%):        360 × $750 = $270,000/mo

Total MRR: $799,560
Total ARR: $9,594,720
```

**Key Growth Drivers:**
1. Superior free tier → high signup rate
2. Aggressive pricing → high conversion rate
3. Specialized features → low churn (<5% monthly)
4. Developer-friendly → strong word-of-mouth

---

## Next Steps

1. **Finalize tier definitions** - Review and approve tier structure
2. **Update database schema** - Migrate existing keys to new tier system
3. **Implement rate limiting** - Build robust rate limiter with burst support
4. **Build pricing page** - Create compelling pricing comparison page
5. **Set up Stripe** - Configure subscription products and webhooks
6. **Create upgrade flows** - Build smooth tier upgrade experience
7. **Launch beta** - Soft launch to existing users for feedback
8. **Marketing campaign** - Announce new pricing tiers

---

**Last Updated:** 2025-11-14
**Author:** Toan Nguyen
**Status:** Draft - Pending Approval
