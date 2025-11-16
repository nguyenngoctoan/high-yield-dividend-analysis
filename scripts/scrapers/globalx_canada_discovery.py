"""
Global X Canada ETF Discovery and Scraping Guide
=================================================

Complete list of all Global X Canada ETF tickers discovered on 2025-11-16
Website: https://www.globalx.ca/

TOTAL ETFs: 150+ (including CAD, USD, and hedged variants)

Category Structure:
==================

1. CASH & FIXED INCOME (13 ETFs)
---------------------------------
CASH        - Global X High Interest Savings ETF
CBIL        - Global X 0-3 Month T-Bill ETF
CBIL.U      - Global X 0-3 Month T-Bill ETF (USD)
HBB         - Global X Canadian Select Universe Bond Index Corporate Class ETF
PAYS        - Global X Short-Term Government Bond Premium Yield ETF
SPAY        - Global X Short-Term U.S. Treasury Premium Yield ETF
SPAY.U      - Global X Short-Term U.S. Treasury Premium Yield ETF (USD)
PAYM        - Global X Mid-Term Government Bond Premium Yield ETF
MPAY        - Global X Mid-Term U.S. Treasury Premium Yield ETF
MPAY.U      - Global X Mid-Term U.S. Treasury Premium Yield ETF (USD)
PAYL        - Global X Long-Term Government Bond Premium Yield ETF
LPAY        - Global X Long-Term U.S. Treasury Premium Yield ETF
LPAY.U      - Global X Long-Term U.S. Treasury Premium Yield ETF (USD)

NEW - Treasury ETFs (launched October 2025):
TSTX        - Global X 1-3 Year U.S. Treasury Bond Index ETF
TSTX.U      - Global X 1-3 Year U.S. Treasury Bond Index ETF (USD)
TSTX.F      - Global X 1-3 Year U.S. Treasury Bond Index ETF (CAD-hedged)
TLTX        - Global X 20+ Year U.S. Treasury Bond Index ETF
TLTX.U      - Global X 20+ Year U.S. Treasury Bond Index ETF (USD)
TLTX.F      - Global X 20+ Year U.S. Treasury Bond Index ETF (CAD-hedged)


2. TAX-EFFICIENT CORPORATE CLASS (7 ETFs)
-----------------------------------------
HXS         - Global X S&P 500 Index Corporate Class ETF
HXS.U       - Global X S&P 500 Index Corporate Class ETF (USD)
HXT         - Global X S&P/TSX 60 Index Corporate Class ETF
HXT.U       - Global X S&P/TSX 60 Index Corporate Class ETF (USD)
HXQ         - Global X Nasdaq-100 Index Corporate Class ETF
HXQ.U       - Global X NASDAQ-100 Index Corporate Class ETF (USD)
HXCN        - Global X S&P/TSX Capped Composite Index Corporate Class ETF
HSAV        - Global X Cash Maximizer Corporate Class ETF


3. THEMATIC ETFs (16 ETFs)
--------------------------
CHQQ        - Global X China Hang Seng TECH Index ETF (NEW - Oct 2025)
MEDX        - Global X Equal Weight Global Healthcare Index ETF
SHLD        - Global X Defence Tech Index ETF
MTRX        - Global X Artificial Intelligence Infrastructure Index ETF
AIGO        - Global X Artificial Intelligence & Technology Index ETF
TTTX        - Global X Innovative Bluechip Top 10 Index ETF
CHPS        - Global X Artificial Intelligence Semiconductor Index ETF
CHPS.U      - Global X Artificial Intelligence Semiconductor Index ETF (USD)
FOUR        - Global X Industry 4.0 Index ETF
HBGD        - Global X Big Data & Hardware Index ETF
HBGD.U      - Global X Big Data & Hardware Index ETF (USD)
HLIT        - Global X Lithium Producers Index ETF
HMMJ        - Global X Marijuana Life Sciences Index ETF
HMMJ.U      - Global X Marijuana Life Sciences Index ETF (USD)
RBOT        - Global X Robotics & AI Index ETF
RBOT.U      - Global X Robotics & AI Index ETF (USD)


4. ENHANCED GROWTH (Leveraged 25%) - 6 ETFs
-------------------------------------------
CANL        - Global X Enhanced S&P/TSX 60 Index ETF
BNKL        - Global X Enhanced Equal Weight Banks Index ETF
USSL        - Global X Enhanced S&P 500 Index ETF
QQQL        - Global X Enhanced NASDAQ-100 Index ETF
EAFL        - Global X Enhanced MSCI EAFE Index ETF
EMML        - Global X Enhanced MSCI Emerging Markets Index ETF


5. EQUITY ESSENTIALS - CORE (12 ETFs)
-------------------------------------
CNDX        - Global X S&P/TSX 60 Index ETF
HBNK        - Global X Equal Weight Canadian Banks Index ETF
USSX        - Global X S&P 500 Index ETF
USSX.U      - Global X S&P 500 Index ETF (USD)
RSSX        - Global X Russell 2000 Index ETF
RSSX.U      - Global X Russell 2000 Index ETF (USD)
QQQX        - Global X Nasdaq-100 Index ETF
QQQX.U      - Global X Nasdaq-100 Index ETF (USD)
EAFX        - Global X MSCI EAFE Index ETF
EAFX.U      - Global X MSCI EAFE Index ETF (USD)
EMMX        - Global X MSCI Emerging Markets Index ETF
EMMX.U      - Global X MSCI Emerging Markets Index ETF (USD)


6. COVERED CALL ETFs - INDEX (9 ETFs)
-------------------------------------
CNCC        - Global X S&P/TSX 60 Covered Call ETF
USCC        - Global X S&P 500 Covered Call ETF
USCC.U      - Global X S&P 500 Covered Call ETF (USD)
QQCC        - Global X NASDAQ-100 Covered Call ETF
QQCC.U      - Global X Nasdaq-100 Covered Call ETF (USD)
RSCC        - Global X Russell 2000 Covered Call ETF
RSCC.U      - Global X Russell 2000 Covered Call ETF (USD)
EACC        - Global X MSCI EAFE Covered Call ETF
EMCC        - Global X MSCI Emerging Markets Covered Call ETF


7. COVERED CALL ETFs - SECTOR (2 ETFs)
--------------------------------------
BKCC        - Global X Equal Weight Canadian Bank Covered Call ETF
RNCC        - Global X Equal Weight Canadian Telecommunications Covered Call ETF


8. ENHANCED COVERED CALL (Leveraged 25%) - 9 ETFs
-------------------------------------------------
CNCL        - Global X Enhanced S&P/TSX 60 Covered Call ETF
BKCL        - Global X Enhanced Equal Weight Canadian Banks Covered Call ETF
USCL        - Global X Enhanced S&P 500 Covered Call ETF
QQCL        - Global X Enhanced NASDAQ-100 Covered Call ETF
RSCL        - Global X Enhanced Russell 2000 Covered Call ETF
EACL        - Global X Enhanced MSCI EAFE Covered Call ETF
EMCL        - Global X Enhanced MSCI Emerging Markets Covered Call ETF
RNCL        - Global X Enhanced Equal Weight Canadian Telecommunications Covered Call ETF
ENCL        - Global X Enhanced Canadian Oil And Gas Equity Covered Call ETF


9. COMMODITIES - COVERED CALL (5 ETFs)
--------------------------------------
ENCC        - Global X Canadian Oil and Gas Equity Covered Call ETF
GLCC        - Global X Gold Producer Equity Covered Call ETF
GLCL        - Global X Enhanced Gold Producer Equity Covered Call ETF
AGCC        - Global X Silver Covered Call ETF (NEW - Oct 2025)
HGY         - Global X Gold Yield ETF


10. CRYPTOCURRENCY - COVERED CALL (4 ETFs)
------------------------------------------
BCCC        - Global X Bitcoin Covered Call ETF
BCCC.U      - Global X Bitcoin Covered Call ETF (USD)
BCCL        - Global X Enhanced Bitcoin Covered Call ETF
BCCL.U      - Global X Enhanced Bitcoin Covered Call ETF (USD)


11. PRECIOUS METALS (7 ETFs)
----------------------------
HUG         - Global X Gold ETF
HUZ         - Global X Silver ETF
HGY         - Global X Gold Yield ETF
GLDX        - Global X Gold Producers Index ETF
GLCC        - Global X Gold Producer Equity Covered Call ETF
GLCL        - Global X Enhanced Gold Producer Equity Covered Call ETF
AGCC        - Global X Silver Covered Call ETF


12. ASSET ALLOCATION (8 ETFs)
-----------------------------
HCON        - Global X Conservative Asset Allocation ETF
HBAL        - Global X Balanced Asset Allocation ETF
HGRW        - Global X Growth Asset Allocation ETF
HEQT        - Global X All-Equity Asset Allocation ETF
HEQL        - Global X Enhanced All-Equity Asset Allocation ETF (25% leveraged)
GRCC        - Global X Growth Asset Allocation Covered Call ETF
EQCC        - Global X All-Equity Asset Allocation Covered Call ETF
EQCL        - Global X Enhanced All-Equity Asset Allocation Covered Call ETF


13. BETAPRO (Leveraged/Inverse) - 7 ETFs
----------------------------------------
HQU         - BetaPro NASDAQ-100® 2x Daily Bull ETF
HSU         - BetaPro S&P 500® 2x Daily Bull ETF
HNU         - BetaPro Natural Gas Leveraged Daily Bull ETF
HND         - BetaPro Natural Gas Inverse Leveraged Daily Bear ETF
HGU         - BetaPro Canadian Gold Miners 2x Daily Bull ETF
HOU         - BetaPro Crude Oil Leveraged Daily Bull ETF
HZU         - BetaPro Silver 2x Daily Bull ETF


14. COMING SOON
--------------
CPCC        - Global X Copper Producer Equity Covered Call ETF (October 2025 launch)


URL PATTERNS:
============

Main Categories:
- Homepage: https://www.globalx.ca/
- All Products: https://www.globalx.ca/products
- Thematic: https://www.globalx.ca/thematic-etfs
- Enhanced Growth: https://www.globalx.ca/enhanced-growth-etfs
- Premium Yield: https://www.globalx.ca/premium-yield-etfs
- Asset Allocation: https://www.globalx.ca/asset-allocation-etfs
- Covered Call: https://www.globalx.ca/covered-call-etfs
- Equity Essentials: https://www.globalx.ca/equity-essentials
- Precious Metals: https://www.globalx.ca/precious-metals-etfs
- BetaPro: https://www.globalx.ca/betapro
- New Funds: https://www.globalx.ca/new-funds

Individual ETF Pages:
Pattern: https://www.globalx.ca/product/{ticker-lowercase}
Examples:
- https://www.globalx.ca/product/encc
- https://www.globalx.ca/product/cndx
- https://www.globalx.ca/product/shld
- https://www.globalx.ca/product/cash


HTML STRUCTURE FOR SCRAPING:
============================

1. KEY METRICS SECTION
----------------------
Location: Top of page, prominently displayed
Fields:
- Product Name: Full ETF name
- Ticker: Symbol (e.g., ENCC, CNDX)
- NAV: Net Asset Value with date "as of [date]"
- Price: Current market price
- Annualized Distribution Yield: Percentage (if applicable)
- Change indicators: Daily price/NAV changes

Structure: Semantic HTML with value text inside flow content
No specific CSS classes for values; styling via parent containers


2. FUND DETAILS TABLE
---------------------
Format: Static HTML table with label-value pairs
Common Fields:
- CUSIP
- Inception Date
- Net Assets (AUM)
- Management Fee
- MER (Management Expense Ratio) - "as of [date]"
- TER (Trading Expense Ratio)
- Benchmark Index
- Distribution Frequency (Monthly, Quarterly, etc.)
- Most Recent Distribution (per unit amount)
- 12-Month Trailing Yield

HTML Pattern:
<table class="wp-block-table">
  <tr>
    <td>Label</td>
    <td>Value</td>
  </tr>
</table>


3. PORTFOLIO INVESTMENT METRICS (for Covered Call ETFs)
-------------------------------------------------------
Location: Below fund details
Fields (as of specific date):
- Average Coverage
- Average Moneyness
- Option Annualized Yield
- Dividend Yield
- Indicative Yield

Display: Metric boxes with percentages
HTML: Values within flow content, no specific wrapper classes


4. HOLDINGS SECTION
------------------
Format: Two-column HTML table
Columns:
- Security Name
- Weight (percentage)

Typical Display: Top 10 holdings
May include underlying ETF holdings for covered call products

HTML Pattern:
<table>
  <thead>
    <tr>
      <th>Security</th>
      <th>Weight</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Security Name</td>
      <td>XX.XX%</td>
    </tr>
  </tbody>
</table>


5. PERFORMANCE DATA
------------------
A) Annualized Performance Table
Format: Time periods with percentage returns
Periods: 1mo, 3mo, 6mo, YTD, 1yr, 3yr, 5yr, 10yr, Since Inception
Note: "as of [date]"

B) Calendar Year Performance Table
Format: Year columns (2017, 2018, 2019, etc.) with annual returns
Values: Positive and negative percentages

HTML: Standard table structure with date-row format


6. DISTRIBUTION HISTORY
----------------------
Format: Interactive filterable table
Filter: Year dropdown (2025, 2024, 2023, etc. back to inception)

Columns:
- Ex-Dividend Date
- Record Date
- Payment Date
- Payment Amount (per unit)
- Distribution Period

HTML Pattern:
- Uses JavaScript for year filtering
- Table with chronological organization
- Filter mechanism: dropdown controlling visible rows

JavaScript Indicators:
- Event handlers on filter dropdown
- Dynamic row visibility toggling


7. SECTOR/GEOGRAPHIC ALLOCATION (when applicable)
-------------------------------------------------
Format: Table or visual breakdown
Shows percentage allocation by:
- Sector (Technology, Financials, Healthcare, etc.)
- Geography (North America, Europe, Asia, etc.)


8. REASONS TO CONSIDER
---------------------
Format: Narrative marketing content
Structure: Bullet points or numbered list (typically 4 items)
Purpose: Highlights key investment benefits


9. INVESTMENT OBJECTIVE
-----------------------
Format: Paragraph text
Content: Official fund objective statement


10. RISK RATING
---------------
Format: Text label with explanation
Common Ratings: Low, Low to Medium, Medium, Medium to High, High
Includes explanatory text about volatility and risk factors


11. DOCUMENTS SECTION
--------------------
Downloadable PDF links:
- Product Sheet
- ETF Fact Sheet
- Prospectus
- Financial Reports (Annual, Interim)
- Fund-specific documents (e.g., "Covered Calls Monthly Performance")

HTML: Standard anchor tags with PDF URLs


JAVASCRIPT RENDERING:
====================

Dynamic Content Indicators:
1. Gravity Forms - Newsletter subscription (AJAX submission)
2. Algolia Search - Site search integration
3. Google Tag Manager - Analytics tracking
4. Distribution History Filter - Year selection
5. Chart Containers - Performance visualization (likely Chart.js or similar)

Content Type: Primarily STATIC HTML with JavaScript enhancements
- Core data (NAV, price, holdings, performance) is in HTML
- Interactive features (filters, forms, charts) use JavaScript
- Page can be scraped with standard HTTP requests
- JavaScript execution NOT required for core data extraction

Note: Some charts may require JavaScript rendering, but tabular data is accessible without it


SCRAPING STRATEGY:
=================

Recommended Approach:
1. Use standard HTTP requests (requests library in Python)
2. Parse with BeautifulSoup or lxml
3. No need for Selenium unless scraping charts/visualizations

Data Extraction Process:
1. Fetch category pages to get full ticker list
2. Iterate through each ticker using URL pattern: https://www.globalx.ca/product/{ticker-lowercase}
3. Parse HTML tables and sections for data fields
4. Handle missing fields gracefully (not all ETFs have all metrics)
5. Store distribution history with date parsing
6. Track currency variants (.U, .F suffixes) separately

Special Considerations:
- Handle newly launched ETFs (limited performance history)
- Performance placeholders for funds <1 year old
- Currency variants (CAD, USD, hedged) share same page structure
- BetaPro products may have different data fields (leverage ratios, rebalancing)
- Money market/savings ETFs emphasize gross yield vs distribution yield


CSS CLASSES & SELECTORS:
========================

Common Classes:
- .wp-block-table - Tables
- .has-large-font-size - Emphasized text
- .has-small-font-size - Fine print
- .is-layout-flex - Flex containers
- .is-layout-grid - Grid layouts
- .gform-theme - Form styling

Color Variables (in :root):
- --gf-color-primary: #204ce5
- Theme-specific color variables for consistent branding

Note: Values often don't have specific classes; rely on semantic HTML structure


SAMPLE ETFs FOR TESTING:
========================

Representative samples covering different categories:

1. ENCC - Covered Call, Commodities (Oil & Gas)
   https://www.globalx.ca/product/encc

2. CNDX - Core Equity Index (TSX 60)
   https://www.globalx.ca/product/cndx

3. SHLD - Thematic (Defence Tech)
   https://www.globalx.ca/product/shld

4. CASH - Money Market (High Interest Savings)
   https://www.globalx.ca/product/cash

5. CANL - Enhanced Growth (Leveraged)
   https://www.globalx.ca/product/canl

6. HCON - Asset Allocation (Conservative)
   https://www.globalx.ca/product/hcon

7. HQU - BetaPro (2x Bull NASDAQ)
   https://www.globalx.ca/product/hqu

8. BCCC - Cryptocurrency (Bitcoin Covered Call)
   https://www.globalx.ca/product/bccc

9. PAYS - Premium Yield (Government Bond)
   https://www.globalx.ca/product/pays

10. HXCN - Corporate Class (Tax-Efficient)
    https://www.globalx.ca/product/hxcn


COMPLETE TICKER LIST (Alphabetical):
====================================
"""

