# Kurv ETF Scrapers

This directory contains scrapers for Kurv ETF data.

## Overview

Kurv ETFs offer innovative income-generating strategies including yield premium strategies on single stocks, precious metals income, and growth & income funds. These scrapers extract comprehensive data from Kurv ETF pages including performance metrics, fund details, distributions, and holdings.

## Available Scrapers

### scrape_kurv_all.py (Recommended)

Universal scraper for all Kurv ETFs. Supports scraping individual tickers or all funds at once.

**Supported ETFs (10 total):**

**Growth & Income (2):**
- KQQQ - Kurv Technology Titans Select ETF
- KYLD - Kurv High Income ETF

**Precious Metals Income (2):**
- KGLD - Kurv Gold Enhanced Income ETF
- KSLV - Kurv Silver Enhanced Income ETF

**Single Stock Income - Yield Premium Strategy (6):**
- AAPY - Kurv Yield Premium Strategy Apple (AAPL) ETF
- AMZP - Kurv Yield Premium Strategy Amazon (AMZN) ETF
- GOOP - Kurv Yield Premium Strategy Google (GOOGL) ETF
- MSFY - Kurv Yield Premium Strategy Microsoft (MSFT) ETF
- NFLP - Kurv Yield Premium Strategy Netflix (NFLX) ETF
- TSLP - Kurv Yield Premium Strategy Tesla (TSLA) ETF

**Data Collected:**

Extracted Fields:
- Expense ratio - extracted as text (e.g., "0.99%")
- Inception date - normalized to MM/DD/YYYY format (2-digit years converted to 20YY)
- Distribution rate - annual distribution rate
- Distribution frequency - frequency of distributions (Weekly, Monthly, etc.)
- 30-day SEC yield - standardized yield measure
- NAV - net asset value per share
- Market price - current market price
- Premium/discount - premium or discount to NAV

JSON Fields:
- Fund details - comprehensive fund information (CUSIP, exchange, etc.) as JSON
- Performance data - returns (1mo, 3mo, 6mo, YTD, 1yr, since inception) as JSON
- Distributions - distribution history as JSON array
- Holdings - top 10 portfolio positions as JSON array

**Usage:**

```bash
# List available tickers
python3 scripts/scrapers/kurv/scrape_kurv_all.py --list

# Scrape a specific ETF
python3 scripts/scrapers/kurv/scrape_kurv_all.py --ticker KQQQ

# Scrape all Kurv ETFs (validates URLs first, default: 5 second delay)
python3 scripts/scrapers/kurv/scrape_kurv_all.py --all

# Scrape all with custom delay (e.g., 10 seconds to be extra cautious)
python3 scripts/scrapers/kurv/scrape_kurv_all.py --all --delay 10

# Scrape all without URL validation (faster but may fail on invalid URLs)
python3 scripts/scrapers/kurv/scrape_kurv_all.py --all --skip-validation

# Run in Docker
docker exec dividend-api python3 /app/scripts/scrapers/kurv/scrape_kurv_all.py --ticker KQQQ
docker exec dividend-api python3 /app/scripts/scrapers/kurv/scrape_kurv_all.py --all --delay 5
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
- Total time for all 10 ETFs: ~1 minute (with 5s delay + validation)

**Database Table:**

Data is stored in the `raw_etfs_kurv` table:

```sql
CREATE TABLE raw_etfs_kurv (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL,
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Extracted fields
    expense_ratio TEXT,
    inception_date TEXT,
    distribution_rate TEXT,
    distribution_frequency TEXT,
    sec_yield_30day TEXT,
    nav TEXT,
    market_price TEXT,
    premium_discount TEXT,

    -- JSON fields
    fund_details JSONB,
    performance_data JSONB,
    distributions JSONB,
    holdings JSONB,

    CONSTRAINT unique_ticker_scraped_date UNIQUE (ticker, scraped_date)
);
```

**View Latest Data:**

```sql
-- Get latest data for all tickers
SELECT * FROM v_kurv_latest;

-- Get latest data for KQQQ
SELECT * FROM v_kurv_latest WHERE ticker = 'KQQQ';

-- Query performance data
SELECT
    ticker,
    scraped_at,
    expense_ratio,
    inception_date,
    distribution_rate,
    distribution_frequency,
    sec_yield_30day,
    nav,
    market_price,
    premium_discount,
    performance_data->>'YTD' as ytd
FROM raw_etfs_kurv
WHERE ticker = 'KQQQ'
ORDER BY scraped_at DESC
LIMIT 1;

