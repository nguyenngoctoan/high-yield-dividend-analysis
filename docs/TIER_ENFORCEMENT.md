# Tier Enforcement System

## Overview

The tier enforcement system restricts API access based on the user's pricing tier. It controls:
- **Stock Coverage**: Which symbols are accessible
- **Features**: Which API features are available
- **Bulk Limits**: How many symbols can be requested at once
- **Historical Data**: How many years of data are accessible
- **Price Frequency**: EOD vs hourly vs real-time data

## Architecture

### TierEnforcer Class

Located in `api/middleware/tier_enforcer.py`, the `TierEnforcer` class provides:

1. **Symbol Access Control**
   - Free tier: 150 curated stocks only
   - Starter tier: US stocks only (~3,000)
   - Premium tier: US + International (~4,600)
   - Professional/Enterprise: All stocks globally

2. **Feature Gating**
   - `bulk_export`: CSV/Excel downloads
   - `webhooks`: Real-time notifications
   - `custom_screeners`: Save custom screens
   - `intraday_data`: Hourly/minute prices
   - `portfolio_tracking`: Number of portfolios

3. **Bulk Request Limits**
   - Free: 0 (no bulk requests)
   - Starter: 50 symbols per request
   - Premium: 200 symbols per request
   - Professional: 1,000 symbols per request
   - Enterprise: Unlimited

## Usage Examples

### 1. Check Symbol Access

```python
from api.middleware.tier_enforcer import TierEnforcer

# Check if symbol is accessible
accessible = await TierEnforcer.check_symbol_access('starter', 'AAPL')
# Returns: True (AAPL is US stock)

accessible = await TierEnforcer.check_symbol_access('starter', 'TD.TO')
# Returns: False (TD.TO is Canadian stock, requires Premium)

accessible = await TierEnforcer.check_symbol_access('free', 'MSFT')
# Returns: False (MSFT not in free tier sample dataset)
```

### 2. Check Feature Access

```python
# Check if bulk export is available
can_export = await TierEnforcer.check_feature_access('starter', 'bulk_export')
# Returns: True

# Check if webhooks are available
has_webhooks = await TierEnforcer.check_feature_access('free', 'webhooks')
# Returns: False

# Check if intraday data is available
has_intraday = await TierEnforcer.check_feature_access('premium', 'intraday_data')
# Returns: True (Premium has 15-min data)
```

### 3. Filter Accessible Symbols

```python
symbols = ['AAPL', 'MSFT', 'TD.TO', 'SHOP.TO', 'GOOGL']

# Filter for free tier
accessible = await TierEnforcer.filter_accessible_symbols('free', symbols)
# Returns: [] (none in free tier sample)

# Filter for starter tier
accessible = await TierEnforcer.filter_accessible_symbols('starter', symbols)
# Returns: ['AAPL', 'MSFT', 'GOOGL'] (US stocks only)

# Filter for premium tier
accessible = await TierEnforcer.filter_accessible_symbols('premium', symbols)
# Returns: ['AAPL', 'MSFT', 'TD.TO', 'SHOP.TO', 'GOOGL'] (US + Canada)
```

### 4. Get Bulk Limits

```python
# Get max symbols per bulk request
max_symbols = await TierEnforcer.get_max_bulk_symbols('premium')
# Returns: 200

max_symbols = await TierEnforcer.get_max_bulk_symbols('free')
# Returns: 0 (no bulk requests allowed)
```

### 5. Get Historical Data Limits

```python
# Get years of historical data allowed
years = await TierEnforcer.get_historical_data_years('starter')
# Returns: 5

years = await TierEnforcer.get_historical_data_years('professional')
# Returns: 100 (essentially unlimited)
```

### 6. Get Price Data Frequency

```python
# Get allowed price frequency
frequency = await TierEnforcer.get_price_data_frequency('free')
# Returns: 'eod' (end-of-day only)

frequency = await TierEnforcer.get_price_data_frequency('premium')
# Returns: '15min' (15-minute intraday)

frequency = await TierEnforcer.get_price_data_frequency('professional')
# Returns: '1min' (1-minute intraday)
```

## Integration with FastAPI Routes

### Method 1: Manual Checking (Recommended)

