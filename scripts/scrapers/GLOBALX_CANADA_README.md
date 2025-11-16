# Global X Canada ETF Discovery & Scraping

Complete discovery and scraping implementation for Global X Canada ETFs.

## Quick Summary

- **Total ETFs Discovered:** 107 (106 active + 1 coming soon)
- **Website:** https://www.globalx.ca/
- **Discovery Date:** 2025-11-16
- **Scraping Method:** Static HTML (no JavaScript required)
- **Categories:** 13 distinct categories

## Files in This Directory

### 1. `globalx_canada_discovery.py`
Complete inventory of all Global X Canada ETFs with:
- Full ticker lists (107 ETFs)
- Category organization (13 categories)
- URL patterns and builders
- Documentation of website structure

### 2. `globalx_canada_scraper.py`
Production-ready web scraper with:
- GlobalXCanadaScraper class
- Complete data extraction for all ETF fields
- CLI interface for easy usage
- Error handling and rate limiting
- JSON output format

### 3. `test_globalx_scraper.py`
Test suite for validating scraper functionality:
- Tests on representative sample ETFs
- Validation of data extraction
- Output summary and reporting

## ETF Categories Discovered

| Category | Count | Examples |
|----------|-------|----------|
| Cash & Fixed Income | 19 | CASH, CBIL, PAYS, TSTX, TLTX |
| Corporate Class (Tax-Efficient) | 8 | HXS, HXT, HXQ, HXCN |
| Thematic | 16 | SHLD, AIGO, CHPS, HMMJ, MEDX |
| Enhanced Growth (25% Leveraged) | 6 | CANL, USSL, QQQL, EAFL |
| Equity Essentials - Core | 12 | CNDX, HBNK, USSX, QQQX |
| Covered Call - Index | 9 | CNCC, USCC, QQCC, EACC |
| Covered Call - Sector | 2 | BKCC, RNCC |
| Enhanced Covered Call (25% Lev) | 9 | CNCL, USCL, QQCL, ENCL |
| Commodities - Covered Call | 5 | ENCC, GLCC, AGCC, HGY |
| Cryptocurrency - Covered Call | 4 | BCCC, BCCL (CAD & USD) |
| Precious Metals | 7 | HUG, HUZ, GLDX, GLCC |
| Asset Allocation | 8 | HCON, HBAL, HGRW, HEQT |
| BetaPro (Leveraged/Inverse) | 7 | HQU, HSU, HNU, HND, HGU |
| **Total** | **107** | |

## Quick Start

### Install Dependencies

```bash
pip install requests beautifulsoup4
```

### Run Test

```bash
cd /Users/toan/dev/high-yield-dividend-analysis/scripts/scrapers
python test_globalx_scraper.py
```

### Scrape Single ETF

```bash
python globalx_canada_scraper.py --ticker ENCC --output encc_data.json
```

### Scrape All Covered Call ETFs

```bash
python globalx_canada_scraper.py --category "Covered Call - Index" --output covered_calls.json
```

### Scrape All ETFs

```bash
python globalx_canada_scraper.py --all --output all_globalx_etfs.json --delay 1.5
```

## Data Fields Extracted

### Basic Information
- Ticker symbol
- Full product name
- CUSIP
- Inception date

### Pricing
- NAV (Net Asset Value)
- Market price
- Premium/discount
- As-of date

### Metrics
- Management fee
- MER (Management Expense Ratio)
- TER (Trading Expense Ratio)
- Net assets (AUM)
- Distribution yield

### Distributions
- Distribution frequency (monthly, quarterly, etc.)
- Most recent distribution amount
- 12-month trailing yield
- Full payment history with dates

### Holdings
- Top 10 holdings
- Security names
- Portfolio weights

### Performance
- Annualized returns: 1mo, 3mo, 6mo, YTD, 1yr, 3yr, 5yr, 10yr, Since Inception
- Calendar year returns (2017-2024)

### Additional (Covered Call ETFs)
- Average coverage
- Average moneyness
- Option annualized yield
- Dividend yield
- Indicative yield

## URL Patterns

