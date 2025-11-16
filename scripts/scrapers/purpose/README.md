# Purpose Investments ETF Scraper

Complete web scraper for all 81 Purpose Investments ETFs across 7 categories. Uses simple HTTP requests + BeautifulSoup (NO Selenium needed!) and stores comprehensive data in Supabase.

## Overview

Purpose Investments offers 81 ETFs across 7 distinct categories, including their popular Yield Shares covered call strategy ETFs.

### 1. Equity - Yield Shares US Tech (16 ETFs)

Covered call strategies on major US tech stocks for enhanced income:
- **MSFY** - Microsoft (MSFT) Yield Shares Purpose ETF
- **YTSL** - Tesla (TSLA) Yield Shares Purpose ETF
- **APLY** - Apple (AAPL) Yield Shares Purpose ETF
- **YNVD** - NVIDIA (NVDA) Yield Shares Purpose ETF
- **YGOG** - Alphabet (GOOGL) Yield Shares Purpose ETF
- **YMET** - Meta (META) Yield Shares Purpose ETF
- **YAMD** - AMD (AMD) Yield Shares Purpose ETF
- **YAMZ** - Amazon (AMZN) Yield Shares Purpose ETF
- **BRKY** - Berkshire Hathaway (BRK) Yield Shares Purpose ETF
- **YCST** - Costco (COST) Yield Shares Purpose ETF
- **YNET** - Netflix (NFLX) Yield Shares Purpose ETF
- **YAVG** - Broadcom (AVGO) Yield Shares Purpose ETF
- **YCON** - Coinbase (COIN) Yield Shares Purpose ETF
- **YUNH** - UnitedHealth Group (UNH) Yield Shares Purpose ETF
- **YPLT** - Palantir (PLTR) Yield Shares Purpose ETF
- **YMAG** - Tech Innovators Yield Shares Purpose ETF (Tech Basket)

### 2. Equity - Yield Shares Canadian (10 ETFs)

Covered call strategies on major Canadian stocks:
- **TDY** - Purpose TD (TD) Yield Shares ETF
- **CNQY** - Canadian Natural Resources (CNQ) Yield Shares ETF
- **BNSY** - Scotiabank (BNS) Yield Shares ETF
- **RBCY** - RBC (RY) Yield Shares ETF
- **ATDY** - Couche-Tard (ATD) Yield Shares ETF
- **DOLY** - Dollarama (DOL) Yield Shares ETF
- **SHPY** - Shopify (SHOP) Yield Shares ETF
- **ENBY** - Enbridge (ENB) Yield Shares ETF
- **BNY** - Brookfield (BN) Yield Shares ETF
- **TY** - Telus (T) Yield Shares ETF

### 3. Equity - Traditional (12 ETFs)

Traditional equity strategies without covered calls:
- **PBI** - Purpose Best Ideas Fund
- **PINV** - Purpose Global Innovators Fund
- **REDRGI** - Purpose Global Resource Fund
- **PHR** - Purpose Real Estate Income Fund
- **RDE** - Purpose Core Equity Income Fund
- **PDF** - Purpose Core Dividend Fund
- **BNC** - Purpose Canadian Financial Income Fund
- **PDIV** - Purpose Enhanced Dividend Fund
- **PRP** - Purpose Conservative Income Fund
- **PID** - Purpose International Dividend Fund
- **REM** - Purpose Emerging Markets Dividend Fund
- **RTT** - Purpose Tactical Thematic Fund

### 4. Fixed Income (7 ETFs)

Bond and preferred share strategies:
- **IGB** - Purpose Global Bond Class
- **RPS** - Purpose Canadian Preferred Share Fund
- **SYLD** - Purpose Strategic Yield Fund
- **BND** - Purpose Global Bond Fund
- **FLX** - Purpose Global Flexible Credit Fund
- **RPU** - Purpose US Preferred Share Fund
- **PBD** - Purpose Total Return Bond Fund

### 5. Cryptocurrency (9 ETFs)

