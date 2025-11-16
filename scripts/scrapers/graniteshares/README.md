# GraniteShares ETF Scraper

Complete web scraper for all 59 GraniteShares ETFs across 6 categories. Uses Selenium for JavaScript-rendered content and stores comprehensive data in Supabase.

## Overview

GraniteShares offers 59 ETFs across 6 distinct categories:

### 1. YieldBOOST (16 ETFs)
Income-generating ETFs using put spread strategies on leveraged ETFs:
- AMYY - GraniteShares YieldBOOST AMD ETF (2x leverage on AMD)
- AZYY - GraniteShares YieldBOOST AMZN ETF (2x leverage on Amazon)
- BBYY - GraniteShares YieldBOOST BABA ETF (2x leverage on Alibaba)
- COYY - GraniteShares YieldBOOST COIN ETF (2x leverage on Coinbase)
- FBYY - GraniteShares YieldBOOST META ETF (2x leverage on Meta)
- HOYY - GraniteShares YieldBOOST HOOD ETF (2x leverage on Robinhood)
- IOYY - GraniteShares YieldBOOST IONQ ETF (2x leverage on IonQ)
- MAAY - GraniteShares YieldBOOST MARA ETF (2x leverage on MARA)
- MTYY - GraniteShares YieldBOOST MSTR ETF (2x leverage on MicroStrategy)
- NVYY - GraniteShares YieldBOOST NVDA ETF (2x leverage on NVIDIA)
- PLYY - GraniteShares YieldBOOST PLTR ETF (2x leverage on Palantir)
- SMYY - GraniteShares YieldBOOST SMCI ETF (2x leverage on Super Micro)
- TQQY - GraniteShares YieldBOOST QQQ ETF (3x leverage on Nasdaq-100)
- TSYY - GraniteShares YieldBOOST TSLA ETF (2x leverage on Tesla)
- XBTY - GraniteShares YieldBOOST Bitcoin ETF (2x leverage on Bitcoin)
- YSPY - GraniteShares YieldBOOST SPY ETF (3x leverage on S&P 500)

### 2. Leveraged (38 ETFs)
2x long/short leveraged and 1.25x long exposure to individual stocks:
- AAPB, AMDL, AMZZ, AVGU, BABX, BULX, CONI, CONL, CRWL, DLLL
- ETRL, FBL, INTW, IONL, ISUL, LCDL, MRAL, MSDD, MSFL, MSTP
- MULL, MVLL, NBIL, NOWL, NVD, NVDL, PDDL, PTIR, QCML, RDTL
- RVNL, SMCL, TSDD, TSL, TSLR, TSMU, UBRL, VRTL

### 3. Commodities (2 ETFs)
- COMB - GraniteShares Bloomberg Commodity Broad Strategy No K-1 ETF
- PLTM - GraniteShares Platinum Trust (physical platinum)

### 4. Gold (1 ETF)
- BAR - GraniteShares Gold Trust (physical gold)

### 5. Equity (1 ETF)
- DRUP - GraniteShares Nasdaq Select Disruptors ETF

### 6. Income (1 ETF)
- HIPS - GraniteShares HIPS US High Income ETF

## Features

- Universal scraper for all 59 GraniteShares ETFs
- Selenium-based scraping (handles JavaScript-rendered content)
- URL validation before scraping
- Category-based filtering
- Rate limiting with configurable delays
- Comprehensive error handling
- Supabase integration for data storage
- Progress tracking and logging

## Data Captured

### Core Fields
- Ticker symbol
- Fund name
- Category (YieldBOOST, Leveraged, etc.)
- Underlying security/asset
- Leverage multiplier (2, -2, 1.25, 3, 0)
- Expense ratio
- Inception date
- NAV (Net Asset Value)
- AUM (Assets Under Management)
- Market price
- Premium/discount to NAV

