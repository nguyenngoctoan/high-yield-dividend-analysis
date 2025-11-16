# Global X Canada ETFs Scraper

Comprehensive web scraper for all 107 Global X Canada ETF products. Extracts fund metrics, covered call statistics, holdings, distributions, and performance data.

**Key Feature**: Uses standard HTTP requests + BeautifulSoup - **NO Selenium required**! All data is in static HTML.

## Overview

Global X Canada offers 107 ETFs across 13 categories with diverse investment strategies:
- Traditional index tracking
- Covered call income generation
- 25% leveraged growth products (Enhanced)
- 2x leveraged/inverse products (BetaPro)
- Tax-efficient corporate class structures
- Thematic technology and sector exposure
- Asset allocation and cash management

**Total ETFs**: 107 (106 active + 1 coming soon)

## ETF Categories

### 1. Cash & Fixed Income (19 ETFs)
Money market, T-bills, government bonds, and premium yield strategies.

**Examples**:
- `CASH` - High Interest Savings ETF
- `CBIL` / `CBIL.U` - 0-3 Month T-Bill ETF (CAD/USD)
- `PAYS` - Short-Term Government Bond Premium Yield
- `TSTX` / `TSTX.U` / `TSTX.F` - 1-3 Year U.S. Treasury (CAD/USD/Hedged)
- `TLTX` / `TLTX.U` / `TLTX.F` - 20+ Year U.S. Treasury (CAD/USD/Hedged)

### 2. Corporate Class (8 ETFs)
Tax-efficient swap-based structures for Canadian investors.

**Examples**:
- `HXS` / `HXS.U` - S&P 500 Index Corporate Class
- `HXT` / `HXT.U` - S&P/TSX 60 Index Corporate Class
- `HXQ` / `HXQ.U` - Nasdaq-100 Index Corporate Class
- `HSAV` - Cash Maximizer Corporate Class

### 3. Thematic (16 ETFs)
Focused exposure to specific themes and sectors.

**Examples**:
- `SHLD` - Defence Tech Index
- `MTRX` - AI Infrastructure Index
- `AIGO` - AI & Technology Index
- `CHPS` / `CHPS.U` - AI Semiconductor Index
- `HLIT` - Lithium Producers Index
- `HMMJ` / `HMMJ.U` - Marijuana Life Sciences Index
- `MEDX` - Equal Weight Global Healthcare Index

### 4. Enhanced Growth (6 ETFs)
25% leveraged index exposure for amplified returns.

**Examples**:
- `CANL` - Enhanced S&P/TSX 60 Index (1.25x)
- `USSL` - Enhanced S&P 500 Index (1.25x)
- `QQQL` - Enhanced NASDAQ-100 Index (1.25x)
- `BNKL` - Enhanced Equal Weight Banks Index (1.25x)

### 5. Equity Essentials - Core (12 ETFs)
Fundamental index tracking for portfolio building.

**Examples**:
- `CNDX` - S&P/TSX 60 Index
- `HBNK` - Equal Weight Canadian Banks Index
- `USSX` / `USSX.U` - S&P 500 Index
- `QQQX` / `QQQX.U` - Nasdaq-100 Index
- `RSSX` / `RSSX.U` - Russell 2000 Index

### 6. Covered Call - Index (9 ETFs)
Index-based covered call strategies for enhanced income.

**Examples**:
- `CNCC` - S&P/TSX 60 Covered Call
- `USCC` / `USCC.U` - S&P 500 Covered Call
- `QQCC` / `QQCC.U` - NASDAQ-100 Covered Call
- `RSCC` / `RSCC.U` - Russell 2000 Covered Call

**Covered Call Metrics Captured**:
- Average Coverage (%)
- Average Moneyness (%)
- Option Annualized Yield (%)
- Dividend Yield (%)

### 7. Covered Call - Sector (2 ETFs)
Sector-specific covered call strategies.

