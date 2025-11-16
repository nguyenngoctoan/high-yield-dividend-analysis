#!/usr/bin/env python3
"""
NEOS Funds ETF Scraper (All Funds)

Scrapes comprehensive data from all NEOS ETF pages including:
- Performance data
- Fund overview
- Fund details (expense ratio, inception date, net assets)
- Distributions
- Holdings

All data stored as JSON in raw_etfs_neos table.
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
import re

# Add paths to import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from supabase_helpers import supabase_upsert, get_supabase_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# NEOS ETF Configuration
NEOS_ETFS = {
    'SPYI': {
        'name': 'NEOS S&P 500 High Income ETF',
        'url': 'https://neosfunds.com/spyi/'
    },
    'QQQI': {
        'name': 'NEOS Nasdaq-100 High Income ETF',
        'url': 'https://neosfunds.com/qqqi/'
    },
    'IWMI': {
        'name': 'NEOS Russell 2000 High Income ETF',
        'url': 'https://neosfunds.com/iwmi/'
    },
    'NIHI': {
        'name': 'NEOS Enhanced Income 1-3 Month T-Bill ETF',
        'url': 'https://neosfunds.com/nihi/'
    },
    'QQQH': {
        'name': 'NEOS Nasdaq-100 Enhanced Income ETF',
        'url': 'https://neosfunds.com/qqqh/'
    },
    'SPYH': {
        'name': 'NEOS S&P 500 Enhanced Income ETF',
        'url': 'https://neosfunds.com/spyh/'
    },
    'BTCI': {
        'name': 'NEOS Bitcoin High Income ETF',
        'url': 'https://neosfunds.com/btci/'
    },
    'IYRI': {
        'name': 'NEOS iShares Russell 2000 ETF Enhanced Income ETF',
        'url': 'https://neosfunds.com/iyri/'
    },
    'IAUI': {
        'name': 'NEOS iShares Gold Trust Enhanced Income ETF',
        'url': 'https://neosfunds.com/iaui/'
    },
    'BNDI': {
        'name': 'NEOS Enhanced Income Aggregate Bond ETF',
        'url': 'https://neosfunds.com/bndi/'
    },
    'HYBI': {
        'name': 'NEOS Enhanced Income High Yield Bond ETF',
        'url': 'https://neosfunds.com/hybi/'
    },
    'CSHI': {
        'name': 'NEOS Enhanced Income Cash Alternative ETF',
        'url': 'https://neosfunds.com/cshi/'
    },
    'TLTI': {
        'name': 'NEOS Enhanced Income 20+ Year Treasury ETF',
        'url': 'https://neosfunds.com/tlti/'
    }
}


class NEOSScraper:
    """Scraper for NEOS ETF data"""

    def __init__(self, ticker: str, fund_name: str, url: str):
        """
        Initialize the scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            url: NEOS ETF page URL
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
                'inception_date': self._extract_inception_date(soup),
                'net_assets': self._extract_net_assets(soup),
                'shares_outstanding': self._extract_shares_outstanding(soup),
                'distribution_rate': self._extract_distribution_rate(soup),
                'sec_yield_30day': self._extract_sec_yield(soup),
                'nav': self._extract_nav(soup),
                'market_price': self._extract_market_price(soup),
                'premium_discount': self._extract_premium_discount(soup),
                'fund_details': self._extract_fund_details(soup),
                'performance_data': self._extract_performance_data(soup),
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

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """
        Normalize date format to MM/DD/YYYY
        Handles 2-digit years by converting YY to 20YY
        Filters out percentage values (they have %)

        Args:
            date_str: Date string in various formats

        Returns:
            Normalized date string or None
        """
        try:
            # Filter out percentage values
            if '%' in date_str:
                return None

            # Try to find date pattern in the string
            # Formats: MM/DD/YY, MM/DD/YYYY, MM-DD-YY, MM-DD-YYYY
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_str)
            if date_match:
                month, day, year = date_match.groups()

                # Normalize 2-digit years to 4-digit years
                if len(year) == 2:
                    year_int = int(year)
                    # Assume years 00-99 are 2000-2099 (ETFs are modern)
                    full_year = 2000 + year_int
                    normalized_date = f"{month}/{day}/{full_year}"
                    logger.info(f"✅ Normalized date: {normalized_date} (from {date_str})")
                    return normalized_date
                else:
                    normalized_date = f"{month}/{day}/{year}"
                    return normalized_date

            # Also accept text dates like "April 11, 2023"
            text_date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', date_str)
            if text_date_match:
                return date_str

            return None

        except Exception as e:
            logger.error(f"❌ Error normalizing date: {e}")
            return None

    def _validate_numeric_field(self, value: str, field_name: str) -> Optional[str]:
        """
        Validate that a field contains numeric data (numbers, decimals, commas, %, $)
        Reject date-like patterns

        Args:
            value: Value to validate
            field_name: Name of field for logging

        Returns:
            Validated value or None
        """
        try:
            # Filter out date patterns
            if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', value):
                logger.warning(f"⚠️  Rejected {field_name}: contains date pattern")
                return None

            # Must contain at least one digit
            if not re.search(r'\d', value):
                return None

            # Should be numeric-like (allow $, %, commas, decimals, parentheses, dashes)
            if re.match(r'^[\d\$\%\,\.\(\)\-\s]+$', value.strip()):
                return value.strip()

            return None

        except Exception as e:
            logger.error(f"❌ Error validating {field_name}: {e}")
            return None

    def _extract_expense_ratio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract expense ratio"""
        try:
            keywords = ['expense ratio', 'net expense ratio', 'total expense ratio', 'gross expense']

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
                            # Validate it's numeric
                            validated = self._validate_numeric_field(value, 'expense_ratio')
                            if validated:
                                logger.info(f"✅ Extracted expense ratio: {validated}")
                                return validated

            # Also try text search
            for text_elem in soup.find_all(string=True):
                text = text_elem.strip().lower()
                for keyword in keywords:
                    if keyword in text:
                        parent = text_elem.parent
                        if parent:
                            siblings = [s.get_text(strip=True) for s in parent.find_next_siblings()[:3]]
                            combined_text = ' '.join([text] + siblings)
                            match = re.search(r'(\d+\.\d+%)', combined_text)
                            if match:
                                logger.info(f"✅ Extracted expense ratio: {match.group(1)}")
                                return match.group(1)

            logger.warning("⚠️  No expense ratio found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting expense ratio: {e}")
            return None

    def _extract_inception_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract fund inception date with normalization"""
        try:
            keywords = ['inception date', 'inception', 'launch date', 'commenced', 'fund inception']

            # Search in tables first
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            # Normalize the date
                            normalized = self._normalize_date(value)
                            if normalized:
                                logger.info(f"✅ Extracted inception date: {normalized}")
                                return normalized

            logger.warning("⚠️  No inception date found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting inception date: {e}")
            return None

    def _extract_net_assets(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract net assets"""
        try:
            keywords = ['net assets', 'assets under management', 'aum', 'total assets', 'fund assets']

            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            validated = self._validate_numeric_field(value, 'net_assets')
                            if validated:
                                logger.info(f"✅ Extracted net assets: {validated}")
                                return validated

            logger.warning("⚠️  No net assets found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting net assets: {e}")
            return None

    def _extract_shares_outstanding(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract shares outstanding"""
        try:
            keywords = ['shares outstanding', 'outstanding shares', 'total shares']

            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            # Must be pure number or number with commas
                            if re.match(r'^\d+(?:,\d{3})*$', value):
                                logger.info(f"✅ Extracted shares outstanding: {value}")
                                return value

            logger.warning("⚠️  No shares outstanding found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting shares outstanding: {e}")
            return None

    def _extract_distribution_rate(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract distribution rate"""
        try:
            keywords = ['distribution rate', '30-day distribution rate', 'distribution yield']

            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            validated = self._validate_numeric_field(value, 'distribution_rate')
                            if validated:
                                logger.info(f"✅ Extracted distribution rate: {validated}")
                                return validated

            logger.warning("⚠️  No distribution rate found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting distribution rate: {e}")
            return None

    def _extract_sec_yield(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract 30-day SEC yield"""
        try:
            keywords = ['30-day sec yield', 'sec yield', '30 day sec yield', 'sec 30-day']

            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            validated = self._validate_numeric_field(value, 'sec_yield_30day')
                            if validated:
                                logger.info(f"✅ Extracted 30-day SEC yield: {validated}")
                                return validated

            logger.warning("⚠️  No 30-day SEC yield found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting 30-day SEC yield: {e}")
            return None

    def _extract_nav(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract NAV (Net Asset Value)"""
        try:
            keywords = ['nav', 'net asset value', 'net asset val']

            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword == label for keyword in keywords):
                            validated = self._validate_numeric_field(value, 'nav')
                            if validated:
                                logger.info(f"✅ Extracted NAV: {validated}")
                                return validated

            logger.warning("⚠️  No NAV found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting NAV: {e}")
            return None

    def _extract_market_price(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract market price"""
        try:
            keywords = ['market price', 'closing price', 'price']

            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            validated = self._validate_numeric_field(value, 'market_price')
                            if validated:
                                logger.info(f"✅ Extracted market price: {validated}")
                                return validated

            logger.warning("⚠️  No market price found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting market price: {e}")
            return None

    def _extract_premium_discount(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract premium/discount to NAV"""
        try:
            keywords = ['premium/discount', 'premium discount', 'premium / discount']

            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            validated = self._validate_numeric_field(value, 'premium_discount')
                            if validated:
                                logger.info(f"✅ Extracted premium/discount: {validated}")
                                return validated

            logger.warning("⚠️  No premium/discount found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting premium/discount: {e}")
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

            # Also check all tables for useful info
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            fund_details[key] = value

            if fund_details:
                logger.info(f"✅ Extracted fund details: {len(fund_details)} fields")
                return fund_details

            logger.warning("⚠️  No fund details found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting fund details: {e}")
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
                if any(keyword in header_text for keyword in ['performance', 'return', 'ytd', 'month', 'quarter', 'year', 'inception']):
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

    def _extract_distributions(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """
        Extract distributions data

        Note: NEOS pages have TWO tables:
        1. First table: "Distribution Information" summary box (we want to SKIP this)
        2. Second table: Actual distributions with dates and amounts (this is what we want)

        We look for tables with specific date-related columns to ensure we get the right one.
        """
        try:
            distributions = []

            # Look for distributions table
            tables = soup.find_all('table')

            logger.info(f"📊 Found {len(tables)} total tables on page")

            for idx, table in enumerate(tables):
                headers = table.find_all('th')
                if not headers:
                    continue

                header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])
                logger.info(f"   Table {idx + 1} headers: {header_text[:100]}")

                # Skip the "Distribution Information" summary table
                # This table has headers like "Distribution Information", "Distribution Frequency", etc.
                if 'distribution information' in header_text or 'distribution frequency' in header_text:
                    logger.info(f"   ⏭️  Skipping Distribution Information summary table")
                    continue

                # Look for the actual distributions table
                # This table has columns: Declaration Date, Ex-Div Date, Record Date, Payable Date, Amount
                if all(keyword in header_text for keyword in ['declaration date', 'ex-div date', 'record date', 'payable date', 'amount']):
                    logger.info(f"   ✅ Found distributions table with all required columns")

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

                            # Only add if we have actual data (not empty)
                            if distribution_data and any(v and v.strip() for v in distribution_data.values()):
                                distributions.append(distribution_data)

                    if distributions:
                        break

            if distributions:
                logger.info(f"✅ Extracted distributions: {len(distributions)} records")
                return distributions

            logger.warning("⚠️  No distributions found")
            return []  # Return empty list instead of None

        except Exception as e:
            logger.error(f"❌ Error extracting distributions: {e}")
            import traceback
            traceback.print_exc()
            return []  # Return empty list instead of None

    def _extract_holdings(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """Extract fund holdings (top 10)"""
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

                    # Extract rows (limit to top 10)
                    rows = table.find_all('tr')[1:]  # Skip header row

                    for i, row in enumerate(rows[:10]):
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
                'inception_date': data.get('inception_date'),
                'net_assets': data.get('net_assets'),
                'shares_outstanding': data.get('shares_outstanding'),
                'distribution_rate': data.get('distribution_rate'),
                'sec_yield_30day': data.get('sec_yield_30day'),
                'nav': data.get('nav'),
                'market_price': data.get('market_price'),
                'premium_discount': data.get('premium_discount'),
                'fund_details': data.get('fund_details'),
                'performance_data': data.get('performance_data'),
                'distributions': data.get('distributions'),
                'holdings': data.get('holdings')
            }

            # Upsert to database
            result = supabase_upsert('raw_etfs_neos', [record])

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
    Scrape a single NEOS ETF

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if successful, False otherwise
    """
    if ticker not in NEOS_ETFS:
        logger.error(f"❌ Unknown ticker: {ticker}")
        logger.info(f"Available tickers: {', '.join(NEOS_ETFS.keys())}")
        return False

    etf_info = NEOS_ETFS[ticker]
    scraper = NEOSScraper(ticker, etf_info['name'], etf_info['url'])

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
    print(f"  • Inception Date: {data.get('inception_date') or '❌'}")
    print(f"  • Net Assets: {data.get('net_assets') or '❌'}")
    print(f"  • Shares Outstanding: {data.get('shares_outstanding') or '❌'}")
    print(f"  • Distribution Rate: {data.get('distribution_rate') or '❌'}")
    print(f"  • 30-Day SEC Yield: {data.get('sec_yield_30day') or '❌'}")
    print(f"  • NAV: {data.get('nav') or '❌'}")
    print(f"  • Market Price: {data.get('market_price') or '❌'}")
    print(f"  • Premium/Discount: {data.get('premium_discount') or '❌'}")

    details = data.get('fund_details') or {}
    print(f"  • Fund Details: {'✅' if details else '❌'} ({len(details)} fields)")

    performance = data.get('performance_data') or {}
    print(f"  • Performance Data: {'✅' if performance else '❌'} ({len(performance)} metrics)")

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

    for ticker, info in NEOS_ETFS.items():
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
        print(f"✅ All {len(NEOS_ETFS)} ETF URLs validated successfully!")
        print()

    return validation_results


def scrape_all_etfs(delay: int = 5, skip_validation: bool = False) -> Dict[str, bool]:
    """
    Scrape all NEOS ETFs

    Args:
        delay: Seconds to wait between requests (default: 5)
        skip_validation: Skip URL validation step (default: False)

    Returns:
        Dictionary mapping ticker to success status
    """
    # Validate URLs first unless skipped
    valid_tickers = list(NEOS_ETFS.keys())
    if not skip_validation:
        validation_results = validate_etf_urls()
        valid_tickers = [ticker for ticker, is_valid in validation_results.items() if is_valid]

        if len(valid_tickers) < len(NEOS_ETFS):
            invalid_count = len(NEOS_ETFS) - len(valid_tickers)
            print(f"⏭️  Skipping {invalid_count} invalid ticker(s)")
            print()

    results = {}

    print(f"🚀 Scraping {len(valid_tickers)} NEOS ETFs...")
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
    parser = argparse.ArgumentParser(description='Scrape NEOS ETF data')
    parser.add_argument('--ticker', '-t', type=str, help='Specific ticker to scrape (e.g., SPYI)')
    parser.add_argument('--all', '-a', action='store_true', help='Scrape all NEOS ETFs')
    parser.add_argument('--list', '-l', action='store_true', help='List available tickers')
    parser.add_argument('--delay', '-d', type=int, default=5,
                       help='Delay in seconds between requests when scraping all (default: 5)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip URL validation before scraping (faster but may fail on invalid URLs)')

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 NEOS ETF Scraper")
    print("=" * 80)
    print()

    # List available tickers
    if args.list:
        print(f"Available NEOS ETFs ({len(NEOS_ETFS)}):")
        print()
        for ticker, info in NEOS_ETFS.items():
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