### Category Pages
```
All Products:      https://www.globalx.ca/products
Thematic:          https://www.globalx.ca/thematic-etfs
Covered Call:      https://www.globalx.ca/covered-call-etfs
Enhanced Growth:   https://www.globalx.ca/enhanced-growth-etfs
Premium Yield:     https://www.globalx.ca/premium-yield-etfs
Asset Allocation:  https://www.globalx.ca/asset-allocation-etfs
Equity Essentials: https://www.globalx.ca/equity-essentials
Precious Metals:   https://www.globalx.ca/precious-metals-etfs
BetaPro:           https://www.globalx.ca/betapro
```

### Individual ETF Pages
```
Pattern: https://www.globalx.ca/product/{ticker-lowercase}

Examples:
ENCC  → https://www.globalx.ca/product/encc
CNDX  → https://www.globalx.ca/product/cndx
HXS.U → https://www.globalx.ca/product/hxs  (note: .U removed)
```

## Technical Details

### HTML Structure
- **Content Type:** Primarily static HTML
- **JavaScript Required:** NO (for core data)
- **Table Format:** Standard HTML tables with `wp-block-table` class
- **Data Location:** Semantic HTML structure with label-value pairs

### Scraping Strategy
```python
# Use standard HTTP requests
import requests
from bs4 import BeautifulSoup

# No Selenium needed
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')
```

### Rate Limiting
- Default: 1 second delay between requests
- Customizable via `--delay` flag
- Be respectful of server resources

## Sample ETFs for Testing

Recommended test cases covering different categories:

| Ticker | Category | Special Features |
|--------|----------|------------------|
| ENCC | Covered Call - Commodities | Oil & gas, covered call metrics |
| CNDX | Core Equity | TSX 60, standard structure |
| SHLD | Thematic | Defence tech, new fund (2025) |
| CASH | Money Market | High interest savings, unique fields |
| CANL | Enhanced Growth | 25% leveraged |
| HQU | BetaPro | 2x leveraged NASDAQ |
| BCCC | Cryptocurrency | Bitcoin covered call |
| HCON | Asset Allocation | Multi-asset portfolio |

## Complete Ticker List (Alphabetical)

```
AGCC, AIGO, BCCC, BCCC.U, BCCL, BCCL.U, BKCC, BKCL, BNKL,
CANL, CASH, CBIL, CBIL.U, CHPS, CHPS.U, CHQQ, CNCC, CNCL,
CNDX, CPCC*, EACC, EACL, EAFL, EAFX, EAFX.U, EMCC, EMCL,
EMML, EMMX, EMMX.U, ENCC, ENCL, EQCC, EQCL, FOUR, GLCC,
GLCL, GLDX, GRCC, HBAL, HBB, HBGD, HBGD.U, HBNK, HCON,
HGU, HGY, HEQL, HEQT, HGRW, HLIT, HMMJ, HMMJ.U, HND,
HNU, HOU, HQU, HSAV, HSU, HUG, HUZ, HXCN, HXQ, HXQ.U,
HXS, HXS.U, HXT, HXT.U, HZU, LPAY, LPAY.U, MEDX, MPAY,
MPAY.U, MTRX, PAYL, PAYM, PAYS, QQQX, QQQX.U, QQCC, QQCC.U,
QQCL, QQQL, RBOT, RBOT.U, RNCC, RNCL, RSCC, RSCC.U, RSCL,
RSSX, RSSX.U, SHLD, SPAY, SPAY.U, TLTX, TLTX.F, TLTX.U,
TSTX, TSTX.F, TSTX.U, TTTX, USCC, USCC.U, USCL, USSL,
USSX, USSX.U
```
*CPCC = Coming soon (October 2025)

## Special Considerations

### Currency Variants
- Base ticker (CAD): USCC
- USD variant: USCC.U
- CAD-hedged: TSTX.F
- All share same product page URL (base ticker)

### New ETFs (< 1 year)
- Limited performance data
- May show placeholder text for restricted fields
- Shorter distribution history

### Money Market ETFs
- "Gross Yield" instead of distribution yield
- Holdings show bank accounts not securities
- Different regulatory disclosures

