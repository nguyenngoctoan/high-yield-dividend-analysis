# Defiance ETF Scrapers

This directory contains scrapers for Defiance ETF data.

## Overview

Defiance ETFs offer a diverse range of strategies including thematic investing, leveraged exposure, and enhanced income generation. These scrapers extract comprehensive data from Defiance ETF pages including performance metrics, fund details, distributions, and holdings.

## Available Scrapers

### scrape_defiance_all.py (Recommended)

Universal scraper for all Defiance ETFs. Supports scraping individual tickers or all funds at once.

**Supported ETFs (57 total):**

**Thematic (6):**
- QTUM - Defiance Quantum ETF
- JEDI - Defiance Star Wars & Beyond ETF
- SIXG - Defiance Connective Technologies ETF
- TRIL - Defiance Fintech AI ETF
- XMAG - Defiance Mega Cap ETF
- AIPO - Defiance AI & Productivity ETF

**Leveraged (39):**
- MSTX - Defiance Daily Target 2X Long MSTR ETF
- SMCX - Defiance Daily Target 2X Long SMCI ETF
- HIMZ - Defiance Daily Target 2X Short MSTR ETF
- LLYX - Defiance Daily Target 2X Long LILY ETF
- IONX - Defiance Daily Target 2X Long IONQ ETF
- AVGX - Defiance Daily Target 2X Long AVGO ETF
- NVOX - Defiance Daily Target 2X Long NVDA ETF
- SOFX - Defiance Daily Target 2X Long SOFI ETF
- RKLX - Defiance Daily Target 2X Long RKLB ETF
- OKLL - Defiance Daily Target 2X Long OKLO ETF
- PLTZ - Defiance Daily Target 2X Short PLTR ETF
- ORCX - Defiance Daily Target 2X Long ORCL ETF
- RGTX - Defiance Daily Target 2X Long RGTI ETF
- SMST - Defiance Daily Target 2X Long SMST ETF
- RIOX - Defiance Daily Target 2X Long RIOT ETF
- SOUX - Defiance Daily Target 2X Long SQ ETF
- HOOX - Defiance Daily Target 2X Long HOOD ETF
- SMCZ - Defiance Daily Target 2X Short SMCI ETF
- IONZ - Defiance Daily Target 2X Short IONQ ETF
- QPUX - Defiance Daily Target 2X Long QBTS ETF
- VSTL - Defiance Daily Target 2X Long VST ETF
- DKNX - Defiance Daily Target 2X Long DKS ETF
- JPX - Defiance Daily Target 2X Long JPM ETF
- CVNX - Defiance Daily Target 2X Long CVS ETF
- VIXI - Defiance Daily Target 2X Long VIX ETF
- ANEL - Defiance Daily Target 2X Long ANET ETF
- LLYZ - Defiance Daily Target 2X Short LILY ETF
- XPM - Defiance Daily Target 2X Long PM ETF
- QBTZ - Defiance Daily Target 2X Short QBTS ETF
- OSCX - Defiance Daily Target 2X Long OSCR ETF
- RGTZ - Defiance Daily Target 2X Short RGTI ETF
- LMNX - Defiance Daily Target 2X Long LMND ETF
- IRE - Defiance Daily Target 2X Long IREN ETF
- QSU - Defiance Daily Target 2X Long QSI ETF
- MPL - Defiance Daily Target 2X Long MPWR ETF
- AVXX - Defiance Daily Target 2X Short AVGO ETF
- HOOZ - Defiance Daily Target 2X Short HOOD ETF
- BMNZ - Defiance Daily Target 2X Short BITF ETF
- DAMD - Defiance Daily Target 2X Long AMD ETF

**Leveraged + Income (7):**
- MST - Defiance Daily Target 1.75X Long MSTR ETF
- HIMY - Defiance Daily Target 1.75X Short MSTR ETF
- SMCC - Defiance Daily Target 1.75X Long SMCI ETF
- AMDU - Defiance Daily Target 1.75X Long AMD ETF
- PLT - Defiance Daily Target 1.75X Long PLTR ETF
- HOOI - Defiance Daily Target 1.75X Long HOOD ETF
- ETHI - Defiance Daily Target 1.75X Long COIN ETF

