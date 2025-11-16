#!/usr/bin/env python3
"""
Purpose Investments ETF Scraper

Scrapes ETF data from Purpose Investments website.
Data is extracted from embedded JSON in the page source.

Author: Auto-generated
Date: 2025-11-16
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PurposeETFScraper:
    """Scraper for Purpose Investments ETF data."""

    BASE_URL = "https://www.purposeinvest.com"
    INVEST_PAGE = f"{BASE_URL}/invest"
    FUND_DOCUMENTS_PAGE = f"{BASE_URL}/fund-documents"

    def __init__(self, delay: float = 1.5):
        """
        Initialize scraper.

        Args:
            delay: Delay between requests in seconds (default: 1.5)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Purpose ETF Data Aggregator (research purposes)'
        })
        self.delay = delay
        self.ticker_to_slug = {}

    def _make_request(self, url: str) -> Optional[str]:
        """
        Make HTTP request with error handling and rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if request failed
        """
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None

    def _extract_json_data(self, html: str) -> Optional[Dict]:
        """
        Extract embedded JSON data from Next.js page.

        Args:
            html: HTML content

        Returns:
            Parsed JSON data or None if extraction failed
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

            if not script_tag or not script_tag.string:
                logger.error("Could not find __NEXT_DATA__ script tag")
                return None

            data = json.loads(script_tag.string)
            return data.get('props', {}).get('pageProps', {})
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Failed to parse JSON data: {e}")
            return None

    def discover_all_tickers(self) -> List[Dict[str, str]]:
        """
        Discover all Purpose ETF tickers from the invest page.

        Returns:
            List of dictionaries with ticker, name, and category
        """
        logger.info("Discovering all Purpose ETF tickers...")

        html = self._make_request(self.INVEST_PAGE)
        if not html:
            return []

        page_data = self._extract_json_data(html)
        if not page_data:
            return []

        # Extract fund list from page data
        # Note: Structure may vary, adjust based on actual page data
        etfs = []
        try:
            # This is a placeholder - actual structure needs to be verified
            funds = page_data.get('funds', [])
            for fund in funds:
                etfs.append({
                    'ticker': fund.get('code', ''),
                    'name': fund.get('name', ''),
                    'slug': fund.get('slug', ''),
                    'category': fund.get('category', '')
                })
        except Exception as e:
            logger.error(f"Failed to extract ticker list: {e}")

        logger.info(f"Discovered {len(etfs)} ETF tickers")
        return etfs

    def get_fund_data(self, fund_slug: str) -> Optional[Dict[str, Any]]:
        """
        Get complete fund data for a single ETF.

        Args:
            fund_slug: Fund slug (e.g., 'tesla-yield-shares-purpose-etf')

        Returns:
            Dictionary with fund data or None if failed
        """
        url = f"{self.BASE_URL}/funds/{fund_slug}"
        logger.info(f"Fetching data for {fund_slug}...")

        html = self._make_request(url)
        if not html:
            return None

        page_data = self._extract_json_data(html)
        if not page_data:
            return None

        fund_data = page_data.get('fundData', {})
        if not fund_data:
            logger.error(f"No fundData found for {fund_slug}")
            return None

        return self._parse_fund_data(fund_data)

    def _parse_fund_data(self, fund_data: Dict) -> Dict[str, Any]:
        """
        Parse fund data into structured format.

        Args:
            fund_data: Raw fund data from JSON

        Returns:
            Structured fund data dictionary
        """
        # Extract basic info
        ticker = fund_data.get('code', '')
        name = fund_data.get('name', '')

        # Get ETF series details (most common series)
        series = 'ETF'
        details = fund_data.get('details', {}).get(series, [{}])[0]

        # Extract key metrics
        parsed_data = {
            'ticker': ticker,
            'name': name,
            'series': series,
            'nav': details.get('nav'),
            'current_yield': details.get('current_yield'),
            'aum': details.get('aum', {}).get('cad'),
            'mgmt_fee': details.get('mgmt_fee'),
            'mer': details.get('mer'),
            'fund_structure': details.get('fund_structure'),
            'cusip': details.get('cusip'),
            'exchange': details.get('exchange'),
            'distribution_frequency': details.get('distribution_frequency'),
            'currency_hedged': details.get('curr_hedged'),
            'settlement': details.get('settlement_date'),
            'scraped_at': datetime.now().isoformat()
        }

        # Add fixed income specific fields if available
        if details.get('duration'):
            parsed_data['duration'] = details.get('duration')
            parsed_data['coupon'] = details.get('coupon')
            parsed_data['maturity_yield'] = details.get('maturity_yield')

        # Extract portfolio data
        portfolio = fund_data.get('portfolio', {})
        if portfolio:
            parsed_data['portfolio'] = self._parse_portfolio(portfolio)

        # Extract distribution data
        distributions = fund_data.get('distributions', {}).get(series, [])
        if distributions:
            parsed_data['latest_distribution'] = distributions[0] if distributions else None
            parsed_data['distribution_history'] = distributions

        # Extract eligibilities
        eligibilities = fund_data.get('eligibilities', {}).get(series, {})
        parsed_data['eligibilities'] = eligibilities

        # Extract returns data
        returns = fund_data.get('returns', {}).get(series, {})
        if returns:
            # Get latest NAV and historical data
            sorted_dates = sorted(returns.keys(), reverse=True)
            if sorted_dates:
                parsed_data['latest_nav_date'] = sorted_dates[0]
                parsed_data['historical_returns'] = {
                    'count': len(returns),
                    'inception_date': min(returns.keys()),
                    'latest_date': sorted_dates[0]
                }

        return parsed_data

    def _parse_portfolio(self, portfolio: Dict) -> Dict:
        """
        Parse portfolio holdings and allocation data.

        Args:
            portfolio: Raw portfolio data

        Returns:
            Structured portfolio dictionary
        """
        parsed = {
            'date': portfolio.get('dt'),
            'asset_allocation': {},
            'sector_allocation': {},
            'top_holdings': []
        }

        # Level 1: Asset class breakdown
        level1 = portfolio.get('Level1', {})
        if 'asset_class' in level1:
            parsed['asset_allocation'] = level1['asset_class']

        # Level 2: Sector/credit profile
        level2 = portfolio.get('Level2', {})
        if 'sector' in level2:
            parsed['sector_allocation'] = level2['sector']
        if 'credit_profile' in level2:
            parsed['credit_profile'] = level2['credit_profile']

        # Yield Shares specific: option statistics
        if 'portfolio_stats_options' in level2:
            parsed['option_statistics'] = level2['portfolio_stats_options']

        # Level 4: Individual holdings
        level4 = portfolio.get('Level4', {})
        if 'holdings' in level4:
            holdings = level4['holdings']
            parsed['top_holdings'] = [
                {
                    'name': h.get('name'),
                    'weight': h.get('weight'),
                    'yield': h.get('yield')
                }
                for h in holdings[:10]  # Top 10 holdings
            ]

        return parsed

    def scrape_all_etfs(self, tickers: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Scrape data for all Purpose ETFs.

        Args:
            tickers: List of ticker dictionaries. If None, will discover automatically.

        Returns:
            List of fund data dictionaries
        """
        if tickers is None:
            tickers = self.discover_all_tickers()

        all_data = []
        total = len(tickers)

        for idx, ticker_info in enumerate(tickers, 1):
            slug = ticker_info.get('slug')
            ticker = ticker_info.get('ticker')

            if not slug:
                logger.warning(f"No slug found for ticker {ticker}, skipping")
                continue

            logger.info(f"Processing {ticker} ({idx}/{total})...")

            fund_data = self.get_fund_data(slug)
            if fund_data:
                all_data.append(fund_data)
            else:
                logger.error(f"Failed to get data for {ticker}")

        logger.info(f"Successfully scraped {len(all_data)}/{total} ETFs")
        return all_data

    def get_etf_by_ticker(self, ticker: str, slug: str) -> Optional[Dict]:
        """
        Get ETF data by ticker symbol.

        Args:
            ticker: ETF ticker symbol (e.g., 'YTSL')
            slug: Fund slug (e.g., 'tesla-yield-shares-purpose-etf')

        Returns:
            Fund data dictionary or None if failed
        """
        return self.get_fund_data(slug)


