# Global X Canada ETF Scraping Guide

**Website:** https://www.globalx.ca/
**Discovery Date:** 2025-11-16
**Total ETFs:** 106 active + 1 coming soon = 107 total

## Executive Summary

Global X Canada offers a comprehensive suite of ETFs across 13 categories, from traditional index funds to innovative covered call and leveraged strategies. Their website structure is scraper-friendly with primarily static HTML content, making data extraction straightforward without requiring JavaScript execution.

---

## Complete ETF Inventory

### Summary by Category

| Category | Count | Key Features |
|----------|-------|--------------|
| Cash & Fixed Income | 19 | T-Bills, government bonds, premium yield strategies |
| Corporate Class (Tax-Efficient) | 8 | Swap-based structures for tax efficiency |
| Thematic | 16 | AI, semiconductors, healthcare, cannabis, defence |
| Enhanced Growth | 6 | 25% leveraged index exposure |
| Equity Essentials - Core | 12 | Core Canadian, US, and international indexes |
| Covered Call - Index | 9 | Index-based covered call strategies |
| Covered Call - Sector | 2 | Banks and telecommunications |
| Enhanced Covered Call | 9 | Leveraged (25%) covered call strategies |
| Commodities - Covered Call | 5 | Oil & gas, gold, silver covered calls |
| Cryptocurrency - Covered Call | 4 | Bitcoin covered call strategies |
| Precious Metals | 7 | Gold, silver, and mining equities |
| Asset Allocation | 8 | Multi-asset portfolios (conservative to aggressive) |
| BetaPro (Leveraged/Inverse) | 7 | 2x bull and inverse bear strategies |
| **Total Active** | **106** | Plus 1 coming soon (CPCC) |

---

## URL Structure

### Category Pages

```
Homepage:             https://www.globalx.ca/
All Products:         https://www.globalx.ca/products
Thematic ETFs:        https://www.globalx.ca/thematic-etfs
Enhanced Growth:      https://www.globalx.ca/enhanced-growth-etfs
Premium Yield:        https://www.globalx.ca/premium-yield-etfs
Asset Allocation:     https://www.globalx.ca/asset-allocation-etfs
Covered Call:         https://www.globalx.ca/covered-call-etfs
Equity Essentials:    https://www.globalx.ca/equity-essentials
Precious Metals:      https://www.globalx.ca/precious-metals-etfs
BetaPro:              https://www.globalx.ca/betapro
New Funds:            https://www.globalx.ca/new-funds
```

### Individual ETF Pages

**Pattern:** `https://www.globalx.ca/product/{ticker-lowercase}`

**Examples:**
- ENCC: https://www.globalx.ca/product/encc
- CNDX: https://www.globalx.ca/product/cndx
- HXS.U: https://www.globalx.ca/product/hxs (note: .U suffix removed)
- BCCC: https://www.globalx.ca/product/bccc

**Important:** Currency variants (.U, .F) share the same base URL. Remove suffixes when building URLs.

---

## HTML Structure Analysis

### Page Layout

ETF product pages follow a consistent template with these sections:

```
1. Header Navigation
2. Product Hero Section (Ticker, Name, Key Metrics)
3. NAV/Pricing Box (prominently displayed)
4. Reasons to Consider (marketing narrative)
5. Fund Details Table
6. Portfolio Investment Metrics (for covered call ETFs)
7. Holdings Section
8. Performance Data (Annualized & Calendar)
9. Distribution History (interactive table)
10. Sector/Geographic Allocation
11. Investment Objective & Risk Rating
12. Documents Section (PDFs)
13. Footer
```

### Data Fields by Section

#### 1. NAV/Pricing Box (Top of Page)

```html
Location: Prominent box near top
Fields:
  - Product Name (full name)
  - Ticker Symbol
  - NAV (Net Asset Value) - e.g., "$10.93"
  - Price (Market Price) - e.g., "$10.92"
  - Annualized Distribution Yield - e.g., "13.41%"
  - Change Indicators (daily change in price/NAV)
  - "As of [Date]" timestamp

Structure: Values in flow content, no specific CSS classes
Parent containers provide styling
```