First-in-Canada cryptocurrency ETFs:
- **BTCC** - Purpose Bitcoin ETF (first Bitcoin ETF in North America!)
- **ETHH** - Purpose Ether ETF
- **ETHY** - Purpose Ether Yield ETF
- **BTCY** - Purpose Bitcoin Yield ETF
- **ETHO.B** - Purpose Core Ether ETF
- **BTCO.B** - Purpose Core Bitcoin ETF
- **XRPP** - Purpose XRP ETF
- **SOLL** - Purpose Solana ETF
- **ETHC.B** - Purpose Ether Staking Corp. ETF

### 6. Alternatives (12 ETFs)

Alternative investment strategies:
- **CROP** - Purpose Credit Opportunities Fund
- **PHW** - Purpose International Enhanced Equity Income Fund
- **PSY2** - Purpose Structured Equity Yield Fund
- **PAYF** - Purpose Enhanced Premium Yield Fund
- **PYF** - Purpose Premium Yield Fund
- **PSG** - Purpose Structured Equity Growth Fund
- **PSYL** - Purpose Structured Equity Yield Plus Fund
- **PHE** - Purpose Tactical Hedged Equity Fund
- **PMM** - Purpose Multi-Strategy Market Neutral Fund
- **BNK** - Big Banc Split Corp

### 7. Multi-Asset (8 ETFs)

Diversified multi-asset allocation:
- **RTA** - Purpose Tactical Asset Allocation Fund
- **PABF** - Purpose Active Balanced Fund
- **PACF** - Purpose Active Conservative Fund
- **PAGF** - Purpose Active Growth Fund
- **PINC** - Purpose Multi-Asset Income Fund
- **PIN** - Purpose Monthly Income Fund
- **PRA** - Purpose Diversified Real Asset Fund
- **LPF** - Longevity Pension Fund

### 8. Commodities (2 ETFs)

Physical precious metals:
- **KILO** - Purpose Gold Bullion Fund
- **SBT** - Purpose Silver Bullion Fund

### 9. Cash Management (5 ETFs)

High-interest savings and money market:
- **MNY** - Purpose Cash Management Fund
- **MNU.U** - Purpose USD Cash Management Fund
- **PSA** - Purpose High Interest Savings Fund
- **PSU.U** - Purpose US Cash Fund
- **PMR** - Purpose Premium Money Market Fund

## Key Features

- **NO Selenium Required!** Uses simple requests + BeautifulSoup
- Server-side rendered data extraction from Next.js `__NEXT_DATA__` tag
- Universal scraper for all 81 Purpose ETFs
- Category-based filtering
- Fast rate limiting (2 second default - no browser overhead)
- Comprehensive error handling
- Supabase integration for data storage
- Progress tracking and logging

## Technical Approach

**Important Discovery**: Purpose Investments uses Next.js server-side rendering. All fund data is embedded as JSON in the page source within a `<script id="__NEXT_DATA__">` tag. This means:

- ✅ NO Selenium/browser automation needed
- ✅ Faster scraping (2 second delay vs 5+ for Selenium)
- ✅ More reliable extraction (JSON parsing vs HTML scraping)
- ✅ Lower resource usage

## Data Captured

### Core Fields
- Ticker symbol
- Fund name
- Series (ETF, F, A, I)
- Category
- NAV (Net Asset Value)
- AUM (Assets Under Management)
- Management fee
- MER (Management Expense Ratio)
- Distribution frequency
- Current yield (especially for Yield Shares)
- Fund structure (Investment Trust, Corporation)
- CUSIP identifier
- Exchange (NEOE, NEO, etc.)
- Currency hedged status
- Settlement period

### Fixed Income Specific
- Duration
- Coupon rate
- Maturity yield
- Credit profile

### Yield Shares Specific
- Underlying stock ticker
- Current yield (typically 15-35%)
- Covered call statistics:
  - Call options written
  - Underlying equities count
  - Covered call expiries
  - Out of the money distribution
- Leverage component

### Cryptocurrency Specific
- Coin holdings amount
- Storage method
- Units per coin
- Wallet allocation

### JSON Fields (JSONB in database)
- **fund_details**: Series available, additional metadata
- **portfolio_data**:
  - Asset allocation (Level 1)
  - Sector allocation (Level 2)
  - Credit profile (Level 2)
  - Option statistics for Yield Shares (Level 2)
  - Top 10 holdings (Level 4)
  - Portfolio date