# Known ticker to slug mappings
TICKER_SLUG_MAP = {
    # Yield Shares - US Tech
    'MSFY': 'microsoft-yield-shares-purpose-etf',
    'YTSL': 'tesla-yield-shares-purpose-etf',
    'APLY': 'apple-yield-shares-purpose-etf',
    'YNVD': 'nvidia-yield-shares-purpose-etf',
    'YGOG': 'alphabet-yield-shares-purpose-etf',
    'YMET': 'meta-yield-shares-purpose-etf',
    'YAMD': 'amd-yield-shares-purpose-etf',
    'YAMZ': 'amazon-yield-shares-purpose-etf',
    'BRKY': 'berkshire-hathaway-yield-shares-purpose-etf',
    'YCST': 'costco-yield-shares-purpose-etf',
    'YNET': 'netflix-yield-shares-purpose-etf',
    'YAVG': 'broadcom-yield-shares-purpose-etf',
    'YCON': 'coinbase-yield-shares-purpose-etf',
    'YUNH': 'unitedhealth-group-yield-shares-purpose-etf',
    'YPLT': 'palantir-yield-shares-purpose-etf',
    'YMAG': 'tech-innovators-yield-shares-purpose-etf',

    # Yield Shares - Canadian
    'TDY': 'purpose-td-yield-shares-etf',
    'CNQY': 'canadian-natural-resources-yield-shares-purpose-etf',
    'BNSY': 'scotiabank-yield-shares-purpose-etf',
    'RBCY': 'rbc-yield-shares-purpose-etf',
    'ATDY': 'couche-tard-yield-shares-purpose-etf',
    'DOLY': 'dollarama-yield-shares-purpose-etf',
    'SHPY': 'shopify-yield-shares-purpose-etf',
    'ENBY': 'enbridge-yield-shares-purpose-etf',
    'BNY': 'brookfield-yield-shares-purpose-etf',
    'TY': 'telus-yield-shares-purpose-etf',

    # Cryptocurrency
    'BTCC': 'purpose-bitcoin-etf',
    'ETHH': 'purpose-ether-etf',
    'ETHY': 'purpose-ether-yield-etf',
    'BTCY': 'purpose-bitcoin-yield-etf',
    'XRPP': 'purpose-xrp-etf',
    'SOLL': 'purpose-solana-etf',

    # Fixed Income
    'RPS': 'purpose-canadian-preferred-share-fund',
    'BND': 'purpose-global-bond-fund',
    'SYLD': 'purpose-strategic-yield-fund',

    # Commodities
    'KILO': 'purpose-gold-bullion-fund',
    'SBT': 'purpose-silver-bullion-fund',

    # Add more mappings as needed...
}


def main():
    """Main execution function."""
    scraper = PurposeETFScraper(delay=1.5)

    # Example 1: Get single ETF data
    logger.info("Example 1: Fetching single ETF (YTSL)")
    ytsl_data = scraper.get_etf_by_ticker('YTSL', TICKER_SLUG_MAP['YTSL'])
    if ytsl_data:
        print(json.dumps(ytsl_data, indent=2))

    # Example 2: Get multiple ETFs
    logger.info("\nExample 2: Fetching multiple ETFs")
    sample_tickers = [
        {'ticker': 'YTSL', 'slug': TICKER_SLUG_MAP['YTSL']},
        {'ticker': 'BTCC', 'slug': TICKER_SLUG_MAP['BTCC']},
        {'ticker': 'RPS', 'slug': TICKER_SLUG_MAP['RPS']},
    ]
    all_data = scraper.scrape_all_etfs(sample_tickers)
    print(f"\nScraped {len(all_data)} ETFs successfully")

    # Save to file
    output_file = 'purpose_etf_data.json'
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)
    logger.info(f"Data saved to {output_file}")


if __name__ == '__main__':
    main()