#### 2. Fund Details Table

```html
<table class="wp-block-table">
  <tr>
    <td>CUSIP</td>
    <td>37964B101</td>
  </tr>
  <tr>
    <td>Inception Date</td>
    <td>April 11, 2011</td>
  </tr>
  <tr>
    <td>Net Assets</td>
    <td>$632,886,910</td>
  </tr>
  <!-- Additional rows -->
</table>

Common Fields:
  - CUSIP
  - Inception Date
  - Net Assets (AUM)
  - Management Fee - e.g., "0.65%"
  - MER - e.g., "0.77% (as of June 30, 2025)"
  - TER
  - Benchmark Index
  - Distribution Frequency - "Monthly", "Quarterly", etc.
  - Most Recent Distribution - "per unit" amount
  - 12-Month Trailing Yield
```

#### 3. Portfolio Investment Metrics (Covered Call ETFs Only)

```
Displayed as metric boxes with percentages
Date-stamped: "as of October 31, 2025"

Fields:
  - Average Coverage - e.g., "40.27%"
  - Average Moneyness - e.g., "2.56%"
  - Option Annualized Yield - e.g., "11.87%"
  - Dividend Yield - e.g., "4.32%"
  - Indicative Yield - e.g., "16.19%"

Note: Not present on non-covered-call ETFs
```

#### 4. Holdings Table

```html
<table>
  <thead>
    <tr>
      <th>Security</th>
      <th>Weight</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Global X Equal Weight Cdn Oil & Gas Idx ETF (NRGY)</td>
      <td>40.13%</td>
    </tr>
    <tr>
      <td>Cenovus Energy Inc</td>
      <td>4.94%</td>
    </tr>
    <!-- More holdings -->
  </tbody>
</table>

Typical Display: Top 10 holdings
Format: Two-column table (Security Name | Weight %)
```

#### 5. Performance Data

**A) Annualized Performance Table**

```
Header: "Annualized Performance" or similar
Date: "as of October 31, 2025"

Time Periods:
  1mo, 3mo, 6mo, YTD, 1yr, 3yr, 5yr, 10yr, Since Inception

Format: Table with period | return %
Values: Can be positive or negative
```

**B) Calendar Year Performance Table**

```html
<table>
  <thead>
    <tr>
      <th>Year</th>
      <th>Return</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>2024</td><td>+12.35%</td></tr>
    <tr><td>2023</td><td>-5.67%</td></tr>
    <!-- More years -->
  </tbody>
</table>

Years: 2017-2024 (depending on inception date)
Values: Annual percentage returns
Range: Can vary widely (e.g., -30.92% to +83.52%)
```

#### 6. Distribution History Table

```html
<table>
  <thead>
    <tr>
      <th>Ex-Dividend Date</th>
      <th>Record Date</th>
      <th>Payment Date</th>
      <th>Payment Amount</th>
      <th>Distribution Period</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>November 20, 2025</td>
      <td>November 20, 2025</td>
      <td>November 27, 2025</td>
      <td>$0.12000</td>
      <td>November 2025</td>
    </tr>
    <!-- More distributions -->
  </tbody>
</table>

Features:
  - Year filter dropdown (JavaScript-controlled)
  - Chronological organization (newest first)
  - Goes back to inception date
  - Monthly/quarterly/annual payments depending on fund
```

#### 7. Sector/Geographic Allocation

```
Format: Table or list showing percentage breakdowns
Categories vary by fund type:
  - Equity funds: Sector allocation (Technology, Financials, etc.)
  - Global funds: Geographic allocation (North America, Europe, Asia)
  - Thematic funds: Exposure by theme/strategy

Display: Percentage values summing to ~100%
```

#### 8. Documents Section

```html
Common Document Links:
  - Product Sheet (PDF)
  - ETF Fact Sheet (PDF)
  - Prospectus (PDF)
  - Annual Financial Reports (PDF)
  - Interim Financial Reports (PDF)
  - Fund-specific documents (e.g., "Covered Calls Monthly Performance")

Format: Standard <a> tags linking to PDF URLs
```