- **distributions**: Full distribution history with ex-dates, record dates, payment dates, amounts
- **performance_data**: Historical NAV returns from inception to current
- **eligibilities**: DRIP, PACC, SWP, RRSP eligibility flags

## Installation

```bash
# Install dependencies
pip install requests beautifulsoup4 python-dotenv

# No Selenium needed!
```

## Usage

### List Available ETFs

```bash
python scrape_purpose_all.py --list
```

### Scrape Single ETF

```bash
# Scrape YTSL (Tesla Yield Shares)
python scrape_purpose_all.py --ticker YTSL

# Scrape BTCC (Bitcoin ETF)
python scrape_purpose_all.py --ticker BTCC

# Scrape MSFY (Microsoft Yield Shares)
python scrape_purpose_all.py --ticker MSFY
```

### Scrape by Category

```bash
# Scrape all Yield Shares US Tech ETFs
python scrape_purpose_all.py --category "Yield Shares US Tech"

# Scrape all Cryptocurrency ETFs
python scrape_purpose_all.py --category Cryptocurrency

# Scrape all Fixed Income ETFs
python scrape_purpose_all.py --category "Fixed Income"
```

### Scrape All ETFs

```bash
# Scrape all 81 ETFs with 2-second delay
python scrape_purpose_all.py --all

# Scrape with custom delay (5 seconds)
python scrape_purpose_all.py --all --delay 5

# Skip URL validation (faster but may fail)
python scrape_purpose_all.py --all --skip-validation
```

### Test Mode

```bash
# Test mode: scrape only 3 ETFs
python scrape_purpose_all.py --test
```

### Limit Number of ETFs

```bash
# Scrape first 10 ETFs only
python scrape_purpose_all.py --all --limit 10
```

## Command Line Options

```
--ticker, -t      Specific ticker to scrape (e.g., YTSL, BTCC)
--all, -a         Scrape all Purpose ETFs
--category, -c    Scrape by category (partial match supported)
--list, -l        List available tickers by category
--delay, -d       Delay in seconds between requests (default: 2)
--limit           Limit number of ETFs to scrape
--test            Test mode: scrape only 3 ETFs
--skip-validation Skip URL validation before scraping
```

## Database Schema

Data is stored in `raw_purpose_etf_data` table:

```sql
CREATE TABLE raw_purpose_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Core fields
    series VARCHAR(10),
    nav TEXT,
    aum TEXT,
    management_fee TEXT,
    mer TEXT,
    distribution_frequency TEXT,
    category TEXT,
    current_yield TEXT,
    fund_structure TEXT,
    cusip TEXT,
    exchange TEXT,
    currency_hedged BOOLEAN,
    settlement TEXT,

    -- Fixed income specific
    duration TEXT,
    coupon TEXT,
    maturity_yield TEXT,

    -- Yield Shares specific
    underlying TEXT,

    -- JSON fields
    fund_details JSONB,
    portfolio_data JSONB,
    distributions JSONB,
    performance_data JSONB,
    eligibilities JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_purpose_ticker_scraped_date UNIQUE (ticker, scraped_date)
);
```

## Query Examples

### Get Latest Data for All ETFs

```sql
SELECT * FROM v_purpose_latest;
```

### Filter by Category

```sql
SELECT ticker, fund_name, category, current_yield, nav, aum
FROM v_purpose_latest
WHERE category LIKE '%Yield Shares%'
ORDER BY current_yield DESC NULLS LAST;
```

### Find Highest Yielding Yield Shares ETFs

```sql
SELECT ticker, fund_name, underlying, current_yield, nav
FROM v_purpose_latest
WHERE category LIKE '%Yield Shares%'
  AND current_yield IS NOT NULL
ORDER BY CAST(REPLACE(current_yield, '%', '') AS DECIMAL) DESC
LIMIT 10;
```

### Get Cryptocurrency ETFs

```sql
SELECT ticker, fund_name, underlying, nav, aum
FROM v_purpose_latest
WHERE category = 'Cryptocurrency'
ORDER BY ticker;
```

### Option Statistics for Yield Shares

