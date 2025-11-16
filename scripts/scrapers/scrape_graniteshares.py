#!/usr/bin/env python3
"""
GraniteShares ETF Scraper

This script scrapes ETF data from GraniteShares website including:
- Complete list of all 59 ETFs
- Individual ETF details (NAV, distributions, holdings, performance)
- Distribution history
- Holdings data

Usage:
    python scrape_graniteshares.py --mode list    # Get all ETF tickers
    python scrape_graniteshares.py --mode detail --ticker TQQY  # Get specific ETF details
    python scrape_graniteshares.py --mode all     # Get all data for all ETFs

Requirements:
    pip install selenium beautifulsoup4 lxml
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import argparse
from typing import Dict, List, Optional
from datetime import datetime


class GraniteSharesScraper:
    """Scraper for GraniteShares ETF data"""

    BASE_URL = "https://graniteshares.com/institutional/us/en-us/etfs/"

    def __init__(self, headless: bool = True):
        """Initialize scraper with Chrome driver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait_time = 5  # seconds to wait for JS to load

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def get_all_etfs(self) -> List[Dict]:
        """
        Scrape the main ETF listing page to get all ETFs with basic info

        Returns:
            List of dicts containing ETF data:
            {
                'ticker': str,
                'name': str,
                'description': str,
                'type': str,  # category
                'underlying': str,
                'leverage': str,
                'nav': str,
                'aum': str,
                'daily_change': str,
                'url': str
            }
        """
        print(f"Fetching ETF list from {self.BASE_URL}")
        self.driver.get(self.BASE_URL)
        time.sleep(self.wait_time)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Find all ticker cells
        ticker_cells = soup.find_all('span', class_='etf-table-cell--ticker__symbol')
        etfs = []

        print(f"Found {len(ticker_cells)} ETFs")

        for ticker_elem in ticker_cells:
            ticker = ticker_elem.get_text(strip=True)

            # Find parent span with data attributes
            parent = ticker_elem.find_parent('span', class_='etf-table-cell--ticker')
            if not parent:
                continue

            data_id = parent.get('data-id', '')
            data_type = parent.get('data-type', '')
            data_underlying = parent.get('data-underlying', '')
            data_leverage = parent.get('data-leverage', '')

            # Find the name cell (same data-id)
            name_cell = soup.find('span', class_='etf-table-cell--name', attrs={'data-id': data_id})
            name = ''
            description = ''
            if name_cell:
                name_title = name_cell.find('span', class_='etf-table-cell--name-title')
                name_desc = name_cell.find('span', class_='etf-table-cell--name-description')
                name = name_title.get_text(strip=True) if name_title else ''
                description = name_desc.get_text(strip=True) if name_desc else ''

            # Find NAV
            nav_cell = soup.find('span', class_='etf-table-cell--nav', attrs={'data-id': data_id})
            nav = nav_cell.get_text(strip=True) if nav_cell else ''

            # Find AUM
            aum = ''
            aum_cell = soup.find('span', class_='etf-table-cell--aum', attrs={'data-id': data_id})
            if aum_cell:
                aum_span = aum_cell.find('span', class_='pAum')
                aum = aum_span.get_text(strip=True) if aum_span else ''

            # Find daily change
            change = ''
            change_cell = soup.find('span', class_='etf-table-cell--change', attrs={'data-id': data_id})
            if change_cell:
                change_span = change_cell.find('span', class_='pChange')
                change = change_span.get_text(strip=True) if change_span else ''

            etf = {
                'ticker': ticker,
                'name': name,
                'description': description,
                'type': data_type,
                'underlying': data_underlying,
                'leverage': data_leverage,
                'nav': nav,
                'aum': aum,
                'daily_change': change,
                'url': f'{self.BASE_URL}{ticker.lower()}/'
            }
            etfs.append(etf)

        return sorted(etfs, key=lambda x: x['ticker'])

    def get_etf_details(self, ticker: str) -> Dict:
        """
        Scrape detailed data for a specific ETF

        Args:
            ticker: ETF ticker symbol (e.g., 'TQQY')

        Returns:
            Dict containing detailed ETF data including:
            - Basic info (name, inception date, expense ratio)
            - Current pricing (NAV, close, premium/discount)
            - Performance metrics
            - Distribution history
            - Holdings
            - Documents
        """
        url = f'{self.BASE_URL}{ticker.lower()}/'
        print(f"Fetching details for {ticker} from {url}")

        self.driver.get(url)
        time.sleep(self.wait_time)

        soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        details = {
            'ticker': ticker.upper(),
            'url': url,
            'scraped_at': datetime.now().isoformat(),
        }

        # Extract basic info
        details['basic_info'] = self._extract_basic_info(soup)

        # Extract pricing data
        details['pricing'] = self._extract_pricing(soup)

        # Extract performance
        details['performance'] = self._extract_performance(soup)

        # Extract distributions
        details['distributions'] = self._extract_distributions(soup)

        # Extract holdings
        details['holdings'] = self._extract_holdings(soup)

        return details

    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict:
        """Extract basic ETF information"""
        info = {}

        # Name from hero section
        hero = soup.find('h1')
        if hero:
            info['name'] = hero.get_text(strip=True)

        # Look for inception date
        inception = soup.find(string=lambda text: text and 'inception date' in text.lower())
        if inception:
            parent = inception.parent
            next_elem = parent.find_next_sibling()
            if next_elem:
                info['inception_date'] = next_elem.get_text(strip=True)

        # Look for expense ratio
        expense = soup.find(string=lambda text: text and 'expense ratio' in text.lower())
        if expense:
            parent = expense.parent
            next_elem = parent.find_next_sibling()
            if next_elem:
                info['expense_ratio'] = next_elem.get_text(strip=True)

        return info

    def _extract_pricing(self, soup: BeautifulSoup) -> Dict:
        """Extract current pricing data"""
        pricing = {}

        # NAV
        nav_elem = soup.find('span', class_='pNav')
        if nav_elem:
            pricing['nav'] = nav_elem.get_text(strip=True)

        # Close price
        close_elem = soup.find('span', class_='pClose')
        if close_elem:
            pricing['close'] = close_elem.get_text(strip=True)

        # Premium/Discount
        disc_elem = soup.find('span', class_='pDisc')
        if disc_elem:
            pricing['premium_discount'] = disc_elem.get_text(strip=True)

        # As-of date
        date_elem = soup.find('span', class_='pDate')
        if date_elem:
            pricing['as_of_date'] = date_elem.get_text(strip=True)

        return pricing

    def _extract_performance(self, soup: BeautifulSoup) -> Dict:
        """Extract performance metrics"""
        performance = {}

        perf_section = soup.find('div', class_='etf-chart-details_content_performance-table')
        if perf_section:
            # Get all spans - headers and values
            spans = perf_section.find_all('span', class_='Mono2')

            # Headers are typically: "All Data...", "1 Month", "3 Months", "YTD", "1 Year", "3 Years"
            # Values follow in subsequent rows
            # This is a simplified extraction - adjust based on actual structure
            performance['raw_data'] = [span.get_text(strip=True) for span in spans]

        return performance

    def _extract_distributions(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract distribution history"""
        distributions = []

        dist_section = soup.find('div', class_='etf-chart-details_content_distribution-calendar-table')
        if dist_section:
            # Get all spans
            spans = dist_section.find_all('span')

            # Parse distribution data
            # Structure: Ex Date | Record Date | Payment Date | Distribution
            # This is simplified - implement proper parsing based on actual structure
            dist_data = [span.get_text(strip=True) for span in spans if span.get_text(strip=True)]

            # Group by 4s (if that's the pattern)
            for i in range(0, len(dist_data), 4):
                if i + 3 < len(dist_data):
                    distributions.append({
                        'ex_date': dist_data[i],
                        'record_date': dist_data[i + 1],
                        'payment_date': dist_data[i + 2],
                        'amount': dist_data[i + 3]
                    })

        return distributions

    def _extract_holdings(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract fund holdings"""
        holdings = []

        holdings_section = soup.find('div', class_='etf-chart-details_content_fund-allocation-table')
        if holdings_section:
            # Look for security names
            security_names = holdings_section.find_all('span', class_='security-name')

            # Get corresponding values
            all_spans = holdings_section.find_all('span')

            # This is simplified - implement proper pairing logic
            for security in security_names:
                name = security.get_text(strip=True)
                if name:
                    holdings.append({
                        'security': name,
                        # Add share count, value, allocation parsing
                    })

        return holdings


def main():
    parser = argparse.ArgumentParser(description='Scrape GraniteShares ETF data')
    parser.add_argument('--mode', choices=['list', 'detail', 'all'], default='list',
                        help='Scraping mode: list (all ETFs), detail (single ETF), all (everything)')
    parser.add_argument('--ticker', help='Ticker symbol for detail mode')
    parser.add_argument('--output', default='graniteshares_data.json',
                        help='Output JSON file')
    parser.add_argument('--headless', action='store_true', default=True,
                        help='Run browser in headless mode')

    args = parser.parse_args()

    if args.mode == 'detail' and not args.ticker:
        parser.error('--ticker required for detail mode')

    with GraniteSharesScraper(headless=args.headless) as scraper:
        if args.mode == 'list':
            # Get all ETF tickers and basic info
            etfs = scraper.get_all_etfs()
            output = {
                'total_etfs': len(etfs),
                'scraped_at': datetime.now().isoformat(),
                'etfs': etfs
            }

        elif args.mode == 'detail':
            # Get detailed info for one ETF
            output = scraper.get_etf_details(args.ticker)

        elif args.mode == 'all':
            # Get everything
            etfs = scraper.get_all_etfs()
            detailed_data = []

            for etf in etfs:
                print(f"\nScraping details for {etf['ticker']}...")
                try:
                    details = scraper.get_etf_details(etf['ticker'])
                    detailed_data.append(details)
                    time.sleep(2)  # Be polite
                except Exception as e:
                    print(f"Error scraping {etf['ticker']}: {e}")
                    continue

            output = {
                'total_etfs': len(etfs),
                'scraped_at': datetime.now().isoformat(),
                'summary': etfs,
                'detailed_data': detailed_data
            }

        # Save to file
        with open(args.output, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✓ Data saved to {args.output}")


if __name__ == '__main__':
    main()