```python
from fastapi import APIRouter, Request, HTTPException
from api.middleware.tier_enforcer import TierEnforcer, get_tier_from_request

router = APIRouter()

@router.get("/stocks/{symbol}")
async def get_stock(symbol: str, request: Request):
    # Get user's tier from request state
    tier = await get_tier_from_request(request)

    # Check if symbol is accessible
    accessible = await TierEnforcer.check_symbol_access(tier, symbol)

    if not accessible:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "access_denied",
                "message": f"Symbol {symbol} is not accessible on the {tier} tier",
                "upgrade_url": "http://localhost:3000/pricing"
            }
        )

    # Continue with normal logic
    # ...
```

### Method 2: Using Dependencies

```python
from fastapi import Depends

@router.get("/stocks/{symbol}")
async def get_stock(
    symbol: str,
    request: Request,
    # Add tier enforcement as dependency
    _: bool = Depends(TierEnforcer.enforce_symbol_access('premium'))
):
    # If we get here, symbol is accessible
    # ...
```

### Method 3: Bulk Request Enforcement

```python
@router.post("/stocks/bulk")
async def get_stocks_bulk(
    symbols: List[str],
    request: Request
):
    tier = await get_tier_from_request(request)

    # Check bulk limit
    max_symbols = await TierEnforcer.get_max_bulk_symbols(tier)

    if max_symbols == 0:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "bulk_requests_not_available",
                "message": f"Bulk requests are not available on the {tier} tier",
                "upgrade_url": "http://localhost:3000/pricing"
            }
        )

    if len(symbols) > max_symbols:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "bulk_limit_exceeded",
                "message": f"Requested {len(symbols)} symbols, but {tier} tier allows maximum {max_symbols}",
                "max_symbols": max_symbols,
                "requested_symbols": len(symbols),
                "upgrade_url": "http://localhost:3000/pricing"
            }
        )

    # Filter symbols to only accessible ones
    accessible_symbols = await TierEnforcer.filter_accessible_symbols(tier, symbols)

    # Process only accessible symbols
    # ...
```

## Stock Coverage by Tier

### Free Tier (150 stocks)
- Dividend Aristocrats (68 stocks) - 25+ years of increases
- Dividend Kings (32 stocks) - 50+ years of increases
- Top yielders (50 stocks) - >4% yield, $1B+ market cap

Examples: `JNJ`, `KO`, `PG`, `MMM`, `ABT`, `PEP`, `CL`, `MCD`

### Starter Tier (~3,000 stocks)
- All US dividend-paying stocks
- NYSE, NASDAQ, AMEX exchanges
- Must have paid dividend in last 12 months

Examples: US stocks like `AAPL`, `MSFT`, `GOOGL`, `JPM`, `BAC`

### Premium Tier (~4,600 stocks)
- All Starter tier stocks
- Plus international stocks:
  - Canada (TSX): ~400 stocks
  - UK (LSE): ~500 stocks
  - Germany (XETRA): ~200 stocks
  - France (Euronext): ~200 stocks
  - Australia (ASX): ~300 stocks

Examples: `TD.TO`, `RY.TO`, `BP.L`, `VOD.L`, `SAP.DE`, `BHP.AX`

### Professional Tier (~8,000+ stocks)
- All Premium tier stocks
- Plus additional coverage:
  - Japan, Hong Kong, Singapore
  - Switzerland, Netherlands, Spain, Italy
  - REITs and MLPs
  - ADRs

### Enterprise Tier (Unlimited)
- Full global coverage (30+ exchanges)
- Custom stock lists
- Private company data (on request)

## Feature Availability Matrix

| Feature | Free | Starter | Premium | Professional | Enterprise |
|---------|------|---------|---------|--------------|------------|
| Stock Coverage | 150 | 3,000 | 4,600 | 8,000+ | Unlimited |
| Historical Years | 1 | 5 | 30+ | Full | Full |
| Price Frequency | EOD | Hourly | 15-min | 1-min | Real-time |
| Bulk Export | ❌ | ✅ | ✅ | ✅ | ✅ |
| Max Bulk Symbols | 0 | 50 | 200 | 1,000 | Unlimited |
| Webhooks | ❌ | ❌ | ✅ | ✅ | ✅ |
| Custom Screeners | ❌ | ❌ | ❌ | ✅ | ✅ |
| Portfolio Tracking | 0 | 1 | 3 | Unlimited | Unlimited |
| White-Label API | ❌ | ❌ | ❌ | ✅ | ✅ |