---

## JavaScript & Rendering

### Content Type: **Primarily Static HTML**

**Key Finding:** Core data does NOT require JavaScript execution.

### JavaScript Usage

1. **Enhancement Only** (Non-Critical):
   - Gravity Forms (newsletter subscription)
   - Algolia Search (site search)
   - Google Tag Manager (analytics)
   - Distribution history year filter
   - Performance chart visualizations

2. **Data Availability:**
   - NAV, prices, yields: **Static HTML**
   - Fund details table: **Static HTML**
   - Holdings: **Static HTML**
   - Performance tables: **Static HTML**
   - Distribution history: **Static HTML** (filter is JavaScript, but data is in HTML)

3. **Scraping Implication:**
   - **No Selenium required** for data extraction
   - Standard HTTP requests (requests library) sufficient
   - BeautifulSoup/lxml can parse all data
   - Charts may need JavaScript, but tabular data is accessible

---

## CSS Classes & Selectors

### Common CSS Classes

```css
/* Tables */
.wp-block-table

/* Typography */
.has-large-font-size
.has-small-font-size

/* Layout */
.is-layout-flex
.is-layout-grid

/* Forms */
.gform-theme

/* Color System */
:root {
  --gf-color-primary: #204ce5;
  /* Other theme variables */
}
```

### Selector Strategy

**Important:** Data values typically lack specific CSS classes. Use semantic HTML structure:

```python
# Example: Extract fund details table
fund_details = {}
for table in soup.find_all('table', class_='wp-block-table'):
    rows = table.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            fund_details[label] = value
```

**Strategy:**
1. Use heading text to identify sections
2. Find next table/content after heading
3. Parse table rows for label-value pairs
4. Extract values using regex for numbers/dates

---

## Special Considerations

### 1. Currency Variants

Many ETFs have multiple currency variants:
- **Base ticker** (CAD): `USCC`
- **USD variant**: `USCC.U`
- **CAD-hedged**: `TSTX.F`

**Handling:**
- All variants share the same product page URL (base ticker)
- Data may show multiple NAVs/prices for different variants
- Distribution amounts may be in different currencies

### 2. New ETFs (< 1 year old)

**Example:** SHLD (launched April 2025)

**Data Limitations:**
- Performance sections show placeholder text:
  - "Investment fund regulations restrict performance data for funds less than 1 year old"
- Limited distribution history
- May show "Consolidated Prior Day Volume" and "Average Daily Trading Volume"

**Scraping Impact:**
- Handle missing performance data gracefully
- Check for placeholder text in performance sections
- Distribution history may be short

### 3. Money Market ETFs

**Example:** CASH (High Interest Savings)

**Unique Fields:**
- **Gross Yield** instead of distribution yield
- Holdings are "Bank Deposit Accounts" not securities
- NAV stability emphasized
- Deposit insurance disclaimers

**Differences:**
- Holdings table shows bank accounts, not equities
- Yield calculation methodology different
- Regulatory disclosures more prominent

### 4. BetaPro Products

**Leverage/Inverse ETFs:** HQU, HSU, HNU, HND, etc.

**Unique Characteristics:**
- 2x leverage or inverse exposure
- "Daily" rebalancing noted
- Higher risk ratings
- Different benchmark structures
- May have additional risk disclosures

### 5. Covered Call ETFs

**Most Common Category** (30+ ETFs)

**Additional Data Fields:**
- Portfolio Investment Metrics section
- Average Coverage, Moneyness, Option Yield
- Monthly covered call performance reports
- Enhanced versions with 25% leverage (ENCL, BKCL, etc.)

---

## Complete Ticker Lists

### 1. Cash & Fixed Income (19 ETFs)

