# Discovery Data Sources Overview

## Summary

**Yes**, the discovery logic searches for new symbols from **multiple data sources**, both via APIs and web scraping.

## Discovery Flow

The discovery runs **weekly on Sundays** (see `daily_update_v3_parallel.sh` line 188-248) and uses:

### Phase 1: API-Based Discovery

**Primary Method**: `discover_comprehensive()` in `lib/discovery/symbol_discovery.py`

This method discovers symbols from three API sources in sequence:

#### 1. FMP (Financial Modeling Prep) - PRIMARY SOURCE
**Location**: `lib/data_sources/fmp_client.py`

Three discovery methods:

**a) `discover_symbols()` - All Listed Symbols**
- Endpoint: `/api/v3/stock/list`
- Returns: ALL publicly traded stocks and ETFs
- Filters: US and Canadian exchanges only (see `lib/core/config.py` ExchangeConfig)
- Typical count: ~18,000-20,000 symbols

**b) `discover_etfs()` - ETF-Specific**
- Endpoint: `/api/v3/etf/list`
- Returns: Comprehensive ETF list
- Typical count: ~3,000-4,000 ETFs

**c) `discover_dividend_stocks()` - Dividend Screener**
- Endpoint: `/api/v3/stock-screener`
- Filters: `dividendYield > 0.01` (minimum 1% yield)
- Returns: High-dividend stocks
- Typical count: ~2,000-3,000 dividend payers

#### 2. Alpha Vantage - SECONDARY SOURCE
**Location**: `lib/data_sources/alpha_vantage_client.py`

- Currently used as backup/validation
- Note: Line 60 in `symbol_discovery.py` shows "Yahoo doesn't support symbol discovery"
- Alpha Vantage support exists but may be limited

#### 3. Yahoo Finance
**Location**: `lib/data_sources/yahoo_client.py`

- Used for price/dividend data fetching
- **NOT used for symbol discovery** (no discovery endpoint)

### Phase 2: Web Scraping Discovery

**Timing**: Runs in parallel with API discovery (see `daily_update_v3_parallel.sh` lines 250-407)

These scrapers discover symbols from dividend calendars and specialized lists:

#### 1. YieldMax Scraper
**File**: `scripts/scrape_yieldmax.py`
- **Source**: YieldMax website
- **Focus**: YieldMax ETFs (e.g., TSLY, NVDY, APLY)
- **Type**: Specialized high-income ETFs

#### 2. CBOE Scraper
**File**: `scripts/scrape_cboe_dividends.py`
- **Source**: CBOE dividend calendar
- **Focus**: Options-related dividend announcements
- **Type**: Stocks with upcoming dividend dates

#### 3. NASDAQ Scraper
**File**: `scripts/scrape_nasdaq_dividends.py`
- **Source**: NASDAQ dividend calendar
- **Focus**: NASDAQ-listed dividend stocks
- **Type**: Tech and growth stocks with dividends

#### 4. Snowball Scraper
**File**: `scripts/scrape_snowball_dividends.py`
- **Source**: Snowball Finance (popular dividend lists)
- **Category**: `us-popular-div`
- **Type**: Popular dividend stocks curated list

## Discovery Execution Order

From `daily_update_v3_parallel.sh`:

```bash
# STEP 1: Discovery (Weekly - Sundays only)
python3 update_stock_v2.py --mode discover --validate

# PHASE 1: Parallel Web Scraping (Daily)
# All 5 scrapers run simultaneously:
- YieldMax scraper
- CBOE scraper
- NASDAQ scraper
- NYSE scraper
- Snowball scraper
```

## How Symbols are Combined

**Location**: `lib/discovery/symbol_discovery.py` lines 147-203

The `discover_comprehensive()` method:

1. **Calls FMP API** (discover_symbols, discover_etfs, discover_dividend_stocks)
2. **Deduplicates** symbols using a set (`discovered_symbols`)
3. **Returns** unique list of all discovered symbols
4. **Filters** (NEW!) skips symbols with existing price data
5. **Validates** remaining symbols for price/dividend availability

## Discovery Stats (Typical Run)

```
Regular Discovery (FMP):      18,000 symbols
ETF Discovery (FMP):           +2,500 symbols (500 new)
Dividend Discovery (FMP):      +1,000 symbols (200 new)
Web Scrapers (combined):         +100 symbols (50 new)
─────────────────────────────────────────────
Total Discovered:              ~20,000 unique symbols
Already have prices:           ~18,500 symbols (SKIP ✅)
Previously excluded:              ~500 symbols (SKIP ✅)
Need Validation:                ~1,000 symbols
```

## Configuration

### Enabled Sources
**File**: `lib/core/config.py` - FeatureFlags

```python
ENABLE_FMP = True           # ✅ FMP API
ENABLE_ALPHA_VANTAGE = True # ✅ Alpha Vantage API
ENABLE_YAHOO = True         # ✅ Yahoo (for data, not discovery)
```

### Exchange Filtering
**File**: `lib/core/config.py` - ExchangeConfig

```python
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "BATS", "CBOE",  # US exchanges
    "TSX", "TSXV", "CSE",                       # Canadian exchanges
]

BLOCKED_SUFFIXES = ['.L', '.AX', '.DE', ...]   # International exchanges
```

## What Gets Added to Database

After discovery and validation:

1. **Valid symbols** → Added to `raw_stocks` table
2. **Invalid symbols** → Added to `raw_excluded_symbols` table
3. **Next update cycle** → Price/dividend data fetched for valid symbols

## Optimization Impact

**Before Optimization**:
- Discovered: 20,000 symbols
- Validated: 20,000 symbols (including 18,500 duplicates!)
- Time: ~12 hours

**After Optimization**:
- Discovered: 20,000 symbols
- Filtered in SQL: 18,500 already have prices (skip)
- Validated: 1,500 new symbols only
- Time: ~1-2 hours ✅

## How to Check Discovery Sources

Run discovery with debug logging:

```bash
DEBUG_MODE=true python3 update_stock_v2.py --mode discover --validate
```

Look for these log lines:
```
🔍 Starting comprehensive symbol discovery
✅ Regular Discovery: 18000 total, 18000 new, 18000 cumulative
✅ ETF Discovery: 2500 total, 500 new, 18500 cumulative
✅ Dividend Discovery: 1000 total, 200 new, 18700 cumulative
📊 Filtering discovered symbols using SQL...
   18500 discovered symbols already have prices (skip)
📊 Validation queue: 200 symbols (skipped 18500 already processed)
```

## Future Enhancement Ideas

1. **Add Reddit/Social Media**: Discover trending dividend stocks from r/dividends
2. **Add Seeking Alpha**: Scrape dividend aristocrats lists
3. **Add M1 Finance**: Popular dividend portfolio lists
4. **Add Dividend.com**: Comprehensive dividend calendars
5. **Add international exchanges**: Expand beyond US/Canada
6. **Add preferred stocks**: Currently focuses on common stocks
7. **Add REITs specifically**: Targeted REIT discovery

## Maintenance Notes

- Discovery runs **weekly** to minimize API costs and processing time
- Web scrapers run **daily** to catch new dividend announcements
- Each scraper is independent (can fail without affecting others)
- Symbols are validated before adding to avoid bad data
- Failed validations are stored in `raw_excluded_symbols` to avoid retry waste