**Examples**:
- `BKCC` - Equal Weight Canadian Bank Covered Call
- `RNCC` - Equal Weight Canadian Telecommunications Covered Call

### 8. Enhanced Covered Call (9 ETFs)
25% leveraged covered call strategies combining growth and income.

**Examples**:
- `CNCL` - Enhanced S&P/TSX 60 Covered Call (1.25x)
- `USCL` - Enhanced S&P 500 Covered Call (1.25x)
- `QQCL` - Enhanced NASDAQ-100 Covered Call (1.25x)
- `BKCL` - Enhanced Equal Weight Canadian Banks Covered Call (1.25x)

### 9. Commodities - Covered Call (5 ETFs)
Covered call strategies on commodity-related equities.

**Examples**:
- `ENCC` - Canadian Oil and Gas Equity Covered Call
- `GLCC` - Gold Producer Equity Covered Call
- `GLCL` - Enhanced Gold Producer Equity Covered Call (1.25x)
- `AGCC` - Silver Covered Call
- `HGY` - Gold Yield ETF

### 10. Cryptocurrency - Covered Call (4 ETFs)
Covered call strategies on cryptocurrency exposure.

**Examples**:
- `BCCC` / `BCCC.U` - Bitcoin Covered Call
- `BCCL` / `BCCL.U` - Enhanced Bitcoin Covered Call (1.25x)

### 11. Precious Metals (7 ETFs)
Physical bullion and mining equity exposure.

**Examples**:
- `HUG` - Gold ETF (Physical Bullion)
- `HUZ` - Silver ETF (Physical Bullion)
- `GLDX` - Gold Producers Index ETF

### 12. Asset Allocation (8 ETFs)
Multi-asset portfolios with varying risk profiles.

**Examples**:
- `HCON` - Conservative Asset Allocation
- `HBAL` - Balanced Asset Allocation
- `HGRW` - Growth Asset Allocation
- `HEQT` - All-Equity Asset Allocation
- `HEQL` - Enhanced All-Equity Asset Allocation (1.25x)
- `EQCC` - All-Equity Asset Allocation Covered Call

### 13. BetaPro (7 ETFs)
2x leveraged and inverse leveraged daily products.

**Examples**:
- `HQU` - NASDAQ-100® 2x Daily Bull
- `HSU` - S&P 500® 2x Daily Bull
- `HNU` - Natural Gas Leveraged Daily Bull (2x)
- `HND` - Natural Gas Inverse Leveraged Daily Bear (-2x)
- `HGU` - Canadian Gold Miners 2x Daily Bull
- `HOU` - Crude Oil Leveraged Daily Bull (2x)
- `HZU` - Silver 2x Daily Bull

## Data Fields Captured

### Core Fund Metrics
- Ticker, Fund Name, Category
- CUSIP, Inception Date
- NAV, Market Price, Premium/Discount
- Management Fee, MER, TER
- Net Assets (AUM)
- Distribution Yield, Distribution Frequency
- Benchmark Index
- Leverage Ratio (for Enhanced/BetaPro products)

### Covered Call Specific (30+ ETFs)
- Average Coverage
- Average Moneyness
- Option Annualized Yield
- Dividend Yield

### JSONB Fields
- **fund_details**: Investment objective, risk rating, reasons to consider
- **holdings**: Top 10 holdings with security name and weight
- **distributions**: Complete distribution history with ex-div, record, payment dates
- **performance_data**: Annualized returns (1mo, 3mo, 6mo, YTD, 1yr, 3yr, 5yr, 10yr, inception) and calendar year returns
- **sector_allocation**: Sector breakdown (for equity ETFs)
- **geographic_allocation**: Geographic breakdown (for international ETFs)

## URL Structure

**Pattern**: `https://www.globalx.ca/product/{ticker-lowercase}`

**Note**: Currency variants (.U, .F) share the same base URL:
- `USCC` → https://www.globalx.ca/product/uscc
- `USCC.U` → https://www.globalx.ca/product/uscc (same URL)
- `TSTX.F` → https://www.globalx.ca/product/tstx (same URL)

