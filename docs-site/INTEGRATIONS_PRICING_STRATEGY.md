# Integrations & Pricing Strategy

**Date**: 2025-11-14

---

## How Integrations Tie Into Pricing

### **Key Principle**: Integrations use the same API, so they follow the same pricing tiers.

---

## Pricing Tiers Applied to Integrations

### **Free Tier - $0/month**
- **10,000 API calls/month**
- **10 calls/minute**
- **Attributes**: Price, Open, High, Low, Dividend Yield, Dividend Amount
- **Perfect for**: Testing the DIVV() function, small portfolios (10-20 stocks)

**Example Google Sheets Usage**:
```javascript
// Track 15 stocks, updated daily
=DIVV("AAPL", "price")          // ✅ Free tier
=DIVV("MSFT", "dividendYield")  // ✅ Free tier
=DIVV("JNJ", "dayHigh")         // ✅ Free tier
... 15 stocks total

// Calculation:
// 15 stocks × 30 days = 450 calls/month
// Well within 10,000 limit ✅
```

**What you can do**:
- ✅ Track stock prices (current, open, high, low)
- ✅ Monitor dividend yields
- ✅ Small dividend portfolio tracker (15-20 stocks)
- ✅ Manual refresh (not auto-updating)
- ✅ Learning and testing
- ❌ Advanced metrics (PE ratio, volume, market cap, etc.)
- ❌ Dividend history (DIVVDIVIDENDS)
- ❌ Aristocrat detection (DIVVARISTOCRAT)
- ❌ Real-time auto-refresh
- ❌ Large portfolios (100+ stocks)

---

### **Starter Tier - $9/month**
- **50,000 API calls/month**
- **30 calls/minute**
- **Attributes**: All stock attributes (price, PE ratio, volume, market cap, etc.)
- **Advanced Functions**: DIVVDIVIDENDS(), DIVVARISTOCRAT()
- **Perfect for**: Personal portfolio tracking, auto-updating sheets

**Example Google Sheets Usage**:
```javascript
// Track 50 stocks, auto-refresh every 5 minutes during market hours
=DIVV("AAPL", "price")
=DIVV("AAPL", "peRatio")        // ✅ Paid tier only
=DIVV("AAPL", "marketCap")      // ✅ Paid tier only
=DIVVDIVIDENDS("AAPL", 12)      // ✅ Paid tier only
... 50 stocks

// Calculation:
// 50 stocks × 78 refreshes/day (every 5 min, 6.5 hours) × 22 trading days
// = 85,800 calls/month (with caching: ~17,000)
// With 5-min cache: Well within 50,000 ✅
```

**What you can do**:
- ✅ All stock attributes (PE, volume, market cap, etc.)
- ✅ Portfolio tracker with auto-refresh
- ✅ Dividend dashboard with 50-100 stocks
- ✅ DIVVDIVIDENDS() for dividend history
- ✅ DIVVARISTOCRAT() checks
- ❌ Real-time tick data
- ❌ Multiple large sheets

---

### **Premium Tier - $29/month**
- **250,000 API calls/month**
- **100 calls/minute**
- **Perfect for**: Power users, multiple sheets, shared templates

**Example Usage**:
```javascript
// Multiple Google Sheets:
// - Personal portfolio: 100 stocks
// - Dividend Aristocrats screener: 65 stocks
// - Monthly payers tracker: 40 stocks
// - Family portfolios: 3 × 30 stocks
// Total: 295 unique symbols

// With caching and smart refresh: ~50,000 calls/month ✅
```

**What you can do**:
- ✅ Multiple sophisticated dashboards
- ✅ Shared templates for family/team
- ✅ Bulk operations (DIVVBULK)
- ✅ Full dividend history for 100+ stocks
- ❌ Commercial redistribution

---

### **Professional Tier - $79/month**
- **1M API calls/month**
- **300 calls/minute**
- **Perfect for**: Financial advisors, content creators, commercial use

**Example Usage**:
```javascript
// Financial advisor with:
// - 20 client portfolios (avg 40 stocks each) = 800 stocks
// - Research sheet: 200 stocks
// - Screeners: 500+ stocks
// - Public templates shared with clients

// Auto-refresh every 15 min: ~400,000 calls/month ✅
```

**What you can do**:
- ✅ Commercial use of templates
- ✅ Client-facing dashboards
- ✅ Content creation (YouTube, courses)
- ✅ White-label solutions
- ✅ Priority support

