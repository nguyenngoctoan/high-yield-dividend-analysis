# AUM (Assets Under Management) Tracking

## Overview

The system tracks **AUM (Assets Under Management)** for ETFs daily in the `stock_prices` table. This allows you to monitor ETF growth, fund flows, and popularity trends over time.

## What is AUM?

**AUM (Assets Under Management)** represents the total market value of assets that an ETF manages. It's calculated as:
```
AUM = Number of Shares Outstanding × Current Share Price
```

- **High AUM**: Popular, liquid ETF with significant investor interest
- **Growing AUM**: Increasing investor inflows (bullish signal)
- **Declining AUM**: Investor outflows or price decline (bearish signal)

## Database Schema

### stock_prices Table

AUM is stored alongside daily price data:

```sql
Column:  aum
Type:    BIGINT
Purpose: Store total assets under management (in dollars)
Index:   idx_stock_prices_aum, idx_stock_prices_symbol_date_aum
```

## Data Collection Status

### ✅ What's Working:
- AUM column exists in `stock_prices` table
- `update_stock.py` collects AUM from Yahoo Finance (`info.get('totalAssets')`)
- AUM is included in price records during data fetch

### ✅ Recent Fix (October 11, 2025):
**Problem**: AUM was only added to the most recent record, not all daily records
**Solution**: Updated `fetch_yahoo_prices` to add AUM to ALL price records for daily tracking

**Before**:
```python
# Only add AUM to the most recent (last) record
if aum and idx == len(hist) - 1:
    record['aum'] = int(aum)
```

**After**:
```python
# Add AUM to ALL records for daily AUM tracking
if aum:
    record['aum'] = int(aum)
```

## How It Works

### Daily Update Process

The `daily_update.sh` script runs automatically at 10 PM EST:

1. **Discovery Mode**: Finds new ETF symbols
2. **Prices Mode**: Updates daily prices + AUM for all symbols
3. **Dividends Mode**: Updates dividend history
4. **Splits Mode**: Updates stock splits

During **Prices Mode** (`python update_stock.py --mode prices`):
- Fetches current AUM from Yahoo Finance
- Adds AUM to today's price record
- Historical AUM backfill occurs when fetching historical prices

### Data Sources

**Yahoo Finance** (yfinance):
```python
ticker = yf.Ticker("SPY")
info = ticker.info
aum = info.get('totalAssets')  # e.g., 450000000000 ($450 billion)
```

### Data Flow

```
Yahoo Finance API
    ↓
fetch_yahoo_prices(symbol)
    ↓
Extracts info.get('totalAssets')
    ↓
Adds to each price record
    ↓
process_symbol_prices_hybrid()
    ↓
Upserts to stock_prices table
```

## Usage Examples

### Query AUM Data

```sql
-- Current AUM for top ETFs
SELECT symbol, date, close, aum
FROM stock_prices
WHERE aum IS NOT NULL
  AND date = CURRENT_DATE
ORDER BY aum DESC
LIMIT 20;

-- AUM growth tracking for SPY
SELECT
    symbol,
    date,
    aum,
    LAG(aum) OVER (ORDER BY date) as prev_aum,
    aum - LAG(aum) OVER (ORDER BY date) as aum_change,
    ROUND(((aum - LAG(aum) OVER (ORDER BY date))::numeric / LAG(aum) OVER (ORDER BY date) * 100), 2) as aum_change_pct
FROM stock_prices
WHERE symbol = 'SPY'
  AND aum IS NOT NULL
ORDER BY date DESC
LIMIT 30;

-- ETFs with largest AUM growth (last 30 days)
SELECT
    symbol,
    MAX(aum) FILTER (WHERE date = CURRENT_DATE) as current_aum,
    MAX(aum) FILTER (WHERE date = CURRENT_DATE - INTERVAL '30 days') as aum_30d_ago,
    MAX(aum) FILTER (WHERE date = CURRENT_DATE) - MAX(aum) FILTER (WHERE date = CURRENT_DATE - INTERVAL '30 days') as aum_change,
    ROUND(
        ((MAX(aum) FILTER (WHERE date = CURRENT_DATE) - MAX(aum) FILTER (WHERE date = CURRENT_DATE - INTERVAL '30 days'))::numeric
        / MAX(aum) FILTER (WHERE date = CURRENT_DATE - INTERVAL '30 days') * 100),
        2
    ) as aum_change_pct
FROM stock_prices
WHERE aum IS NOT NULL
  AND date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY symbol
HAVING
    MAX(aum) FILTER (WHERE date = CURRENT_DATE) IS NOT NULL
    AND MAX(aum) FILTER (WHERE date = CURRENT_DATE - INTERVAL '30 days') IS NOT NULL
ORDER BY aum_change_pct DESC
LIMIT 20;

-- AUM vs Price correlation
SELECT
    symbol,
    CORR(aum, close) as aum_price_correlation,
    AVG(aum) as avg_aum,
    AVG(close) as avg_price
FROM stock_prices
WHERE aum IS NOT NULL
  AND date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY symbol
HAVING COUNT(*) >= 60  -- At least 60 days of data
ORDER BY aum_price_correlation DESC;
```

### Python Integration

```python
from supabase_helpers import get_supabase_client

# Get current AUM for an ETF
supabase = get_supabase_client()
result = supabase.table('stock_prices')\
    .select('symbol,date,close,aum')\
    .eq('symbol', 'SPY')\
    .not_.is_('aum', 'null')\
    .order('date', desc=True)\
    .limit(90)\
    .execute()

aum_data = result.data

# Calculate AUM growth
if len(aum_data) >= 2:
    current_aum = aum_data[0]['aum']
    previous_aum = aum_data[1]['aum']
    aum_growth = ((current_aum - previous_aum) / previous_aum) * 100
    print(f"Daily AUM growth: {aum_growth:.2f}%")
```