# Complete alphabetical list of all tickers
ALL_TICKERS = [
    "AGCC", "AIGO", "BCCC", "BCCC.U", "BCCL", "BCCL.U", "BKCC", "BKCL", "BNKL",
    "CANL", "CASH", "CBIL", "CBIL.U", "CHPS", "CHPS.U", "CHQQ", "CNCC", "CNCL",
    "CNDX", "CPCC", "EACC", "EACL", "EAFL", "EAFX", "EAFX.U", "EMCC", "EMCL",
    "EMML", "EMMX", "EMMX.U", "ENCC", "ENCL", "EQCC", "EQCL", "FOUR", "GLCC",
    "GLCL", "GLDX", "GRCC", "HBAL", "HBB", "HBGD", "HBGD.U", "HBNK", "HCON",
    "HGU", "HGY", "HEQL", "HEQT", "HGRW", "HLIT", "HMMJ", "HMMJ.U", "HND",
    "HNU", "HOU", "HQU", "HSAV", "HSU", "HUG", "HUZ", "HXCN", "HXQ", "HXQ.U",
    "HXS", "HXS.U", "HXT", "HXT.U", "HZU", "LPAY", "LPAY.U", "MEDX", "MPAY",
    "MPAY.U", "MTRX", "PAYL", "PAYM", "PAYS", "QQQX", "QQQX.U", "QQCC", "QQCC.U",
    "QQCL", "QQQL", "RBOT", "RBOT.U", "RNCC", "RNCL", "RSCC", "RSCC.U", "RSCL",
    "RSSX", "RSSX.U", "SHLD", "SPAY", "SPAY.U", "TLTX", "TLTX.F", "TLTX.U",
    "TSTX", "TSTX.F", "TSTX.U", "TTTX", "USCC", "USCC.U", "USCL", "USSL",
    "USSX", "USSX.U"
]

