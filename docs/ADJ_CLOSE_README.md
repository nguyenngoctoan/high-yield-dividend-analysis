# Adjusted Close Price Implementation

This document explains the adjusted close price feature and how to use it.

## Overview

**Adjusted close price** (`adj_close`) accounts for:
- **Stock splits** (e.g., 2:1 split)
- **Dividends** (some sources adjust for dividend distributions)
- **Corporate actions** (mergers, spinoffs)

This is essential for accurate historical analysis and portfolio tracking.

## Why It Matters

Without adjusted prices, historical analysis can be misleading:

### Example: Stock Split
- **Before 2:1 split**: Stock at $400/share
- **After split**: Stock at $200/share
- **Unadjusted chart**: Shows 50% crash 📉
- **Adjusted chart**: Shows continuity ✅

### Example: Apple (AAPL) 4:1 Split (Aug 2020)
- **Unadjusted**: $400 → $100 (looks like -75% crash)
- **Adjusted**: $100 throughout history (retroactively adjusted)

## Database Schema

### Added Columns

**stock_prices (daily prices)**
```sql
ALTER TABLE stock_prices ADD COLUMN adj_close NUMERIC(12, 4);
```

**stock_prices_hourly (intraday prices)**
```sql
ALTER TABLE stock_prices_hourly ADD COLUMN adj_close NUMERIC(12, 4);
```

## Data Sources

### FMP API (Primary)
- Field: `adjClose`
- Returns split-adjusted and dividend-adjusted prices
- Available in `historical-price-full` endpoint

### Alpha Vantage (Secondary)
- Endpoint: `TIME_SERIES_DAILY_ADJUSTED`
- Field: `5. adjusted close`
- Includes split and dividend adjustments

### Yahoo Finance (Fallback)
- The `history()` function already returns adjusted prices
- `Close` column = adjusted close

## Implementation

### 1. Run Migration

```bash
# Connect to your Supabase database and run the migration
PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres \
  -f migrations/002_add_adj_close.sql
```

### 2. Update Existing Data (Backfill)

For existing price data, run the backfill script:

```bash
# Activate virtual environment
source venv/bin/activate

# Test with 10 symbols first
python backfill_adj_close.py 10

# Run full backfill
python backfill_adj_close.py
```

The backfill script will:
1. Find all price records missing `adj_close`
2. Fetch adjusted prices from FMP API
3. Update records with adjusted close values
4. Fallback to `close` if `adjClose` not available

### 3. New Data Collection

All new data fetched by `update_stock.py` will automatically include `adj_close`:

```bash
# Normal daily update - now includes adj_close
python update_stock.py --discover-symbols --validate-discovered
```

## Usage Examples

### SQL Query - Get Adjusted Prices

```sql
SELECT
    symbol,
    date,
    close AS unadjusted_close,
    adj_close AS adjusted_close,
    (close - adj_close) AS adjustment_amount,
    ROUND(((close - adj_close) / close * 100)::numeric, 2) AS adjustment_percent
FROM stock_prices
WHERE symbol = 'AAPL'
    AND date >= '2020-08-01'
    AND date <= '2020-09-01'
ORDER BY date;
```

### Python - Calculate Returns

```python
from supabase_helpers import get_supabase_client

supabase = get_supabase_client()

# Get adjusted prices for return calculation
result = supabase.table('stock_prices')\
    .select('date,adj_close')\
    .eq('symbol', 'AAPL')\
    .order('date')\
    .execute()

prices = result.data

# Calculate returns using adjusted prices
for i in range(1, len(prices)):
    prev_price = float(prices[i-1]['adj_close'])
    curr_price = float(prices[i]['adj_close'])
    daily_return = (curr_price - prev_price) / prev_price * 100
    print(f"{prices[i]['date']}: {daily_return:.2f}%")
```

## Important Notes

### For Daily Prices (stock_prices)
- Use `adj_close` for all historical analysis
- Use `close` only when you specifically need unadjusted prices

### For Hourly Prices (stock_prices_hourly)
- Intraday data typically doesn't have adjustments
- `adj_close` = `close` for hourly data
- Adjustments are applied at end-of-day

### Backward Compatibility
- The `close` column is unchanged
- Existing queries still work
- Add `adj_close` to new analysis queries

## Testing

To verify the implementation works:

```bash
# 1. Run migration
PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres \
  -f migrations/002_add_adj_close.sql

# 2. Test with a few symbols
python backfill_adj_close.py 5

# 3. Check the results
PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres \
  -c "SELECT symbol, date, close, adj_close FROM stock_prices WHERE adj_close IS NOT NULL LIMIT 10;"

# 4. Fetch new data for a test symbol
python update_stock.py --symbols AAPL

# 5. Verify new data has adj_close
PGPASSWORD=postgres psql -h localhost -p 54322 -U postgres -d postgres \
  -c "SELECT symbol, date, close, adj_close FROM stock_prices WHERE symbol = 'AAPL' ORDER BY date DESC LIMIT 5;"
```

## Files Modified

1. **migrations/002_add_adj_close.sql** - Database migration
2. **update_stock.py** - Added adj_close to price fetching (FMP, Alpha Vantage, Yahoo)
3. **fetch_hourly_prices.py** - Added adj_close to hourly price data
4. **backfill_adj_close.py** - New script to backfill existing data
5. **supabase_helpers.py** - No changes needed (automatically handles new column)

## Troubleshooting

### Issue: Backfill script hangs
**Solution**: Reduce max_workers or add rate limiting delay

### Issue: adj_close = close for all records
**Possible causes**:
- Symbol has never had a split or significant dividend
- FMP API not returning adjClose (fallback to close)
- Need to check with a known split stock (e.g., AAPL, TSLA)

### Issue: Migration fails
**Solution**: Check if column already exists:
```sql
SELECT column_name FROM information_schema.columns
WHERE table_name = 'stock_prices' AND column_name = 'adj_close';
```

## Next Steps

1. **Update portfolio_performance_calculator.py** to use `adj_close`
2. **Create charts/visualizations** comparing adjusted vs unadjusted
3. **Add adj_close to any analytics queries** for accurate returns
