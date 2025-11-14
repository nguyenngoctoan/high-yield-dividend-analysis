# Discovery Phase Optimization

## Problem Statement

The discovery phase was validating symbols that already had price data in the database, wasting time and API calls on unnecessary validation.

## Solution Implemented

### 1. Skip Symbols with Existing Price Data

**Before**: Discovery validated ALL discovered symbols, even if they already had price data.

**After**: Discovery now skips symbols that:
- Already have price data in `raw_stocks` (price IS NOT NULL)
- Are in the excluded symbols table (`raw_excluded_symbols`)

### 2. SQL-Based Filtering (Not Python)

**Before**:
```python
# Fetched ALL symbols into Python, then filtered
all_records = supabase_select('raw_stocks', 'symbol', limit=None)  # 19,205 symbols
excluded = supabase_select('raw_excluded_symbols', 'symbol', limit=None)
# Then filter in Python
```

**After**:
```python
# Filter using SQL IN clause - only fetch symbols that need checking
skip_with_prices = supabase.table('raw_stocks') \
    .select('symbol') \
    .not_.is_('price', 'null') \
    .in_('symbol', symbol_strings) \  # Only check discovered symbols
    .execute()
```

## Performance Impact

### Discovery Metrics (Weekly Run)

**Example Scenario**:
- Discovered symbols: 20,000 (from FMP API)
- Already in DB with prices: 18,000
- Excluded: 500
- **Symbols to validate: 1,500** (instead of 20,000)

**Time Saved**:
- Validation: ~18,500 symbols × 2 seconds = **10 hours saved**
- API calls avoided: ~55,500 (3 calls per symbol × 18,500)

### SQL Performance

**Before** (Python filtering):
- 2 full table scans: `raw_stocks` (19,205 rows) + `raw_excluded_symbols` (~500 rows)
- Memory: Load all symbols into Python sets
- Time: ~5-10 seconds

**After** (SQL filtering):
- 2 targeted queries with IN clause (only checks discovered symbols)
- Memory: Minimal (only symbols to skip)
- Time: ~1-2 seconds

## Code Changes

### File: `update_stock_v2.py`

**Lines 98-183**: Completely rewrote discovery filtering logic

**Key Changes**:
1. Query `raw_stocks` with `.in_('symbol', discovered_symbols)` to only check relevant symbols
2. Filter by `price IS NOT NULL` in SQL, not Python
3. Query `raw_excluded_symbols` with `.in_('symbol', discovered_symbols)`
4. Combine skip lists and filter discovered symbols

## Validation Logic

The optimization maintains the same validation logic:

1. **Skip**: Symbols in `raw_stocks` with price data (already processed successfully)
2. **Skip**: Symbols in `raw_excluded_symbols` (already failed validation)
3. **Validate**: Symbols in `raw_stocks` without prices (need retry)
4. **Validate**: Completely new symbols (need initial validation)

## How to Verify

Run discovery mode and check the logs:

```bash
python3 update_stock_v2.py --mode discover --validate
```

Look for these log lines:
```
📊 Analyzing existing symbols...
   18,000 symbols with price data
   1,205 symbols without price data
   500 previously excluded symbols
🔍 Filtering discovered symbols using SQL...
   18,000 discovered symbols already have prices (skip)
   500 discovered symbols are excluded (skip)
📊 Validation queue: 1,500 symbols (skipped 18,500 already processed)
⚡ DISCOVERY OPTIMIZATION: SQL filtering complete
```

## Future Enhancements

1. **Add index**: `CREATE INDEX idx_raw_stocks_price_not_null ON raw_stocks(symbol) WHERE price IS NOT NULL;`
2. **Batch IN queries**: If discovered symbols > 10,000, batch the IN queries to avoid URL length limits
3. **Cache excluded symbols**: Store excluded symbols in memory for the session
4. **Use RPC function**: Create a PostgreSQL function for even faster filtering

## Maintenance Notes

- Discovery runs **weekly on Sundays** (see `daily_update_v3_parallel.sh` line 188)
- The `raw_stocks.price` field is updated by the price processor
- Excluded symbols are added automatically when validation fails
- If a symbol was excluded but later becomes valid, remove it from `raw_excluded_symbols`
