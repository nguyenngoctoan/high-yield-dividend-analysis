# NEOS Funds ETF Scrapers

This directory contains scrapers for NEOS Funds ETF data.

## Overview

NEOS Funds specializes in income-generating ETFs using covered call and enhanced income strategies. These scrapers extract comprehensive data from NEOS ETF pages including performance metrics, fund details, distributions, and holdings.

## Available Scrapers

### scrape_neos_all.py (Recommended)

Universal scraper for all NEOS ETFs. Supports scraping individual tickers or all funds at once.

**Supported ETFs (13 total):**

- SPYI - NEOS S&P 500 High Income ETF
- QQQI - NEOS Nasdaq-100 High Income ETF
- IWMI - NEOS Russell 2000 High Income ETF
- NIHI - NEOS Enhanced Income 1-3 Month T-Bill ETF
- QQQH - NEOS Nasdaq-100 Enhanced Income ETF
- SPYH - NEOS S&P 500 Enhanced Income ETF
- BTCI - NEOS Bitcoin High Income ETF
- IYRI - NEOS iShares Russell 2000 ETF Enhanced Income ETF
- IAUI - NEOS iShares Gold Trust Enhanced Income ETF
- BNDI - NEOS Enhanced Income Aggregate Bond ETF
- HYBI - NEOS Enhanced Income High Yield Bond ETF
- CSHI - NEOS Enhanced Income Cash Alternative ETF
- TLTI - NEOS Enhanced Income 20+ Year Treasury ETF

**Data Collected:**

Extracted Fields:
- Expense ratio - extracted as text (e.g., "0.68%")
- Inception date - normalized to MM/DD/YYYY format (2-digit years converted to 20YY)
- Net assets - total assets under management
- Shares outstanding - number of shares outstanding
- Distribution rate - annual distribution rate
- 30-day SEC yield - standardized yield measure
- NAV - net asset value per share
- Market price - current market price
- Premium/discount - premium or discount to NAV

JSON Fields:
- Fund details - comprehensive fund information (CUSIP, exchange, etc.) as JSON
- Performance data - returns (1mo, 3mo, 6mo, YTD, 1yr, since inception) as JSON
- Distributions - monthly distribution history as JSON array
- Holdings - top 10 portfolio positions as JSON array

**Usage:**