```
CASH    - Global X High Interest Savings ETF
CBIL    - Global X 0-3 Month T-Bill ETF
CBIL.U  - Global X 0-3 Month T-Bill ETF (USD)
HBB     - Global X Canadian Select Universe Bond Index Corporate Class ETF
PAYS    - Global X Short-Term Government Bond Premium Yield ETF
SPAY    - Global X Short-Term U.S. Treasury Premium Yield ETF
SPAY.U  - Global X Short-Term U.S. Treasury Premium Yield ETF (USD)
PAYM    - Global X Mid-Term Government Bond Premium Yield ETF
MPAY    - Global X Mid-Term U.S. Treasury Premium Yield ETF
MPAY.U  - Global X Mid-Term U.S. Treasury Premium Yield ETF (USD)
PAYL    - Global X Long-Term Government Bond Premium Yield ETF
LPAY    - Global X Long-Term U.S. Treasury Premium Yield ETF
LPAY.U  - Global X Long-Term U.S. Treasury Premium Yield ETF (USD)
TSTX    - Global X 1-3 Year U.S. Treasury Bond Index ETF (NEW Oct 2025)
TSTX.U  - Global X 1-3 Year U.S. Treasury Bond Index ETF (USD)
TSTX.F  - Global X 1-3 Year U.S. Treasury Bond Index ETF (CAD-hedged)
TLTX    - Global X 20+ Year U.S. Treasury Bond Index ETF (NEW Oct 2025)
TLTX.U  - Global X 20+ Year U.S. Treasury Bond Index ETF (USD)
TLTX.F  - Global X 20+ Year U.S. Treasury Bond Index ETF (CAD-hedged)
```

### 2. Corporate Class / Tax-Efficient (8 ETFs)

```
HXS     - Global X S&P 500 Index Corporate Class ETF
HXS.U   - Global X S&P 500 Index Corporate Class ETF (USD)
HXT     - Global X S&P/TSX 60 Index Corporate Class ETF
HXT.U   - Global X S&P/TSX 60 Index Corporate Class ETF (USD)
HXQ     - Global X Nasdaq-100 Index Corporate Class ETF
HXQ.U   - Global X NASDAQ-100 Index Corporate Class ETF (USD)
HXCN    - Global X S&P/TSX Capped Composite Index Corporate Class ETF
HSAV    - Global X Cash Maximizer Corporate Class ETF
```

### 3. Thematic (16 ETFs)

```
CHQQ    - Global X China Hang Seng TECH Index ETF (NEW Oct 2025)
MEDX    - Global X Equal Weight Global Healthcare Index ETF
SHLD    - Global X Defence Tech Index ETF
MTRX    - Global X Artificial Intelligence Infrastructure Index ETF
AIGO    - Global X Artificial Intelligence & Technology Index ETF
TTTX    - Global X Innovative Bluechip Top 10 Index ETF
CHPS    - Global X Artificial Intelligence Semiconductor Index ETF
CHPS.U  - Global X Artificial Intelligence Semiconductor Index ETF (USD)
FOUR    - Global X Industry 4.0 Index ETF
HBGD    - Global X Big Data & Hardware Index ETF
HBGD.U  - Global X Big Data & Hardware Index ETF (USD)
HLIT    - Global X Lithium Producers Index ETF
HMMJ    - Global X Marijuana Life Sciences Index ETF
HMMJ.U  - Global X Marijuana Life Sciences Index ETF (USD)
RBOT    - Global X Robotics & AI Index ETF
RBOT.U  - Global X Robotics & AI Index ETF (USD)
```

### 4. Enhanced Growth - 25% Leveraged (6 ETFs)

```
CANL    - Global X Enhanced S&P/TSX 60 Index ETF
BNKL    - Global X Enhanced Equal Weight Banks Index ETF
USSL    - Global X Enhanced S&P 500 Index ETF
QQQL    - Global X Enhanced NASDAQ-100 Index ETF
EAFL    - Global X Enhanced MSCI EAFE Index ETF
EMML    - Global X Enhanced MSCI Emerging Markets Index ETF
```

### 5. Equity Essentials - Core (12 ETFs)

