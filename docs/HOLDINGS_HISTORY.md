# ETF Holdings History Tracking

**Date**: October 12, 2025
**Status**: ✅ Implemented and active

---

## Overview

The system now tracks ETF holdings changes over time by storing daily snapshots in the `holdings_history` table. This allows you to:
- See when ETFs rebalance their portfolios
- Track weight changes for specific holdings
- Analyze portfolio composition trends
- Compare holdings across different dates

---

## Database Schema

### Table: holdings_history

```sql
CREATE TABLE holdings_history (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    holdings JSONB NOT NULL,
    holdings_count INTEGER,
    data_source VARCHAR(50) DEFAULT 'FMP',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- One record per symbol per day
    CONSTRAINT holdings_history_symbol_date_unique UNIQUE (symbol, date)
);
```

### Indexes

- `idx_holdings_history_symbol` - Fast symbol lookups
- `idx_holdings_history_date` - Fast date filtering
- `idx_holdings_history_symbol_date` - Fast symbol+date queries
- `idx_holdings_history_holdings` - GIN index for JSONB queries

---

## How It Works

### Daily Updates

When the daily automation runs (`daily_update_v2.sh`):

1. **Holdings Processor** fetches latest holdings from FMP API
2. **Stocks Table** updated with latest holdings (for current queries)
3. **Holdings History** stores a daily snapshot (for historical analysis)

```
┌─────────────────┐
│ FMP API         │
│ (ETF Holdings)  │
└────────┬────────┘
         │
         ├──────────────┬────────────────┐
         │              │                │
         v              v                v
   ┌──────────┐  ┌──────────────┐  ┌──────────────────┐
   │ stocks   │  │ holdings     │  │ holdings_history │
   │ (current)│  │ _history     │  │ (time series)    │
   │          │  │ (daily)      │  │                  │
   └──────────┘  └──────────────┘  └──────────────────┘
```

### Upsert Logic

The system uses **upsert** to handle daily updates:
- If no record exists for symbol+date → **INSERT**
- If record already exists for symbol+date → **UPDATE**

This means running the script multiple times per day won't create duplicates.

---

## Query Examples

### 1. View Holdings History for an ETF

```sql
-- Get all holdings snapshots for SPY
SELECT
    date,
    holdings_count,
    created_at
FROM holdings_history
WHERE symbol = 'SPY'
ORDER BY date DESC;
```

### 2. Get Holdings for a Specific Date

```sql
-- What did SPY hold on September 1, 2025?
SELECT
    symbol,
    date,
    jsonb_array_elements(holdings)->>'asset' as holding,
    jsonb_array_elements(holdings)->>'name' as holding_name,
    (jsonb_array_elements(holdings)->>'weightPercentage')::numeric as weight
FROM holdings_history
WHERE symbol = 'SPY'
  AND date = '2025-09-01'
ORDER BY weight DESC
LIMIT 10;
```

### 3. Compare Holdings Between Two Dates

```sql
-- What changed in QQQ between two dates?
WITH current_holdings AS (
    SELECT
        jsonb_array_elements(holdings)->>'asset' as asset,
        (jsonb_array_elements(holdings)->>'weightPercentage')::numeric as weight
    FROM holdings_history
    WHERE symbol = 'QQQ' AND date = '2025-10-12'
),
previous_holdings AS (
    SELECT
        jsonb_array_elements(holdings)->>'asset' as asset,
        (jsonb_array_elements(holdings)->>'weightPercentage')::numeric as weight
    FROM holdings_history
    WHERE symbol = 'QQQ' AND date = '2025-09-12'
)
SELECT
    COALESCE(c.asset, p.asset) as asset,
    c.weight as current_weight,
    p.weight as previous_weight,
    (c.weight - COALESCE(p.weight, 0)) as weight_change,
    CASE
        WHEN c.weight IS NULL THEN 'REMOVED'
        WHEN p.weight IS NULL THEN 'ADDED'
        WHEN c.weight > p.weight THEN 'INCREASED'
        WHEN c.weight < p.weight THEN 'DECREASED'
        ELSE 'NO CHANGE'
    END as change_type
FROM current_holdings c
FULL OUTER JOIN previous_holdings p ON c.asset = p.asset
WHERE c.weight IS DISTINCT FROM p.weight
ORDER BY ABS(COALESCE(c.weight, 0) - COALESCE(p.weight, 0)) DESC
LIMIT 20;
```

### 4. Find ETFs That Rebalanced Recently

```sql
-- Find ETFs that changed holdings in the last 7 days
SELECT DISTINCT
    h1.symbol,
    h1.date as latest_date,
    h1.holdings_count as current_count,
    h2.holdings_count as previous_count,
    h1.holdings_count - h2.holdings_count as count_change
FROM holdings_history h1
INNER JOIN holdings_history h2
    ON h1.symbol = h2.symbol
    AND h2.date < h1.date
WHERE h1.date >= CURRENT_DATE - INTERVAL '7 days'
  AND h1.holdings IS DISTINCT FROM h2.holdings
  AND h2.date = (
      SELECT MAX(date)
      FROM holdings_history h3
      WHERE h3.symbol = h1.symbol
        AND h3.date < h1.date
  )
ORDER BY h1.date DESC, h1.symbol;
```

