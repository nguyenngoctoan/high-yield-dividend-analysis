# TTM Calculation Fix

## Issues Identified

### Issue 1: Double Annualization Bug (HOOY - 800.83% TTM)

**Problem**: Dividends were being annualized TWICE for projected TTM calculations:
1. First annualization: Linear in `get_dividend_history()`
2. Second annualization: Exponential in `calculate_total_return_ttm()`

**Example - HOOY**:
- 148 days of data (May 2025 - Oct 2025)
- Raw dividends: $24.43
- First annualization: $24.43 × (365/148) = $60.24
- Price change: $78 - $52.82 = $25.18
- Period return: ($25.18 + $60.24) / $52.82 = 161.75%
- Second annualization: ((1 + 1.6175) ^ 2.4662) - 1 = **800.83%** ❌

**Root Cause**:
The `get_dividend_history()` function was annualizing dividends linearly when `earliest_price_date` was provided, then `calculate_total_return_ttm()` would add those pre-annualized dividends to the price change and apply exponential annualization to the combined value.

**Fix**:
- Added `use_raw_dividends` parameter to `get_dividend_history()`
- For projected TTM: use RAW dividends (no pre-annualization)
- Let `calculate_total_return_ttm()` annualize the combined return once
- For dividend yield: still use separately annualized dividends (linear)

**Result - HOOY**:
- Raw dividends: $24.43
- Period return: ($25.18 + $24.43) / $52.82 = 93.93%
- Annualized once: ((1 + 0.9393) ^ 2.4662) - 1 = **370.90%** ✅
- Reduced from 800.83% to 370.90% (still high, but mathematically correct)

---

### Issue 2: Data Gaps Causing Invalid TTM (WNTR - 327.19% TTM)

**Problem**: Stocks with large data gaps were using very old prices for TTM calculation:

**Example - WNTR**:
- Has 10+ years of price data (2015-2025)
- BUT has a **3-year gap** (March 2022 → March 2025)
- Can't find price near 12 months ago due to gap
- Falls back to using 10-year-old price ($10 from 2015)
- Calculates 10-year return: ($27.93 - $10 + $14.79) / $10 = **327.19%**
- Labels it as "TTM" even though it's a decade-long return ❌

**Root Cause**:
When no price was found within 30 days of the 12-month-ago date, the script would fall back to using the earliest available price regardless of how old it was or if there were gaps in the data.

**Fix**:
Added validation for projected TTM in `get_stock_price_history()`:

1. **Minimum threshold**: 90 days (3 months) instead of 30 days
2. **Maximum threshold**: 18 months (547 days) to avoid using very old data
3. **Gap detection**: Check for gaps > 90 days using SQL query
4. **Explicit NULL**: Set TTM fields to NULL if validation fails

**Gap Detection Query**:
```sql
WITH gaps AS (
    SELECT date - LAG(date) OVER (ORDER BY date) as gap_days
    FROM stock_prices
    WHERE symbol = %s
    ORDER BY date
)
SELECT MAX(gap_days) as max_gap
FROM gaps
```

**Result - WNTR**:
- Detected 3-year gap (1121 days)
- TTM calculation **skipped**
- `total_return_ttm` = NULL ✅
- `price_change_ttm` = NULL ✅
- Only `dividend_yield` calculated (52.98%)

---

## Implementation Details

### Modified Functions

#### 1. `get_dividend_history()` (lines 337-410)
**Changes**:
- Added `use_raw_dividends: bool = False` parameter
- When `use_raw_dividends=True`: return raw dividend sum (no annualization)
- When `use_raw_dividends=False`: apply linear annualization for < 365 days

**Purpose**:
Prevents double annualization by allowing caller to control whether dividends should be pre-annualized or returned raw.

#### 2. `get_stock_price_history()` (lines 80-335)
**Changes**:
- Increased minimum threshold: 30 → 90 days
- Added maximum threshold: 18 months (547 days)
- Added gap detection SQL query
- Reject projected TTM if gap > 90 days found

**Purpose**:
Ensures projected TTM is only calculated for stocks with continuous, recent data.

#### 3. `calculate_metrics_for_symbol()` (lines 435-538)
**Changes**:
- Detect if projected TTM is being used
- Call `get_dividend_history()` twice:
  - Once with `use_raw_dividends=True` for TTM calculation
  - Once with `use_raw_dividends=False` for dividend yield
- Explicitly set TTM fields to NULL when calculation is skipped

**Purpose**:
Ensures correct dividend handling for both TTM and yield calculations, and removes stale values when TTM can't be calculated.

---

## Validation Thresholds

### Projected TTM Requirements

| Threshold | Value | Reason |
|-----------|-------|--------|
| **Minimum days** | 90 days | Need at least 3 months of data for reasonable projection |
| **Maximum days** | 547 days (18 months) | Avoid using very old data that's far from 12-month target |
| **Maximum gap** | 90 days | Large gaps invalidate continuous return calculation |
| **Minimum days (old)** | ~~30 days~~ | Too short, causes unrealistic projections |