### Covered Call ETFs (30+ products)
- Additional "Portfolio Investment Metrics" section
- Coverage, moneyness, option yield data
- Monthly covered call performance reports available

### BetaPro Products
- 2x leverage or inverse exposure
- Daily rebalancing
- Higher risk ratings
- Different benchmark structures

## Python Usage Example

```python
from globalx_canada_scraper import GlobalXCanadaScraper
from globalx_canada_discovery import ALL_TICKERS, CATEGORIES

# Initialize scraper
scraper = GlobalXCanadaScraper(delay=1.0)

# Scrape single ETF
encc_data = scraper.scrape_etf('ENCC')
print(encc_data['metrics']['distribution_yield'])

# Scrape multiple ETFs
my_tickers = ['ENCC', 'CNDX', 'SHLD']
results = scraper.scrape_all(my_tickers)

# Scrape by category
thematic_etfs = scraper.scrape_category('Thematic')

# Access all tickers
print(f"Total tickers: {len(ALL_TICKERS)}")

# Browse categories
for category, tickers in CATEGORIES.items():
    print(f"{category}: {len(tickers)} ETFs")
```

## Output Format

JSON structure for each ETF:

```json
{
  "ticker": "ENCC",
  "url": "https://www.globalx.ca/product/encc",
  "scraped_at": "2025-11-16T10:30:00",
  "basic_info": {
    "name": "Global X Canadian Oil and Gas Equity Covered Call ETF",
    "ticker": "ENCC",
    "CUSIP": "37964B101",
    "Inception Date": "April 11, 2011"
  },
  "pricing": {
    "nav": 10.93,
    "price": 10.92,
    "as_of_date": "2025-11-13"
  },
  "metrics": {
    "management_fee": 0.65,
    "mer": 0.77,
    "ter": 0.25,
    "net_assets": 632886910,
    "distribution_yield": 13.41
  },
  "distributions": {
    "frequency": "Monthly",
    "most_recent": 0.12,
    "trailing_12m_yield": 13.92
  },
  "holdings": [
    {
      "security": "Global X Equal Weight Cdn Oil & Gas Idx ETF (NRGY)",
      "weight": 40.13
    }
  ],
  "performance": {
    "1mo": 2.5,
    "3mo": 5.8,
    "YTD": 12.3,
    "1yr": 15.6
  },
  "calendar_returns": {
    "2024": 12.35,
    "2023": -5.67
  },
  "distribution_history": [
    {
      "ex-dividend date": "2025-11-20",
      "payment date": "2025-11-27",
      "payment amount": 0.12
    }
  ]
}
```

## Error Handling

The scraper includes comprehensive error handling:

```python
# Network errors
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    return {"ticker": ticker, "error": str(e)}

# Missing data
value = data.get('field', None)  # Returns None if missing

# Parse errors
try:
    numeric_value = float(text)
except ValueError:
    numeric_value = None
```

## Performance Notes

- **Average scrape time:** 1-2 seconds per ETF (including delay)
- **Total scrape time (all 107 ETFs):** ~3-5 minutes with 1.5s delay
- **Data size:** ~5-10 KB per ETF (JSON)
- **Total output:** ~500 KB - 1 MB for all ETFs

## Maintenance

### Monitoring Website Changes

The scraper may need updates if Global X changes:
- Page layout or HTML structure
- CSS classes or table formats
- URL patterns
- Data field labels

### Recommended Checks
1. Run test script monthly
2. Compare output to website manually
3. Watch for new ETF launches
4. Monitor for deprecated tickers

## Documentation

See `/Users/toan/dev/high-yield-dividend-analysis/docs/GLOBALX_CANADA_SCRAPING_GUIDE.md` for:
- Detailed HTML structure analysis
- Complete field documentation
- Advanced scraping strategies
- Edge cases and special considerations

## License

Part of the high-yield-dividend-analysis project.

## Contact

For questions or issues with this scraper, please refer to the project repository.

---

**Last Updated:** 2025-11-16
**Status:** Production Ready
**Testing:** Validated on sample ETFs