```
CNDX    - Global X S&P/TSX 60 Index ETF
HBNK    - Global X Equal Weight Canadian Banks Index ETF
USSX    - Global X S&P 500 Index ETF
USSX.U  - Global X S&P 500 Index ETF (USD)
RSSX    - Global X Russell 2000 Index ETF
RSSX.U  - Global X Russell 2000 Index ETF (USD)
QQQX    - Global X Nasdaq-100 Index ETF
QQQX.U  - Global X Nasdaq-100 Index ETF (USD)
EAFX    - Global X MSCI EAFE Index ETF
EAFX.U  - Global X MSCI EAFE Index ETF (USD)
EMMX    - Global X MSCI Emerging Markets Index ETF
EMMX.U  - Global X MSCI Emerging Markets Index ETF (USD)
```

### 6. Covered Call - Index (9 ETFs)

```
CNCC    - Global X S&P/TSX 60 Covered Call ETF
USCC    - Global X S&P 500 Covered Call ETF
USCC.U  - Global X S&P 500 Covered Call ETF (USD)
QQCC    - Global X NASDAQ-100 Covered Call ETF
QQCC.U  - Global X Nasdaq-100 Covered Call ETF (USD)
RSCC    - Global X Russell 2000 Covered Call ETF
RSCC.U  - Global X Russell 2000 Covered Call ETF (USD)
EACC    - Global X MSCI EAFE Covered Call ETF
EMCC    - Global X MSCI Emerging Markets Covered Call ETF
```

### 7. Covered Call - Sector (2 ETFs)

```
BKCC    - Global X Equal Weight Canadian Bank Covered Call ETF
RNCC    - Global X Equal Weight Canadian Telecommunications Covered Call ETF
```

### 8. Enhanced Covered Call - 25% Leveraged (9 ETFs)

```
CNCL    - Global X Enhanced S&P/TSX 60 Covered Call ETF
BKCL    - Global X Enhanced Equal Weight Canadian Banks Covered Call ETF
USCL    - Global X Enhanced S&P 500 Covered Call ETF
QQCL    - Global X Enhanced NASDAQ-100 Covered Call ETF
RSCL    - Global X Enhanced Russell 2000 Covered Call ETF
EACL    - Global X Enhanced MSCI EAFE Covered Call ETF
EMCL    - Global X Enhanced MSCI Emerging Markets Covered Call ETF
RNCL    - Global X Enhanced Equal Weight Canadian Telecommunications Covered Call ETF
ENCL    - Global X Enhanced Canadian Oil And Gas Equity Covered Call ETF
```

### 9. Commodities - Covered Call (5 ETFs)

```
ENCC    - Global X Canadian Oil and Gas Equity Covered Call ETF
GLCC    - Global X Gold Producer Equity Covered Call ETF
GLCL    - Global X Enhanced Gold Producer Equity Covered Call ETF
AGCC    - Global X Silver Covered Call ETF (NEW Oct 2025)
HGY     - Global X Gold Yield ETF
```

### 10. Cryptocurrency - Covered Call (4 ETFs)

```
BCCC    - Global X Bitcoin Covered Call ETF
BCCC.U  - Global X Bitcoin Covered Call ETF (USD)
BCCL    - Global X Enhanced Bitcoin Covered Call ETF
BCCL.U  - Global X Enhanced Bitcoin Covered Call ETF (USD)
```

### 11. Precious Metals (7 ETFs)

```
HUG     - Global X Gold ETF
HUZ     - Global X Silver ETF
HGY     - Global X Gold Yield ETF
GLDX    - Global X Gold Producers Index ETF
GLCC    - Global X Gold Producer Equity Covered Call ETF
GLCL    - Global X Enhanced Gold Producer Equity Covered Call ETF
AGCC    - Global X Silver Covered Call ETF
```

### 12. Asset Allocation (8 ETFs)

```
HCON    - Global X Conservative Asset Allocation ETF
HBAL    - Global X Balanced Asset Allocation ETF
HGRW    - Global X Growth Asset Allocation ETF
HEQT    - Global X All-Equity Asset Allocation ETF
HEQL    - Global X Enhanced All-Equity Asset Allocation ETF (25% leveraged)
GRCC    - Global X Growth Asset Allocation Covered Call ETF
EQCC    - Global X All-Equity Asset Allocation Covered Call ETF
EQCL    - Global X Enhanced All-Equity Asset Allocation Covered Call ETF
```

