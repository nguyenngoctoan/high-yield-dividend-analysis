# GraniteShares ETF Scraping Guide

## Overview
This document provides a comprehensive guide for scraping GraniteShares ETF data, including all ticker symbols, HTML structure analysis, and implementation recommendations.

## Complete ETF List

### Total: 59 ETFs across 5 categories

### 1. YieldBOOST (16 ETFs)
Income-generating ETFs using put spread strategies on leveraged ETFs
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
2x long/short leveraged and 1.25x long exposure to individual stocks
- AAPB - GraniteShares 2x Long AAPL Daily ETF (Apple)
- AMDL - GraniteShares 2x Long AMD Daily ETF
- AMZZ - GraniteShares 2x Long AMZN Daily ETF (Amazon)
- AVGU - GraniteShares 2x Long AVGO Daily ETF (Broadcom)
- BABX - GraniteShares 2x Long BABA Daily ETF (Alibaba)
- BULX - GraniteShares 2x Long BULL Daily ETF (Webull)
- CONI - GraniteShares 2x Short COIN Daily ETF (Coinbase inverse)
- CONL - GraniteShares 2x Long COIN Daily ETF (Coinbase)
- CRWL - GraniteShares 2x Long CRWD Daily ETF (CrowdStrike)
- DLLL - GraniteShares 2x Long DELL Daily ETF
- ETRL - GraniteShares 2x Long ETOR Daily ETF (eToro)
- FBL - GraniteShares 2x Long META Daily ETF
- INTW - GraniteShares 2x Long INTC Daily ETF (Intel)
- IONL - GraniteShares 2x Long IONQ Daily ETF
- ISUL - GraniteShares 2x Long ISRG Daily ETF (Intuitive Surgical)
- LCDL - GraniteShares 2x Long LCID Daily ETF (Lucid)
- MRAL - GraniteShares 2x Long MARA Daily ETF
- MSDD - GraniteShares 2x Short MSTR Daily ETF (MicroStrategy inverse)
- MSFL - GraniteShares 2x Long MSFT Daily ETF (Microsoft)
- MSTP - GraniteShares 2x Long MSTR Daily ETF (MicroStrategy)
- MULL - GraniteShares 2x Long MU Daily ETF (Micron)
- MVLL - GraniteShares 2x Long MRVL Daily ETF (Marvell)
- NBIL - GraniteShares 2x Long NBIS Daily ETF (Nebius)
- NOWL - GraniteShares 2x Long NOW Daily ETF (ServiceNow)
- NVD - GraniteShares 2x Short NVDA Daily ETF (NVIDIA inverse)
- NVDL - GraniteShares 2x Long NVDA Daily ETF (NVIDIA)
- PDDL - GraniteShares 2x Long PDD Daily ETF
- PTIR - GraniteShares 2x Long PLTR Daily ETF (Palantir)
- QCML - GraniteShares 2x Long QCOM Daily ETF (Qualcomm)
- RDTL - GraniteShares 2x Long RDDT Daily ETF (Reddit)
- RVNL - GraniteShares 2x Long RIVN Daily ETF (Rivian)
- SMCL - GraniteShares 2x Long SMCI Daily ETF (Super Micro)
- TSDD - GraniteShares 2x Short TSLA Daily ETF (Tesla inverse)
- TSL - GraniteShares 1.25x Long TSLA Daily ETF (Tesla)
- TSLR - GraniteShares 2x Long TSLA Daily ETF (Tesla)
- TSMU - GraniteShares 2x Long TSM Daily ETF (Taiwan Semi)
- UBRL - GraniteShares 2x Long Uber Daily ETF
- VRTL - GraniteShares 2x Long VRT Daily ETF (Vertiv)

### 3. Commodities (2 ETFs)
- COMB - GraniteShares Bloomberg Commodity Broad Strategy No K-1 ETF
- PLTM - GraniteShares Platinum Trust (physical platinum)

### 4. Gold (1 ETF)
- BAR - GraniteShares Gold Trust (physical gold)

