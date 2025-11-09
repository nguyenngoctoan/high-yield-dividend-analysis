# ETF Holdings Implementation

**Date**: October 12, 2025
**Status**: ✅ Complete and tested

## Overview

Successfully implemented ETF holdings data fetching and storage using Financial Modeling Prep API. Holdings are stored as JSONB in the stocks table for fast querying and analysis.

**Update Schedule**: Daily (automated via daily_update_v2.sh)

---

## Database Schema

### New Columns Added

```sql
-- Holdings data (JSONB array)
holdings JSONB

-- Last update timestamp
holdings_updated_at TIMESTAMP WITH TIME ZONE

-- GIN index for JSON queries
CREATE INDEX idx_stocks_holdings ON stocks USING GIN (holdings)
WHERE holdings IS NOT NULL;

-- B-tree index for timestamp filtering
CREATE INDEX idx_stocks_holdings_updated_at ON stocks(holdings_updated_at)
WHERE holdings_updated_at IS NOT NULL;
```

### Holdings Data Structure

```json
[
  {
    "symbol": "SPY",
    "asset": "NVDA",
    "name": "NVIDIA Corporation",
    "isin": "",
    "securityCusip": "67066G104",
    "sharesNumber": 289359053,
    "weightPercentage": 7.988,
    "marketValue": 54219192650,
    "updatedAt": "2025-10-10 08:10:46"
  },
  ...
]
```

---

## Implementation Details

### 1. FMP Client Enhancement

Added `fetch_etf_holdings()` method to `FMPClient` (`lib/data_sources/fmp_client.py:477-517`):

```python
def fetch_etf_holdings(self, symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch ETF holdings from FMP."""
    url = f"{self.BASE_URL}/stable/etf/holdings?symbol={symbol}&apikey={self.api_key}"
    data = self._fetch_with_retry(url, symbol=symbol)

    if data and isinstance(data, list) and len(data) > 0:
        return {
            'source': 'FMP',
            'symbol': symbol,
            'holdings': data,
            'count': len(data),
            'updated_at': data[0].get('updatedAt')
        }
    return None
```

### 2. Holdings Processor Module

Created `HoldingsProcessor` class (`lib/processors/holdings_processor.py`):

**Features**:
- Fetch holdings for individual ETFs
- Batch processing for multiple ETFs
- Automatic ETF identification (by investment_strategy or name patterns)
- Statistics tracking
- Error handling and logging

**Key Methods**:
- `fetch_and_store_holdings(symbol)` - Single ETF processing
- `process_batch(symbols)` - Batch processing
- `update_all_etfs(limit)` - Update all ETFs in database

### 3. Main Script Integration

Added `update-holdings` mode to `update_stock_v2.py`:

```bash
python3 update_stock_v2.py --mode update-holdings [--limit N]
```

---

## Usage Examples

### Command Line

```bash
# Update all ETF holdings
python3 update_stock_v2.py --mode update-holdings

# Update limited number of ETFs (for testing)
python3 update_stock_v2.py --mode update-holdings --limit 10
```

### Python API

```python
from lib.processors.holdings_processor import fetch_etf_holdings, update_all_etf_holdings

# Fetch holdings for a single ETF
success = fetch_etf_holdings('SPY')

# Update all ETFs
summary = update_all_etf_holdings(limit=100)
print(f"Updated {summary['successful']} ETFs")
```

---

## Query Examples

### Get ETF Holdings

```sql
-- Get all holdings for SPY
SELECT
    jsonb_array_elements(holdings)->>'asset' as holding_symbol,
    jsonb_array_elements(holdings)->>'name' as holding_name,
    (jsonb_array_elements(holdings)->>'weightPercentage')::numeric as weight,
    (jsonb_array_elements(holdings)->>'marketValue')::numeric as market_value
FROM stocks
WHERE symbol = 'SPY'
ORDER BY weight DESC
LIMIT 10;
```

### Find ETFs Holding a Specific Stock

```sql
-- Find all ETFs that hold TSLA
SELECT
    symbol,
    name,
    elem->>'weightPercentage' as weight,
    elem->>'sharesNumber' as shares
FROM stocks,
     jsonb_array_elements(holdings) as elem
WHERE elem->>'asset' = 'TSLA'
ORDER BY (elem->>'weightPercentage')::numeric DESC;
```

### ETF Overlap Analysis

