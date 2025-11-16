# Roundhill Investments ETF Scrapers

This directory contains scrapers for Roundhill Investments ETF data.

## Overview

Roundhill Investments offers a range of thematic and income-focused ETFs, including their popular 0DTE covered call strategies and WeeklyPay series. These scrapers extract comprehensive data from Roundhill ETF pages including performance metrics, fund details, distributions, and holdings.

## Available Scrapers

### scrape_roundhill_all.py (Recommended)

Universal scraper for all Roundhill ETFs. Supports scraping individual tickers or all funds at once.

**Supported ETFs (44 total):**

**Core ETFs (22):**
- METV - Roundhill Ball Metaverse ETF
- BETZ - Roundhill Sports Betting & iGaming ETF
- CHAT - Roundhill Generative AI & Technology ETF
- MAGS - Roundhill Magnificent Seven ETF
- NERD - Roundhill BITKRAFT Esports & Digital Entertainment ETF
- WEED - Roundhill Cannabis ETF
- YBTC - Roundhill Bitcoin Covered Call Strategy ETF
- MAGX - Roundhill Magnificent Seven 2X Strategy ETF
- QDTE - Roundhill Nasdaq 100 0DTE Covered Call Strategy ETF
- XDTE - Roundhill S&P 500 0DTE Covered Call Strategy ETF
- OZEM - Roundhill GLP-1 & Weight Loss ETF
- YETH - Roundhill Ether Covered Call Strategy ETF
- RDTE - Roundhill Russell 2000 0DTE Covered Call Strategy ETF
- MAGC - Roundhill Magnificent Seven Covered Call ETF
- XPAY - Roundhill S&P 500 0DTE Covered Call Strategy Monthly Distribution ETF
- UX - Roundhill Uranium & Nuclear Energy ETF
- MAGY - Roundhill Magnificent Seven Income & Growth ETF
- WEEK - Roundhill Weekly Dividend ETF
- XDIV - Roundhill S&P Dividend Monarchs ETF
- HUMN - Roundhill Humankind US Equity ETF
- MEME - Roundhill MEME ETF
- WPAY - Roundhill PYPL Stock Weekly Income ETF

**WeeklyPay ETFs (22):**
- AAPW - Roundhill AAPL Stock Weekly Income ETF
- AMDW - Roundhill AMD Stock Weekly Income ETF
- ARMW - Roundhill ARM Stock Weekly Income ETF
- AMZW - Roundhill AMZN Stock Weekly Income ETF
- AVGW - Roundhill AVGO Stock Weekly Income ETF
- BABW - Roundhill BABA Stock Weekly Income ETF
- BRKW - Roundhill BRK.B Stock Weekly Income ETF
- COIW - Roundhill COIN Stock Weekly Income ETF
- COSW - Roundhill COST Stock Weekly Income ETF
- GDXW - Roundhill GDX Miners Weekly Income ETF
- GLDW - Roundhill GLD Gold Weekly Income ETF
- GOOW - Roundhill GOOG Stock Weekly Income ETF
- HOOW - Roundhill HYG Bond Weekly Income ETF
- METW - Roundhill META Stock Weekly Income ETF
- MSFW - Roundhill MSFT Stock Weekly Income ETF
- MSTW - Roundhill MSTR Stock Weekly Income ETF
- NFLW - Roundhill NFLX Stock Weekly Income ETF
- NVDW - Roundhill NVDA Stock Weekly Income ETF
- PLTW - Roundhill PLTR Stock Weekly Income ETF
- TSLW - Roundhill TSLA Stock Weekly Income ETF
- TSYW - Roundhill TSY Treasury Bond Weekly Income ETF
- UBEW - Roundhill UBER Stock Weekly Income ETF

**Data Collected:**
- Expense ratio - extracted as text
- Launch date - extracted as text
- Holdings count - extracted as text
- Fund overview - key fund information as JSON
- Performance data - returns and metrics as JSON
- Fund details - fund facts and characteristics as JSON
- Distributions - dividend/distribution history as JSON array
- Holdings - portfolio positions as JSON array