## Error Responses

### Access Denied (403)

```json
{
  "error": "access_denied",
  "message": "Symbol TD.TO is not accessible on the starter tier",
  "upgrade_url": "http://localhost:3000/pricing"
}
```

### Feature Not Available (403)

```json
{
  "error": "feature_not_available",
  "message": "Feature 'webhooks' is not available on the starter tier",
  "upgrade_url": "http://localhost:3000/pricing"
}
```

### Bulk Limit Exceeded (400)

```json
{
  "error": "bulk_limit_exceeded",
  "message": "Requested 100 symbols, but starter tier allows maximum 50 symbols per request",
  "max_symbols": 50,
  "requested_symbols": 100,
  "upgrade_url": "http://localhost:3000/pricing"
}
```

## Implementation Checklist

### Phase 1: Core Enforcement (✅ COMPLETE)
- [x] Create `TierEnforcer` class
- [x] Implement symbol access checking
- [x] Implement feature gating
- [x] Add bulk limit enforcement
- [x] Create helper functions

### Phase 2: Router Integration (NEXT)
- [ ] Update `/stocks/{symbol}` endpoint
- [ ] Update `/dividends/{symbol}` endpoint
- [ ] Update `/prices/{symbol}` endpoint
- [ ] Add bulk endpoints (see BULK_ENDPOINTS.md)
- [ ] Add tier info to responses

### Phase 3: Advanced Features
- [ ] Implement historical data filters
- [ ] Add intraday data gating
- [ ] Create custom screener endpoints (Professional+)
- [ ] Add webhook management endpoints (Premium+)
- [ ] Implement portfolio tracking limits

### Phase 4: Testing
- [ ] Unit tests for TierEnforcer
- [ ] Integration tests for all tiers
- [ ] Test upgrade/downgrade flows
- [ ] Test edge cases (empty free tier, etc.)

## Testing the Tier Enforcer

### Manual Testing

```bash
# Create test API keys for each tier (using Supabase dashboard)
# Free tier key: divv_free_xxx
# Starter tier key: divv_starter_xxx
# Premium tier key: divv_premium_xxx

# Test free tier access
curl -H "Authorization: Bearer divv_free_xxx" \
  "http://localhost:8000/v1/stocks/AAPL"
# Expected: 403 (AAPL not in free tier sample)

curl -H "Authorization: Bearer divv_free_xxx" \
  "http://localhost:8000/v1/stocks/JNJ"
# Expected: 200 (JNJ is Dividend Aristocrat in free tier)

# Test starter tier access
curl -H "Authorization: Bearer divv_starter_xxx" \
  "http://localhost:8000/v1/stocks/AAPL"
# Expected: 200 (AAPL is US stock)

curl -H "Authorization: Bearer divv_starter_xxx" \
  "http://localhost:8000/v1/stocks/TD.TO"
# Expected: 403 (TD.TO is Canadian, requires Premium)

# Test premium tier access
curl -H "Authorization: Bearer divv_premium_xxx" \
  "http://localhost:8000/v1/stocks/TD.TO"
# Expected: 200 (TD.TO accessible on Premium)
```

## Notes

- The tier enforcer caches tier limits in memory to reduce database queries
- Symbol access checks query the database each time (consider caching if performance is an issue)
- Free tier stocks are stored in the `free_tier_stocks` table
- Tier limits are stored in the `tier_limits` table
- The rate limiter middleware sets `request.state.rate_limit_info` which includes the tier
- All tier enforcement errors include an `upgrade_url` pointing to the pricing page

## Next Steps

1. **Integrate into existing routers** - Add tier checks to all symbol-specific endpoints
2. **Create bulk endpoints** - Implement `/stocks/bulk`, `/dividends/bulk`, `/prices/bulk`
3. **Add tier info to responses** - Include tier limits in response headers or metadata
4. **Build upgrade flows** - Create endpoints for upgrading/downgrading tiers
5. **Implement Stripe integration** - Connect payment processing for tier changes

---

**Last Updated**: 2025-11-14
**Status**: Phase 1 Complete