### 13. BetaPro - Leveraged/Inverse (7 ETFs)

```
HQU     - BetaPro NASDAQ-100® 2x Daily Bull ETF
HSU     - BetaPro S&P 500® 2x Daily Bull ETF
HNU     - BetaPro Natural Gas Leveraged Daily Bull ETF
HND     - BetaPro Natural Gas Inverse Leveraged Daily Bear ETF
HGU     - BetaPro Canadian Gold Miners 2x Daily Bull ETF
HOU     - BetaPro Crude Oil Leveraged Daily Bull ETF
HZU     - BetaPro Silver 2x Daily Bull ETF
```

### 14. Coming Soon (1 ETF)

```
CPCC    - Global X Copper Producer Equity Covered Call ETF (October 2025 launch)
```

---

## Sample ETF Pages for Testing

Test scraper implementation with these representative samples:

| Ticker | Category | URL | Special Features |
|--------|----------|-----|------------------|
| ENCC | Covered Call - Commodities | https://www.globalx.ca/product/encc | Oil & gas, covered call metrics |
| CNDX | Core Equity | https://www.globalx.ca/product/cndx | TSX 60, standard structure |
| SHLD | Thematic | https://www.globalx.ca/product/shld | Defence tech, new fund (2025) |
| CASH | Money Market | https://www.globalx.ca/product/cash | High interest savings, unique fields |
| CANL | Enhanced Growth | https://www.globalx.ca/product/canl | 25% leveraged |
| HCON | Asset Allocation | https://www.globalx.ca/product/hcon | Multi-asset portfolio |
| HQU | BetaPro | https://www.globalx.ca/product/hqu | 2x leveraged, daily rebalancing |
| BCCC | Cryptocurrency | https://www.globalx.ca/product/bccc | Bitcoin covered call |
| PAYS | Premium Yield | https://www.globalx.ca/product/pays | Government bond, option premiums |
| HXCN | Corporate Class | https://www.globalx.ca/product/hxcn | Tax-efficient structure |

---

## Scraping Implementation

### Recommended Tools

```python
# Python libraries
import requests          # HTTP requests
from bs4 import BeautifulSoup  # HTML parsing
import re               # Regex for data extraction
from datetime import datetime  # Date handling
import time             # Rate limiting

# NOT NEEDED (but available if charts required):
# from selenium import webdriver
```

### Basic Scraping Pattern

```python
import requests
from bs4 import BeautifulSoup

def scrape_globalx_etf(ticker):
    # Build URL
    url = f"https://www.globalx.ca/product/{ticker.lower()}"

    # Fetch page
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract data
    data = {}

    # 1. Find fund details table
    for table in soup.find_all('table', class_='wp-block-table'):
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                data[label] = value

    # 2. Extract NAV/price from text
    text = soup.get_text()
    nav_match = re.search(r'NAV[:\s]+\$?([\d,]+\.?\d*)', text)
    if nav_match:
        data['NAV'] = float(nav_match.group(1).replace(',', ''))

    # 3. Extract holdings
    holdings = []
    for header in soup.find_all(['h2', 'h3', 'h4']):
        if 'holdings' in header.get_text().lower():
            table = header.find_next('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        holdings.append({
                            'security': cells[0].get_text(strip=True),
                            'weight': cells[1].get_text(strip=True)
                        })

    data['holdings'] = holdings

    return data
```

### Rate Limiting

```python
import time

# Be respectful - 1 second delay between requests
delay = 1.0

for ticker in ticker_list:
    data = scrape_globalx_etf(ticker)
    time.sleep(delay)
```

### Error Handling