**Usage:**

```bash
# List available tickers
python3 scripts/scrapers/roundhill/scrape_roundhill_all.py --list

# Scrape a specific ETF
python3 scripts/scrapers/roundhill/scrape_roundhill_all.py --ticker METV

# Scrape all Roundhill ETFs (validates URLs first, default: 5 second delay)
python3 scripts/scrapers/roundhill/scrape_roundhill_all.py --all

# Scrape all with custom delay (e.g., 10 seconds to be extra cautious)
python3 scripts/scrapers/roundhill/scrape_roundhill_all.py --all --delay 10

# Scrape all without URL validation (faster but may fail on invalid URLs)
python3 scripts/scrapers/roundhill/scrape_roundhill_all.py --all --skip-validation

# Run in Docker
docker exec dividend-api python3 /app/scripts/scrapers/roundhill/scrape_roundhill_all.py --ticker METV
docker exec dividend-api python3 /app/scripts/scrapers/roundhill/scrape_roundhill_all.py --all --delay 5
```

**URL Validation:**
- By default, validates all URLs before scraping (quick HEAD requests)
- Identifies and skips invalid/404 pages automatically
- Use `--skip-validation` to bypass validation for faster execution
- Validation adds ~10-15 seconds but prevents wasted scraping attempts

**Rate Limiting:**
- Default delay between requests: **5 seconds** (when using `--all`)
- Configurable via `--delay` flag
- Recommended minimum: 3-5 seconds to avoid overwhelming the server
- Total time for all 44 ETFs: ~4-5 minutes (with 5s delay + validation)

**Database Table:**

Data is stored in the `raw_roundhill_etf_data` table:

```sql
CREATE TABLE raw_roundhill_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL,
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Extracted fields
    expense_ratio TEXT,
    launch_date TEXT,
    holdings_count TEXT,

    -- JSON fields
    fund_overview JSONB,
    performance_data JSONB,
    fund_details JSONB,
    distributions JSONB,
    holdings JSONB,

    CONSTRAINT unique_ticker_scraped_date UNIQUE (ticker, scraped_date)
);
```

**View Latest Data:**

```sql
-- Get latest data for all tickers
SELECT * FROM v_roundhill_latest;

-- Get latest data for METV
SELECT * FROM v_roundhill_latest WHERE ticker = 'METV';

-- Query performance data
SELECT
    ticker,
    scraped_at,
    expense_ratio,
    launch_date,
    holdings_count,
    performance_data->>'YTD' as ytd
FROM raw_roundhill_etf_data
WHERE ticker = 'METV'
ORDER BY scraped_at DESC
LIMIT 1;

-- Query distributions
SELECT
    ticker,
    jsonb_array_elements(distributions) as distribution
FROM v_roundhill_latest
WHERE ticker = 'METV';

-- Query holdings
SELECT
    ticker,
    jsonb_array_elements(holdings) as holding
FROM v_roundhill_latest
WHERE ticker = 'METV';

-- Compare expense ratios across all ETFs
SELECT
    ticker,
    fund_name,
    expense_ratio,
    scraped_date
FROM v_roundhill_latest
ORDER BY expense_ratio;

-- Get all WeeklyPay ETFs
SELECT
    ticker,
    fund_name,
    expense_ratio,
    launch_date
FROM v_roundhill_latest
WHERE ticker LIKE '%W'
ORDER BY ticker;
```

## Adding New Roundhill ETFs

To add new Roundhill ETFs to the scraper:

1. Edit `scrape_roundhill_all.py`
2. Add the new ETF to the `ROUNDHILL_ETFS` dictionary:
   ```python
   ROUNDHILL_ETFS = {
       # ... existing ETFs ...
       'NEWF': {
           'name': 'Roundhill New Fund ETF',
           'url': 'https://www.roundhillinvestments.com/etf/newf/'
       }
   }
   ```
3. Test with: `python3 scrape_roundhill_all.py --ticker NEWF`
4. All data will be stored in the same `raw_roundhill_etf_data` table

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
- Date-based unique constraint (one scrape per ticker per day)
- Upsert functionality (prevents duplicates)

