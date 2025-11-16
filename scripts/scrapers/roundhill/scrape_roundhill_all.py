#!/usr/bin/env python3
"""
Roundhill Investments ETF Scraper (All Funds)

Scrapes comprehensive data from all Roundhill ETF pages including:
- Performance data
- Fund overview
- Fund details (expense ratio, launch date, holdings count)
- Distributions
- Holdings

All data stored as JSON in raw_roundhill_etf_data table.
"""

import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
from bs4 import BeautifulSoup
import argparse

# Add paths to import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from supabase_helpers import supabase_upsert, get_supabase_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Roundhill ETF Configuration
ROUNDHILL_ETFS = {
    # Core ETFs
    'METV': {
        'name': 'Roundhill Ball Metaverse ETF',
        'url': 'https://www.roundhillinvestments.com/etf/metv/'
    },
    'BETZ': {
        'name': 'Roundhill Sports Betting & iGaming ETF',
        'url': 'https://www.roundhillinvestments.com/etf/betz/'
    },
    'CHAT': {
        'name': 'Roundhill Generative AI & Technology ETF',
        'url': 'https://www.roundhillinvestments.com/etf/chat/'
    },
    'MAGS': {
        'name': 'Roundhill Magnificent Seven ETF',
        'url': 'https://www.roundhillinvestments.com/etf/mags/'
    },
    'NERD': {
        'name': 'Roundhill BITKRAFT Esports & Digital Entertainment ETF',
        'url': 'https://www.roundhillinvestments.com/etf/nerd/'
    },
    'WEED': {
        'name': 'Roundhill Cannabis ETF',
        'url': 'https://www.roundhillinvestments.com/etf/weed/'
    },
    'YBTC': {
        'name': 'Roundhill Bitcoin Covered Call Strategy ETF',
        'url': 'https://www.roundhillinvestments.com/etf/ybtc/'
    },
    'MAGX': {
        'name': 'Roundhill Magnificent Seven 2X Strategy ETF',
        'url': 'https://www.roundhillinvestments.com/etf/magx/'
    },
    'QDTE': {
        'name': 'Roundhill Nasdaq 100 0DTE Covered Call Strategy ETF',
        'url': 'https://www.roundhillinvestments.com/etf/qdte/'
    },
    'XDTE': {
        'name': 'Roundhill S&P 500 0DTE Covered Call Strategy ETF',
        'url': 'https://www.roundhillinvestments.com/etf/xdte/'
    },
    'OZEM': {
        'name': 'Roundhill GLP-1 & Weight Loss ETF',
        'url': 'https://www.roundhillinvestments.com/etf/ozem/'
    },
    'YETH': {
        'name': 'Roundhill Ether Covered Call Strategy ETF',
        'url': 'https://www.roundhillinvestments.com/etf/yeth/'
    },
    'RDTE': {
        'name': 'Roundhill Russell 2000 0DTE Covered Call Strategy ETF',
        'url': 'https://www.roundhillinvestments.com/etf/rdte/'
    },
    'MAGC': {
        'name': 'Roundhill Magnificent Seven Covered Call ETF',
        'url': 'https://www.roundhillinvestments.com/etf/magc/'
    },
    'XPAY': {
        'name': 'Roundhill S&P 500 0DTE Covered Call Strategy Monthly Distribution ETF',
        'url': 'https://www.roundhillinvestments.com/etf/xpay/'
    },
    'UX': {
        'name': 'Roundhill Uranium & Nuclear Energy ETF',
        'url': 'https://www.roundhillinvestments.com/etf/ux/'
    },
    'MAGY': {
        'name': 'Roundhill Magnificent Seven Income & Growth ETF',
        'url': 'https://www.roundhillinvestments.com/etf/magy/'
    },
    'WEEK': {
        'name': 'Roundhill Weekly Dividend ETF',
        'url': 'https://www.roundhillinvestments.com/etf/week/'
    },
    'XDIV': {
        'name': 'Roundhill S&P Dividend Monarchs ETF',
        'url': 'https://www.roundhillinvestments.com/etf/xdiv/'
    },
    'HUMN': {
        'name': 'Roundhill Humankind US Equity ETF',
        'url': 'https://www.roundhillinvestments.com/etf/humn/'
    },
    'MEME': {
        'name': 'Roundhill MEME ETF',
        'url': 'https://www.roundhillinvestments.com/etf/meme/'
    },
    'WPAY': {
        'name': 'Roundhill PYPL Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/wpay/'
    },

    # WeeklyPay ETFs
    'AAPW': {
        'name': 'Roundhill AAPL Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/aapw/'
    },
    'AMDW': {
        'name': 'Roundhill AMD Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/amdw/'
    },
    'ARMW': {
        'name': 'Roundhill ARM Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/armw/'
    },
    'AMZW': {
        'name': 'Roundhill AMZN Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/amzw/'
    },
    'AVGW': {
        'name': 'Roundhill AVGO Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/avgw/'
    },
    'BABW': {
        'name': 'Roundhill BABA Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/babw/'
    },
    'BRKW': {
        'name': 'Roundhill BRK.B Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/brkw/'
    },
    'COIW': {
        'name': 'Roundhill COIN Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/coiw/'
    },
    'COSW': {
        'name': 'Roundhill COST Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/cosw/'
    },
    'GDXW': {
        'name': 'Roundhill GDX Miners Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/gdxw/'
    },
    'GLDW': {
        'name': 'Roundhill GLD Gold Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/gldw/'
    },
    'GOOW': {
        'name': 'Roundhill GOOG Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/goow/'
    },
    'HOOW': {
        'name': 'Roundhill HYG Bond Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/hoow/'
    },
    'METW': {
        'name': 'Roundhill META Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/metw/'
    },
    'MSFW': {
        'name': 'Roundhill MSFT Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/msfw/'
    },
    'MSTW': {
        'name': 'Roundhill MSTR Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/mstw/'
    },
    'NFLW': {
        'name': 'Roundhill NFLX Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/nflw/'
    },
    'NVDW': {
        'name': 'Roundhill NVDA Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/nvdw/'
    },
    'PLTW': {
        'name': 'Roundhill PLTR Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/pltw/'
    },
    'TSLW': {
        'name': 'Roundhill TSLA Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/tslw/'
    },
    'TSYW': {
        'name': 'Roundhill TSY Treasury Bond Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/tsyw/'
    },
    'UBEW': {
        'name': 'Roundhill UBER Stock Weekly Income ETF',
        'url': 'https://www.roundhillinvestments.com/etf/ubew/'
    }
}