---

## Smart Usage Tips for Integrations

### **Maximize Free Tier**:
1. **Use caching** (5-min default) - reduces calls by 90%+
2. **Manual refresh** instead of auto-refresh
3. **Track 15-20 stocks** max
4. **Use DIVVBULK()** for efficiency

### **Optimize Starter Tier**:
1. **Increase cache to 15 minutes** (edit script)
2. **Refresh during market hours only**
3. **Use DIVVDIVIDENDS()** sparingly (cached separately)
4. **Batch updates** instead of real-time

### **Best Practices for All Tiers**:
```javascript
// ✅ GOOD: Efficient bulk fetch
=DIVVBULK(A2:A50, "price")  // 1 call for all

// ❌ BAD: Individual calls
=DIVV(A2, "price")
=DIVV(A3, "price")
=DIVV(A4, "price")
// ... 50 individual calls
```

---

## API Key Configuration

### **Adding API Key to Scripts**:

**Google Sheets** (`DIVV.gs`):
```javascript
// Line 45: Add your API key
const API_KEY = 'your-api-key-here';

// Get your API key at:
// https://divv.com/api-keys
```

**Excel** (`DIVV.bas`):
```vba
' Line 27: Add your API key
Const API_KEY As String = "your-api-key-here"
```

### **How to Get API Key**:
1. Visit `/api-keys` page
2. Sign in with Google
3. Create new API key
4. Copy and paste into script
5. Save and refresh

---

## Rate Limiting Behavior

### **What Happens When You Hit Limits**:

**Free Tier (10 calls/min)**:
```javascript
// If you make 11 calls in 1 minute:
// Call 1-10: ✅ Success
// Call 11: ⏸️ Automatic retry after 1 second
// Call 12: ⏸️ Automatic retry (exponential backoff)
// Call 13: ❌ #ERROR: Rate limit exceeded
```

**Script Behavior**:
- Built-in retry logic (3 attempts)
- Exponential backoff (1s, 2s, 4s)
- Graceful error messages
- Suggests upgrading plan

---

## Cost Analysis for Common Use Cases

### **Use Case 1: Personal Portfolio Tracker**
- **Setup**: 30 stocks, manual refresh daily
- **Calls/month**: 30 × 30 = 900
- **Recommended Tier**: Free ($0/mo) ✅
- **Savings vs. competitors**: N/A (free)

### **Use Case 2: Auto-Updating Dashboard**
- **Setup**: 50 stocks, refresh every 15 min (market hours)
- **Calls/month**: 50 × 26 × 22 = 28,600 (with cache: ~5,000)
- **Recommended Tier**: Starter ($9/mo) ✅
- **Savings vs. Alpha Vantage**: $40.99/mo (82% cheaper)

### **Use Case 3: Financial Advisor**
- **Setup**: 500 stocks across 15 clients, hourly refresh
- **Calls/month**: ~300,000 (with caching)
- **Recommended Tier**: Premium ($29/mo) ✅
- **Savings vs. Polygon**: $170/mo (85% cheaper)

### **Use Case 4: Content Creator**
- **Setup**: Public templates, multiple sheets, 1000+ stocks
- **Calls/month**: ~800,000
- **Recommended Tier**: Professional ($79/mo) ✅
- **Savings vs. competitors**: $120-300/mo (60-80% cheaper)

---

## Upgrade Triggers

### **You Should Upgrade When**:

**Free → Starter**:
- ❌ Hitting 10,000 calls/month
- ❌ Getting rate limit errors
- ❌ Want auto-refresh capability
- ❌ Need more than 150 stocks

**Starter → Premium**:
- ❌ Hitting 50,000 calls/month
- ❌ Managing multiple portfolios
- ❌ Need faster refresh rates
- ❌ Want bulk operations

**Premium → Professional**:
- ❌ Commercial use required
- ❌ Client-facing applications
- ❌ Need white-label capabilities
- ❌ Require priority support

---

## Integration-Specific Pricing Features

### **Included in All Tiers**:
✅ Google Sheets script (DIVV.gs)
✅ Excel VBA module (DIVV.bas)
✅ Automatic caching (5 min default)
✅ Retry logic with backoff
✅ Error handling
✅ GOOGLEFINANCE() parity

### **Premium Features** (Premium+ tiers):
✅ Higher refresh rates (every 5-15 min)
✅ Bulk operations (200-1000 symbols)
✅ Priority API queue
✅ Webhooks for updates (coming soon)
✅ Custom screeners
✅ Commercial use license