```sql
-- Find common holdings between two ETFs
WITH spy_holdings AS (
    SELECT jsonb_array_elements(holdings)->>'asset' as asset
    FROM stocks WHERE symbol = 'SPY'
),
qqq_holdings AS (
    SELECT jsonb_array_elements(holdings)->>'asset' as asset
    FROM stocks WHERE symbol = 'QQQ'
)
SELECT
    s.asset,
    spy_h.elem->>'weightPercentage' as spy_weight,
    qqq_h.elem->>'weightPercentage' as qqq_weight
FROM spy_holdings s
INNER JOIN qqq_holdings q ON s.asset = q.asset
INNER JOIN LATERAL (
    SELECT jsonb_array_elements(holdings) as elem
    FROM stocks WHERE symbol = 'SPY'
) spy_h ON spy_h.elem->>'asset' = s.asset
INNER JOIN LATERAL (
    SELECT jsonb_array_elements(holdings) as elem
    FROM stocks WHERE symbol = 'QQQ'
) qqq_h ON qqq_h.elem->>'asset' = q.asset
ORDER BY (spy_h.elem->>'weightPercentage')::numeric DESC
LIMIT 20;
```

### Holdings Concentration

```sql
-- Calculate top 10 holdings concentration for each ETF
SELECT
    symbol,
    name,
    SUM((elem->>'weightPercentage')::numeric) as top10_concentration
FROM stocks,
     LATERAL (
         SELECT jsonb_array_elements(holdings) as elem
         FROM stocks s2
         WHERE s2.symbol = stocks.symbol
         ORDER BY (elem->>'weightPercentage')::numeric DESC
         LIMIT 10
     ) top_holdings
WHERE holdings IS NOT NULL
GROUP BY symbol, name
ORDER BY top10_concentration DESC;
```

---

## Data Quality

### Validation Tests

```sql
-- Check data completeness
SELECT
    COUNT(*) FILTER (WHERE holdings IS NOT NULL) as has_holdings,
    COUNT(*) FILTER (WHERE holdings IS NULL) as no_holdings,
    COUNT(*) as total_etfs
FROM stocks
WHERE investment_strategy IS NOT NULL;

-- Check holdings freshness
SELECT
    symbol,
    name,
    jsonb_array_length(holdings) as holdings_count,
    holdings_updated_at,
    NOW() - holdings_updated_at as age
FROM stocks
WHERE holdings IS NOT NULL
ORDER BY age DESC
LIMIT 10;
```

---

## Performance Considerations

1. **JSONB Type**: Uses JSONB (not JSON) for better query performance
2. **GIN Index**: Enables fast JSON path queries
3. **Selective Indexing**: Only indexes rows with non-NULL holdings
4. **Rate Limiting**: Respects FMP API rate limits (144 concurrent requests)

---

## Example Holdings Data

### SPY (S&P 500 ETF)
- **Holdings Count**: 504
- **Top Holdings**:
  1. NVDA - 7.988%
  2. MSFT - 6.754%
  3. AAPL - 6.63%

### TSLY (YieldMax TSLA ETF)
- **Holdings Count**: 26
- **Components**:
  - Treasury Bills (70%+)
  - TSLA Stock options (calls/puts)
  - Cash & equivalents
  - Money market funds

---

## Troubleshooting

### Schema Cache Issue
If you get "Column 'holdings' does not exist" error after migration:

```bash
# Restart Supabase REST API to refresh schema cache
/Applications/Docker.app/Contents/Resources/bin/docker restart dividend-tracker-supabase-rest
```

### No ETFs Found
If `update-holdings` finds 0 ETFs:
- Ensure ETFs have `investment_strategy` populated
- Or names contain 'ETF' or 'FUND'
- Run classification first: `python3 update_stock_v2.py --mode update --companies-only`

---

## Files Created/Modified

### New Files
1. `migrations/005_add_holdings_column.sql` - Database migration
2. `lib/processors/holdings_processor.py` - Holdings processor module
3. `docs/ETF_HOLDINGS_IMPLEMENTATION.md` - This documentation

### Modified Files
1. `lib/data_sources/fmp_client.py` - Added `fetch_etf_holdings()` method
2. `update_stock_v2.py` - Added `update-holdings` mode
3. `lib/processors/holdings_processor.py` - Holdings processor implementation

---

## Next Steps

Potential enhancements:
1. **Historical Holdings**: Track holdings changes over time
2. **Holdings Analysis Dashboard**: Visualize holdings and overlaps
3. **Sector Exposure**: Calculate sector weights from holdings
4. **Holding Alerts**: Notify when significant holdings changes occur
5. **Custom Portfolios**: Build portfolios from holdings data

---

## Summary

✅ Database schema extended with JSONB columns
✅ FMP API integration for holdings data
✅ Holdings processor module created
✅ CLI command added (`--mode update-holdings`)
✅ Comprehensive query examples provided
✅ Tested with SPY (504 holdings) and TSLY (26 holdings)
✅ Performance optimized with GIN indexes

**Holdings data is now available for all ETFs!** 🎉
