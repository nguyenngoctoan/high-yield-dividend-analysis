#!/usr/bin/env python3
"""
YieldMax ETF Scraper (All Funds)

Scrapes comprehensive data from all YieldMax ETF pages including:
- Performance (month-end and quarter-end)
- Fund overview
- Investment objective
- Fund details
- Distributions
- Top 10 holdings

All data stored as JSON in raw_etfs_yieldmax table.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
from bs4 import BeautifulSoup
import argparse

# Add paths to import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from supabase_helpers import supabase_upsert, get_supabase_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# YieldMax ETF Configuration - Complete List (57 ETFs)
# Last updated: 2025-11-16
YIELDMAX_ETFS = {
    'ABNY': {'name': 'YieldMax ABNB Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/abny/'},
    'AIYY': {'name': 'YieldMax AI Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/aiyy/'},
    'AMDY': {'name': 'YieldMax AMD Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/amdy/'},
    'AMZY': {'name': 'YieldMax AMZN Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/amzy/'},
    'APLY': {'name': 'YieldMax AAPL Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/aply/'},
    'BABO': {'name': 'YieldMax BABA Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/babo/'},
    'BIGY': {'name': 'YieldMax Big Tech Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/bigy/'},
    'BRKC': {'name': 'YieldMax BRK.B Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/brkc/'},
    'CHPY': {'name': 'YieldMax CHP Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/chpy/'},
    'CONY': {'name': 'YieldMax COIN Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/cony/'},
    'CRCO': {'name': 'YieldMax CRM Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/crco/'},
    'CRSH': {'name': 'YieldMax CRSP Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/crsh/'},
    'CVNY': {'name': 'YieldMax CVS Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/cvny/'},
    'DIPS': {'name': 'YieldMax Buy the Dip Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/dips/'},
    'DISO': {'name': 'YieldMax DIS Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/diso/'},
    'DRAY': {'name': 'YieldMax DoorDash Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/dray/'},
    'FBY': {'name': 'YieldMax META Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/fby/'},
    'FEAT': {'name': 'YieldMax Featured ETF Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/feat/'},
    'FIAT': {'name': 'YieldMax F Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/fiat/'},
    'FIVY': {'name': 'YieldMax FIVE Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/fivy/'},
    'GDXY': {'name': 'YieldMax GDX Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/gdxy/'},
    'GMEY': {'name': 'YieldMax GME Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/gmey/'},
    'GOOY': {'name': 'YieldMax GOOGL Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/gooy/'},
    'GPTY': {'name': 'YieldMax GPT Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/gpty/'},
    'HIYY': {'name': 'YieldMax High Yield Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/hiyy/'},
    'HOOY': {'name': 'YieldMax HD Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/hooy/'},
    'JPMO': {'name': 'YieldMax JPM Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/jpmo/'},
    'LFGY': {'name': 'YieldMax LFG Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/lfgy/'},
    'MARO': {'name': 'YieldMax MAR Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/maro/'},
    'MRNY': {'name': 'YieldMax MRNA Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/mrny/'},
    'MSFO': {'name': 'YieldMax MSFT Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/msfo/'},
    'MSTY': {'name': 'YieldMax MSTR Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/msty/'},
    'NFLY': {'name': 'YieldMax NFLX Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/nfly/'},
    'NVDY': {'name': 'YieldMax NVDA Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/nvdy/'},
    'OARK': {'name': 'YieldMax ARKK Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/oark/'},
    'PLTY': {'name': 'YieldMax PLTR Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/plty/'},
    'PYPY': {'name': 'YieldMax PY Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/pypy/'},
    'QDTY': {'name': 'YieldMax QQQ 0DTE Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/qdty/'},
    'RBLY': {'name': 'YieldMax RBLX Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/rbly/'},
    'RDTY': {'name': 'YieldMax RDDT Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/rdty/'},
    'RDYY': {'name': 'YieldMax RDY Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/rdyy/'},
    'RNTY': {'name': 'YieldMax RENT Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/rnty/'},
    'SDTY': {'name': 'YieldMax SPY 0DTE Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/sdty/'},
    'SLTY': {'name': 'YieldMax SLT Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/slty/'},
    'SMCY': {'name': 'YieldMax SMC Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/smcy/'},
    'SNOY': {'name': 'YieldMax SNO Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/snoy/'},
    'SOXY': {'name': 'YieldMax SOX Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/soxy/'},
    'TSLY': {'name': 'YieldMax TSLA Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/tsly/'},
    'TSMY': {'name': 'YieldMax TSM Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/tsmy/'},
    'ULTY': {'name': 'YieldMax Ultra Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/ulty/'},
    'WNTR': {'name': 'YieldMax Barbell Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/wntr/'},
    'XOMO': {'name': 'YieldMax XOM Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/xomo/'},
    'XYZY': {'name': 'YieldMax XYZ Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/xyzy/'},
    'YBIT': {'name': 'YieldMax BTC Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/ybit/'},
    'YMAG': {'name': 'YieldMax Magnificent 7 Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/ymag/'},
    'YMAX': {'name': 'YieldMax Universe Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/ymax/'},
    'YQQQ': {'name': 'YieldMax QQQ Option Income Strategy ETF', 'url': 'https://yieldmaxetfs.com/our-etfs/yqqq/'}
}


class YieldMaxScraper:
    """Scraper for YieldMax ETF data"""

    def __init__(self, ticker: str, fund_name: str, url: str):
        """
        Initialize the scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            url: YieldMax ETF page URL
        """
        self.ticker = ticker
        self.fund_name = fund_name
        self.url = url

    def scrape_data(self) -> Optional[Dict[str, Any]]:
        """
        Scrape all data from the ETF page using Selenium

        Returns:
            Dictionary containing all scraped data or None if error
        """
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        # Set binary location (for Docker container with Chromium)
        chrome_binary = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        if os.path.exists(chrome_binary):
            chrome_options.binary_location = chrome_binary

        driver = None
        try:
            logger.info(f"🌐 Starting browser for {self.ticker}...")

            # Use ChromeDriver path from environment if available
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
            if os.path.exists(chromedriver_path):
                from selenium.webdriver.chrome.service import Service
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)

            logger.info(f"📊 Loading page: {self.url}")
            driver.get(self.url)

            # Wait for page to load
            logger.info("⏳ Waiting for page to load...")
            time.sleep(5)  # Allow time for dynamic content

            # Get page source
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract all data sections
            data = {
                'ticker': self.ticker,
                'fund_name': self.fund_name,
                'url': self.url,
                'scraped_at': datetime.now().isoformat(),
                'performance_month_end': self._extract_performance(soup, 'month-end'),
                'performance_quarter_end': self._extract_performance(soup, 'quarter-end'),
                'fund_overview': self._extract_fund_overview(soup),
                'investment_objective': self._extract_investment_objective(soup),
                'fund_details': self._extract_fund_details(soup),
                'distributions': self._extract_distributions(soup),
                'top_10_holdings': self._extract_top_holdings(soup)
            }

            logger.info("✅ Data extraction complete")
            return data

        except Exception as e:
            logger.error(f"❌ Error scraping {self.ticker}: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            if driver:
                driver.quit()
                logger.info("🔚 Browser closed")

    def _extract_performance(self, soup: BeautifulSoup, period_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract performance data (month-end or quarter-end)

        Args:
            soup: BeautifulSoup object
            period_type: 'month-end' or 'quarter-end'

        Returns:
            Dictionary with performance metrics
        """
        try:
            # Look for performance table - adjust selectors based on actual HTML
            tables = soup.find_all('table')

            for table in tables:
                # Check if this is the performance table
                headers = table.find_all('th')
                if not headers:
                    continue

                header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])

                # Look for performance-related keywords
                if any(keyword in header_text for keyword in ['performance', 'return', 'ytd', 'month', 'quarter']):
                    performance_data = {}

                    # Extract headers
                    header_cols = [h.get_text(strip=True) for h in headers]

                    # Extract rows
                    rows = table.find_all('tr')[1:]  # Skip header row

                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            row_data = {}
                            row_label = cells[0].get_text(strip=True)

                            for i, cell in enumerate(cells[1:], 1):
                                if i < len(header_cols):
                                    value = cell.get_text(strip=True)
                                    row_data[header_cols[i]] = value

                            performance_data[row_label] = row_data

                    logger.info(f"✅ Extracted {period_type} performance: {len(performance_data)} metrics")
                    return performance_data

            logger.warning(f"⚠️  No performance table found for {period_type}")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting {period_type} performance: {e}")
            return None

    def _extract_fund_overview(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract fund overview information"""
        try:
            overview_data = {}

            # Look for fund overview section - adjust selectors based on actual HTML
            # Common patterns: divs with class containing 'overview', 'fund-info', etc.
            overview_sections = soup.find_all(['div', 'section'],
                                             class_=lambda c: c and any(x in c.lower() for x in ['overview', 'fund-info', 'details']))

            for section in overview_sections:
                # Look for label-value pairs
                labels = section.find_all(['dt', 'div', 'span'],
                                         class_=lambda c: c and 'label' in c.lower())

                for label in labels:
                    label_text = label.get_text(strip=True)
                    # Find corresponding value (next sibling or parent's next element)
                    value_elem = label.find_next_sibling(['dd', 'div', 'span'])
                    if value_elem:
                        value_text = value_elem.get_text(strip=True)
                        overview_data[label_text] = value_text

            # Also check for tables with overview info
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            overview_data[key] = value

            if overview_data:
                logger.info(f"✅ Extracted fund overview: {len(overview_data)} fields")
                return overview_data

            logger.warning("⚠️  No fund overview found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting fund overview: {e}")
            return None

    def _extract_investment_objective(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract investment objective text"""
        try:
            # Look for investment objective section
            objective_keywords = ['investment objective', 'objective', 'strategy', 'about the fund']

            for keyword in objective_keywords:
                # Search for headers containing the keyword
                headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'b'])

                for header in headers:
                    if keyword in header.get_text(strip=True).lower():
                        # Get the next paragraph or div
                        next_elem = header.find_next(['p', 'div'])
                        if next_elem:
                            objective_text = next_elem.get_text(strip=True)
                            if len(objective_text) > 50:  # Ensure it's substantial text
                                logger.info(f"✅ Extracted investment objective ({len(objective_text)} chars)")
                                return objective_text

            logger.warning("⚠️  No investment objective found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting investment objective: {e}")
            return None

    def _extract_fund_details(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract fund details as key-value pairs"""
        try:
            fund_details = {}

            # Look for fund details table or list
            detail_keywords = ['fund details', 'fund information', 'details', 'fund facts']

            # Search in headings
            for keyword in detail_keywords:
                headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5'])

                for header in headers:
                    if keyword in header.get_text(strip=True).lower():
                        # Find next table or list
                        next_table = header.find_next('table')
                        if next_table:
                            rows = next_table.find_all('tr')
                            for row in rows:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    key = cells[0].get_text(strip=True)
                                    value = cells[1].get_text(strip=True)
                                    if key and value:
                                        fund_details[key] = value

            # Also look for dl/dt/dd structure
            definition_lists = soup.find_all('dl')
            for dl in definition_lists:
                terms = dl.find_all('dt')
                for term in terms:
                    key = term.get_text(strip=True)
                    definition = term.find_next_sibling('dd')
                    if definition:
                        value = definition.get_text(strip=True)
                        fund_details[key] = value

            if fund_details:
                logger.info(f"✅ Extracted fund details: {len(fund_details)} fields")
                return fund_details

            logger.warning("⚠️  No fund details found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting fund details: {e}")
            return None

    def _extract_distributions(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """Extract distributions data"""
        try:
            distributions = []

            # Look for distributions table
            tables = soup.find_all('table')

            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue

                header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])

                # Look for distribution-related keywords
                if any(keyword in header_text for keyword in ['distribution', 'dividend', 'payment', 'ex-date', 'record date']):
                    # Extract headers
                    header_cols = [h.get_text(strip=True) for h in headers]

                    # Extract rows
                    rows = table.find_all('tr')[1:]  # Skip header row

                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= len(header_cols):
                            distribution_data = {}
                            for i, cell in enumerate(cells):
                                if i < len(header_cols):
                                    distribution_data[header_cols[i]] = cell.get_text(strip=True)

                            if distribution_data:
                                distributions.append(distribution_data)

                    if distributions:
                        break

            if distributions:
                logger.info(f"✅ Extracted distributions: {len(distributions)} records")
                return distributions

            logger.warning("⚠️  No distributions found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting distributions: {e}")
            return None

    def _extract_top_holdings(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """Extract top 10 holdings"""
        try:
            holdings = []

            # Look for holdings table
            tables = soup.find_all('table')

            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue

                header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])

                # Look for holdings-related keywords
                if any(keyword in header_text for keyword in ['holding', 'position', 'security', 'ticker', 'allocation', 'weight']):
                    # Extract headers
                    header_cols = [h.get_text(strip=True) for h in headers]

                    # Extract rows (max 10)
                    rows = table.find_all('tr')[1:]  # Skip header row

                    for i, row in enumerate(rows[:10]):  # Limit to top 10
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            holding_data = {}
                            for j, cell in enumerate(cells):
                                if j < len(header_cols):
                                    holding_data[header_cols[j]] = cell.get_text(strip=True)

                            if holding_data:
                                holdings.append(holding_data)

                    if holdings:
                        break

            if holdings:
                logger.info(f"✅ Extracted top holdings: {len(holdings)} positions")
                return holdings

            logger.warning("⚠️  No holdings found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting holdings: {e}")
            return None

    def save_to_database(self, data: Dict[str, Any]) -> bool:
        """
        Save scraped data to database

        Args:
            data: Dictionary containing all scraped data

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("💾 Saving data to database...")

            # Prepare record for database
            record = {
                'ticker': data['ticker'],
                'fund_name': data['fund_name'],
                'url': data['url'],
                'scraped_at': data['scraped_at'],
                'performance_month_end': data.get('performance_month_end'),
                'performance_quarter_end': data.get('performance_quarter_end'),
                'fund_overview': data.get('fund_overview'),
                'investment_objective': data.get('investment_objective'),
                'fund_details': data.get('fund_details'),
                'distributions': data.get('distributions'),
                'top_10_holdings': data.get('top_10_holdings')
            }

            # Upsert to database
            result = supabase_upsert('raw_etfs_yieldmax', [record])

            if result:
                logger.info(f"✅ Saved {data['ticker']} data to database")
                return True
            else:
                logger.error("❌ Failed to save data to database")
                return False

        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            return False


def scrape_single_etf(ticker: str) -> bool:
    """
    Scrape a single YieldMax ETF

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if successful, False otherwise
    """
    if ticker not in YIELDMAX_ETFS:
        logger.error(f"❌ Unknown ticker: {ticker}")
        logger.info(f"Available tickers: {', '.join(YIELDMAX_ETFS.keys())}")
        return False

    etf_info = YIELDMAX_ETFS[ticker]
    scraper = YieldMaxScraper(ticker, etf_info['name'], etf_info['url'])

    # Scrape data
    logger.info(f"🚀 Starting scrape for {ticker}...")
    data = scraper.scrape_data()

    if not data:
        logger.error(f"❌ Failed to scrape {ticker}")
        return False

    # Print summary
    print()
    print(f"📊 Scraping Results for {ticker}:")
    print(f"  • Fund Name: {data['fund_name']}")
    print(f"  • Performance (Month-End): {'✅' if data.get('performance_month_end') else '❌'}")
    print(f"  • Performance (Quarter-End): {'✅' if data.get('performance_quarter_end') else '❌'}")

    overview = data.get('fund_overview') or {}
    print(f"  • Fund Overview: {'✅' if overview else '❌'} ({len(overview)} fields)")

    print(f"  • Investment Objective: {'✅' if data.get('investment_objective') else '❌'}")

    details = data.get('fund_details') or {}
    print(f"  • Fund Details: {'✅' if details else '❌'} ({len(details)} fields)")

    distributions = data.get('distributions') or []
    print(f"  • Distributions: {'✅' if distributions else '❌'} ({len(distributions)} records)")

    holdings = data.get('top_10_holdings') or []
    print(f"  • Top Holdings: {'✅' if holdings else '❌'} ({len(holdings)} positions)")
    print()

    # Save to database
    return scraper.save_to_database(data)


def validate_etf_urls() -> Dict[str, bool]:
    """
    Validate all ETF URLs before scraping

    Returns:
        Dictionary mapping ticker to availability status (True if accessible)
    """
    import requests

    print("🔍 Validating ETF URLs...")
    print()

    validation_results = {}
    invalid_tickers = []

    for ticker, info in YIELDMAX_ETFS.items():
        try:
            response = requests.head(info['url'], timeout=10, allow_redirects=True)
            is_valid = response.status_code == 200
            validation_results[ticker] = is_valid

            if is_valid:
                print(f"  ✅ {ticker:6s} - OK")
            else:
                print(f"  ❌ {ticker:6s} - HTTP {response.status_code}")
                invalid_tickers.append(ticker)
                logger.warning(f"URL validation failed for {ticker}: HTTP {response.status_code}")

        except Exception as e:
            validation_results[ticker] = False
            print(f"  ❌ {ticker:6s} - {str(e)[:50]}")
            invalid_tickers.append(ticker)
            logger.error(f"URL validation error for {ticker}: {e}")

    print()
    if invalid_tickers:
        print(f"⚠️  {len(invalid_tickers)} invalid URLs found: {', '.join(invalid_tickers)}")
        print("   These tickers will be skipped during scraping")
        print()
    else:
        print(f"✅ All {len(YIELDMAX_ETFS)} ETF URLs validated successfully!")
        print()

    return validation_results


def scrape_all_etfs(delay: int = 5, skip_validation: bool = False) -> Dict[str, bool]:
    """
    Scrape all YieldMax ETFs

    Args:
        delay: Seconds to wait between requests (default: 5)
        skip_validation: Skip URL validation step (default: False)

    Returns:
        Dictionary mapping ticker to success status
    """
    # Validate URLs first unless skipped
    valid_tickers = list(YIELDMAX_ETFS.keys())
    if not skip_validation:
        validation_results = validate_etf_urls()
        valid_tickers = [ticker for ticker, is_valid in validation_results.items() if is_valid]

        if len(valid_tickers) < len(YIELDMAX_ETFS):
            invalid_count = len(YIELDMAX_ETFS) - len(valid_tickers)
            print(f"⏭️  Skipping {invalid_count} invalid ticker(s)")
            print()

    results = {}

    print(f"🚀 Scraping {len(valid_tickers)} YieldMax ETFs...")
    print(f"⏱️  Delay between requests: {delay} seconds")
    print()

    for i, ticker in enumerate(valid_tickers, 1):
        print("=" * 80)
        print(f"[{i}/{len(valid_tickers)}] {ticker}")
        print("=" * 80)

        success = scrape_single_etf(ticker)
        results[ticker] = success

        if success:
            print(f"✅ {ticker} complete")
        else:
            print(f"❌ {ticker} failed")
        print()

        # Delay between requests to be respectful and avoid rate limiting
        if i < len(valid_tickers):
            logger.info(f"⏳ Waiting {delay} seconds before next scrape...")
            time.sleep(delay)

    return results


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Scrape YieldMax ETF data')
    parser.add_argument('--ticker', '-t', type=str, help='Specific ticker to scrape (e.g., TSLY)')
    parser.add_argument('--all', '-a', action='store_true', help='Scrape all YieldMax ETFs')
    parser.add_argument('--list', '-l', action='store_true', help='List available tickers')
    parser.add_argument('--delay', '-d', type=int, default=5,
                       help='Delay in seconds between requests when scraping all (default: 5)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip URL validation before scraping (faster but may fail on invalid URLs)')

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 YieldMax ETF Scraper")
    print("=" * 80)
    print()

    # List available tickers
    if args.list:
        print(f"Available YieldMax ETFs ({len(YIELDMAX_ETFS)}):")
        print()
        for ticker, info in YIELDMAX_ETFS.items():
            print(f"  {ticker:8s} - {info['name']}")
        print()
        print("=" * 80)
        return 0

    # Scrape all ETFs
    if args.all:
        results = scrape_all_etfs(delay=args.delay, skip_validation=args.skip_validation)

        # Summary
        print()
        print("=" * 80)
        print("📊 Summary:")
        print("=" * 80)
        successful = sum(1 for success in results.values() if success)
        failed = sum(1 for success in results.values() if not success)
        total = len(results)
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {failed}/{total}")

        if failed > 0:
            print()
            print("Failed tickers:")
            for ticker, success in results.items():
                if not success:
                    print(f"  • {ticker}")

        print("=" * 80)
        return 0 if failed == 0 else 1

    # Scrape specific ticker
    if args.ticker:
        ticker = args.ticker.upper()
        success = scrape_single_etf(ticker)

        print()
        print("=" * 80)
        if success:
            print(f"✅ {ticker} scraping complete!")
        else:
            print(f"❌ {ticker} scraping failed")
        print("=" * 80)

        return 0 if success else 1

    # Default: show help
    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