-- Query distributions
SELECT
    ticker,
    jsonb_array_elements(distributions) as distribution
FROM v_kurv_latest
WHERE ticker = 'KQQQ';

-- Query holdings
SELECT
    ticker,
    jsonb_array_elements(holdings) as holding
FROM v_kurv_latest
WHERE ticker = 'KQQQ';

-- Compare distribution rates across all ETFs
SELECT
    ticker,
    fund_name,
    distribution_rate,
    distribution_frequency,
    sec_yield_30day,
    expense_ratio,
    scraped_date
FROM v_kurv_latest
ORDER BY distribution_rate DESC;

-- Compare single stock income ETFs
SELECT
    ticker,
    fund_name,
    distribution_rate,
    nav,
    market_price,
    premium_discount
FROM v_kurv_latest
WHERE ticker IN ('AAPY', 'AMZP', 'GOOP', 'MSFY', 'NFLP', 'TSLP')
ORDER BY ticker;

-- Compare precious metals ETFs
SELECT
    ticker,
    fund_name,
    distribution_rate,
    distribution_frequency,
    nav,
    market_price
FROM v_kurv_latest
WHERE ticker IN ('KGLD', 'KSLV')
ORDER BY ticker;

-- Get growth & income ETFs
SELECT
    ticker,
    fund_name,
    expense_ratio,
    distribution_rate,
    nav,
    market_price,
    scraped_date
FROM v_kurv_latest
WHERE ticker IN ('KQQQ', 'KYLD')
ORDER BY ticker;

-- Track NAV premium/discount across all ETFs
SELECT
    ticker,
    fund_name,
    nav,
    market_price,
    premium_discount,
    scraped_date
