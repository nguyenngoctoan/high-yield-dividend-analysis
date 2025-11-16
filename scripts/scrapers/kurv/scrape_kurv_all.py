#!/usr/bin/env python3
"""
Kurv ETF Scraper (All Funds)

Scrapes comprehensive data from all Kurv ETF pages including:
- Performance data
- Fund overview
- Fund details (expense ratio, inception date, distribution info)
- Distributions
- Holdings

All data stored as JSON in raw_kurv_etf_data table.
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


# Kurv ETF Configuration
KURV_ETFS = {
    # Growth & Income (2)
    'KQQQ': {
        'name': 'Kurv Technology Titans Select ETF',
        'category': 'Growth & Income',
        'url': 'https://www.kurvinvest.com/kqqq'
    },
    'KYLD': {
        'name': 'Kurv High Income ETF',
        'category': 'Growth & Income',
        'url': 'https://www.kurvinvest.com/kyld'
    },

    # Precious Metals Income (2)
    'KGLD': {
        'name': 'Kurv Gold Enhanced Income ETF',
        'category': 'Precious Metals Income',
        'url': 'https://www.kurvinvest.com/kgld'
    },
    'KSLV': {
        'name': 'Kurv Silver Enhanced Income ETF',
        'category': 'Precious Metals Income',
        'url': 'https://www.kurvinvest.com/kslv'
    },

    # Single Stock Income - Yield Premium Strategy (6)
    'AAPY': {
        'name': 'Kurv Yield Premium Strategy Apple (AAPL) ETF',
        'category': 'Single Stock Income',
        'url': 'https://www.kurvinvest.com/aapy'
    },
    'AMZP': {
        'name': 'Kurv Yield Premium Strategy Amazon (AMZN) ETF',
        'category': 'Single Stock Income',
        'url': 'https://www.kurvinvest.com/amzp'
    },
    'GOOP': {
        'name': 'Kurv Yield Premium Strategy Google (GOOGL) ETF',
        'category': 'Single Stock Income',
        'url': 'https://www.kurvinvest.com/goop'
    },
    'MSFY': {
        'name': 'Kurv Yield Premium Strategy Microsoft (MSFT) ETF',
        'category': 'Single Stock Income',
        'url': 'https://www.kurvinvest.com/msfy'
    },
    'NFLP': {
        'name': 'Kurv Yield Premium Strategy Netflix (NFLX) ETF',
        'category': 'Single Stock Income',
        'url': 'https://www.kurvinvest.com/nflp'
    },
    'TSLP': {
        'name': 'Kurv Yield Premium Strategy Tesla (TSLA) ETF',
        'category': 'Single Stock Income',
        'url': 'https://www.kurvinvest.com/tslp'
    }
}


class KurvScraper:
    """Scraper for Kurv ETF data"""

    def __init__(self, ticker: str, fund_name: str, url: str, category: str = None):
        """
        Initialize the scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            url: Kurv ETF page URL
            category: ETF category (Growth & Income, Precious Metals Income, etc.)
        """
        self.ticker = ticker
        self.fund_name = fund_name
        self.url = url
        self.category = category

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
                'distribution_rate': self._extract_distribution_rate(soup),
                'distribution_frequency': self._extract_distribution_frequency(soup),
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
        """Extract expense ratio using snapshot-value pattern"""
        try:
            keywords = ['expense ratio', 'net expense ratio', 'total expense ratio', 'gross expense']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for i, div in enumerate(all_divs):
                text = div.get_text(strip=True).lower()

                if any(keyword in text for keyword in keywords):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        validated = self._validate_numeric_field(value, 'expense_ratio')
                        if validated:
                            logger.info(f"✅ Extracted expense ratio: {validated}")
                            return validated

            # Fallback: Search in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            validated = self._validate_numeric_field(value, 'expense_ratio')
                            if validated:
                                logger.info(f"✅ Extracted expense ratio: {validated}")
                                return validated

            logger.warning("⚠️  No expense ratio found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting expense ratio: {e}")
            return None

    def _extract_inception_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract fund inception date with normalization using snapshot-value pattern"""
        try:
            keywords = ['inception date', 'inception', 'launch date', 'commenced', 'fund inception']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True).lower()

                if any(keyword in text for keyword in keywords):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        normalized = self._normalize_date(value)
                        if normalized:
                            logger.info(f"✅ Extracted inception date: {normalized}")
                            return normalized

            # Fallback: Search in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            normalized = self._normalize_date(value)
                            if normalized:
                                logger.info(f"✅ Extracted inception date: {normalized}")
                                return normalized

            logger.warning("⚠️  No inception date found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting inception date: {e}")
            return None

    def _extract_distribution_rate(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract distribution rate using snapshot-value pattern"""
        try:
            keywords = ['distribution rate', '30-day distribution rate', 'distribution yield', 'current distribution', '30 day distribution']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True).lower()

                if any(keyword in text for keyword in keywords):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        validated = self._validate_numeric_field(value, 'distribution_rate')
                        if validated:
                            logger.info(f"✅ Extracted distribution rate: {validated}")
                            return validated

            # Fallback: Search in tables
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

    def _extract_distribution_frequency(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract distribution frequency using snapshot-value pattern"""
        try:
            keywords = ['distribution frequency', 'dividend frequency', 'frequency', 'distribution schedule']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True).lower()

                if any(keyword in text for keyword in keywords):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        logger.info(f"✅ Extracted distribution frequency: {value}")
                        return value

            # Fallback: Search in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[1].get_text(strip=True)

                        if any(keyword in label for keyword in keywords):
                            logger.info(f"✅ Extracted distribution frequency: {value}")
                            return value

            # Check for common frequency terms in text
            page_text = soup.get_text().lower()
            frequency_terms = ['weekly', 'monthly', 'quarterly', 'annually', 'daily']
            for term in frequency_terms:
                if f'{term} distribution' in page_text or f'distributed {term}' in page_text:
                    logger.info(f"✅ Extracted distribution frequency: {term.capitalize()}")
                    return term.capitalize()

            logger.warning("⚠️  No distribution frequency found")
            return None

        except Exception as e:
            logger.error(f"❌ Error extracting distribution frequency: {e}")
            return None

    def _extract_sec_yield(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract 30-day SEC yield using snapshot-value pattern"""
        try:
            keywords = ['30-day sec yield', 'sec yield', '30 day sec yield', 'sec 30-day', '30-day sec', '30 day sec']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True).lower()

                if any(keyword in text for keyword in keywords):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        validated = self._validate_numeric_field(value, 'sec_yield_30day')
                        if validated:
                            logger.info(f"✅ Extracted 30-day SEC yield: {validated}")
                            return validated

            # Fallback: Search in tables
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
        """Extract NAV (Net Asset Value) using snapshot-value pattern"""
        try:
            keywords = ['nav', 'net asset value', 'net asset val']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True).lower()

                # Use exact match for "nav" to avoid false positives
                if text == 'nav' or any(keyword in text for keyword in keywords[1:]):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        validated = self._validate_numeric_field(value, 'nav')
                        if validated:
                            logger.info(f"✅ Extracted NAV: {validated}")
                            return validated

            # Fallback: Search in tables
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
        """Extract market price using snapshot-value pattern"""
        try:
            keywords = ['market price', 'closing price', 'last price', 'close price']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True).lower()

                if any(keyword in text for keyword in keywords):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        validated = self._validate_numeric_field(value, 'market_price')
                        if validated:
                            logger.info(f"✅ Extracted market price: {validated}")
                            return validated

            # Fallback: Search in tables
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
        """Extract premium/discount to NAV using snapshot-value pattern"""
        try:
            keywords = ['premium/discount', 'premium discount', 'premium / discount', 'prem/disc', 'premium or discount']

            # Search for divs containing keyword text, followed by snapshot-value
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True).lower()

                if any(keyword in text for keyword in keywords):
                    # Look for next sibling div with class="snapshot-value"
                    next_sibling = div.find_next_sibling('div')
                    if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                        value = next_sibling.get_text(strip=True)
                        validated = self._validate_numeric_field(value, 'premium_discount')
                        if validated:
                            logger.info(f"✅ Extracted premium/discount: {validated}")
                            return validated

            # Fallback: Search in tables
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
        """Extract fund details as key-value pairs using snapshot-value pattern"""
        try:
            fund_details = {}

            # Extract all label-value pairs using snapshot-value pattern
            all_divs = soup.find_all('div')
            for div in all_divs:
                text = div.get_text(strip=True)

                # Skip empty divs
                if not text:
                    continue

                # Look for next sibling div with class="snapshot-value"
                next_sibling = div.find_next_sibling('div')
                if next_sibling and 'snapshot-value' in next_sibling.get('class', []):
                    key = text
                    value = next_sibling.get_text(strip=True)
                    if key and value:
                        fund_details[key] = value

            # Also check tables for useful info
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
        Extract distributions data from Kurv website

        Note: Kurv uses div-based tables (not HTML <table> elements)
        Structure: H3 "Distributions" heading followed by div-based table
        """
        try:
            distributions = []

            # Method 1: Look for traditional HTML tables first
            dist_table = soup.find('table', id='table-distribution')
            if not dist_table:
                dist_table = soup.find('table', class_=re.compile(r'distribution'))

            if dist_table:
                headers = dist_table.find_all('th')
                if headers:
                    header_cols = [h.get_text(strip=True) for h in headers]
                    rows = dist_table.find_all('tr')[1:]

                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= len(header_cols):
                            distribution_data = {}
                            for i, cell in enumerate(cells):
                                if i < len(header_cols):
                                    distribution_data[header_cols[i]] = cell.get_text(strip=True)
                            if distribution_data:
                                distributions.append(distribution_data)

            # Method 2: Look for Kurv-specific div-based tables
            if not distributions:
                logger.info("🔍 Looking for Kurv div-based distribution table...")

                # Find "Distributions" heading (not the "Distribution Rate" or "Notification" headings)
                dist_heading = None
                for h in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                    heading_text = h.get_text(strip=True).lower()
                    if heading_text == 'distributions' or (
                        'distribution' in heading_text and
                        'rate' not in heading_text and
                        'notification' not in heading_text
                    ):
                        dist_heading = h
                        logger.info(f"📍 Found distributions heading: {h.get_text(strip=True)}")
                        break

                if dist_heading:
                    # Search for div-based table after the heading
                    # Look through next siblings for table-like divs
                    current = dist_heading.find_next()

                    for _ in range(30):  # Search next 30 elements
                        if not current:
                            break

                        if current.name == 'div':
                            classes = current.get('class', [])
                            class_str = ' '.join(classes).lower()

                            # Look for divs that might contain table data
                            if any(keyword in class_str for keyword in ['table', 'data', 'grid', 'distribution']):
                                logger.info(f"📊 Found potential table div: {' '.join(classes)}")

                                # Try to extract rows from this div structure
                                # Look for child divs that might be rows
                                rows = current.find_all('div', recursive=True, limit=100)

                                # Filter for row-like divs
                                row_candidates = []
                                for row_div in rows:
                                    row_text = row_div.get_text(strip=True, separator='|')
                                    # Check if this looks like a data row (has dates and/or dollar amounts)
                                    if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', row_text) and len(row_text) > 10:
                                        row_candidates.append(row_div)

                                if row_candidates:
                                    logger.info(f"✅ Found {len(row_candidates)} potential distribution rows")

                                    # Check if this is a Webflow dynamic list (w-dyn-list) structure
                                    # These have ALL data concatenated in ONE div with pattern: Declaration, Ex-Div, Record, Payable, Amount (repeating)
                                    for row_div in row_candidates[:50]:  # Limit to 50 rows
                                        row_classes = ' '.join(row_div.get('class', [])).lower()

                                        # Detect w-dyn-list structure
                                        if 'w-dyn-list' in row_classes or 'table-rows-distributions' in row_classes:
                                            logger.info(f"📝 Detected Webflow dynamic list structure")

                                            # For w-dyn-list, all data is in one concatenated string
                                            # Pattern: Declaration | Ex-Div | Record | Payable | Amount | Declaration | Ex-Div | ...
                                            text = row_div.get_text(strip=True, separator='|')
                                            parts = [p.strip() for p in text.split('|') if p.strip()]

                                            # Filter out header text
                                            header_keywords = ['declaration date', 'ex-dividend date', 'record date', 'payable date', '$ per share']
                                            parts = [p for p in parts if p.lower() not in header_keywords]

                                            logger.info(f"📊 Found {len(parts)} data fields in dynamic list")

                                            # Chunk into groups of 5 (Declaration, Ex-Div, Record, Payable, Amount)
                                            for i in range(0, len(parts), 5):
                                                if i + 4 < len(parts):
                                                    dist_record = {
                                                        'Declaration Date': parts[i],
                                                        'Ex-Dividend Date': parts[i + 1],
                                                        'Record Date': parts[i + 2],
                                                        'Payable Date': parts[i + 3],
                                                        '$ per Share': parts[i + 4]
                                                    }
                                                    distributions.append(dist_record)

                                            logger.info(f"✅ Extracted {len(distributions)} distributions from dynamic list")
                                            break  # Stop after processing the dynamic list

                                        else:
                                            # Regular row-by-row parsing for non-dynamic lists
                                            text = row_div.get_text(strip=True, separator='|')
                                            parts = [p.strip() for p in text.split('|') if p.strip()]

                                            # Look for date patterns and dollar amounts
                                            dates = [p for p in parts if re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}$', p)]
                                            amounts = [p for p in parts if re.match(r'^\$?\d+\.\d{2,4}$', p) or p == '--']

                                            if len(dates) >= 3 or (dates and amounts):  # At least 3 dates or some dates + amounts
                                                dist_record = {}

                                                # Try to map to standard fields
                                                if len(dates) >= 4:
                                                    dist_record['Declaration Date'] = dates[0] if len(dates) > 0 else ''
                                                    dist_record['Ex-Dividend Date'] = dates[1] if len(dates) > 1 else ''
                                                    dist_record['Record Date'] = dates[2] if len(dates) > 2 else ''
                                                    dist_record['Payable Date'] = dates[3] if len(dates) > 3 else ''
                                                elif len(dates) == 3:
                                                    dist_record['Ex-Dividend Date'] = dates[0]
                                                    dist_record['Record Date'] = dates[1]
                                                    dist_record['Payable Date'] = dates[2]

                                                if amounts:
                                                    dist_record['$ per Share'] = amounts[0]

                                                if dist_record:
                                                    distributions.append(dist_record)

                                    if distributions:
                                        break

                        current = current.find_next()

            # Method 3: Fallback for traditional tables with keywords
            if not distributions:
                tables = soup.find_all('table')
                for table in tables:
                    headers = table.find_all('th')
                    if not headers:
                        first_row = table.find('tr')
                        if first_row:
                            headers = first_row.find_all('td')

                    if not headers:
                        continue

                    header_text = ' '.join([h.get_text(strip=True).lower() for h in headers])

                    if any(keyword in header_text for keyword in [
                        'distribution', 'dividend', 'payment', 'ex-date', 'ex-dividend',
                        'record date', 'payable', 'declaration', '$ per share'
                    ]):
                        header_cols = [h.get_text(strip=True) for h in headers]
                        rows = table.find_all('tr')[1:]

                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= len(header_cols):
                                distribution_data = {}
                                for i, cell in enumerate(cells):
                                    if i < len(header_cols):
                                        distribution_data[header_cols[i]] = cell.get_text(strip=True)

                                if distribution_data and any(v and v.strip() for v in distribution_data.values()):
                                    distributions.append(distribution_data)

                        if distributions:
                            break

            if distributions:
                logger.info(f"✅ Extracted distributions: {len(distributions)} records")
                return distributions

            logger.warning("⚠️  No distributions found")
            return []

        except Exception as e:
            logger.error(f"❌ Error extracting distributions: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_holdings(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """Extract fund holdings (top 10)"""
        try:
            holdings = []

            # Look for holdings table (id="table-top-holdings")
            holdings_table = soup.find('table', id='table-top-holdings')
            if not holdings_table:
                holdings_table = soup.find('table', class_=re.compile(r'holding'))

            if holdings_table:
                headers = holdings_table.find_all('th')
                if headers:
                    # Extract headers
                    header_cols = [h.get_text(strip=True) for h in headers]

                    # Extract rows (limit to top 10)
                    rows = holdings_table.find_all('tr')[1:]  # Skip header row

                    for i, row in enumerate(rows[:10]):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            holding_data = {}
                            for j, cell in enumerate(cells):
                                if j < len(header_cols):
                                    holding_data[header_cols[j]] = cell.get_text(strip=True)

                            if holding_data:
                                holdings.append(holding_data)

            # Fallback: Look for any table with holdings keywords
            if not holdings:
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
                'distribution_rate': data.get('distribution_rate'),
                'distribution_frequency': data.get('distribution_frequency'),
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
            result = supabase_upsert('raw_kurv_etf_data', [record])

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
    Scrape a single Kurv ETF

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if successful, False otherwise
    """
    if ticker not in KURV_ETFS:
        logger.error(f"❌ Unknown ticker: {ticker}")
        logger.info(f"Available tickers: {', '.join(KURV_ETFS.keys())}")
        return False

    etf_info = KURV_ETFS[ticker]
    scraper = KurvScraper(
        ticker,
        etf_info['name'],
        etf_info['url'],
        etf_info.get('category')
    )

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
    print(f"  • Distribution Rate: {data.get('distribution_rate') or '❌'}")
    print(f"  • Distribution Frequency: {data.get('distribution_frequency') or '❌'}")
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

    for ticker, info in KURV_ETFS.items():
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
        print(f"✅ All {len(KURV_ETFS)} ETF URLs validated successfully!")
        print()

    return validation_results


def scrape_all_etfs(delay: int = 5, skip_validation: bool = False) -> Dict[str, bool]:
    """
    Scrape all Kurv ETFs

    Args:
        delay: Seconds to wait between requests (default: 5)
        skip_validation: Skip URL validation step (default: False)

    Returns:
        Dictionary mapping ticker to success status
    """
    # Validate URLs first unless skipped
    valid_tickers = list(KURV_ETFS.keys())
    if not skip_validation:
        validation_results = validate_etf_urls()
        valid_tickers = [ticker for ticker, is_valid in validation_results.items() if is_valid]

        if len(valid_tickers) < len(KURV_ETFS):
            invalid_count = len(KURV_ETFS) - len(valid_tickers)
            print(f"⏭️  Skipping {invalid_count} invalid ticker(s)")
            print()

    results = {}

    print(f"🚀 Scraping {len(valid_tickers)} Kurv ETFs...")
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
    parser = argparse.ArgumentParser(description='Scrape Kurv ETF data')
    parser.add_argument('--ticker', '-t', type=str, help='Specific ticker to scrape (e.g., KQQQ)')
    parser.add_argument('--all', '-a', action='store_true', help='Scrape all Kurv ETFs')
    parser.add_argument('--list', '-l', action='store_true', help='List available tickers')
    parser.add_argument('--delay', '-d', type=int, default=5,
                       help='Delay in seconds between requests when scraping all (default: 5)')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip URL validation before scraping (faster but may fail on invalid URLs)')

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 Kurv ETF Scraper")
    print("=" * 80)
    print()

    # List available tickers
    if args.list:
        print(f"Available Kurv ETFs ({len(KURV_ETFS)}):")
        print()

        # Group by category
        categories = {}
        for ticker, info in KURV_ETFS.items():
            category = info.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append((ticker, info['name']))

        for category in ['Growth & Income', 'Precious Metals Income', 'Single Stock Income', 'Other']:
            if category in categories:
                print(f"{category} ({len(categories[category])}):")
                for ticker, name in sorted(categories[category]):
                    print(f"  {ticker:8s} - {name}")
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
