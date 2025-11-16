# YieldMax ETF Scrapers

This directory contains scrapers for YieldMax ETF data.

## Overview

YieldMax ETFs are option income strategy ETFs that provide high monthly distributions. These scrapers extract comprehensive data from YieldMax ETF pages including performance metrics, fund details, distributions, and holdings.

## Available Scrapers

### scrape_yieldmax_all.py (Recommended)

Universal scraper for all YieldMax ETFs. Supports scraping individual tickers or all funds at once.

**Supported ETFs (20 total):**
- TSLY, NVDY, MSTY, GOOY, AMZY, OARK, CONY, ULTY, APLY, SNOY
- DISO, MARO, GDXY, SOXY, ABNY, CRSH, NFLY, YMAX, YBIT, YMAG

**Note:** FJJY removed - page not found (404)

**Data Collected:**
- Performance (month-end and quarter-end) - stored as JSON
- Fund overview - key fund information as JSON
- Investment objective - text description
- Fund details - fund facts and characteristics as JSON
- Distributions - dividend/distribution history as JSON array
- Top 10 holdings - portfolio positions as JSON array

**Usage:**

```bash
# List available tickers
python3 scripts/scrapers/yieldmax/scrape_yieldmax_all.py --list

# Scrape a specific ETF
python3 scripts/scrapers/yieldmax/scrape_yieldmax_all.py --ticker TSLY

# Scrape all YieldMax ETFs (validates URLs first, default: 5 second delay)
python3 scripts/scrapers/yieldmax/scrape_yieldmax_all.py --all

# Scrape all with custom delay (e.g., 10 seconds to be extra cautious)
python3 scripts/scrapers/yieldmax/scrape_yieldmax_all.py --all --delay 10

# Scrape all without URL validation (faster but may fail on invalid URLs)
python3 scripts/scrapers/yieldmax/scrape_yieldmax_all.py --all --skip-validation

# Run in Docker
docker exec dividend-api python3 /app/scripts/scrapers/yieldmax/scrape_yieldmax_all.py --ticker TSLY
docker exec dividend-api python3 /app/scripts/scrapers/yieldmax/scrape_yieldmax_all.py --all --delay 5
```

**URL Validation:**
- By default, validates all URLs before scraping (quick HEAD requests)
- Identifies and skips invalid/404 pages automatically
- Use `--skip-validation` to bypass validation for faster execution
- Validation adds ~5-10 seconds but prevents wasted scraping attempts

**Rate Limiting:**
- Default delay between requests: **5 seconds** (when using `--all`)
- Configurable via `--delay` flag
- Recommended minimum: 3-5 seconds to avoid overwhelming the server
- Total time for all 20 ETFs: ~2 minutes (with 5s delay + validation)

### scrape_yieldmax_tsly.py (Legacy)

Original single-ticker scraper for TSLY. Use `scrape_yieldmax_all.py` instead for new implementations.

**Database Table:**

Data is stored in the `raw_yieldmax_etf_data` table:

```sql
CREATE TABLE raw_yieldmax_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL,

    -- JSON fields
    performance_month_end JSONB,
    performance_quarter_end JSONB,
    fund_overview JSONB,
    investment_objective TEXT,
    fund_details JSONB,
    distributions JSONB,
    top_10_holdings JSONB,

    CONSTRAINT unique_ticker_scraped_at UNIQUE (ticker, scraped_at)
);
```

**View Latest Data:**

```sql
-- Get latest data for all tickers
SELECT * FROM v_yieldmax_latest;

-- Get latest data for TSLY
SELECT * FROM v_yieldmax_latest WHERE ticker = 'TSLY';

-- Query performance data
SELECT
    ticker,
    scraped_at,
    performance_month_end->'1 Month' as one_month,
    performance_month_end->'YTD' as ytd
FROM raw_yieldmax_etf_data
WHERE ticker = 'TSLY'
ORDER BY scraped_at DESC
LIMIT 1;

-- Query distributions
SELECT
    ticker,
    jsonb_array_elements(distributions) as distribution
FROM v_yieldmax_latest
WHERE ticker = 'TSLY';

-- Query holdings
SELECT
    ticker,
    jsonb_array_elements(top_10_holdings) as holding
FROM v_yieldmax_latest
WHERE ticker = 'TSLY';
```

## Adding New YieldMax ETFs

To add new YieldMax ETFs to the scraper:

1. Edit `scrape_yieldmax_all.py`
2. Add the new ETF to the `YIELDMAX_ETFS` dictionary:
   ```python
   YIELDMAX_ETFS = {
       # ... existing ETFs ...
       'NEWF': {
           'name': 'YieldMax NEW Option Income Strategy ETF',
           'url': 'https://yieldmaxetfs.com/our-etfs/newf/'
       }
   }
   ```
3. Test with: `python3 scrape_yieldmax_all.py --ticker NEWF`
4. All data will be stored in the same `raw_yieldmax_etf_data` table

## Technical Details

**Requirements:**
- Selenium WebDriver
- BeautifulSoup4
- Chrome/Chromium browser (for headless scraping)

**Features:**
- Headless browser scraping for dynamic content
- Robust error handling
- JSON storage for flexible data structures
- Automatic timestamping
- Upsert functionality (prevents duplicates)

## Data Refresh Schedule

Recommended scraping frequency:
- **Daily**: Full scrape of all ETFs (automated via cron)
  - Best run during off-peak hours (e.g., 2 AM)
  - Use default 5-second delay to be respectful
  - Total runtime: ~2 minutes for all 20 ETFs
- **On-demand**: Scrape specific tickers as needed
  - No rate limiting needed for single ticker scrapes

**Note:** The date-based unique constraint ensures only one scrape per ticker per day, preventing accidental duplicates.

## Migration

Run the migration to create the table:

```bash
# Via Supabase SQL Editor
# Copy contents of: supabase/migrations/20251116_add_yieldmax_etf_data.sql
# Paste and run in: https://supabase.com/dashboard/project/[PROJECT_ID]/sql/new
```

## Troubleshooting

**Issue: Browser not found**
- Ensure Chrome/Chromium is installed in Docker container
- Check environment variables: `CHROME_BIN` and `CHROMEDRIVER_PATH`

**Issue: Table doesn't exist**
- Run the migration: `20251116_add_yieldmax_etf_data.sql`

**Issue: No data extracted**
- Check website structure hasn't changed
- Verify selectors in extraction methods
- Run with debug logging

## Future Enhancements

- [x] Add scrapers for all YieldMax ETFs (21 supported)
- [x] Create unified scraper for all YieldMax funds (scrape_yieldmax_all.py)
- [x] Add historical data tracking (via scraped_date column)
- [ ] Create dashboard/visualization for performance comparison
- [ ] Add automated scheduling (cron jobs)
- [ ] Add data validation and quality checks
- [ ] Add API endpoints for YieldMax data