### 5. Track Weight Changes for a Specific Stock

```sql
-- How has NVDA's weight changed in SPY over time?
SELECT
    date,
    elem->>'weightPercentage' as weight,
    elem->>'sharesNumber' as shares,
    elem->>'marketValue' as market_value
FROM holdings_history,
     jsonb_array_elements(holdings) as elem
WHERE symbol = 'SPY'
  AND elem->>'asset' = 'NVDA'
ORDER BY date DESC;
```

### 6. Portfolio Turnover Analysis

```sql
-- Calculate how much of the portfolio changed month-over-month
WITH monthly_holdings AS (
    SELECT
        symbol,
        date_trunc('month', date)::date as month,
        holdings,
        ROW_NUMBER() OVER (PARTITION BY symbol, date_trunc('month', date) ORDER BY date DESC) as rn
    FROM holdings_history
)
SELECT
    curr.symbol,
    curr.month as current_month,
    COUNT(DISTINCT curr_hold.value->>'asset') as current_holdings_count,
    COUNT(DISTINCT prev_hold.value->>'asset') as previous_holdings_count,
    COUNT(DISTINCT CASE
        WHEN prev_hold.value->>'asset' IS NULL THEN curr_hold.value->>'asset'
    END) as new_holdings,
    COUNT(DISTINCT CASE
        WHEN curr_hold.value->>'asset' IS NULL THEN prev_hold.value->>'asset'
    END) as removed_holdings
FROM monthly_holdings curr
LEFT JOIN monthly_holdings prev
    ON curr.symbol = prev.symbol
    AND prev.month = curr.month - INTERVAL '1 month'
    AND prev.rn = 1
LEFT JOIN LATERAL jsonb_array_elements(curr.holdings) curr_hold ON true
LEFT JOIN LATERAL jsonb_array_elements(prev.holdings) prev_hold ON true
WHERE curr.rn = 1
  AND curr.month >= '2025-01-01'
GROUP BY curr.symbol, curr.month
ORDER BY curr.month DESC, curr.symbol;
```

---

## Data Retention

### Current Strategy

- **Unlimited retention**: All historical records are kept
- **Storage**: JSONB is efficient, ~1-5KB per ETF per day
- **Est. size**: 4,000 ETFs × 365 days × 3KB ≈ 4.4GB per year

### Future Considerations

If storage becomes an issue, implement retention policies:

```sql
-- Example: Delete records older than 2 years
DELETE FROM holdings_history
WHERE date < CURRENT_DATE - INTERVAL '2 years';

-- Or: Keep only month-end snapshots after 1 year
DELETE FROM holdings_history
WHERE date < CURRENT_DATE - INTERVAL '1 year'
  AND date != date_trunc('month', date + INTERVAL '1 month' - INTERVAL '1 day')::date;
```

---

## Performance Optimization

### Index Usage

The table has indexes optimized for common query patterns:

```sql
-- Uses idx_holdings_history_symbol
SELECT * FROM holdings_history WHERE symbol = 'SPY';

-- Uses idx_holdings_history_date
SELECT * FROM holdings_history WHERE date = '2025-10-12';

-- Uses idx_holdings_history_symbol_date
SELECT * FROM holdings_history WHERE symbol = 'SPY' AND date = '2025-10-12';

-- Uses idx_holdings_history_holdings (GIN)
SELECT * FROM holdings_history WHERE holdings @> '[{"asset": "AAPL"}]';
```

### Query Tips

1. **Always filter by symbol or date** - Avoid full table scans
2. **Use date ranges wisely** - Limit to necessary time periods
3. **Limit results** - Use LIMIT when exploring data
4. **Materialize complex queries** - Create views for frequently-used analysis

---

## Monitoring

### Check Daily Updates

```sql
-- How many ETFs were updated today?
SELECT COUNT(*) as etfs_updated_today
FROM holdings_history
WHERE date = CURRENT_DATE;

-- Which ETFs haven't been updated recently?
SELECT
    s.symbol,
    s.name,
    MAX(h.date) as last_update,
    CURRENT_DATE - MAX(h.date) as days_since_update
FROM stocks s
LEFT JOIN holdings_history h ON s.symbol = h.symbol
WHERE s.investment_strategy IS NOT NULL  -- Only ETFs
GROUP BY s.symbol, s.name
HAVING MAX(h.date) < CURRENT_DATE - INTERVAL '7 days'
   OR MAX(h.date) IS NULL
ORDER BY days_since_update DESC NULLS FIRST
LIMIT 20;
```

### Storage Usage