### 5. Equity (1 ETF)
- DRUP - GraniteShares Nasdaq Select Disruptors ETF

### 6. Income (1 ETF)
- HIPS - GraniteShares HIPS US High Income ETF

## URL Patterns

### Main ETF Listing Page
```
https://graniteshares.com/institutional/us/en-us/etfs/
```

### Individual ETF Pages
```
https://graniteshares.com/institutional/us/en-us/etfs/{ticker}/
```
Example: `https://graniteshares.com/institutional/us/en-us/etfs/tqqy/`

Note: Use lowercase ticker in URL

## HTML Structure Analysis

### Main ETF Listing Page Structure

#### ETF Table Container
```html
<div class="etf-table">
  <!-- Headers -->
  <span class="etf-table-cell etf-table-header etf-table-header--ticker">Ticker</span>
  <span class="etf-table-cell etf-table-header etf-table-header--name">Name / Description</span>
  <span class="etf-table-cell etf-table-header etf-table-header--tag"></span>
  <span class="etf-table-cell etf-table-header etf-table-header--nav">Nav</span>
  <span class="etf-table-cell etf-table-header etf-table-header--change">Today's change</span>
  <span class="etf-table-cell etf-table-header etf-table-header--aum">AUM</span>

  <!-- ETF Rows -->
  <span data-id="1084"
        data-type="leveraged"
        data-underlying="Tesla Inc"
        data-leverage="1.25"
        class="etf-table-cell etf-all etf-table-cell--ticker">
    <a href="/institutional/us/en-us/etfs/tsl/">
      <span class="etf-table-cell--ticker__symbol">TSL</span>
    </a>
  </span>

  <span data-id="1084" class="etf-table-cell etf-all etf-table-cell--name">
    <span class="etf-table-cell--name-title">GraniteShares 1.25x Long TSLA Daily ETF</span>
    <span class="etf-table-cell--name-description">1.25x long exposure to Tesla Inc (TSLA)</span>
  </span>

  <span class="etf-table-cell etf-all etf-table-cell--nav">$ 16.38</span>
  <span class="etf-table-cell etf-all etf-table-cell--change">
    <span class="pChange">8.31%</span>
  </span>
  <span class="etf-table-cell etf-all etf-table-cell--aum">
    <span class="pAum">$ 13,101,923</span>
  </span>
</div>
```

#### Key CSS Classes for Main Listing
- `etf-table` - Main table container
- `etf-table-cell--ticker` - Ticker cell (contains `data-id`, `data-type`, `data-underlying`, `data-leverage`)
- `etf-table-cell--ticker__symbol` - Actual ticker symbol
- `etf-table-cell--name-title` - Full ETF name
- `etf-table-cell--name-description` - Short description
- `etf-table-cell--nav` - NAV price (look for span.pNav)
- `etf-table-cell--change` - Performance change (look for span.pChange)
- `etf-table-cell--aum` - Assets under management (look for span.pAum)

#### Data Attributes
- `data-id` - Unique ETF ID (use to match cells across columns)
- `data-type` - Category: leveraged, yieldboost, commodities, gold, equity, income
- `data-underlying` - Underlying security name
- `data-leverage` - Leverage multiplier (2, -2, 1.25, 3, 0)

### Individual ETF Page Structure

#### Main Content Container
```html
<div class="etf-chart-details_content">
  <!-- Various data sections -->
</div>
```

#### Key Data Sections

##### 1. Distribution Calendar Table
```html
<div class="etf-chart-details_content_distribution-calendar-table">
  <span class="Mono2">Ex Date</span>
  <span class="Mono2">Record Date</span>
  <span class="Mono2">Payment Date</span>
  <span class="Mono2">Distribution</span>
  <!-- Data rows follow -->
</div>
```

CSS Class: `etf-chart-details_content_distribution-calendar-table`

