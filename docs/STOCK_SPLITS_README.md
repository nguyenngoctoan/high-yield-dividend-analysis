# Stock Splits Tracking System

## Overview

This system tracks historical stock split events with dates and ratios using a 3-tier data fetching approach:
1. **FMP** (Primary) - Financial Modeling Prep API
2. **Alpha Vantage** (Secondary) - Currently limited split data
3. **Yahoo Finance** (Fallback) - Using yfinance library

## Database Schema

### Table: `stock_splits`

| Column | Type | Description |
|--------|------|-------------|
| `id` | bigserial | Primary key |
| `symbol` | varchar(20) | Stock symbol (foreign key to stocks) |
| `split_date` | date | Date of the split |
| `split_ratio` | numeric(12,8) | Decimal ratio (2:1 = 2.0, 3:2 = 1.5) |
| `numerator` | integer | Numerator (3 in 3:2 split) |
| `denominator` | integer | Denominator (2 in 3:2 split) |
| `split_string` | varchar(20) | Human-readable format ("3:2") |
| `description` | text | Optional description from provider |
| `source` | varchar(50) | Data source (FMP, Alpha Vantage, Yahoo) |
| `created_at` | timestamptz | Record creation timestamp |
| `updated_at` | timestamptz | Record update timestamp |

**Indexes:**
- `idx_splits_symbol` - Fast symbol lookups
- `idx_splits_date` - Fast date filtering
- `idx_splits_symbol_date` - Optimized for symbol + date queries

**Constraints:**
- `unique_symbol_split_date` - Prevents duplicate splits for same symbol/date

## Setup

### 1. Create the Table

```bash
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d postgres -f migrations/create_stock_splits.sql
```

### 2. Restart Supabase REST API

After creating new tables, restart the REST service to reload the schema:

```bash
/Applications/Docker.app/Contents/Resources/bin/docker restart dividend-tracker-supabase-rest
```

## Usage

### Fetch Splits for All Stocks

```bash
python fetch_stock_splits.py
```

### Fetch Splits for Specific Symbol(s)

```bash
# Single symbol
python fetch_stock_splits.py --symbol AAPL

# Multiple symbols
python fetch_stock_splits.py --symbols AAPL NVDA TSLA GOOGL AMZN
```

### Limit Number of Stocks

```bash
python fetch_stock_splits.py --limit 100
```

### Recent Stocks Only (Last 30 Days)

```bash
python fetch_stock_splits.py --recent-only
```

### Adjust Parallel Workers

```bash
python fetch_stock_splits.py --workers 10
```

## Example Output

```
================================================================================
📊 FETCHING STOCK SPLITS DATA
================================================================================
✅ Processing 5 symbols
🔄 Using 5 parallel workers
📡 Data sources: FMP → Alpha Vantage → Yahoo Finance

  ✅ [FMP] AAPL: 5 split(s)
  ✅ [FMP] NVDA: 6 split(s)
  ✅ [FMP] TSLA: 2 split(s)
  ✅ [FMP] GOOGL: 2 split(s)
  ✅ [FMP] AMZN: 4 split(s)
  💾 Saved final batch of 19 splits

================================================================================
✅ STOCK SPLITS FETCH COMPLETE
================================================================================
Total symbols processed: 5
Symbols with splits: 5 (100%)
Total splits found: 19
No splits found: 0

📊 Data Source Statistics:
  FMP: 5 symbols
================================================================================
```

## Query Examples

### Get All Splits for a Symbol

```sql
SELECT * FROM stock_splits
WHERE symbol = 'AAPL'
ORDER BY split_date DESC;
```

### Recent Splits (Last Year)

```sql
SELECT symbol, split_date, split_string, split_ratio
FROM stock_splits
WHERE split_date >= NOW() - INTERVAL '1 year'
ORDER BY split_date DESC;
```

### Symbols with Most Splits

```sql
SELECT symbol, COUNT(*) as split_count
FROM stock_splits
GROUP BY symbol
ORDER BY split_count DESC
LIMIT 10;
```

### Largest Split Ratios

```sql
SELECT symbol, split_date, split_string, split_ratio
FROM stock_splits
WHERE split_ratio >= 10
ORDER BY split_ratio DESC;
```

## Integration with Other Scripts

The stock splits data can be used to:
- Adjust historical price data
- Correct dividend per share calculations
- Normalize volume data
- Calculate split-adjusted returns

## Data Sources

### FMP (Primary)
- **Endpoint**: `/historical-price-full/stock_split/{symbol}`
- **Coverage**: Comprehensive historical splits
- **Format**: Provides numerator/denominator directly
- **Rate Limit**: Conservative (10 concurrent requests)

### Alpha Vantage (Secondary)
- **Note**: Limited split data in free tier
- **Currently**: Returns None (no dedicated splits endpoint)
- **Future**: Can be enhanced if needed

### Yahoo Finance (Fallback)
- **Library**: yfinance
- **Coverage**: Good historical coverage
- **Format**: Provides decimal ratio
- **Note**: Requires `pip install yfinance`

## Files Created

- `migrations/create_stock_splits.sql` - Database schema
- `fetch_stock_splits.py` - Main fetching script
- `stock_splits.log` - Execution log file
- `STOCK_SPLITS_README.md` - This documentation

## Troubleshooting

### "JSON could not be generated" Error

This occurs when Supabase REST API hasn't loaded the new table schema:

```bash
/Applications/Docker.app/Contents/Resources/bin/docker restart dividend-tracker-supabase-rest
```

### No Splits Found

- Not all stocks have split history
- Some ETFs may never split
- Check if symbol exists in stocks table first

### Rate Limiting

If you encounter rate limits:
- Reduce `--workers` parameter (default: 5)
- The script includes built-in rate limiting
- FMP: 10 concurrent requests max
- Alpha Vantage: 5 per minute (12 second delay)

## Future Enhancements

- [ ] Reverse splits detection (ratio < 1.0)
- [ ] Split announcements (future splits)
- [ ] Automatic price/dividend adjustment
- [ ] Integration with portfolio calculations
- [ ] Historical split calendar view