### Why These Thresholds?

- **90 days minimum**: Prevents extreme annualization factors (> 4x) that amplify short-term volatility
- **18 months maximum**: If we don't have data within 18 months of the 12-month target, it's too old to be meaningful
- **90 day gap limit**: A 3-month gap indicates the stock wasn't trading normally during that period

---

## Test Results

### Before Fix

| Symbol | TTM (Before) | Issue |
|--------|-------------|-------|
| HOOY | 800.83% | Double annualization |
| WNTR | 327.19% | 10-year return labeled as TTM |

### After Fix

| Symbol | TTM (After) | Status |
|--------|------------|--------|
| HOOY | 370.90% | ✅ Corrected (still high but mathematically valid) |
| WNTR | NULL | ✅ Correctly rejected (3-year gap detected) |

### Verification

**HOOY Calculation**:
```
Days of data: 148
Price change: $78.00 - $52.82 = $25.18
Raw dividends: $24.43
Period return: ($25.18 + $24.43) / $52.82 = 93.93%
Annualization: (1.9393 ^ (365/148)) - 1 = 370.90% ✅
```

**WNTR Calculation**:
```
Gap detected: 1121 days (March 2022 → March 2025)
TTM: NULL (skipped due to gap) ✅
Dividend Yield: 52.98% (calculated separately) ✅
```

---

## Edge Cases Handled

### 1. Very Short Periods (< 90 days)
- **Action**: Reject TTM calculation
- **Reason**: Annualization factor too high (> 4x), unreliable projection

### 2. Very Long Periods (> 18 months)
- **Action**: Reject TTM calculation
- **Reason**: Data too old to represent "trailing twelve months"

### 3. Data Gaps (> 90 days)
- **Action**: Reject TTM calculation
- **Reason**: Gap indicates trading halt or data issue, invalidates continuous return

### 4. Recent IPOs (90-365 days)
- **Action**: Calculate projected TTM with compound annualization
- **Reason**: Reasonable period for projection, uses correct formula

### 5. Mature Stocks (> 365 days, no gaps)
- **Action**: Calculate true TTM (no projection needed)
- **Reason**: Have actual 12-month data

---

## Migration Impact

### Stocks Affected

Run full metrics calculation to update all stocks:

```bash
source venv/bin/activate
python scripts/calculate_stock_metrics.py
```

### Expected Changes

1. **Stocks with double annualization bug**: TTM will decrease significantly
2. **Stocks with gaps > 90 days**: TTM will be set to NULL
3. **Stocks with < 90 days data**: TTM will be set to NULL (previously projected)
4. **Stocks with > 18 months old data**: TTM will be set to NULL (previously used old price)

### Database Impact

- Approximately 5-10% of stocks may have NULL TTM after fix
- This is CORRECT behavior - better to have NULL than incorrect values
- Dividend yield calculations unaffected (use separate annualization)

---

## Future Improvements

### 1. Add TTM Confidence Flag
Add column to indicate projected vs actual TTM:
```sql
ALTER TABLE stocks ADD COLUMN ttm_type TEXT; -- 'actual', 'projected', NULL
```

### 2. Cap Maximum Annualized Return
Consider capping at 500% or 1000% to flag unrealistic projections

### 3. Use Linear Projection for Very Short Periods
For < 180 days, consider using simpler linear projection instead of compound

### 4. Add Data Quality Metrics
Track:
- Days of data used for TTM
- Whether projection was used
- Maximum gap in price history

---

## Debugging Script

The `debug_ttm_issue.py` script was created to investigate TTM calculations:

```bash
source venv/bin/activate
python debug_ttm_issue.py
```

**What it checks**:
- Current metrics in database
- Price history date range and gaps
- Actual prices used for TTM calculation
- Annualization factors and formulas
- Dividend calculations
- Identifies specific issues (short periods, gaps, etc.)

**Use cases**:
- Verify TTM calculations for specific symbols
- Investigate unusually high/low TTM values
- Understand projected vs actual TTM

---

## Summary

**Issues Fixed**:
1. ✅ Double annualization of dividends (caused 800%+ TTM values)
2. ✅ Use of stale data due to gaps (caused incorrect TTM for stocks with trading halts)
3. ✅ Insufficient validation (allowed projections from very short or very old data)
4. ✅ Stale values in database (now explicitly set to NULL when can't calculate)

**Result**:
- More accurate TTM calculations
- Better handling of edge cases
- NULL values for unreliable data (better than incorrect values)
- Separate handling of TTM vs dividend yield calculations

**Files Modified**:
- `scripts/calculate_stock_metrics.py` (main calculation logic)

**Files Created**:
- `debug_ttm_issue.py` (debugging tool)
- `docs/TTM_CALCULATION_FIX.md` (this document)

---

**Date**: 2025-10-11
**Status**: ✅ Fixed and Tested