```python
def scrape_with_error_handling(ticker):
    try:
        url = f"https://www.globalx.ca/product/{ticker.lower()}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse and extract data
        # ...

    except requests.RequestException as e:
        print(f"Error fetching {ticker}: {e}")
        return {"ticker": ticker, "error": str(e)}

    except Exception as e:
        print(f"Error parsing {ticker}: {e}")
        return {"ticker": ticker, "error": str(e)}
```

---

## Data Quality Notes

### Reliable Fields (Always Present)

- Ticker
- Product Name
- Inception Date
- Management Fee
- MER
- CUSIP

### Often Present

- NAV
- Market Price
- Net Assets (AUM)
- Distribution Frequency
- Most Recent Distribution
- 12-Month Trailing Yield
- Top 10 Holdings

### Sometimes Missing

- Performance data (new funds < 1 year)
- Calendar year returns (depends on inception date)
- Distribution history (limited for new funds)
- Portfolio metrics (covered call ETFs only)
- Sector allocation (depends on fund type)

### Field Variations

- **Yield Fields:** Different for money market vs equity vs covered call
- **Holdings:** Equities vs bank accounts vs futures
- **Benchmarks:** Index name varies by fund
- **Distributions:** Monthly, quarterly, or annual

---

## Usage Examples

### Scrape Single ETF

```bash
python globalx_canada_scraper.py --ticker ENCC --output encc_data.json
```

### Scrape All Covered Call ETFs

```bash
python globalx_canada_scraper.py --category "Covered Call - Index" --output covered_call_data.json
```

### Scrape All ETFs

```bash
python globalx_canada_scraper.py --all --output all_globalx_data.json --delay 1.5
```

### Import and Use in Python

```python
from globalx_canada_scraper import GlobalXCanadaScraper

scraper = GlobalXCanadaScraper(delay=1.0)

# Single ETF
data = scraper.scrape_etf('ENCC')

# Multiple ETFs
tickers = ['ENCC', 'CNDX', 'SHLD']
results = scraper.scrape_all(tickers)

# By category
covered_calls = scraper.scrape_category('Covered Call - Index')
```

---

## Files Created

### 1. Discovery File

**Path:** `/Users/toan/dev/high-yield-dividend-analysis/scripts/scrapers/globalx_canada_discovery.py`

**Contents:**
- Complete ticker lists (ALL_TICKERS)
- Categorized tickers (CATEGORIES dict)
- URL builder function
- Documentation of all 107 ETFs

### 2. Scraper Implementation

**Path:** `/Users/toan/dev/high-yield-dividend-analysis/scripts/scrapers/globalx_canada_scraper.py`

**Contents:**
- GlobalXCanadaScraper class
- Data extraction methods
- CLI interface
- Error handling
- JSON output

### 3. This Documentation

**Path:** `/Users/toan/dev/high-yield-dividend-analysis/docs/GLOBALX_CANADA_SCRAPING_GUIDE.md`

**Contents:**
- Complete ETF inventory
- HTML structure analysis
- Scraping strategy
- Implementation examples

---

## Key Takeaways

1. **Large ETF Suite:** 106 active ETFs + 1 coming soon across 13 categories
2. **Scraper-Friendly:** Static HTML, no JavaScript required for data extraction
3. **Consistent Structure:** Template-based pages with predictable data locations
4. **URL Pattern:** Simple pattern based on lowercase ticker
5. **Currency Variants:** .U and .F suffixes for USD and hedged versions
6. **Special Categories:** Covered call ETFs have additional metrics
7. **New Funds:** Handle limited data for recently launched ETFs
8. **Rate Limiting:** Be respectful with request frequency

---

## Next Steps

1. **Test Implementation:** Run scraper on sample ETFs
2. **Validate Data:** Compare scraped data against website
3. **Handle Edge Cases:** Test with new funds, money market, BetaPro
4. **Optimize:** Add caching, parallel requests (carefully)
5. **Monitor:** Watch for website structure changes
6. **Integrate:** Connect to your dividend analysis database

---

**Last Updated:** 2025-11-16
**Total ETFs Discovered:** 107 (106 active + 1 coming soon)
**Website:** https://www.globalx.ca/