##### 2. Performance Table
```html
<div class="etf-chart-details_content_performance-table">
  <span class="Mono2">All Data on Total Return Basis</span>
  <span class="Mono2">1 Month</span>
  <span class="Mono2">3 Months</span>
  <span class="Mono2">YTD</span>
  <span class="Mono2">1 Year</span>
  <span class="Mono2">3 Years</span>
  <!-- Performance data rows -->
</div>
```

CSS Class: `etf-chart-details_content_performance-table`

##### 3. Fund Holdings Table
```html
<div class="etf-chart-details_content_fund-allocation-table">
  <span class="Mono2">Underlying</span>
  <span class="Mono2 text-right">Share/Par</span>
  <span class="Mono2 text-right">Value</span>
  <span class="Mono2 text-right">Allocation</span>

  <!-- Holdings data -->
  <span class="security-name">US Dollars</span>
  <span class="text-right">8,062,082</span>
  <span class="text-right">$ 8,062,081.91315</span>
  <span class="text-right">55.69%</span>
</div>
```

CSS Class: `etf-chart-details_content_fund-allocation-table`

##### 4. Premium/Discount Data
```html
<div class="etf-chart-details_content_fund-allocation-table">
  <span>NAV</span><span class="pNav">$ 17.4041</span>
  <span>Price</span><span class="pClose">$ 17.3934</span>
  <span>Premium / (Discount)</span><span class="pDisc">(0.06%)</span>
</div>
```

##### 5. Documents Table
```html
<div class="etf-chart-details_content_documents-table">
  <span class="Mono2">Document Name</span>
  <!-- Document links -->
</div>
```

CSS Class: `etf-chart-details_content_documents-table`

#### Important CSS Classes for Individual ETF Pages
- `etf-chart-details_content` - Main content wrapper
- `etf-chart-details_content_distribution-calendar-table` - Distribution history
- `etf-chart-details_content_performance-table` - Performance metrics
- `etf-chart-details_content_fund-allocation-table` - Holdings and allocation
- `etf-chart-details_content_documents-table` - Document downloads
- `pNav` - NAV value
- `pClose` - Closing price
- `pDisc` - Premium/discount percentage
- `pDate` - As-of date for data
- `pAum` - AUM value

## Data Fields Available

### From Main Listing Page
1. Ticker symbol
2. Full ETF name
3. Description
4. ETF type/category
5. Underlying security
6. Leverage ratio
7. Current NAV
8. Daily change percentage
9. Total AUM

### From Individual ETF Pages
1. **Basic Info**
   - Ticker
   - Full name
   - Inception date
   - Expense ratio
   - CUSIP/ISIN

2. **Pricing**
   - Current NAV (class: `pNav`)
   - Closing price (class: `pClose`)
   - Premium/Discount (class: `pDisc`)

3. **Performance**
   - 1 Month, 3 Months, YTD, 1 Year, 3 Years returns
   - Available in both Month-End and Quarter-End views

4. **Distributions**
   - Ex Date
   - Record Date
   - Payment Date
   - Distribution amount
   - Distribution frequency (weekly for YieldBOOST)

5. **Holdings**
   - Security name
   - Shares/Par value
   - Dollar value
   - Allocation percentage
   - As-of date (class: `pDate`)

6. **Documents**
   - Factsheets
   - Prospectus
   - SAI (Statement of Additional Information)
   - Annual/Semi-annual reports
   - Holdings files (XLS format)

## Scraping Recommendations

### 1. Technology Stack
- **Selenium Required**: The site uses heavy JavaScript rendering
- **BeautifulSoup**: For HTML parsing after page load
- **Recommended Wait Time**: 5 seconds after page load for JS to complete

### 2. Scraping Strategy