FROM v_kurv_latest
ORDER BY premium_discount;
```

## Data Quality Features

**Date Normalization:**
- Automatically converts 2-digit years (YY) to 4-digit years (20YY)
- Filters out percentage values from date fields
- Validates date format: MM/DD/YYYY
- Example: "01/15/24" → "01/15/2024"

**Numeric Validation:**
- Strict validation for all numeric fields
- Rejects date patterns in numeric fields
- Validates percentage, dollar, and decimal values
- Prevents data corruption from misplaced values

## Adding New Kurv ETFs

To add new Kurv ETFs to the scraper:

1. Edit `scrape_kurv_all.py`
2. Add the new ETF to the `KURV_ETFS` dictionary:
   ```python
   KURV_ETFS = {
       # ... existing ETFs ...
       'NEWF': {
           'name': 'Kurv New Fund ETF',
           'category': 'Single Stock Income',  # or other category
           'url': 'https://www.kurvinvest.com/newf'
       }
   }
   ```
3. Test with: `python3 scrape_kurv_all.py --ticker NEWF`
4. All data will be stored in the same `raw_etfs_kurv` table

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
- Date normalization (YY → 20YY)
- Strict numeric validation
- Date-based unique constraint (one scrape per ticker per day)
- Upsert functionality (prevents duplicates)
- Category-based organization

## Data Refresh Schedule

Recommended scraping frequency:
- **Daily**: Full scrape of all ETFs (automated via cron)
  - Best run during off-peak hours (e.g., 2 AM)
  - Use default 5-second delay to be respectful
  - Total runtime: ~1 minute for all 10 ETFs
- **On-demand**: Scrape specific tickers as needed
  - No rate limiting needed for single ticker scrapes

**Note:** The date-based unique constraint ensures only one scrape per ticker per day, preventing accidental duplicates.

## Migration

Run the migration to create the table:

```bash
# Via Supabase SQL Editor
# Copy contents of: supabase/migrations/20251116_add_kurv_etf_data.sql
# Paste and run in: https://supabase.com/dashboard/project/[PROJECT_ID]/sql/new
```

## Data Structure

**Expense Ratio:** Text field (e.g., "0.99%")
**Inception Date:** Text field in MM/DD/YYYY format (e.g., "01/15/2024")
**Distribution Rate:** Text field (e.g., "35.19%")
**Distribution Frequency:** Text field (e.g., "Weekly", "Monthly")
**30-Day SEC Yield:** Text field (e.g., "2.31%")
**NAV:** Text field (e.g., "$25.43")
**Market Price:** Text field (e.g., "$25.41")
**Premium/Discount:** Text field (e.g., "-0.08%" or "+0.12%")

**Fund Details (JSONB):** Key-value pairs of fund information
```json
{
  "Ticker": "KQQQ",
  "CUSIP": "12345678",
  "Exchange": "NYSE Arca",
  "Primary Listing Exchange": "NYSE Arca"
}
```

**Performance Data (JSONB):** Performance metrics
```json
{
  "Total Return NAV (%)": {
    "YTD": "15.41%",
    "1 Month": "1.78%",
    "3 Months": "6.68%",
    "6 Months": "25.00%",
    "Since Inception": "30.00%"
  }
}
```

**Distributions (JSONB Array):** Distribution history
```json
[
  {
    "Declaration Date": "11/10/2024",
    "Ex-Dividend Date": "11/15/2024",
    "Record Date": "11/16/2024",
    "Payable Date": "11/20/2024",
    "Amount": "$0.45"
  },
  {
    "Declaration Date": "11/03/2024",
    "Ex-Dividend Date": "11/08/2024",
    "Record Date": "11/09/2024",
    "Payable Date": "11/13/2024",
    "Amount": "$0.43"
  }
]
```

**Holdings (JSONB Array):** Top 10 portfolio holdings
```json
[
  {
    "Ticker": "AAPL",
    "CUSIP": "037833100",
    "Description": "Apple Inc.",
    "Quantity": "10,000",
    "Market Value": "$1,500,000",
    "Percentage": "8.5%"
  },
  {
    "Ticker": "MSFT",
    "CUSIP": "594918104",
    "Description": "Microsoft Corporation",
    "Quantity": "8,500",
    "Market Value": "$1,275,000",
    "Percentage": "7.2%"
  }
]
```

## Troubleshooting

**Issue: Browser not found**
- Ensure Chrome/Chromium is installed in Docker container
- Check environment variables: `CHROME_BIN` and `CHROMEDRIVER_PATH`

**Issue: Table doesn't exist**
- Run the migration: `20251116_add_kurv_etf_data.sql`

**Issue: No data extracted**
- Check website structure hasn't changed
- Verify selectors in extraction methods
- Run with debug logging

**Issue: URL validation fails**
- Some ETFs may be recently launched or delisted
- Check the Kurv website directly
- Use `--skip-validation` to bypass (will fail during scraping if URL is invalid)

**Issue: Date format errors**
- The scraper automatically normalizes 2-digit years
- If dates still show as percentages, the website structure may have changed
- Check the `_normalize_date()` and `_validate_numeric_field()` methods

## ETF Categories

**Growth & Income ETFs:** Focus on technology and high-income strategies, combining growth potential with income generation.

**Precious Metals Income ETFs:** Provide exposure to gold and silver while generating enhanced income through options strategies.

**Single Stock Income ETFs (Yield Premium Strategy):** Generate premium income by selling options on popular mega-cap stocks. Each ETF focuses on a single underlying stock (AAPL, AMZN, GOOGL, MSFT, NFLX, TSLA) while selling covered calls and cash-secured puts to enhance yield.

## Important Notes

**Yield Premium Strategy:** The single stock income ETFs use a yield premium strategy that involves selling options on the underlying stock. This generates high income but limits upside potential and can experience volatility.

**Single Stock Concentration:** ETFs like AAPY, AMZP, GOOP, MSFY, NFLP, and TSLP have concentrated exposure to a single stock, which increases risk compared to diversified ETFs. Monitor these carefully for individual stock volatility.

**Precious Metals Volatility:** Gold and silver ETFs (KGLD, KSLV) can experience significant volatility based on commodity prices, inflation expectations, and currency movements.

**Distribution History:** The scraper captures full distribution history including declaration dates, ex-dividend dates, record dates, and payable dates. This is essential for yield analysis and tax planning.

**Premium/Discount Monitoring:** Income ETFs can trade at premiums or discounts to NAV. The scraper tracks this metric for all ETFs to help identify arbitrage opportunities and fair value.

## Future Enhancements

- [x] Add scrapers for all Kurv ETFs (10 supported)
- [x] Create unified scraper for all Kurv funds
- [x] Add historical data tracking (via scraped_date column)
- [x] Add date normalization for 2-digit years
- [x] Add strict numeric validation
- [x] Add category-based organization
- [ ] Create dashboard/visualization for performance comparison
- [ ] Add automated scheduling (cron jobs)
- [ ] Add data validation and quality checks
- [ ] Add API endpoints for Kurv data
- [ ] Add alerting for significant NAV premium/discount changes
- [ ] Add alerting for distribution rate changes
- [ ] Add single stock correlation analysis
- [ ] Add yield premium strategy performance tracking
- [ ] Add precious metals price correlation tracking