```sql
-- Check table size
SELECT
    pg_size_pretty(pg_total_relation_size('holdings_history')) as total_size,
    pg_size_pretty(pg_relation_size('holdings_history')) as table_size,
    pg_size_pretty(pg_total_relation_size('holdings_history') - pg_relation_size('holdings_history')) as indexes_size;

-- Record count
SELECT COUNT(*) as total_records FROM holdings_history;

-- Records per ETF
SELECT
    symbol,
    COUNT(*) as snapshot_count,
    MIN(date) as first_snapshot,
    MAX(date) as last_snapshot
FROM holdings_history
GROUP BY symbol
ORDER BY snapshot_count DESC
LIMIT 10;
```

---

## Troubleshooting

### No History Records Created

**Check if REST API is aware of new table:**
```bash
/Applications/Docker.app/Contents/Resources/bin/docker restart dividend-tracker-supabase-rest
```

**Verify table exists:**
```sql
SELECT * FROM holdings_history LIMIT 1;
```

**Check processor logs:**
```bash
tail -100 logs/daily_update_v2_$(date +%Y%m%d).log | grep "holdings_history"
```

### Duplicate Records

The unique constraint prevents duplicates, but if you see errors:

```sql
-- Check for constraint violations
SELECT symbol, date, COUNT(*)
FROM holdings_history
GROUP BY symbol, date
HAVING COUNT(*) > 1;
```

### Missing Dates

Holdings are only fetched when they change or on the daily schedule. If you see gaps:

```sql
-- Find date gaps for an ETF
WITH RECURSIVE date_series AS (
    SELECT MIN(date) as date FROM holdings_history WHERE symbol = 'SPY'
    UNION ALL
    SELECT date + INTERVAL '1 day'
    FROM date_series
    WHERE date < CURRENT_DATE
)
SELECT d.date
FROM date_series d
LEFT JOIN holdings_history h
    ON h.symbol = 'SPY' AND h.date = d.date::date
WHERE h.date IS NULL
ORDER BY d.date;
```

---

## Integration with Daily Automation

The holdings history is automatically populated by `daily_update_v2.sh`:

```bash
# Step 4: Update ETF Holdings (daily)
# This updates both stocks.holdings AND holdings_history
python3 update_stock_v2.py --mode update-holdings
```

**What happens:**
1. Fetches latest holdings from FMP for all ETFs
2. Updates `stocks` table with current holdings
3. **Inserts/updates daily snapshot** in `holdings_history`
4. Uses upsert to prevent duplicates

---

## Use Cases

### Portfolio Management

- Track when fund managers rebalance
- See which holdings are being added/removed
- Analyze concentration changes over time

### Risk Analysis

- Identify increasing concentration in top holdings
- Monitor sector drift
- Track correlation changes

### Research & Analysis

- Study rebalancing frequency by ETF type
- Analyze seasonal patterns in holdings changes
- Compare holdings strategies across providers

### Alerts & Notifications

Build alerts for:
- Major holdings changes (>1% weight change)
- New positions added
- Complete removals
- Concentration thresholds exceeded

---

## Example Analysis Workflow

```sql
-- 1. Find ETFs with significant recent changes
WITH recent_changes AS (
    SELECT DISTINCT
        h1.symbol,
        h1.date
    FROM holdings_history h1
    INNER JOIN holdings_history h2
        ON h1.symbol = h2.symbol
        AND h2.date = h1.date - INTERVAL '7 days'
    WHERE h1.date = CURRENT_DATE
      AND h1.holdings IS DISTINCT FROM h2.holdings
)
-- 2. Get details on what changed
SELECT
    rc.symbol,
    s.name,
    rc.date,
    h.holdings_count
FROM recent_changes rc
INNER JOIN stocks s ON rc.symbol = s.symbol
INNER JOIN holdings_history h ON rc.symbol = h.symbol AND rc.date = h.date
ORDER BY s.name;

-- 3. Drill into specific changes for one ETF
-- (Use the compare holdings between two dates query from above)
```

---

## Summary

✅ **Holdings history tracking implemented**
✅ **Daily snapshots automatically saved**
✅ **Efficient JSONB storage with indexes**
✅ **Comprehensive query examples provided**
✅ **Integrated into daily automation**
✅ **Upsert prevents duplicates**

**Benefits:**
- 📊 Track portfolio changes over time
- 🔍 Identify rebalancing events
- 📈 Analyze weight trends
- ⚠️  Build change alerts
- 🎯 Research fund strategies

**Storage:** ~4-5GB per year for 4,000 ETFs (very reasonable!)

---

## Related Documentation

- `docs/ETF_HOLDINGS_IMPLEMENTATION.md` - Holdings feature overview
- `docs/DAILY_AUTOMATION.md` - Daily automation setup
- `migrations/006_create_holdings_history.sql` - Table schema

---

**Implementation Complete**: October 12, 2025
**Status**: ✅ Active and tracking
**Next Update**: Runs daily automatically