### **Professional Features** (Professional tier):
✅ White-label templates
✅ Dedicated support (4hr SLA)
✅ Custom endpoints
✅ On-premise deployment option
✅ Bulk data exports

---

## Recommendations by User Type

### **Individual Investor**:
- **Portfolio Size**: 10-50 stocks
- **Recommended Tier**: Free → Starter
- **Cost**: $0-9/month
- **Features Needed**: Basic DIVV(), manual/auto refresh

### **Active Trader**:
- **Portfolio Size**: 50-200 stocks
- **Recommended Tier**: Starter → Premium
- **Cost**: $9-29/month
- **Features Needed**: Auto-refresh, bulk ops, dividend history

### **Financial Advisor**:
- **Portfolio Size**: 500+ stocks (multi-client)
- **Recommended Tier**: Premium → Professional
- **Cost**: $29-79/month
- **Features Needed**: Commercial license, white-label, support

### **Content Creator / Educator**:
- **Portfolio Size**: Variable, public templates
- **Recommended Tier**: Professional
- **Cost**: $79/month
- **Features Needed**: Commercial use, white-label, sharing

---

## Transparent Cost Comparison

### **Divv API + Google Sheets vs. Competitors**:

| Provider | Entry Cost | Free Tier | Sheets Integration | Dividend Quality |
|----------|-----------|-----------|-------------------|------------------|
| **Divv** | **$9/mo** | **10K/mo** | **✅ Native DIVV()** | **⭐⭐⭐⭐⭐** |
| Alpha Vantage | $49.99/mo | 25/day | ❌ Manual | ⭐⭐ |
| Polygon | $199/mo | 5/min | ❌ Manual | ⭐⭐ |
| Finnhub | $50/mo | 60/min* | ❌ Manual | ⭐⭐⭐ |

*No dividends in free tier

**Divv Advantage**:
- 5-20x cheaper ✅
- Native spreadsheet functions ✅
- Superior dividend data ✅
- Built for income investors ✅

---

## Future Pricing Enhancements

### **Coming Soon**:
1. **Team Plans** - Share API key across 5-10 users
2. **Educational Discounts** - 50% off for students/educators
3. **Annual Billing** - 2 months free (17% discount)
4. **Usage-Based Pricing** - Pay only for what you use
5. **Add-ons** - Historical data packs, real-time streaming

---

## Attribute Access by Tier

### **Free Tier Attributes**:
✅ `price` - Current stock price
✅ `open` - Opening price
✅ `dayHigh` - Day's high price
✅ `dayLow` - Day's low price
✅ `previousClose` - Previous close
✅ `dividendYield` - Current dividend yield %
✅ `dividendAmount` - Annual dividend per share

### **Paid Tier Attributes** (Starter+):
✅ All free tier attributes, PLUS:
✅ `peRatio` - Price-to-earnings ratio
✅ `marketCap` - Market capitalization
✅ `volume` - Trading volume
✅ `eps` - Earnings per share
✅ `yearHigh` / `yearLow` - 52-week range
✅ `change` / `changePercent` - Price changes
✅ `priceAvg50` / `priceAvg200` - Moving averages
✅ `sharesOutstanding` - Total shares
✅ `avgVolume` - Average volume
✅ And 20+ more attributes

### **Advanced Functions** (Starter+):
✅ `DIVVDIVIDENDS(symbol, limit)` - Dividend history
✅ `DIVVARISTOCRAT(symbol)` - Aristocrat detection
✅ `DIVVBULK(symbols, attribute)` - Bulk operations

### **How It Works**:
When using the free tier, attempting to access restricted attributes will return:
```
#UPGRADE: This attribute requires a paid plan. Visit divv.com/pricing
```

Simply change `ACCOUNT_TIER = 'free'` to `ACCOUNT_TIER = 'paid'` in the script after upgrading.

---

## Summary

**Integrations + Pricing Model**:
- ✅ Same API, same pricing
- ✅ Free tier: price & dividend yield
- ✅ Paid tiers: all attributes + advanced functions
- ✅ Transparent usage tracking
- ✅ Built-in caching reduces costs
- ✅ Smart retry logic prevents waste
- ✅ Clear upgrade paths
- ✅ 5-20x cheaper than competitors

**Key Message**: "Track prices & dividends for free, upgrade for advanced metrics"

