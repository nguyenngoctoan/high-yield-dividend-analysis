# API Enhancements Changelog

## Version 1.1.0 - Industry-Standard Improvements

### Overview

Updated the Dividend API to match industry-leading APIs (Polygon, IEX Cloud, Twelve Data) with enhanced date filtering, preset ranges, and flexible query options.

---

## Prices Endpoints

### `/v1/prices/{symbol}` - Enhanced

**New Parameters:**

1. **`range`** (NEW) - Preset time ranges
   - Options: `1d`, `5d`, `1m`, `3m`, `6m`, `ytd`, `1y`, `2y`, `5y`, `max`
   - Example: `/prices/AAPL?range=1y`
   - Overrides `start_date`/`end_date` if provided

2. **`sort`** (NEW) - Control sort order
   - Options: `asc` (oldest first), `desc` (newest first)
   - Default: `desc`
   - Example: `/prices/AAPL?range=1m&sort=asc`

3. **`adjusted`** (NEW) - Choose price type
   - Options: `true` (adjusted for splits/dividends), `false` (raw)
   - Default: `true`
   - Example: `/prices/AAPL?adjusted=false`

4. **`limit`** (ENHANCED)
   - Previous max: 1000
   - New max: 5000
   - Default: 100

**Enhanced Behaviors:**

- **start_date only**: Now goes to current date (was: required both dates)
  ```
  /prices/AAPL?start_date=2023-01-01  → Jan 1, 2023 to today
  ```

- **end_date only**: Returns 30 days before end_date
  ```
  /prices/AAPL?end_date=2024-01-31  → Jan 1 to Jan 31, 2024
  ```

- **No parameters**: Last 30 days (unchanged)
  ```
  /prices/AAPL  → Last 30 days
  ```

**New Examples:**

```bash
# Preset ranges
GET /prices/AAPL?range=ytd          # Year to date
GET /prices/AAPL?range=1y           # Last year
GET /prices/AAPL?range=max          # All available data

# Flexible date filtering
GET /prices/AAPL?start_date=2023-01-01              # Jan 1, 2023 to today
GET /prices/AAPL?start_date=2023-01-01&end_date=2023-12-31  # Full year 2023

# Sort control
GET /prices/AAPL?range=1m&sort=asc  # Last month, oldest first
GET /prices/AAPL?range=1m&sort=desc # Last month, newest first (default)

# Adjusted vs raw prices
GET /prices/AAPL?range=1y&adjusted=true   # Split/dividend adjusted
GET /prices/AAPL?range=1y&adjusted=false  # Raw prices

# Combined
GET /prices/AAPL?range=1y&sort=asc&adjusted=false&limit=500
```

**Error Handling:**

- Invalid range → 400 Bad Request with helpful message
- Invalid sort → 400 Bad Request
- Maintains existing 404 for symbol not found

---

## Dividends Endpoints

### `/v1/dividends/calendar` - Enhanced

**New Parameters:**

1. **`range`** (NEW) - Preset time ranges
   - Options: `1w`, `1m`, `3m`, `6m`, `1y`
   - Example: `/dividends/calendar?range=1m`
   - Overrides `start_date`/`end_date` if provided

2. **`sort`** (NEW) - Control sort order
   - Options: `asc` (earliest first), `desc` (latest first)
   - Default: `asc` (makes sense for calendars - show upcoming first)
   - Example: `/dividends/calendar?range=3m&sort=desc`

3. **`limit`** (ENHANCED)
   - Previous max: 1000
   - New max: 5000
   - Default: 100

**Enhanced Behaviors:**

- **start_date only**: Now adds 90 days (was: required end_date)
  ```
  /dividends/calendar?start_date=2024-01-01  → Jan 1 to Mar 31, 2024
  ```

- **end_date only**: Returns 90 days before end_date
  ```
  /dividends/calendar?end_date=2024-03-31  → Jan 1 to Mar 31, 2024
  ```

- **No parameters**: Next 90 days from today (unchanged)
  ```
  /dividends/calendar  → Next 90 days
  ```

**New Examples:**

```bash
# Preset ranges
GET /dividends/calendar?range=1w            # Next week
GET /dividends/calendar?range=1m            # Next month
GET /dividends/calendar?range=3m            # Next 3 months

# Flexible date filtering
GET /dividends/calendar?start_date=2024-01-01              # Jan 1 + 90 days
GET /dividends/calendar?start_date=2024-01-01&end_date=2024-12-31  # Full year 2024

# Combined with filters
GET /dividends/calendar?range=1m&symbols=AAPL,MSFT         # AAPL/MSFT next month
GET /dividends/calendar?range=3m&min_yield=5.0             # High yield next 3 months
GET /dividends/calendar?range=1m&sort=desc                 # Next month, latest first

# Sort control
GET /dividends/calendar?range=1m&sort=asc   # Earliest ex-dates first (default)
GET /dividends/calendar?range=1m&sort=desc  # Latest ex-dates first
```

**Error Handling:**

- Invalid range → 400 Bad Request with helpful message
- Invalid sort → 400 Bad Request
- Maintains existing behavior for other errors

---

## Breaking Changes

**None!** All changes are backwards compatible:
- Existing queries continue to work unchanged
- New parameters are optional
- Default behaviors preserved where it makes sense
- Only enhancements and new options

---

## Comparison with Industry Standards