The scraper automatically removes suffixes when building URLs.

## Installation & Setup

### Prerequisites

```bash
# Python 3.8+ required
pip install requests beautifulsoup4 lxml

# Supabase database must be running
# Migration file: supabase/migrations/20251116_add_globalx_etf_data.sql
```

### Database Setup

Run the migration to create the table:

```bash
# Using Supabase CLI
supabase db push

# Or apply directly via SQL editor
psql -f supabase/migrations/20251116_add_globalx_etf_data.sql
```

## Usage

### Command-Line Interface

```bash
# Navigate to scraper directory
cd scripts/scrapers/globalx

# Make executable
chmod +x scrape_globalx_all.py
```

### List All Available ETFs

```bash
./scrape_globalx_all.py --list
```

Output shows 107 ETFs organized by 13 categories.

### Scrape Single ETF

```bash
# Scrape a specific ticker
./scrape_globalx_all.py --ticker ENCC

# Examples for different categories
./scrape_globalx_all.py --ticker CNDX   # Core equity
./scrape_globalx_all.py --ticker SHLD   # Thematic (Defence Tech)
./scrape_globalx_all.py --ticker CANL   # Enhanced Growth (1.25x)
./scrape_globalx_all.py --ticker HQU    # BetaPro (2x leveraged)
```

### Scrape by Category

```bash
# Scrape all Covered Call ETFs
./scrape_globalx_all.py --category "Covered Call"

# Scrape all Thematic ETFs
./scrape_globalx_all.py --category "Thematic"

# Scrape all Enhanced Growth ETFs
./scrape_globalx_all.py --category "Enhanced Growth"

# Scrape all BetaPro ETFs
./scrape_globalx_all.py --category "BetaPro"
```

### Scrape All ETFs

```bash
# Scrape all 107 ETFs with default 1.5 second delay
./scrape_globalx_all.py --all

# Scrape with custom delay (3 seconds between requests)
./scrape_globalx_all.py --all --delay 3

# Scrape with limit (first 10 ETFs only)
./scrape_globalx_all.py --all --limit 10
```

### Test Mode

```bash
# Test mode: scrape only 3 ETFs
./scrape_globalx_all.py --test
```

## Python API Usage

```python
from scrape_globalx_all import GlobalXScraper, scrape_single_etf, scrape_all_etfs

# Scrape single ETF
success = scrape_single_etf('ENCC')

# Scrape all ETFs
results = scrape_all_etfs(delay=1.5)

# Scrape by category
results = scrape_all_etfs(category='Covered Call', delay=2.0)

# Custom scraper instance
scraper = GlobalXScraper(
    ticker='CNCC',
    fund_name='Global X S&P/TSX 60 Covered Call ETF',
    category='Covered Call - Index'
)
data = scraper.scrape_data()
if data:
    scraper.save_to_database(data)
```

## Database Queries

### Get Latest Data for All ETFs

```sql
SELECT * FROM v_globalx_latest
ORDER BY category, ticker;
```

### Find All Covered Call ETFs with Metrics

```sql
SELECT
    ticker,
    fund_name,
    category,
    distribution_yield,
    average_coverage,
    moneyness,
    option_yield,
    dividend_yield
FROM v_globalx_latest
WHERE category LIKE '%Covered Call%'
ORDER BY distribution_yield DESC NULLS LAST;
```

### Get All Enhanced (1.25x Leveraged) ETFs

```sql
SELECT
    ticker,
    fund_name,
    category,
    leverage_ratio,
    distribution_yield,
    mer
FROM v_globalx_latest
WHERE leverage_ratio = '1.25x'
ORDER BY category, ticker;
```

### Get All BetaPro (2x Leveraged) ETFs

```sql
SELECT
    ticker,
    fund_name,
    category,
    leverage_ratio,
    mer
FROM v_globalx_latest
WHERE leverage_ratio LIKE '2x' OR leverage_ratio LIKE '-2x'
ORDER BY ticker;
```