## Data Refresh Schedule

Recommended scraping frequency:
- **Daily**: Full scrape of all ETFs (automated via cron)
  - Best run during off-peak hours (e.g., 2 AM)
  - Use default 5-second delay to be respectful
  - Total runtime: ~4-5 minutes for all 44 ETFs
- **On-demand**: Scrape specific tickers as needed
  - No rate limiting needed for single ticker scrapes

**Note:** The date-based unique constraint ensures only one scrape per ticker per day, preventing accidental duplicates.

## Migration

Run the migration to create the table:

```bash
# Via Supabase SQL Editor
# Copy contents of: supabase/migrations/20251116_add_roundhill_etf_data.sql
# Paste and run in: https://supabase.com/dashboard/project/[PROJECT_ID]/sql/new
```

## Data Structure

**Expense Ratio:** Text field (e.g., "0.95%")
**Launch Date:** Text field (e.g., "June 30, 2021")
**Holdings Count:** Text field (e.g., "50")

**Fund Overview (JSONB):** Key-value pairs of fund information
```json
{
  "NAV": "$25.43",
  "Premium/Discount": "-0.12%",
  "Assets Under Management": "$1.2B"
}
```

**Performance Data (JSONB):** Performance metrics
```json
{
  "NAV": {
    "1 Month": "2.34%",
    "YTD": "15.67%",
    "1 Year": "23.45%"
  },
  "Market Price": {
    "1 Month": "2.31%",
    "YTD": "15.52%"
  }
}
```

**Fund Details (JSONB):** Detailed fund characteristics
```json
{
  "Ticker": "METV",
  "CUSIP": "12345678",
  "Inception Date": "June 30, 2021",
  "Expense Ratio": "0.95%",
  "Index": "Ball Metaverse Index"
}
```

**Distributions (JSONB Array):** Distribution history
```json
[
  {
    "Ex-Date": "11/15/2024",
    "Record Date": "11/16/2024",
    "Payable Date": "11/20/2024",
    "Amount": "$0.15"
  }
]
```

**Holdings (JSONB Array):** Portfolio holdings
```json
[
  {
    "Name": "NVIDIA Corporation",
    "Ticker": "NVDA",
    "Weight": "8.5%",
    "Shares": "10,000"
  }
]
```

## Troubleshooting

**Issue: Browser not found**
- Ensure Chrome/Chromium is installed in Docker container
- Check environment variables: `CHROME_BIN` and `CHROMEDRIVER_PATH`

**Issue: Table doesn't exist**
- Run the migration: `20251116_add_roundhill_etf_data.sql`

**Issue: No data extracted**
- Check website structure hasn't changed
- Verify selectors in extraction methods
- Run with debug logging

**Issue: URL validation fails**
- Some ETFs may be recently launched or delisted
- Check the Roundhill website directly
- Use `--skip-validation` to bypass (will fail during scraping if URL is invalid)

## Future Enhancements

- [x] Add scrapers for all Roundhill ETFs (44 supported)
- [x] Create unified scraper for all Roundhill funds
- [x] Add historical data tracking (via scraped_date column)
- [ ] Create dashboard/visualization for performance comparison
- [ ] Add automated scheduling (cron jobs)
- [ ] Add data validation and quality checks
- [ ] Add API endpoints for Roundhill data
- [ ] Add alerting for significant NAV premium/discount changes

## Notes

**0DTE Strategy ETFs:** Roundhill's 0DTE (zero days to expiration) covered call ETFs (QDTE, XDTE, RDTE, XPAY) use a unique daily option strategy. Monitor distributions closely as they can vary significantly.

**WeeklyPay ETFs:** The WeeklyPay series provides weekly distributions. The scraper captures distribution schedules which can be analyzed for income planning.

**Thematic ETFs:** Roundhill specializes in thematic investing (metaverse, AI, gaming, cannabis, etc.). Performance data is particularly useful for tracking emerging sector trends.
