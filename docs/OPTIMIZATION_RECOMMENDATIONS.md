# Daily Sync Optimization Recommendations

## Current Performance Issues

The daily sync is processing **19,205 symbols** and takes ~1 hour. Analysis shows major bottlenecks in:

1. **Discovery Phase**: Fetches ALL symbols to check existence (not critical - only runs weekly)
2. **Update Phase**: Fetches ALL symbols, then filters in Python (HIGH IMPACT)
3. **Price Fetching**: Doesn't check if prices already exist for today/yesterday (MEDIUM IMPACT)

## Recommended Optimizations

### 1. Database-Level Staleness Filtering (HIGH IMPACT - 50% time savings)

**Current Behavior** (update_stock_v2.py:244-265):
```python
# Step 1: Fetch ALL symbols from database (~19,205)
db_symbols = supabase_select('raw_stocks', 'symbol', limit=None)
symbols = [s['symbol'] for s in db_symbols]

# Step 2: Filter in Python (makes another query!)
symbols, skipped = IncrementalProcessor.filter_stale_symbols(symbols, 20)
```

**Optimized Approach**:
```python
# Fetch only stale symbols in a SINGLE query
from datetime import datetime, timedelta

cutoff = (datetime.now() - timedelta(hours=20)).isoformat()

# Query Supabase with filter
from supabase_helpers import get_supabase_client
supabase = get_supabase_client()

result = supabase.table('raw_stocks') \
    .select('symbol') \
    .lt('updated_at', cutoff) \
    .execute()

symbols = [s['symbol'] for s in result.data]
logger.info(f"✅ Found {len(symbols):,} stale symbols (updated > 20h ago)")
```

**Expected Impact**:
- Reduces symbols to process from ~19,205 to ~5,000 (estimated 70% have been updated recently)
- Saves ~45 minutes of processing time

### 2. Skip Symbols with Recent Price Data (MEDIUM IMPACT - 30% additional savings)

**Add to update_stock_v2.py after line 265**:

```python
# Additional optimization: Skip symbols that already have today's or yesterday's prices
from datetime import date, timedelta

today = date.today()
yesterday = today - timedelta(days=1)

logger.info("🔍 Checking which symbols already have recent price data...")

# Query for symbols with recent price data
from supabase_helpers import get_supabase_client
supabase = get_supabase_client()

result = supabase.table('raw_stock_prices') \
    .select('symbol') \
    .gte('date', str(yesterday)) \
    .execute()

symbols_with_recent_prices = {r['symbol'] for r in result.data}

# Filter out symbols with recent prices
original_count = len(symbols)
symbols = [s for s in symbols if s not in symbols_with_recent_prices]

logger.info(
    f"⚡ PRICE DATA FILTER: Processing {len(symbols):,} symbols "
    f"(skipped {original_count - len(symbols):,} with recent prices)"
)
```

**Expected Impact**:
- Further reduces symbols from ~5,000 to ~3,500
- Saves additional ~15 minutes

### 3. Combined Optimization Strategy

**Modify update_stock_v2.py lines 244-269**:

```python
if symbols is None:
    logger.info("📊 Fetching stale symbols from database...")

    from supabase_helpers import get_supabase_client
    from datetime import date, timedelta
    supabase = get_supabase_client()

    # OPTIMIZATION 1: Query only stale symbols (updated > 20h ago)
    if skip_recently_updated:
        cutoff = (datetime.now() - timedelta(hours=staleness_hours)).isoformat()

        result = supabase.table('raw_stocks') \
            .select('symbol') \
            .lt('updated_at', cutoff) \
            .execute()

        symbols = [s['symbol'] for s in result.data]
        logger.info(f"✅ Found {len(symbols):,} stale symbols (>{staleness_hours}h old)")

        # OPTIMIZATION 2: Skip symbols with recent price data
        today = date.today()
        yesterday = today - timedelta(days=1)

        price_result = supabase.table('raw_stock_prices') \
            .select('symbol') \
            .gte('date', str(yesterday)) \
            .execute()

        symbols_with_prices = {r['symbol'] for r in price_result.data}
        original_count = len(symbols)
        symbols = [s for s in symbols if s not in symbols_with_prices]

        skipped_with_prices = original_count - len(symbols)

        logger.info(
            f"⚡ COMBINED FILTERS: Processing {len(symbols):,} symbols"
        )
        logger.info(f"   Skipped due to recent update: {19205 - original_count:,}")
        logger.info(f"   Skipped due to recent prices: {skipped_with_prices:,}")

        # Estimate time saved
        total_skipped = 19205 - len(symbols)
        time_saved_min = total_skipped * 0.2  # ~12 seconds per symbol = 0.2 min
        logger.info(f"⏱️  Estimated time saved: ~{int(time_saved_min)}min")
    else:
        # No filtering - fetch all symbols
        result = supabase.table('raw_stocks').select('symbol').execute()
        symbols = [s['symbol'] for s in result.data]
        logger.info(f"✅ Found {len(symbols):,} symbols in database")

if not symbols:
    logger.warning("⚠️  No symbols to update")
    return {'prices': 0, 'dividends': 0, 'companies': 0}
```

### 4. Discovery Phase Optimization (LOW PRIORITY - only runs weekly)

**Current**: Fetches ALL symbols to check existence (lines 104-110)
**Optimized**: Use database COUNT or EXISTS query

This is already optimized well enough since it only runs weekly.

## Expected Overall Performance Improvement

| Phase | Current Time | Optimized Time | Savings |
|-------|-------------|----------------|---------|
| Discovery | 5 min | 5 min | 0 min (weekly only) |
| Update (Prices) | 50 min | 15 min | 35 min |
| Update (Dividends) | 10 min | 3 min | 7 min |
| Update (Companies) | 5 min | 2 min | 3 min |
| **TOTAL** | **70 min** | **25 min** | **45 min (64% faster)** |

## Implementation Priority

1. **HIGH PRIORITY**: Database-level staleness filtering (Optimization #1)
2. **HIGH PRIORITY**: Skip symbols with recent price data (Optimization #2)
3. **LOW PRIORITY**: Discovery phase optimization (already runs weekly)

## Additional Notes

- The bulk latest dates function exists but times out on large datasets
- Consider adding composite indexes:
  - `raw_stocks(updated_at, symbol)`
  - `raw_stock_prices(date, symbol)`
- Monitor API rate limits - faster processing = more concurrent requests