### Top 10 Holdings for a Specific ETF

```sql
SELECT
    ticker,
    fund_name,
    holdings -> 'top_holdings' AS top_holdings
FROM v_globalx_latest
WHERE ticker = 'ENCC';
```

### Distribution History for an ETF

```sql
SELECT
    ticker,
    fund_name,
    distributions
FROM v_globalx_latest
WHERE ticker = 'CNCC';
```

### Performance Data Analysis

```sql
SELECT
    ticker,
    fund_name,
    category,
    performance_data -> 'annualized' AS annualized_returns,
    performance_data -> 'calendar_year' AS calendar_year_returns
FROM v_globalx_latest
WHERE ticker = 'USCC';
```

### ETFs by Category Count

```sql
SELECT
    category,
    COUNT(*) as etf_count,
    AVG((distribution_yield)::NUMERIC) as avg_yield
FROM v_globalx_latest
WHERE distribution_yield IS NOT NULL
GROUP BY category
ORDER BY etf_count DESC;
```

### Highest Yielding ETFs

```sql
SELECT
    ticker,
    fund_name,
    category,
    distribution_yield,
    mer,
    net_assets
FROM v_globalx_latest
WHERE distribution_yield IS NOT NULL
ORDER BY (distribution_yield)::NUMERIC DESC
LIMIT 20;
```

### Covered Call ETFs - Option vs Dividend Yield

```sql
SELECT
    ticker,
    fund_name,
    option_yield,
    dividend_yield,
    (option_yield)::NUMERIC + (dividend_yield)::NUMERIC as total_yield,
    average_coverage,
    moneyness
FROM v_globalx_latest
WHERE option_yield IS NOT NULL
ORDER BY (option_yield)::NUMERIC + (dividend_yield)::NUMERIC DESC;
```

## Data Quality Notes

### Reliable Fields (Always Present)
- Ticker
- Fund Name
- Category
- URL
- Scraped timestamp

### Usually Present
- Inception Date
- Management Fee
- MER
- Net Assets (AUM)
- Distribution Frequency

### Sometimes Missing
- Performance data (new funds < 1 year old, e.g., SHLD)
- Distribution history (limited for new funds)
- Covered call metrics (only for covered call ETFs)
- Sector allocation (depends on fund type)
- Geographic allocation (only for international/global funds)

### Special Cases

**Money Market ETFs** (CASH, CBIL):
- Gross Yield instead of distribution yield
- Holdings are bank deposit accounts, not securities

**New ETFs** (launched 2025):
- `SHLD`, `CHQQ`, `AGCC`, `TSTX`, `TLTX` have limited performance history
- May show placeholder text: "Investment fund regulations restrict performance data for funds less than 1 year old"

**BetaPro Products** (HQU, HSU, etc.):
- 2x leverage or inverse exposure
- Daily rebalancing noted
- Higher risk ratings
- Different benchmark structures

**Currency Variants**:
- `.U` = USD-denominated
- `.F` = CAD-hedged
- Base ticker = CAD

## Troubleshooting

### Common Issues

**HTTP 404 Error**:
- Verify ticker exists in GLOBALX_ETFS dictionary
- Check that URL pattern is correct: `https://www.globalx.ca/product/{ticker-lowercase}`
- Currency suffixes (.U, .F) are automatically removed

**Missing Data**:
- Some fields are ETF-specific (e.g., covered call metrics only for covered call ETFs)
- New funds may have limited performance history
- Check HTML structure hasn't changed on website

**Database Errors**:
- Ensure migration has been applied: `20251116_add_globalx_etf_data.sql`
- Check Supabase connection in environment variables
- Verify JSONB fields are properly formatted

**Rate Limiting**:
- Default delay is 1.5 seconds between requests
- Increase delay with `--delay 3` if needed
- Website is generally permissive for research purposes

### Validation