#### For Main ETF List:
```python
from selenium import webdriver
from bs4 import BeautifulSoup
import time

# Load page
driver.get('https://graniteshares.com/institutional/us/en-us/etfs/')
time.sleep(5)

# Parse with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Find all ticker cells
ticker_cells = soup.find_all('span', class_='etf-table-cell--ticker')

for ticker_cell in ticker_cells:
    data_id = ticker_cell.get('data-id')
    ticker = ticker_cell.find('span', class_='etf-table-cell--ticker__symbol').text
    etf_type = ticker_cell.get('data-type')
    underlying = ticker_cell.get('data-underlying')
    leverage = ticker_cell.get('data-leverage')

    # Find matching cells by data-id
    name_cell = soup.find('span', class_='etf-table-cell--name', attrs={'data-id': data_id})
    nav_cell = soup.find('span', class_='etf-table-cell--nav', attrs={'data-id': data_id})
    aum_cell = soup.find('span', class_='etf-table-cell--aum', attrs={'data-id': data_id})
```

#### For Individual ETF Data:
```python
# Visit individual ETF page
url = f'https://graniteshares.com/institutional/us/en-us/etfs/{ticker.lower()}/'
driver.get(url)
time.sleep(5)

soup = BeautifulSoup(driver.page_source, 'html.parser')

# Extract NAV
nav = soup.find('span', class_='pNav').text

# Extract distributions
dist_table = soup.find('div', class_='etf-chart-details_content_distribution-calendar-table')

# Extract holdings
holdings_table = soup.find('div', class_='etf-chart-details_content_fund-allocation-table')

# Extract performance
perf_table = soup.find('div', class_='etf-chart-details_content_performance-table')
```

### 3. Special Considerations

#### JavaScript Rendering
- All data is loaded via JavaScript
- Must use Selenium or similar headless browser
- Cannot rely on simple HTTP requests

#### Dynamic Content
- Some data may load on scroll or interaction
- Use explicit waits for specific elements
- Consider using Selenium's `WebDriverWait` with `expected_conditions`

#### Rate Limiting
- No obvious rate limiting detected
- Still recommend 2-3 second delays between requests
- Use polite scraping practices

#### Data Updates
- NAV and pricing updated daily
- Holdings typically updated weekly/monthly (check `pDate` class)
- Distributions added as declared

#### Mobile vs Desktop
- Some elements have `d-mobile` class for mobile view
- Desktop view recommended for scraping (more complete data)

### 4. Chrome Headless Configuration
```python
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')

driver = webdriver.Chrome(options=chrome_options)
```

### 5. Error Handling
- Check for 404 errors (some ETFs may be delisted)
- Verify data elements exist before extracting
- Handle cases where tables/sections may be empty
- Log missing data for review

### 6. Data Validation
- Verify NAV is positive number
- Check that allocations sum to ~100% (may vary slightly)
- Validate distribution dates are in expected format
- Confirm ticker symbols match expected pattern (2-5 uppercase letters)

## Sample Implementation

See the generated JSON files for reference:
- `/Users/toan/dev/high-yield-dividend-analysis/graniteshares_etfs_complete.json` - Complete ETF list with metadata
- `/Users/toan/dev/high-yield-dividend-analysis/graniteshares_structure.json` - Detailed HTML structure

## Notes

1. **Leverage Detection**:
   - 2x long: `data-leverage="2"`
   - 2x short: `data-leverage="-2"`
   - 1.25x long: `data-leverage="1.25"`
   - 3x long: `data-leverage="3"` (for TQQY, YSPY)
   - Unleveraged: `data-leverage="0"`

2. **Category Mapping**:
   - YieldBOOST: Weekly income via options on leveraged ETFs
   - Leveraged: 2x/1.25x exposure to individual stocks
   - Commodities: Broad commodity exposure
   - Gold: Physical gold-backed
   - Equity: Stock market disruptors
   - Income: High-income pass-through securities

3. **Distribution Frequency**:
   - YieldBOOST ETFs: Weekly distributions
   - Other ETFs: Varies by fund type

4. **Holdings Downloads**:
   - Available as XLS files
   - URL pattern: `/media/{hash}/{ticker}_holdings_file.xls`
   - Updated as of date shown in `pDate` class

## Last Updated
2025-11-16