```bash
# List available tickers
python3 scripts/scrapers/neos/scrape_neos_all.py --list

# Scrape a specific ETF
python3 scripts/scrapers/neos/scrape_neos_all.py --ticker SPYI

# Scrape all NEOS ETFs (validates URLs first, default: 5 second delay)
python3 scripts/scrapers/neos/scrape_neos_all.py --all

# Scrape all with custom delay (e.g., 10 seconds to be extra cautious)
python3 scripts/scrapers/neos/scrape_neos_all.py --all --delay 10

# Scrape all without URL validation (faster but may fail on invalid URLs)
python3 scripts/scrapers/neos/scrape_neos_all.py --all --skip-validation

# Run in Docker
docker exec dividend-api python3 /app/scripts/scrapers/neos/scrape_neos_all.py --ticker SPYI
docker exec dividend-api python3 /app/scripts/scrapers/neos/scrape_neos_all.py --all --delay 5
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
- Total time for all 13 ETFs: ~1-2 minutes (with 5s delay + validation)

**Database Table:**

Data is stored in the `raw_etfs_neos` table:

```sql
CREATE TABLE raw_etfs_neos (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL,
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Extracted fields
    expense_ratio TEXT,
    inception_date TEXT,
    net_assets TEXT,
    shares_outstanding TEXT,
    distribution_rate TEXT,
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
SELECT * FROM v_neos_latest;

-- Get latest data for SPYI
SELECT * FROM v_neos_latest WHERE ticker = 'SPYI';

-- Query performance data
SELECT
    ticker,
    scraped_at,
    expense_ratio,
    inception_date,
    net_assets,
    distribution_rate,
    sec_yield_30day,
    nav,
    market_price,
    premium_discount,
    performance_data->>'YTD' as ytd
FROM raw_etfs_neos
WHERE ticker = 'SPYI'
ORDER BY scraped_at DESC
LIMIT 1;

-- Query distributions
SELECT
    ticker,
    jsonb_array_elements(distributions) as distribution
FROM v_neos_latest
WHERE ticker = 'SPYI';

-- Query holdings
SELECT
    ticker,
    jsonb_array_elements(holdings) as holding
FROM v_neos_latest
WHERE ticker = 'SPYI';

-- Compare distribution rates across all ETFs
SELECT
    ticker,
    fund_name,
    distribution_rate,
    sec_yield_30day,
    expense_ratio,
    scraped_date
FROM v_neos_latest
ORDER BY distribution_rate DESC;

-- Get all high income ETFs
SELECT
    ticker,
    fund_name,
    distribution_rate,
    nav,
    market_price,
    premium_discount
FROM v_neos_latest
WHERE ticker IN ('SPYI', 'QQQI', 'IWMI', 'BTCI')
ORDER BY ticker;

-- Compare NAV premium/discount
SELECT
    ticker,
    fund_name,
    nav,
    market_price,
    premium_discount,
    scraped_date
FROM v_neos_latest
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

## Adding New NEOS ETFs

To add new NEOS ETFs to the scraper:

1. Edit `scrape_neos_all.py`
2. Add the new ETF to the `NEOS_ETFS` dictionary:
   ```python
   NEOS_ETFS = {
       # ... existing ETFs ...
       'NEWF': {
           'name': 'NEOS New Fund ETF',
           'url': 'https://neosfunds.com/newf/'
       }
   }
   ```
3. Test with: `python3 scrape_neos_all.py --ticker NEWF`
4. All data will be stored in the same `raw_etfs_neos` table

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

## Data Refresh Schedule

Recommended scraping frequency:
- **Daily**: Full scrape of all ETFs (automated via cron)
  - Best run during off-peak hours (e.g., 2 AM)
  - Use default 5-second delay to be respectful
  - Total runtime: ~1-2 minutes for all 13 ETFs
- **On-demand**: Scrape specific tickers as needed
  - No rate limiting needed for single ticker scrapes

**Note:** The date-based unique constraint ensures only one scrape per ticker per day, preventing accidental duplicates.

## Migration

Run the migration to create the table:

```bash
# Via Supabase SQL Editor
# Copy contents of: supabase/migrations/20251116_add_neos_etf_data.sql
# Paste and run in: https://supabase.com/dashboard/project/[PROJECT_ID]/sql/new
```

## Data Structure

**Expense Ratio:** Text field (e.g., "0.68%")
**Inception Date:** Text field in MM/DD/YYYY format (e.g., "01/15/2024")
**Net Assets:** Text field (e.g., "$1.2B" or "$1,200,000,000")
**Shares Outstanding:** Text field (e.g., "50,000,000")
**Distribution Rate:** Text field (e.g., "12.5%")
**30-Day SEC Yield:** Text field (e.g., "11.2%")
**NAV:** Text field (e.g., "$25.43")
**Market Price:** Text field (e.g., "$25.41")
**Premium/Discount:** Text field (e.g., "-0.08%" or "+0.12%")

**Fund Details (JSONB):** Key-value pairs of fund information
```json
{
  "Ticker": "SPYI",
  "CUSIP": "12345678",
  "Exchange": "NYSE Arca",
  "Bid-Ask Spread": "0.02%"
}
```

**Performance Data (JSONB):** Performance metrics
```json
{
  "NAV": {
    "1 Month": "2.34%",
    "3 Month": "7.12%",
    "6 Month": "14.56%",
    "YTD": "15.67%",
    "1 Year": "23.45%",
    "Since Inception": "28.90%"
  },
  "Market Price": {
    "1 Month": "2.31%",
    "3 Month": "7.08%",
    "YTD": "15.52%"
  }
}
```

**Distributions (JSONB Array):** Distribution history
```json
[
  {
    "Ex-Date": "11/15/2024",
    "Record Date": "11/16/2024",
    "Payable Date": "11/20/2024",
    "Distribution": "$0.45"
  },
  {
    "Ex-Date": "10/15/2024",
    "Record Date": "10/16/2024",
    "Payable Date": "10/20/2024",
    "Distribution": "$0.43"
  }
]
```

**Holdings (JSONB Array):** Top 10 portfolio holdings
```json
[
  {
    "Name": "NVIDIA Corporation",
    "Ticker": "NVDA",
    "Weight": "8.5%",
    "Shares": "10,000"
  },
  {
    "Name": "Microsoft Corporation",
    "Ticker": "MSFT",
    "Weight": "7.2%",
    "Shares": "8,500"
  }
]
```

## Troubleshooting

**Issue: Browser not found**
- Ensure Chrome/Chromium is installed in Docker container
- Check environment variables: `CHROME_BIN` and `CHROMEDRIVER_PATH`

**Issue: Table doesn't exist**
- Run the migration: `20251116_add_neos_etf_data.sql`

**Issue: No data extracted**
- Check website structure hasn't changed
- Verify selectors in extraction methods
- Run with debug logging

**Issue: URL validation fails**
- Some ETFs may be recently launched or delisted
- Check the NEOS Funds website directly
- Use `--skip-validation` to bypass (will fail during scraping if URL is invalid)

**Issue: Date format errors**
- The scraper automatically normalizes 2-digit years
- If dates still show as percentages, the website structure may have changed
- Check the `_normalize_date()` and `_validate_numeric_field()` methods

## Future Enhancements

- [x] Add scrapers for all NEOS ETFs (13 supported)
- [x] Create unified scraper for all NEOS funds
- [x] Add historical data tracking (via scraped_date column)
- [x] Add date normalization for 2-digit years
- [x] Add strict numeric validation
- [ ] Create dashboard/visualization for performance comparison
- [ ] Add automated scheduling (cron jobs)
- [ ] Add data validation and quality checks
- [ ] Add API endpoints for NEOS data
- [ ] Add alerting for significant NAV premium/discount changes
- [ ] Add alerting for distribution rate changes

## Notes

**High Income Strategy:** NEOS's high income ETFs (SPYI, QQQI, IWMI) use covered call strategies to generate enhanced income. Distribution rates can be significantly higher than traditional index ETFs.

**Enhanced Income Strategy:** The enhanced income series (QQQH, SPYH, IYRI, etc.) provides income enhancement while maintaining market exposure. Monitor distribution consistency as they can vary based on market conditions.

**Bitcoin ETF:** BTCI provides Bitcoin exposure with income generation through covered calls. This is a unique offering combining crypto exposure with income strategies.

**Bond ETFs:** NEOS bond ETFs (BNDI, HYBI, TLTI, NIHI, CSHI) provide enhanced income on traditional fixed income exposures. Useful for comparing yields across different bond durations and credit qualities.

**Monthly Distributions:** All NEOS ETFs provide monthly distributions, making them attractive for income investors. The scraper captures the full distribution history for yield analysis.