class RoundhillScraper:
    """Scraper for Roundhill ETF data"""

    def __init__(self, ticker: str, fund_name: str, url: str):
        """
        Initialize the scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            url: Roundhill ETF page URL
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
                'expense_ratio': self._extract_expense_ratio(soup),
                'launch_date': self._extract_launch_date(soup),
                'holdings_count': self._extract_holdings_count(soup),
                'fund_overview': self._extract_fund_overview(soup),
                'performance_data': self._extract_performance_data(soup),
                'fund_details': self._extract_fund_details(soup),
                'distributions': self._extract_distributions(soup),
                'holdings': self._extract_holdings(soup)
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

    def _extract_expense_ratio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract expense ratio"""
        try:
            # Look for expense ratio in common locations
            keywords = ['expense ratio', 'net expense ratio', 'total expense ratio']

            # Search in all text
            for text_elem in soup.find_all(string=True):
                text = text_elem.strip().lower()
                for keyword in keywords:
                    if keyword in text:
                        # Try to find the value nearby
                        parent = text_elem.parent
                        if parent:
                            # Look for percentage pattern
                            import re
                            siblings = [s.get_text(strip=True) for s in parent.find_next_siblings()[:3]]
                            combined_text = ' '.join([text] + siblings)
                            match = re.search(r'(\d+\.\d+%)', combined_text)
                            if match:
                                logger.info(f"✅ Extracted expense ratio: {match.group(1)}")
                                return match.group(1)

            # Also check in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        if any(keyword in label for keyword in keywords):
                            value = cells[1].get_text(strip=True)
                            logger.info(f"✅ Extracted expense ratio: {value}")
                            return value

            logger.warning("⚠️  No expense ratio found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting expense ratio: {e}")
            return None

    def _extract_launch_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract fund launch date"""
        try:
            import re
            from datetime import datetime

            # Look for inception/launch date with more specific matching
            keywords = ['launch', 'inception date', 'inception', 'commenced']

            # Search in tables first
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        # Check if label matches keywords
                        if any(keyword in label for keyword in keywords):
                            # Filter out percentage values (they have % sign)
                            if '%' in value:
                                continue

                            # Check if value looks like a date (contains / or - and digits)
                            # Formats: MM/DD/YY, MM/DD/YYYY, MM-DD-YY, etc.
                            date_match = re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value)
                            if date_match:
                                date_str = date_match.group(0)

                                # Normalize 2-digit years to 4-digit years
                                # Assume years 00-99 are 2000-2099 (ETFs are modern financial instruments)
                                parts = re.split(r'[/-]', date_str)
                                if len(parts) == 3 and len(parts[2]) == 2:
                                    # Two-digit year: convert to 4-digit
                                    year = int(parts[2])
                                    # Years 00-99 become 2000-2099
                                    full_year = 2000 + year
                                    normalized_date = f"{parts[0]}/{parts[1]}/{full_year}"
                                    logger.info(f"✅ Extracted launch date: {normalized_date} (normalized from {date_str})")
                                    return normalized_date
                                else:
                                    logger.info(f"✅ Extracted launch date: {date_str}")
                                    return date_str

                            # Also accept text dates like "April 11, 2023"
                            elif re.search(r'[A-Za-z]+\s+\d{1,2},?\s+\d{4}', value):
                                logger.info(f"✅ Extracted launch date: {value}")
                                return value

            logger.warning("⚠️  No launch date found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting launch date: {e}")
            return None

    def _extract_holdings_count(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract number of holdings"""
        try:
            import re

            # Look for holdings count with more specific keywords
            keywords = ['number of holdings', '# of holdings', 'total holdings', 'num holdings']

            # Search in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            # Filter out percentages and dates
                            if '%' in value or '/' in value or '-' in value:
                                continue

                            # Must be a pure number or number with commas
                            if re.match(r'^\d+(?:,\d{3})*$', value):
                                logger.info(f"✅ Extracted holdings count: {value}")
                                return value

            logger.warning("⚠️  No holdings count found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting holdings count: {e}")
            return None

    def _extract_fund_overview(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract fund overview information"""
        try:
            overview_data = {}

            # Look for fund overview section
            overview_sections = soup.find_all(['div', 'section'],
                                             class_=lambda c: c and any(x in c.lower() for x in ['overview', 'fund-info', 'details', 'summary']))

            for section in overview_sections:
                # Look for label-value pairs
                labels = section.find_all(['dt', 'div', 'span'],
                                         class_=lambda c: c and 'label' in c.lower())

                for label in labels:
                    label_text = label.get_text(strip=True)
                    # Find corresponding value
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

    def _extract_performance_data(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract performance data"""
        try:
            # Look for performance table
            tables = soup.find_all('table')

            for table in tables:
                headers = table.find_all('th')
                if not headers:
                    continue

                header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])

                # Look for performance-related keywords
                if any(keyword in header_text for keyword in ['performance', 'return', 'ytd', 'month', 'quarter', 'year']):
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

                    if performance_data:
                        logger.info(f"✅ Extracted performance data: {len(performance_data)} metrics")
                        return performance_data

            logger.warning("⚠️  No performance data found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting performance data: {e}")
            return None

    def _extract_fund_details(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract fund details as key-value pairs"""
        try:
            fund_details = {}

            # Look for fund details table or list
            detail_keywords = ['fund details', 'fund information', 'details', 'fund facts', 'characteristics']

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
        """
        Extract distributions data

        Note: On Roundhill pages:
        - "Distribution History" section = ACTUAL past distributions (what we want)
        - "Distribution Calendar" section = FUTURE scheduled distributions

        We prioritize Distribution History over Distribution Calendar.
        """
        try:
            distributions = []
            distribution_calendar = []
            distribution_history = []

            # Find all headings to locate sections
            all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

            for heading in all_headings:
                heading_text = heading.get_text(strip=True).lower()

                # Look for Distribution History section (actual distributions)
                if 'distribution history' in heading_text:
                    logger.info("📜 Found Distribution History section (actual distributions)")
                    # Find the next table after this heading
                    table = heading.find_next('table')
                    if table:
                        history_data = self._extract_distribution_table(table)
                        if history_data:
                            # Mark these as actual distributions
                            for record in history_data:
                                record['_source'] = 'Distribution History'
                                record['_type'] = 'actual'
                            distribution_history.extend(history_data)
                            logger.info(f"✅ Extracted {len(history_data)} actual distributions from History")

                # Look for Distribution Calendar section (future distributions)
                elif 'distribution calendar' in heading_text:
                    logger.info("📅 Found Distribution Calendar section (future/scheduled)")
                    # Find the next table after this heading
                    table = heading.find_next('table')
                    if table:
                        calendar_data = self._extract_distribution_table(table)
                        if calendar_data:
                            # Mark these as future/scheduled distributions
                            for record in calendar_data:
                                record['_source'] = 'Distribution Calendar'
                                record['_type'] = 'scheduled'
                            distribution_calendar.extend(calendar_data)
                            logger.info(f"✅ Extracted {len(calendar_data)} scheduled distributions from Calendar")

            # Prioritize Distribution History (actual distributions)
            if distribution_history:
                distributions = distribution_history
                logger.info(f"✅ Using Distribution History: {len(distributions)} actual distribution records")
            elif distribution_calendar:
                distributions = distribution_calendar
                logger.info(f"⚠️  No History found, using Distribution Calendar: {len(distributions)} scheduled records")
            else:
                # Fallback: Look for any distribution table without section headers
                logger.info("🔍 No specific sections found, searching for any distribution table...")
                tables = soup.find_all('table')
                for table in tables:
                    headers = table.find_all('th')
                    if not headers:
                        continue

                    header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])

                    # Look for distribution-related keywords
                    if any(keyword in header_text for keyword in ['distribution', 'dividend', 'payment', 'ex-date', 'record date', 'payable']):
                        distributions = self._extract_distribution_table(table)
                        if distributions:
                            # Mark source as unknown since we didn't find a section header
                            for record in distributions:
                                record['_source'] = 'Unknown'
                                record['_type'] = 'unknown'
                            logger.info(f"✅ Extracted {len(distributions)} distributions from unlabeled table")
                            break

            if distributions:
                logger.info(f"✅ Total distributions extracted: {len(distributions)} records")
                return distributions

            logger.warning("⚠️  No distributions found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting distributions: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_distribution_table(self, table: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract distribution records from a table element

        Args:
            table: BeautifulSoup table element

        Returns:
            List of distribution records as dictionaries
        """
        try:
            distributions = []

            headers = table.find_all('th')
            if not headers:
                return []

            # Extract header columns
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

            return distributions

        except Exception as e:
            logger.error(f"❌ Error extracting distribution table: {e}")
            return []

    def _extract_holdings(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """Extract fund holdings"""
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
                if any(keyword in header_text for keyword in ['holding', 'position', 'security', 'ticker', 'allocation', 'weight', 'name', 'shares']):
                    # Extract headers
                    header_cols = [h.get_text(strip=True) for h in headers]

                    # Extract rows
                    rows = table.find_all('tr')[1:]  # Skip header row

                    for i, row in enumerate(rows):
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
                logger.info(f"✅ Extracted holdings: {len(holdings)} positions")
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
                'expense_ratio': data.get('expense_ratio'),
                'launch_date': data.get('launch_date'),
                'holdings_count': data.get('holdings_count'),
                'fund_overview': data.get('fund_overview'),
                'performance_data': data.get('performance_data'),
                'fund_details': data.get('fund_details'),
                'distributions': data.get('distributions'),
                'holdings': data.get('holdings')
            }

            # Upsert to database
            result = supabase_upsert('raw_roundhill_etf_data', [record])

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
    Scrape a single Roundhill ETF

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if successful, False otherwise
    """
    if ticker not in ROUNDHILL_ETFS:
        logger.error(f"❌ Unknown ticker: {ticker}")
        logger.info(f"Available tickers: {', '.join(ROUNDHILL_ETFS.keys())}")
        return False

    etf_info = ROUNDHILL_ETFS[ticker]
    scraper = RoundhillScraper(ticker, etf_info['name'], etf_info['url'])

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
    print(f"  • Expense Ratio: {data.get('expense_ratio') or '❌'}")
    print(f"  • Launch Date: {data.get('launch_date') or '❌'}")
    print(f"  • Holdings Count: {data.get('holdings_count') or '❌'}")

    overview = data.get('fund_overview') or {}
    print(f"  • Fund Overview: {'✅' if overview else '❌'} ({len(overview)} fields)")

    performance = data.get('performance_data') or {}
    print(f"  • Performance Data: {'✅' if performance else '❌'} ({len(performance)} metrics)")

    details = data.get('fund_details') or {}
    print(f"  • Fund Details: {'✅' if details else '❌'} ({len(details)} fields)")

    distributions = data.get('distributions') or []
    print(f"  • Distributions: {'✅' if distributions else '❌'} ({len(distributions)} records)")

    holdings = data.get('holdings') or []
    print(f"  • Holdings: {'✅' if holdings else '❌'} ({len(holdings)} positions)")
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

    for ticker, info in ROUNDHILL_ETFS.items():
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
        print(f"✅ All {len(ROUNDHILL_ETFS)} ETF URLs validated successfully!")
        print()

    return validation_results


def scrape_all_etfs(delay: int = 5, skip_validation: bool = False) -> Dict[str, bool]:
    """
    Scrape all Roundhill ETFs

    Args:
        delay: Seconds to wait between requests (default: 5)
        skip_validation: Skip URL validation step (default: False)

    Returns:
        Dictionary mapping ticker to success status
    """
    # Validate URLs first unless skipped
    valid_tickers = list(ROUNDHILL_ETFS.keys())
    if not skip_validation:
        validation_results = validate_etf_urls()
        valid_tickers = [ticker for ticker, is_valid in validation_results.items() if is_valid]

        if len(valid_tickers) < len(ROUNDHILL_ETFS):
            invalid_count = len(ROUNDHILL_ETFS) - len(valid_tickers)
            print(f"⏭️  Skipping {invalid_count} invalid ticker(s)")
            print()

    results = {}

    print(f"🚀 Scraping {len(valid_tickers)} Roundhill ETFs...")
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
    parser = argparse.ArgumentParser(description='Scrape Roundhill ETF data')
    parser.add_argument('--ticker', '-t', type=str, help='Specific ticker to scrape (e.g., METV)')
    parser.add_argument('--all', '-a', action='store_true', help='Scrape all Roundhill ETFs')
    parser.add_argument('--list', '-l', action='store_true', help='List available tickers')
    parser.add_argument('--delay', '-d', type=int, default=5,
                       help='Delay in seconds between requests when scraping all (default: 5)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip URL validation before scraping (faster but may fail on invalid URLs)')

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 Roundhill ETF Scraper")
    print("=" * 80)
    print()

    # List available tickers
    if args.list:
        print(f"Available Roundhill ETFs ({len(ROUNDHILL_ETFS)}):")
        print()
        print("Core ETFs:")
        core_etfs = ['METV', 'BETZ', 'CHAT', 'MAGS', 'NERD', 'WEED', 'YBTC', 'MAGX',
                     'QDTE', 'XDTE', 'OZEM', 'YETH', 'RDTE', 'MAGC', 'XPAY', 'UX',
                     'MAGY', 'WEEK', 'XDIV', 'HUMN', 'MEME', 'WPAY']
        for ticker in core_etfs:
            if ticker in ROUNDHILL_ETFS:
                print(f"  {ticker:8s} - {ROUNDHILL_ETFS[ticker]['name']}")

        print()
        print("WeeklyPay ETFs:")
        weeklypay_etfs = [t for t in ROUNDHILL_ETFS.keys() if t not in core_etfs]
        for ticker in weeklypay_etfs:
            print(f"  {ticker:8s} - {ROUNDHILL_ETFS[ticker]['name']}")
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