```sql
SELECT
    ticker,
    fund_name,
    underlying,
    current_yield,
    portfolio_data->'option_statistics' as option_stats
FROM v_purpose_latest
WHERE portfolio_data->'option_statistics' IS NOT NULL
  AND jsonb_typeof(portfolio_data->'option_statistics') = 'object'
  AND portfolio_data->'option_statistics' != '{}'::jsonb
ORDER BY ticker;
```

### Distribution History

```sql
SELECT
    ticker,
    fund_name,
    distribution_frequency,
    jsonb_array_length(distributions) as distribution_count,
    distributions->0 as latest_distribution
FROM v_purpose_latest
WHERE distributions IS NOT NULL
  AND jsonb_array_length(distributions) > 0
ORDER BY jsonb_array_length(distributions) DESC;
```

### Top Holdings by Fund

```sql
SELECT
    ticker,
    fund_name,
    portfolio_data->'top_holdings' as holdings
FROM v_purpose_latest
WHERE portfolio_data->'top_holdings' IS NOT NULL
  AND jsonb_array_length(portfolio_data->'top_holdings') > 0;
```

### Eligibility Programs

```sql
SELECT
    ticker,
    fund_name,
    eligibilities->>'drip' as drip_eligible,
    eligibilities->>'pacc' as pacc_eligible,
    eligibilities->>'swp' as swp_eligible,
    eligibilities->>'rsp' as rrsp_eligible
FROM v_purpose_latest
WHERE eligibilities IS NOT NULL;
```

## URL Pattern

All Purpose ETF pages follow this pattern:

```
https://www.purposeinvest.com/funds/{fund-slug}
```

Examples:
- `https://www.purposeinvest.com/funds/tesla-yield-shares-purpose-etf` (YTSL)
- `https://www.purposeinvest.com/funds/purpose-bitcoin-etf` (BTCC)
- `https://www.purposeinvest.com/funds/microsoft-yield-shares-purpose-etf` (MSFY)

Slug naming patterns:
- **Yield Shares**: `{company-name}-yield-shares-purpose-etf`
- **Regular**: `purpose-{fund-name}-etf` or `purpose-{fund-name}-fund`

## Data Extraction Method

Purpose uses Next.js with server-side rendering. All fund data is embedded in the HTML:

```html
<script id="__NEXT_DATA__" type="application/json">
{
  "props": {
    "pageProps": {
      "fundData": {
        "code": "YTSL",
        "name": "Tesla (TSLA) Yield Shares Purpose ETF",
        "series": {...},
        "details": {...},
        "portfolio": {...},
        "returns": {...},
        "distributions": {...},
        "eligibilities": {...}
      }
    }
  }
}
</script>
```

Our scraper:
1. Makes HTTP GET request (no browser needed)
2. Parses HTML with BeautifulSoup
3. Finds `<script id="__NEXT_DATA__">` tag
4. Extracts and parses JSON
5. Navigates to `props.pageProps.fundData`
6. Extracts all relevant fields

## Data Structure

### fundData Object Structure

```json
{
  "code": "YTSL",
  "name": "Tesla (TSLA) Yield Shares Purpose ETF",
  "series": {
    "ETF": {...},
    "F": {...},
    "A": {...},
    "I": {...}
  },
  "details": {
    "ETF": [{
      "nav": "23.55",
      "current_yield": "30.57%",
      "aum": {"cad": "$500M", "usd": "$370M"},
      "mgmt_fee": "0.40%",
      "mer": "1.65%",
      "fund_structure": "Investment Trust",
      "cusip": "74017E107",
      "exchange": "NEOE",
      "distribution_frequency": "Monthly",
      "curr_hedged": false,
      "settlement_date": "T+1"
    }]
  },
  "portfolio": {
    "dt": "2025-10-31",
    "Level1": {
      "asset_class": {...}
    },
    "Level2": {
      "sector": {...},
      "portfolio_stats_options": {
        "Call Options Written": "1,234",
        "Underlying Equities": "12,345",
        "Covered Call Expiries": {...},
        "Out of the Money (OTM)": {...}
      }
    },
    "Level4": {
      "holdings": [...]
    }
  },
  "distributions": {
    "ETF": [
      {
        "amount": 0.60,
        "date_ex": "2025-10-29",
        "date_pay": "2025-11-04",
        "date_rec": "2025-10-29",
        "dvd_type": "Regular"
      }
    ]
  },
  "returns": {
    "ETF": {
      "2025-11-14": 23.55,
      "2025-11-13": 23.42,
      ...
    }
  },
  "eligibilities": {
    "ETF": {
      "drip": true,
      "pacc": true,
      "swp": true,
      "rsp": true
    }
  }
}
```