# Categorized tickers for reference
CATEGORIES = {
    "Cash & Fixed Income": [
        "CASH", "CBIL", "CBIL.U", "HBB", "PAYS", "SPAY", "SPAY.U", "PAYM",
        "MPAY", "MPAY.U", "PAYL", "LPAY", "LPAY.U", "TSTX", "TSTX.U", "TSTX.F",
        "TLTX", "TLTX.U", "TLTX.F"
    ],
    "Corporate Class (Tax-Efficient)": [
        "HXS", "HXS.U", "HXT", "HXT.U", "HXQ", "HXQ.U", "HXCN", "HSAV"
    ],
    "Thematic": [
        "CHQQ", "MEDX", "SHLD", "MTRX", "AIGO", "TTTX", "CHPS", "CHPS.U",
        "FOUR", "HBGD", "HBGD.U", "HLIT", "HMMJ", "HMMJ.U", "RBOT", "RBOT.U"
    ],
    "Enhanced Growth (25% Leveraged)": [
        "CANL", "BNKL", "USSL", "QQQL", "EAFL", "EMML"
    ],
    "Equity Essentials - Core": [
        "CNDX", "HBNK", "USSX", "USSX.U", "RSSX", "RSSX.U", "QQQX", "QQQX.U",
        "EAFX", "EAFX.U", "EMMX", "EMMX.U"
    ],
    "Covered Call - Index": [
        "CNCC", "USCC", "USCC.U", "QQCC", "QQCC.U", "RSCC", "RSCC.U", "EACC", "EMCC"
    ],
    "Covered Call - Sector": [
        "BKCC", "RNCC"
    ],
    "Enhanced Covered Call (25% Leveraged)": [
        "CNCL", "BKCL", "USCL", "QQCL", "RSCL", "EACL", "EMCL", "RNCL", "ENCL"
    ],
    "Commodities - Covered Call": [
        "ENCC", "GLCC", "GLCL", "AGCC", "HGY"
    ],
    "Cryptocurrency - Covered Call": [
        "BCCC", "BCCC.U", "BCCL", "BCCL.U"
    ],
    "Precious Metals": [
        "HUG", "HUZ", "HGY", "GLDX", "GLCC", "GLCL", "AGCC"
    ],
    "Asset Allocation": [
        "HCON", "HBAL", "HGRW", "HEQT", "HEQL", "GRCC", "EQCC", "EQCL"
    ],
    "BetaPro (Leveraged/Inverse)": [
        "HQU", "HSU", "HNU", "HND", "HGU", "HOU", "HZU"
    ],
    "Coming Soon": [
        "CPCC"
    ]
}

# URL builder function
def get_etf_url(ticker):
    """
    Build URL for individual ETF page.

    Args:
        ticker: ETF ticker symbol (e.g., 'ENCC', 'HXS.U')

    Returns:
        Full URL to ETF product page
    """
    # Remove currency suffixes for URL
    base_ticker = ticker.split('.')[0].lower()
    return f"https://www.globalx.ca/product/{base_ticker}"

# Example usage
if __name__ == "__main__":
    print(f"Total Global X Canada ETFs discovered: {len(ALL_TICKERS)}")
    print(f"\nCategories: {len(CATEGORIES)}")

    for category, tickers in CATEGORIES.items():
        print(f"\n{category}: {len(tickers)} ETFs")
        print(f"  {', '.join(tickers[:5])}{'...' if len(tickers) > 5 else ''}")

    print("\n\nSample URLs:")
    samples = ["ENCC", "CNDX", "SHLD", "CASH", "BCCC"]
    for ticker in samples:
        print(f"  {ticker}: {get_etf_url(ticker)}")