## ETF Screening by AUM

### High AUM ETFs (Most Popular)
```sql
SELECT symbol, aum, close
FROM stock_prices
WHERE date = CURRENT_DATE
  AND aum > 10000000000  -- > $10 billion
ORDER BY aum DESC;
```

### Growing ETFs (Inflows)
```sql
-- ETFs with consistent AUM growth
WITH aum_changes AS (
    SELECT
        symbol,
        date,
        aum,
        LAG(aum, 1) OVER (PARTITION BY symbol ORDER BY date) as aum_1d_ago,
        LAG(aum, 7) OVER (PARTITION BY symbol ORDER BY date) as aum_7d_ago,
        LAG(aum, 30) OVER (PARTITION BY symbol ORDER BY date) as aum_30d_ago
    FROM stock_prices
    WHERE aum IS NOT NULL
)
SELECT
    symbol,
    aum as current_aum,
    ROUND(((aum - aum_1d_ago)::numeric / aum_1d_ago * 100), 2) as growth_1d_pct,
    ROUND(((aum - aum_7d_ago)::numeric / aum_7d_ago * 100), 2) as growth_7d_pct,
    ROUND(((aum - aum_30d_ago)::numeric / aum_30d_ago * 100), 2) as growth_30d_pct
FROM aum_changes
WHERE date = CURRENT_DATE
  AND aum_1d_ago IS NOT NULL
  AND aum_7d_ago IS NOT NULL
  AND aum_30d_ago IS NOT NULL
  AND aum > 100000000  -- > $100 million
  AND ((aum - aum_7d_ago)::numeric / aum_7d_ago * 100) > 5  -- 7-day growth > 5%
ORDER BY growth_7d_pct DESC
LIMIT 20;
```

## Data Quality & Coverage

### Check AUM Coverage

```bash
# Check overall AUM coverage
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d postgres -c "
SELECT
    COUNT(DISTINCT symbol) as etfs_with_aum,
    MAX(date) as most_recent_date,
    COUNT(*) as total_aum_records
FROM stock_prices
WHERE aum IS NOT NULL;
"

# Check recent AUM updates
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d postgres -c "
SELECT
    date,
    COUNT(DISTINCT symbol) as symbols_with_aum,
    AVG(aum) as avg_aum,
    MAX(aum) as max_aum
FROM stock_prices
WHERE aum IS NOT NULL
  AND date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY date
ORDER BY date DESC;
"
```

## Interpreting AUM Data

### AUM Growth Signals

**Positive Signals** (Bullish):
- Consistent AUM growth over weeks/months
- AUM growing faster than price (new inflows)
- Large sudden AUM increase (institutional interest)

**Negative Signals** (Bearish):
- Declining AUM despite stable/rising price (outflows)
- AUM dropping faster than price (panic selling)
- Consistent AUM decline over time (losing popularity)

### AUM vs Price Divergence

**Scenario 1: Rising AUM + Rising Price**
- Strong bullish signal
- Both investor inflows and market appreciation

**Scenario 2: Rising AUM + Falling Price**
- Investors buying the dip
- Contrarian opportunity

**Scenario 3: Falling AUM + Rising Price**
- Fewer shares, higher price (supply/demand)
- May indicate top (investors taking profits)

**Scenario 4: Falling AUM + Falling Price**
- Strong bearish signal
- Both outflows and price decline

## Testing AUM Collection

### Test Single Symbol

```bash
# Test AUM collection for a known ETF
source venv/bin/activate
python -c "
import yfinance as yf
ticker = yf.Ticker('SPY')
info = ticker.info
aum = info.get('totalAssets')
print(f'SPY AUM: \${aum:,.0f}' if aum else 'AUM not available')
"
```

### Test Price Update with AUM

```bash
# Run price update for a few test symbols
source venv/bin/activate
python update_stock.py --mode prices --symbols SPY,QQQ,VOO

# Verify AUM was recorded
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d postgres -c "
SELECT symbol, date, close, aum
FROM stock_prices
WHERE symbol IN ('SPY', 'QQQ', 'VOO')
  AND date = CURRENT_DATE
  AND aum IS NOT NULL;
"
```

## Limitations & Notes

1. **Data Availability**: AUM only available for ETFs (not individual stocks)
2. **Update Frequency**: AUM updated daily during price updates
3. **Historical Data**: Current AUM value backfilled to recent records (represents today's AUM)
4. **Data Source**: Yahoo Finance only (FMP doesn't provide AUM reliably)
5. **NULL Values**: AUM will be NULL for stocks and ETFs where data isn't available

## Related Metrics

Consider tracking these related metrics:

- **Share Price**: Daily closing price
- **Volume**: Trading volume (liquidity indicator)
- **Expense Ratio**: Annual fund operating expenses
- **Holdings Count**: Number of securities in the ETF
- **Turnover Rate**: How frequently holdings change

## Monitoring & Alerts

### Alert Examples

1. **Large AUM Changes**: Alert when daily AUM change exceeds ±10%
2. **New Inflows**: Notify when AUM grows >20% in 7 days
3. **Outflow Warnings**: Alert when AUM declines >15% in 30 days
4. **Liquidity Issues**: Warn when AUM drops below $100M threshold

---

**Implementation Date**: October 11, 2025
**Status**: ✅ Active - AUM collected daily with price updates
**Next Steps**: Monitor data quality, add IV (Implied Volatility) tracking