## Rate Limiting

- Default delay: 2 seconds between requests
- Configurable via `--delay` flag
- Much faster than Selenium-based scrapers (no browser overhead)
- Recommended: 2-5 seconds for polite scraping

## Error Handling

- URL validation before scraping (optional, can skip with `--skip-validation`)
- Comprehensive logging at INFO/WARNING/ERROR levels
- Graceful degradation on missing data
- Per-field extraction with safe getters
- JSON parsing error handling
- HTTP request timeout and retry logic

## Performance Comparison

**Purpose (requests)** vs **GraniteShares/Kurv (Selenium)**:

| Metric | Purpose (requests) | GraniteShares (Selenium) |
|--------|-------------------|-------------------------|
| Dependencies | requests, beautifulsoup4 | selenium, chromedriver, chrome |
| Resource Usage | Low | High (full browser) |
| Speed per ETF | ~3 seconds | ~10 seconds |
| Default delay | 2 seconds | 5 seconds |
| 81 ETFs total time | ~7 minutes | ~25 minutes (if it existed) |
| Reliability | High | Medium (browser issues) |

## Troubleshooting

### Missing Data Fields

Some ETFs may not have all fields populated:
- Fixed income fields (duration, coupon) only on bond/preferred share funds
- Option statistics only on Yield Shares ETFs
- Current yield may be null for non-income funds
- Cryptocurrency-specific fields only on crypto ETFs

The scraper handles missing data gracefully:
- Missing fields are stored as NULL
- JSON fields with no data are stored as empty objects
- Warnings logged for unexpected missing data

### JSON Parsing Errors

If `__NEXT_DATA__` extraction fails:
1. Check if Purpose changed their website structure
2. Verify URL is correct and accessible
3. Check HTML source for `<script id="__NEXT_DATA__">`
4. Review error logs for details

### URL Validation Failures

If URL validation fails but you know the URLs are valid:
```bash
# Skip validation
python scrape_purpose_all.py --all --skip-validation
```

## Maintenance

### Database Migration

Run the migration to create the table:

```bash
# Using Supabase CLI
supabase db push supabase/migrations/20251116_add_purpose_etf_data.sql

# Or apply directly to database
psql -d your_database -f supabase/migrations/20251116_add_purpose_etf_data.sql
```

### Updating ETF List

When Purpose adds new ETFs:

1. Update `PURPOSE_ETFS` dictionary in `scrape_purpose_all.py`
2. Add ticker, name, slug, category, and underlying (if applicable)
3. Test with single ticker: `python scrape_purpose_all.py --ticker NEW_TICKER`

### Finding New ETF Slugs

Visit https://www.purposeinvest.com/invest and inspect fund URLs to find slugs.

## Comparison to Other Scrapers

Similar to YieldMax, Roundhill, NEOS, Defiance, Kurv, and GraniteShares scrapers:
- Same database structure (raw table + latest view)
- Same CLI interface and patterns
- Same error handling approach
- Universal scraper for entire ETF family

**Key difference**: Purpose uses requests instead of Selenium due to server-side rendering!

## License

MIT License - Part of high-yield-dividend-analysis project

## Support

For issues or questions:
1. Check logs for error messages
2. Verify URL accessibility: `curl https://www.purposeinvest.com/funds/tesla-yield-shares-purpose-etf`
3. Test with single ticker first
4. Review database schema and permissions
5. Check if `__NEXT_DATA__` tag exists in page source

## Version History

- v1.0.0 (2025-11-16): Initial release with all 81 ETFs

## Additional Resources

- **Purpose Investments**: https://www.purposeinvest.com
- **Fund Documents**: https://www.purposeinvest.com/fund-documents
- **Discovery Guide**: See `PURPOSE_ETF_SCRAPING_GUIDE.md` for technical details
- **Complete List**: See `PURPOSE_ETF_COMPLETE_LIST.json` for full ticker mapping
