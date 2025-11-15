# Historical Data Feature - DIVV()

**Date**: 2025-11-14
**Version**: 2.0.0

---

## Overview

The DIVV() function now supports historical price data, matching GOOGLEFINANCE()'s functionality for querying past stock prices.

---

## Syntax

```javascript
=DIVV(symbol, attribute, [startDate], [endDate])
```

### Parameters:
- **symbol** (required): Stock ticker symbol (e.g., "AAPL")
- **attribute** (required): Data attribute (e.g., "close", "open", "high", "low", "volume")
- **startDate** (optional): Start date for historical data
  - Can be a string: `"2024-01-15"`
  - Can be DATE() function: `DATE(2024, 1, 15)`
  - Can be cell reference: `A1` (containing a date)
- **endDate** (optional): End date for date range queries

---

## Usage Examples

### 1. Current Price (Free Tier)
```javascript
=DIVV("AAPL", "price")
// Returns: 175.43 (current price)
```

### 2. Historical Price - Single Date (Paid Tier)
```javascript
=DIVV("AAPL", "close", "2024-01-15")
// Returns: 185.59 (closing price on Jan 15, 2024)
```

### 3. Using DATE() Function (Paid Tier)
```javascript
=DIVV("AAPL", "close", DATE(2024, 1, 15))
// Returns: 185.59 (same as above)
```

### 4. Historical Price Range (Paid Tier)
```javascript
=DIVV("AAPL", "close", "2024-01-01", "2024-01-31")
// Returns: 2D array with [date, close] for each day in January 2024
```

### 5. Using Cell References (Paid Tier)
```javascript
// A1 contains: 2024-01-15
=DIVV("AAPL", "close", A1)
// Returns: 185.59
```

---

## Comparison with GOOGLEFINANCE()

| Feature | GOOGLEFINANCE() | DIVV() |
|---------|-----------------|--------|
| Current price | `=GOOGLEFINANCE("AAPL", "price")` | `=DIVV("AAPL", "price")` |
| Historical single date | `=GOOGLEFINANCE("AAPL", "price", DATE(2024,1,15))` | `=DIVV("AAPL", "close", "2024-01-15")` |
| Historical date range | `=GOOGLEFINANCE("AAPL", "price", DATE(2024,1,1), DATE(2024,1,31))` | `=DIVV("AAPL", "close", "2024-01-01", "2024-01-31")` |
| Dividend data | ❌ Limited | ✅ Complete |
| Free tier | ❌ No | ✅ Current data only |

---

## Available Attributes for Historical Data

### Price Attributes (Paid Tier):
- `close` - Closing price (default if not specified)
- `open` - Opening price
- `high` - Day's high price
- `low` - Day's low price
- `volume` - Trading volume

### Note on "price" Attribute:
When used with historical data, `"price"` is automatically mapped to `"close"` to match GOOGLEFINANCE() behavior.

---

## Date Format Support

The function accepts dates in multiple formats:

1. **ISO String**: `"2024-01-15"` (recommended)
2. **DATE() Function**: `DATE(2024, 1, 15)`
3. **Google Sheets Serial Number**: `45307` (automatically converted)
4. **Cell Reference**: Any cell containing a date

All dates are automatically converted to `YYYY-MM-DD` format for the API.

---

## Return Values

### Single Date Query:
Returns a single numeric value (the price for that date).

```javascript
=DIVV("AAPL", "close", "2024-01-15")
// Returns: 185.59
```

### Date Range Query:
Returns a 2D array with headers:

```javascript
=DIVV("AAPL", "close", "2024-01-01", "2024-01-05")
// Returns:
// | Date       | Close  |
// |------------|--------|
// | 2024-01-01 | 185.64 |
// | 2024-01-02 | 185.36 |
// | 2024-01-03 | 184.25 |
// | 2024-01-04 | 181.91 |
// | 2024-01-05 | 181.18 |
```

This output can be used directly for charting or analysis in Google Sheets.

---

## Tier Restrictions

### Free Tier ($0/mo):
- ✅ Current data: `=DIVV("AAPL", "price")`
- ❌ Historical data: Returns `#UPGRADE: Historical data requires a paid plan`

### Starter Tier+ ($9/mo):
- ✅ Current data
- ✅ Historical data (single date)
- ✅ Historical data (date ranges)
- ✅ All price attributes (open, high, low, close, volume)

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `#UPGRADE: Historical data requires a paid plan` | Using dates on free tier | Upgrade to Starter tier |
| `#N/A` | No data available for date | Check if date is valid trading day |
| `#ERROR: Invalid symbol` | Symbol not found | Verify ticker symbol is correct |
| `#ERROR: API error: 404` | Symbol has no historical data | Symbol may be too new or delisted |

---

## Technical Implementation

### API Endpoint Used:
```
GET /v1/prices/{symbol}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```

### Caching:
- Current data is cached for 5 minutes
- Historical data is NOT cached (it doesn't change)
- Consider implementing local caching for frequently accessed historical data

### Performance:
- Single date query: ~100-200ms
- Date range query: ~200-500ms (depending on range size)
- Results are returned from historical database (very fast)

---

## Example Use Cases

### 1. Track Portfolio Performance
```javascript
// A1: Symbol, B1: Purchase Date, C1: Purchase Price
// Calculate return since purchase

// Get historical price on purchase date
=DIVV(A1, "close", B1)

// Calculate % return
=(DIVV(A1, "price") - C1) / C1 * 100
```

### 2. Year-to-Date Performance
```javascript
// Get price at start of year
=DIVV("AAPL", "close", DATE(2024, 1, 1))

// YTD return %
=(DIVV("AAPL", "price") - DIVV("AAPL", "close", DATE(2024, 1, 1)))
  / DIVV("AAPL", "close", DATE(2024, 1, 1)) * 100
```

### 3. Historical Chart Data
```javascript
// Get last 30 days of closing prices
=DIVV("AAPL", "close",
  TEXT(TODAY()-30, "yyyy-mm-dd"),
  TEXT(TODAY(), "yyyy-mm-dd"))
```

Then create a line chart from the returned array.

---

## Migration from GOOGLEFINANCE()

### Before (GOOGLEFINANCE):
```javascript
=GOOGLEFINANCE("AAPL", "price", DATE(2024, 1, 15))
```

### After (DIVV):
```javascript
=DIVV("AAPL", "close", "2024-01-15")
// or
=DIVV("AAPL", "close", DATE(2024, 1, 15))
```

**Key Differences:**
1. DIVV uses string dates by default (more readable)
2. DIVV explicitly uses "close" instead of "price" for clarity
3. DIVV returns dividend-focused data for current queries

---

## Future Enhancements

### Planned Features:
- ✅ ~~Basic historical data~~ (Implemented)
- 🚧 Intraday historical data (hourly bars)
- 🚧 Historical dividend data with dates
- 🚧 Split-adjusted vs. unadjusted prices
- 🚧 Bulk historical queries

---

## Summary

**What's New:**
- ✅ Historical price data support
- ✅ GOOGLEFINANCE() parity for date queries
- ✅ Multiple date format support
- ✅ Single date and date range queries
- ✅ Automatic tier-based access control

**Upgrade Path:**
Free users can test with current data, then upgrade to Starter ($9/mo) to unlock historical data for portfolio tracking and performance analysis.

**Get Started:**
```javascript
// Current price (free)
=DIVV("AAPL", "price")

// Historical price (paid)
=DIVV("AAPL", "close", "2024-01-15")
```

Visit [divv.com/pricing](https://divv.com/pricing) to upgrade.