### Before (v1.0.0)
- ⚠️ Required both start/end dates for custom ranges
- ❌ No preset ranges
- ❌ Fixed sort order
- ❌ Max limit: 1000

**Rating: 7/10**

### After (v1.1.0)
- ✅ Flexible date parameters (start only, end only, both, neither)
- ✅ Preset ranges (`1d`, `1m`, `ytd`, etc.)
- ✅ Sort control (`asc`/`desc`)
- ✅ Adjusted prices option
- ✅ Max limit: 5000
- ✅ Comprehensive error messages

**Rating: 9/10** - On par with Polygon, IEX Cloud, Twelve Data

---

## Implementation Details

### Date Handling Logic

**Priority Order:**
1. If `range` parameter provided → Use preset range (overrides dates)
2. Else if `start_date` AND `end_date` → Use exact range
3. Else if `start_date` only → Add default period (30d for prices, 90d for dividends)
4. Else if `end_date` only → Subtract default period
5. Else → Use default (last 30d for prices, next 90d for calendar)

### Range Mappings

**Prices:**
```python
{
    '1d': 1,         # Last day
    '5d': 5,         # Last 5 days
    '1m': 30,        # Last month
    '3m': 90,        # Last 3 months
    '6m': 180,       # Last 6 months
    '1y': 365,       # Last year
    '2y': 730,       # Last 2 years
    '5y': 1825,      # Last 5 years
    'ytd': dynamic,  # Year to date
    'max': all       # All available data (back to 1990)
}
```

**Dividends Calendar:**
```python
{
    '1w': 7,         # Next week
    '1m': 30,        # Next month
    '3m': 90,        # Next 3 months
    '6m': 180,       # Next 6 months
    '1y': 365        # Next year
}
```

---

## Testing Examples

### Prices Endpoint

```bash
# Test range parameter
curl "http://localhost:8000/v1/prices/AAPL?range=1m&limit=5"

# Test start_date only (should go to today)
curl "http://localhost:8000/v1/prices/AAPL?start_date=2024-11-01&limit=5"

# Test sort ascending
curl "http://localhost:8000/v1/prices/AAPL?range=5d&sort=asc&limit=3"

# Test adjusted prices
curl "http://localhost:8000/v1/prices/AAPL?range=1y&adjusted=false&limit=5"

# Test ytd range
curl "http://localhost:8000/v1/prices/AAPL?range=ytd&limit=5"

# Test max range (all data)
curl "http://localhost:8000/v1/prices/AAPL?range=max&limit=10"
```

### Dividends Calendar

```bash
# Test range parameter
curl "http://localhost:8000/v1/dividends/calendar?range=1m&limit=5"

# Test start_date only (should add 90 days)
curl "http://localhost:8000/v1/dividends/calendar?start_date=2024-01-01&limit=5"

# Test with symbol filter
curl "http://localhost:8000/v1/dividends/calendar?range=3m&symbols=AAPL,MSFT&limit=10"

# Test sort descending
curl "http://localhost:8000/v1/dividends/calendar?range=1m&sort=desc&limit=5"
```

---

## Migration Guide

### For Existing Users

**No changes required!** All existing API calls continue to work:

```bash
# These all work exactly as before
GET /prices/AAPL
GET /prices/AAPL?start_date=2023-01-01&end_date=2023-12-31
GET /dividends/calendar
GET /dividends/calendar?start_date=2024-01-01&end_date=2024-03-31
```

### New Features to Adopt

Consider using these new features for better UX:

1. **Use preset ranges** for common queries:
   ```bash
   # Instead of calculating dates:
   # OLD: ?start_date=2024-01-01&end_date=2024-12-31
   # NEW: ?range=1y
   ```

2. **Omit end_date** when you want "from X to now":
   ```bash
   # OLD: ?start_date=2024-01-01&end_date=2024-11-13
   # NEW: ?start_date=2024-01-01
   ```

3. **Control sort order** for better data presentation:
   ```bash
   # Show oldest prices first for charting:
   ?range=1y&sort=asc
   ```

---

## Performance Impact

**Minimal to none:**
- Added logic is simple date arithmetic
- No new database queries
- Query structures unchanged
- Existing indexes still apply

**Benefits:**
- Reduced client-side date calculation
- Fewer invalid date combinations
- Better error messages reduce support burden

---

## Documentation Updates

Updated:
- OpenAPI/Swagger spec (auto-generated from FastAPI)
- Parameter descriptions with examples
- Docstrings with usage examples
- Error response documentation

---

## Future Enhancements (Not in v1.1.0)

**Possible v1.2.0 features:**
- Field filtering (`fields=date,close,volume`)
- Pagination (`page`, `cursor`)
- CSV format output (`format=csv`)
- Timezone support for intraday data
- Rate limiting headers

---

## Credits

Design inspired by:
- Polygon.io (excellent flexibility)
- IEX Cloud (preset ranges)
- Twelve Data (dual date/limit support)
- Financial Modeling Prep (clean date format)

---

## Summary

The v1.1.0 enhancements bring the Dividend API in line with industry standards while maintaining 100% backwards compatibility. Users can now:

✅ Use intuitive preset ranges like `range=1y` or `range=ytd`
✅ Specify only start_date and automatically go to present
✅ Control sort order for their use case
✅ Choose between adjusted and raw prices
✅ Handle larger datasets (up to 5000 results)

All while existing API consumers continue working without any code changes.