### JSON Fields
- **fund_details**: Additional fund metadata (CUSIP, exchange, etc.)
- **performance_data**: Performance metrics (1mo, 3mo, 6mo, YTD, 1yr, inception)
- **distributions**: Distribution/dividend history
- **holdings**: Fund portfolio composition

## Installation

```bash
# Install dependencies
pip install selenium beautifulsoup4 requests python-dotenv

# Install Chrome/Chromium and ChromeDriver
# For macOS:
brew install chromium chromedriver

# For Ubuntu/Debian:
sudo apt-get install chromium-browser chromium-chromedriver
```

## Usage

### List Available ETFs

```bash
python scrape_graniteshares_all.py --list
```

### Scrape Single ETF

```bash
# Scrape NVDL (2x Long NVDA)
python scrape_graniteshares_all.py --ticker NVDL

# Scrape TSYY (YieldBOOST TSLA)
python scrape_graniteshares_all.py --ticker TSYY
```

### Scrape by Category

```bash
# Scrape all YieldBOOST ETFs
python scrape_graniteshares_all.py --category YieldBOOST

# Scrape all Leveraged ETFs
python scrape_graniteshares_all.py --category Leveraged

# Scrape all Commodities ETFs
python scrape_graniteshares_all.py --category Commodities
```

### Scrape All ETFs

```bash
# Scrape all 59 ETFs with 5-second delay
python scrape_graniteshares_all.py --all

# Scrape with custom delay (10 seconds)
python scrape_graniteshares_all.py --all --delay 10

# Skip URL validation (faster but may fail)
python scrape_graniteshares_all.py --all --skip-validation
```

### Test Mode

```bash
# Test mode: scrape only 3 ETFs
python scrape_graniteshares_all.py --test
```

### Limit Number of ETFs

```bash
# Scrape first 10 ETFs only
python scrape_graniteshares_all.py --all --limit 10
```

## Command Line Options

```
--ticker, -t      Specific ticker to scrape (e.g., NVDL)
--all, -a         Scrape all GraniteShares ETFs
--category, -c    Scrape by category (YieldBOOST, Leveraged, etc.)
--list, -l        List available tickers
--delay, -d       Delay in seconds between requests (default: 5)
--limit           Limit number of ETFs to scrape
--test            Test mode: scrape only 3 ETFs
--skip-validation Skip URL validation before scraping
```

## Database Schema

Data is stored in `raw_etfs_graniteshares` table:

```sql
CREATE TABLE raw_etfs_graniteshares (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Core fields
    expense_ratio TEXT,
    inception_date TEXT,
    nav TEXT,
    aum TEXT,
    market_price TEXT,
    premium_discount TEXT,
    category TEXT,
    underlying TEXT,
    leverage TEXT,

    -- JSON fields
    fund_details JSONB,
    performance_data JSONB,
    distributions JSONB,
    holdings JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_graniteshares_ticker_scraped_date UNIQUE (ticker, scraped_date)
);
```

## Query Examples

### Get Latest Data for All ETFs

```sql
SELECT * FROM v_graniteshares_latest;
```

### Filter by Category

```sql
SELECT ticker, fund_name, category, nav, aum
FROM v_graniteshares_latest
WHERE category = 'YieldBOOST'
ORDER BY aum DESC;
```

### Find Leveraged Long ETFs

```sql
SELECT ticker, fund_name, underlying, leverage
FROM v_graniteshares_latest
WHERE category = 'Leveraged'
  AND leverage::float > 0
ORDER BY leverage DESC, ticker;
```

### Find Inverse (Short) ETFs

```sql
SELECT ticker, fund_name, underlying, leverage
FROM v_graniteshares_latest
WHERE leverage::float < 0
ORDER BY ticker;
```

### Get YieldBOOST ETFs with Highest AUM

```sql
SELECT ticker, fund_name, underlying, aum
FROM v_graniteshares_latest
WHERE category = 'YieldBOOST'
ORDER BY aum DESC
LIMIT 10;
```

### Distribution History