```bash
# Test with a known working ETF
./scrape_globalx_all.py --ticker ENCC

# Test mode (3 ETFs only)
./scrape_globalx_all.py --test

# Check database records
psql -c "SELECT COUNT(*), MAX(scraped_at) FROM raw_globalx_etf_data;"
```

## Technical Details

### Scraping Method
- **HTTP Library**: `requests`
- **HTML Parser**: `BeautifulSoup4` with `lxml`
- **JavaScript**: NOT required - all data is in static HTML
- **Selenium**: NOT needed

### HTML Structure
- Fund details in `<table class="wp-block-table">` elements
- Holdings in standard table format after heading
- Distributions in chronological table
- Performance data in multiple tables (annualized + calendar year)

### Data Storage
- **Table**: `raw_globalx_etf_data`
- **View**: `v_globalx_latest` (latest record per ticker)
- **JSONB Columns**: fund_details, holdings, distributions, performance_data, sector_allocation, geographic_allocation
- **Unique Constraint**: (ticker, scraped_date)

### Rate Limiting
- Default: 1.5 seconds between requests
- Configurable via `--delay` argument
- Respectful scraping practices

## Complete ETF List (Alphabetical)

### A-C
AGCC, AIGO, BCCC, BCCC.U, BCCL, BCCL.U, BKCC, BKCL, BNKL,
CANL, CASH, CBIL, CBIL.U, CHPS, CHPS.U, CHQQ, CNCC, CNCL, CNDX

### E-H
EACC, EACL, EAFL, EAFX, EAFX.U, EMCC, EMCL, EMML, EMMX, EMMX.U,
ENCC, ENCL, EQCC, EQCL, FOUR, GLCC, GLCL, GLDX, GRCC,
HBAL, HBNK, HCON, HGU, HGY, HEQL, HEQT, HGRW, HND,
HNU, HOU, HQU, HSAV, HSU, HUG, HUZ, HXCN, HXQ, HXQ.U,
HXS, HXS.U, HXT, HXT.U, HZU, HBGD, HBGD.U, HLIT, HMMJ, HMMJ.U

### L-T
LPAY, LPAY.U, MEDX, MPAY, MPAY.U, MTRX, PAYL, PAYM, PAYS,
QQQX, QQQX.U, QQCC, QQCC.U, QQCL, QQQL,
RBOT, RBOT.U, RNCC, RNCL, RSCC, RSCC.U, RSCL, RSSX, RSSX.U,
SHLD, SPAY, SPAY.U, TLTX, TLTX.F, TLTX.U, TSTX, TSTX.F, TSTX.U, TTTX

### U-Z
USCC, USCC.U, USCL, USSL, USSX, USSX.U

**Total: 107 ETFs**

## Updates & Maintenance

### Website Changes
Monitor Global X Canada website for:
- New ETF launches
- HTML structure changes
- Field name updates
- New data points

### Future ETFs
Coming soon:
- `CPCC` - Copper Producer Equity Covered Call ETF (October 2025 launch)

Add new ETFs to `GLOBALX_ETFS` dictionary in `scrape_globalx_all.py`.

## Support & Documentation

**Global X Canada Website**: https://www.globalx.ca/
**ETF List**: https://www.globalx.ca/products
**Individual ETF Pattern**: https://www.globalx.ca/product/{ticker-lowercase}

**Project Documentation**:
- Discovery file: `scripts/scrapers/globalx_canada_discovery.py`
- Scraping guide: `docs/GLOBALX_CANADA_SCRAPING_GUIDE.md`
- Migration: `supabase/migrations/20251116_add_globalx_etf_data.sql`

## License

This scraper is for research and analysis purposes. Respect Global X Canada's terms of service and robots.txt. Use appropriate rate limiting.

---

**Last Updated**: 2025-11-16
**Total ETFs**: 107 (106 active + 1 coming soon)
**Categories**: 13
**Scraping Method**: Static HTML (no JavaScript required)