**Income (8):**
- QQQY - Defiance Nasdaq 100 Enhanced Options Income ETF
- IWMY - Defiance Russell 2000 Enhanced Options Income ETF
- SPYT - Defiance S&P 500 Enhanced Options Income ETF
- WDTE - Defiance 0DTE ETF
- USOY - Defiance Ultra Short-Term Fixed Income ETF
- QQQT - Defiance Nasdaq 100 0DTE Income ETF
- GLDY - Defiance Gold Enhanced Options Income ETF
- QLDY - Defiance QQQ Enhanced Options Income ETF

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
python3 scripts/scrapers/defiance/scrape_defiance_all.py --list

# Scrape a specific ETF
python3 scripts/scrapers/defiance/scrape_defiance_all.py --ticker QQQY

# Scrape all Defiance ETFs (validates URLs first, default: 5 second delay)
python3 scripts/scrapers/defiance/scrape_defiance_all.py --all

# Scrape all with custom delay (e.g., 10 seconds to be extra cautious)
python3 scripts/scrapers/defiance/scrape_defiance_all.py --all --delay 10

# Scrape all without URL validation (faster but may fail on invalid URLs)
python3 scripts/scrapers/defiance/scrape_defiance_all.py --all --skip-validation

# Run in Docker
docker exec dividend-api python3 /app/scripts/scrapers/defiance/scrape_defiance_all.py --ticker QQQY
docker exec dividend-api python3 /app/scripts/scrapers/defiance/scrape_defiance_all.py --all --delay 5
```

**URL Validation:**
- By default, validates all URLs before scraping (quick HEAD requests)
- Identifies and skips invalid/404 pages automatically
- Use `--skip-validation` to bypass validation for faster execution
- Validation adds ~10-20 seconds but prevents wasted scraping attempts

**Rate Limiting:**
- Default delay between requests: **5 seconds** (when using `--all`)
- Configurable via `--delay` flag
- Recommended minimum: 3-5 seconds to avoid overwhelming the server
- Total time for all 57 ETFs: ~5-6 minutes (with 5s delay + validation)

**Database Table:**

Data is stored in the `raw_defiance_etf_data` table:

```sql
CREATE TABLE raw_defiance_etf_data (
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
SELECT * FROM v_defiance_latest;

-- Get latest data for QQQY
SELECT * FROM v_defiance_latest WHERE ticker = 'QQQY';

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
FROM raw_defiance_etf_data
WHERE ticker = 'QQQY'
ORDER BY scraped_at DESC
LIMIT 1;

-- Query distributions
SELECT
    ticker,
    jsonb_array_elements(distributions) as distribution
FROM v_defiance_latest
WHERE ticker = 'QQQY';

-- Query holdings
SELECT
    ticker,
    jsonb_array_elements(holdings) as holding
FROM v_defiance_latest
WHERE ticker = 'QQQY';

-- Compare distribution rates across all income ETFs
SELECT
    ticker,
    fund_name,
    distribution_rate,
    distribution_frequency,
    sec_yield_30day,
    expense_ratio,
    scraped_date
FROM v_defiance_latest
WHERE ticker IN ('QQQY', 'IWMY', 'SPYT', 'WDTE', 'USOY', 'QQQT', 'GLDY', 'QLDY')
ORDER BY distribution_rate DESC;

-- Compare leveraged ETFs
SELECT
    ticker,
    fund_name,
    nav,
    market_price,
    premium_discount
FROM v_defiance_latest
WHERE ticker IN ('MSTX', 'NVOX', 'AVGX', 'IONX', 'SMCX')
ORDER BY ticker;

-- Get all thematic ETFs
SELECT
    ticker,
    fund_name,
    expense_ratio,
    nav,
    market_price,
    scraped_date
FROM v_defiance_latest
WHERE ticker IN ('QTUM', 'JEDI', 'SIXG', 'TRIL', 'XMAG', 'AIPO')
ORDER BY ticker;

-- Compare 1.75X vs 2X leverage products
SELECT
    ticker,
    fund_name,
    distribution_rate,
    nav,
    premium_discount
FROM v_defiance_latest
WHERE ticker IN ('MST', 'MSTX', 'HIMY', 'HIMZ')
ORDER BY ticker;

-- Track NAV premium/discount across all ETFs
SELECT
    ticker,
    fund_name,
    nav,
    market_price,
    premium_discount,
    scraped_date
FROM v_defiance_latest
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

## Adding New Defiance ETFs

To add new Defiance ETFs to the scraper:

1. Edit `scrape_defiance_all.py`
2. Add the new ETF to the `DEFIANCE_ETFS` dictionary:
   ```python
   DEFIANCE_ETFS = {
       # ... existing ETFs ...
       'NEWF': {
           'name': 'Defiance New Fund ETF',
           'category': 'Thematic',  # or 'Leveraged', 'Income', etc.
           'url': 'https://www.defianceetfs.com/newf/'
       }
   }
   ```
3. Test with: `python3 scrape_defiance_all.py --ticker NEWF`
4. All data will be stored in the same `raw_defiance_etf_data` table

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
  - Total runtime: ~5-6 minutes for all 57 ETFs
- **On-demand**: Scrape specific tickers as needed
  - No rate limiting needed for single ticker scrapes

**Note:** The date-based unique constraint ensures only one scrape per ticker per day, preventing accidental duplicates.

## Migration

Run the migration to create the table:

```bash
# Via Supabase SQL Editor
# Copy contents of: supabase/migrations/20251116_add_defiance_etf_data.sql
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
  "Ticker": "QQQY",
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
    "Ex-Date": "11/15/2024",
    "Record Date": "11/16/2024",
    "Payable Date": "11/20/2024",
    "Distribution": "$0.45"
  },
  {
    "Ex-Date": "11/08/2024",
    "Record Date": "11/09/2024",
    "Payable Date": "11/13/2024",
    "Distribution": "$0.43"
  }
]
```

**Holdings (JSONB Array):** Top 10 portfolio holdings
```json
[
  {
    "Name": "Apple Inc.",
    "Ticker": "AAPL",
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
- Run the migration: `20251116_add_defiance_etf_data.sql`

**Issue: No data extracted**
- Check website structure hasn't changed
- Verify selectors in extraction methods
- Run with debug logging

**Issue: URL validation fails**
- Some ETFs may be recently launched or delisted
- Check the Defiance ETFs website directly
- Use `--skip-validation` to bypass (will fail during scraping if URL is invalid)

**Issue: Date format errors**
- The scraper automatically normalizes 2-digit years
- If dates still show as percentages, the website structure may have changed
- Check the `_normalize_date()` and `_validate_numeric_field()` methods

## ETF Categories

**Thematic ETFs:** Focus on emerging trends and technologies like quantum computing, AI, and connectivity.

**Leveraged ETFs (2X):** Provide 2X daily leveraged exposure (long or short) to individual stocks. These are designed for short-term trading and daily rebalancing. High risk, high volatility.

**Leveraged + Income ETFs (1.75X):** Combine 1.75X daily leverage with income generation through covered calls. Slightly lower leverage than 2X products, potentially more suitable for income-focused strategies.

**Income ETFs:** Focus on generating enhanced income through options strategies (0DTE, covered calls) while maintaining exposure to underlying indexes. Popular for income investors seeking higher yields than traditional ETFs.

## Important Notes

**0DTE Strategy:** WDTE and QQQT use zero-days-to-expiration (0DTE) options strategies. These ETFs sell very short-dated options to generate high income but with unique risk characteristics.

**Weekly Distributions:** Several income ETFs (like QQQY) provide weekly distributions, making them attractive for investors seeking frequent cash flow. The scraper captures full distribution history for yield analysis.

**Leveraged Product Risks:** All leveraged ETFs (2X and 1.75X) use daily rebalancing and are designed for short-term trading. They are not suitable for long-term buy-and-hold strategies due to compounding effects.

**Short ETFs:** Short/inverse leveraged ETFs (HIMZ, SMCZ, PLTZ, etc.) provide inverse exposure. Monitor these carefully as they can experience significant volatility and decay over time.

**Premium/Discount Monitoring:** Leveraged and income ETFs can trade at premiums or discounts to NAV. The scraper tracks this metric for all ETFs to help identify arbitrage opportunities.

## Future Enhancements

- [x] Add scrapers for all Defiance ETFs (57 supported)
- [x] Create unified scraper for all Defiance funds
- [x] Add historical data tracking (via scraped_date column)
- [x] Add date normalization for 2-digit years
- [x] Add strict numeric validation
- [x] Add category-based organization
- [ ] Create dashboard/visualization for performance comparison
- [ ] Add automated scheduling (cron jobs)
- [ ] Add data validation and quality checks
- [ ] Add API endpoints for Defiance data
- [ ] Add alerting for significant NAV premium/discount changes
- [ ] Add alerting for distribution rate changes
- [ ] Add leverage decay analysis for 2X products
- [ ] Add 0DTE strategy performance tracking
