# Batch Processing Analysis & Optimization Opportunities

## Current State

### How It Works Now

**Price Processing**: `lib/processors/price_processor.py`

```python
# Current: process_batch() uses ThreadPoolExecutor with 30 workers
with ThreadPoolExecutor(max_workers=30) as executor:
    futures = {executor.submit(process_symbol, symbol): symbol for symbol in symbols}
    # Each symbol makes 1 API call: GET /api/v3/historical-price-full/{symbol}
```

**Problem**:
- ✅ **Already parallelized** (30 concurrent requests)
- ❌ **One API call per symbol** for historical data
- ❌ Rate: ~3-5 symbols/second (varies with network, API response time)
- ❌ For 19,205 symbols: ~1-2 hours of API calls

## FMP API Limitations

### What FMP Supports:

1. **Batch Quote (Current Prices Only)** ✅
   - Endpoint: `/stable/batch-quote?symbols=AAPL,MSFT,GOOGL`
   - Returns: Current quote data only (no historical)
   - Limit: Unknown (probably 50-100 symbols per request)

2. **Batch EOD by Date** ✅ (Professional/Enterprise only)
   - Endpoint: `/api/v4/batch-request-end-of-day-prices?date=2021-05-18`
   - Returns: ALL symbols' prices for ONE specific date
   - Format: CSV
   - Problem: Need to call once per date for historical data

3. **Historical Prices per Symbol** ✅ (Current method)
   - Endpoint: `/api/v3/historical-price-full/{symbol}?from=2020-01-01`
   - Returns: All historical prices for ONE symbol
   - **This is the ONLY way to get historical data per symbol**

### What FMP Does NOT Support:

❌ **Batch Historical Prices** (multiple symbols, date range)
- No endpoint like: `/api/v3/historical-price-full?symbols=AAPL,MSFT&from=2020-01-01`
- Would need FMP API v5 or custom enterprise endpoint

## Current Performance

From logs analysis:

```
📊 Processing prices for 19,205 symbols with 30 workers
Processing rate: ~3-5 symbols/second
Total time: ~60-90 minutes
```

### Breakdown:
- API call time: ~200-500ms per symbol
- Network latency: ~50-100ms
- Database upsert: ~50-100ms per batch
- **Bottleneck: FMP API response time**

## Optimization Opportunities

### 1. ✅ **Already Implemented: Parallel Processing**

Current: 30 concurrent workers (FMP Professional plan allows 750 req/min = 12.5 req/sec)

```python
max_workers = Config.API.FMP_CONCURRENT_REQUESTS  # 30
```

**Status**: Optimal for current API rate limits

### 2. ⚡ **NEW: Use Batch EOD for Recent Data**

For recent data (last 30 days), use batch EOD endpoint:

**Before**:
```python
# 19,205 API calls to get last 30 days
for symbol in symbols:
    GET /api/v3/historical-price-full/{symbol}?from=30_days_ago
```

**After**:
```python
# 30 API calls to get all symbols' data
for day in last_30_days:
    GET /api/v4/batch-request-end-of-day-prices?date={day}
    # Returns CSV with ALL symbols for that date
```

**Savings**:
- Calls: 19,205 → 30 (99.8% reduction!)
- Time: ~90 min → ~30 seconds for recent data

**Limitation**: Only works for recent data; still need per-symbol calls for historical backfill

### 3. ⚡ **NEW: Increase Concurrent Workers**

FMP Professional allows 750 requests/min = 12.5 req/sec

**Current**: 30 workers ≈ 3-5 req/sec (underutilized!)

**Optimized**: Increase to 50-60 workers

```python
FMP_CONCURRENT_REQUESTS = 60  # Up from 30
```

**Expected improvement**:
- Rate: 3-5 → 8-10 symbols/second
- Time: 90 min → 35-40 min

### 4. ⚡ **NEW: Smart Incremental Updates**

Currently uses incremental logic (checks last date in DB), but can optimize further:

**Add**: Bulk query to get last update dates for ALL symbols in one query

```python
# NEW: Get last price dates for all symbols at once
last_dates = IncrementalProcessor.get_bulk_latest_dates('raw_stock_prices', 'date')

# Then for each symbol, calculate from_date
for symbol in symbols:
    from_date = last_dates.get(symbol, default_5_years_ago)
    # Fetch only new data
```

**Note**: This function exists but may timeout (see line 165 in `incremental_processor.py`)

### 5. ⚡ **NEW: Database Batch Optimization**

Currently upserting in batches of 250:

```python
UPSERT_BATCH_SIZE = 250  # In config.py
```

**Optimize**: Group by symbol and batch across symbols

```python
# Instead of: process symbol 1 (fetch + store) → symbol 2 (fetch + store)
# Do: fetch symbols 1-50 → batch store all → fetch 51-100 → batch store all
```

### 6. ⚡ **NEW: Use Latest Quote First**

Before fetching full historical data, get latest quote to validate symbol:

```python
# Batch call for 50 symbols at once
quotes = GET /stable/batch-quote?symbols=AAPL,MSFT,GOOGL,...

# Filter out symbols with no quote (invalid/delisted)
valid_symbols = [s for s in symbols if s in quotes]

# Only fetch historical for valid symbols
for symbol in valid_symbols:
    fetch_historical(symbol)
```

**Savings**: Skip historical calls for delisted/invalid symbols

## Recommended Implementation Order

### Phase 1: Quick Wins (1-2 hours to implement)

1. **Increase concurrent workers to 60** ✅
   - Change `FMP_CONCURRENT_REQUESTS = 60` in `config.py`
   - Expected: 2x speedup (90 min → 45 min)

2. **Use batch quote validation** ⚡
   - Add batch quote check before historical fetch
   - Skip invalid symbols early
   - Expected: 10-20% fewer API calls

### Phase 2: Batch EOD Integration (4-6 hours)

3. **Implement batch EOD for recent data** ⚡⚡⚡
   - Use batch EOD for last 30 days
   - Fall back to per-symbol for older data
   - Expected: 50% reduction in daily update time

### Phase 3: Advanced Optimizations (8+ hours)

4. **Better incremental updates with bulk queries** ⚡
5. **Cross-symbol batch database operations** ⚡
6. **Caching layer for frequently accessed data** ⚡

## FMP API Costs

**Current Usage** (per daily run):
- Price calls: ~19,205 requests
- Dividend calls: ~19,205 requests
- **Total**: ~38,410 requests/day

**With Optimizations**:
- Price calls: ~30 (batch EOD) + ~5,000 (historical backfill) = ~5,030
- Dividend calls: ~19,205 (no batch endpoint available)
- **Total**: ~24,235 requests/day

**Savings**: 37% reduction in API calls

## Alternative: Switch to Different API

If FMP limitations are too restrictive, consider:

1. **Polygon.io**: Batch historical data supported
2. **IEX Cloud**: Better batch endpoints
3. **Alpha Vantage Premium**: Batch support
4. **Direct Exchange Data**: NASDAQ/NYSE feeds

## Conclusion

**Current bottleneck is NOT the code - it's the FMP API design**

The code is already well-optimized with:
- ✅ Parallel processing (30 workers)
- ✅ Batch database operations
- ✅ Incremental updates
- ✅ Hybrid fallback logic

**Easiest wins**:
1. Increase workers to 60 (2x speedup)
2. Add batch quote validation (10-20% reduction)
3. Implement batch EOD for recent data (50% speedup for daily updates)

**Expected final performance**:
- Current: ~90 minutes for full update
- After optimizations: ~20-30 minutes for daily update