```sql
SELECT
    ticker,
    fund_name,
    jsonb_array_length(distributions) as distribution_count,
    distributions
FROM v_graniteshares_latest
WHERE distributions IS NOT NULL
ORDER BY jsonb_array_length(distributions) DESC;
```

### Search Fund Details

```sql
SELECT
    ticker,
    fund_name,
    fund_details->>'CUSIP' as cusip,
    fund_details->>'Exchange' as exchange
FROM v_graniteshares_latest
WHERE fund_details IS NOT NULL;
```

## URL Pattern

All GraniteShares ETF pages follow this pattern:

```
https://graniteshares.com/institutional/us/en-us/etfs/{ticker}/
```

Example: `https://graniteshares.com/institutional/us/en-us/etfs/nvdl/`

Note: Use lowercase ticker in URL.

## HTML Structure

GraniteShares uses JavaScript-heavy rendering. Key CSS classes:

- `.pNav` - NAV value
- `.pClose` - Closing/market price
- `.pDisc` - Premium/discount percentage
- `.pAum` - Assets under management
- `.pInception` - Inception date
- `.pExpenseRatio` - Expense ratio
- `.etf-chart-details_content_performance-table` - Performance metrics
- `.etf-chart-details_content_distribution-calendar-table` - Distributions
- `.etf-chart-details_content_fund-allocation-table` - Holdings

## Rate Limiting

- Default delay: 5 seconds between requests
- Configurable via `--delay` flag
- Recommended: 5-10 seconds for polite scraping
- URL validation uses HTTP HEAD requests (faster)

## Error Handling

- URL validation before scraping (optional, can skip with `--skip-validation`)
- Comprehensive logging at INFO/WARNING/ERROR levels
- Graceful degradation on missing data
- Per-field extraction with fallback strategies
- Browser cleanup on error or completion

## Troubleshooting

### Chrome/ChromeDriver Issues

```bash
# Set environment variables
export CHROME_BIN=/usr/bin/chromium
export CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Or for macOS with Homebrew
export CHROME_BIN=/Applications/Chromium.app/Contents/MacOS/Chromium
export CHROMEDRIVER_PATH=/opt/homebrew/bin/chromedriver
```

### Missing Data Fields

Some ETFs may not have all fields populated. The scraper handles missing data gracefully:
- Missing fields are stored as NULL
- JSON fields with no data are stored as empty objects/arrays
- Warnings logged for missing data

### URL Validation Failures

If URL validation fails but you know the URLs are valid:
```bash
# Skip validation
python scrape_graniteshares_all.py --all --skip-validation
```

## Maintenance

### Database Migration

Run the migration to create the table:

```bash
# Using Supabase CLI
supabase db push supabase/migrations/20251116_add_graniteshares_etf_data.sql

# Or apply directly to database
psql -d your_database -f supabase/migrations/20251116_add_graniteshares_etf_data.sql
```

### Updating ETF List

When GraniteShares adds new ETFs:

1. Update `GRANITESHARES_ETFS` dictionary in `scrape_graniteshares_all.py`
2. Add ticker, name, category, underlying, leverage, and URL
3. Test with single ticker: `python scrape_graniteshares_all.py --ticker NEW_TICKER`

## Performance

- Single ETF: ~10 seconds (5s page load + 5s processing)
- 59 ETFs with 5s delay: ~15 minutes
- Test mode (3 ETFs): ~45 seconds

## Comparison to Other Scrapers

Similar to Kurv, Defiance, NEOS, YieldMax, and Roundhill scrapers:
- Same database structure (raw table + latest view)
- Same CLI interface and patterns
- Same error handling approach
- Universal scraper for entire ETF family

## License

MIT License - Part of high-yield-dividend-analysis project

## Support

For issues or questions:
1. Check logs for error messages
2. Verify URL accessibility: `curl -I https://graniteshares.com/institutional/us/en-us/etfs/nvdl/`
3. Test with single ticker first
4. Review database schema and permissions

## Version History

- v1.0.0 (2025-11-16): Initial release with all 59 ETFs
