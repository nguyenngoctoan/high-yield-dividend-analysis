#!/usr/bin/env python3
"""
Global X Canada ETF Web Scraper
================================

Scrapes ETF data from Global X Canada website (https://www.globalx.ca/)

Data Fields Extracted:
- Basic Info: Ticker, Name, CUSIP, Inception Date
- Pricing: NAV, Market Price, Premium/Discount
- Metrics: Distribution Yield, MER, Management Fee, TER, Net Assets
- Distributions: Frequency, Most Recent Amount, 12-Month Trailing Yield
- Holdings: Top 10 holdings with weights
- Performance: Annualized returns (1mo, 3mo, 6mo, YTD, 1yr, 3yr, 5yr, 10yr, SI)
- Calendar Returns: Annual returns by year
- Distribution History: Full payment history with dates and amounts

Usage:
    python globalx_canada_scraper.py --ticker ENCC
    python globalx_canada_scraper.py --all
    python globalx_canada_scraper.py --category "Covered Call - Index"
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import time
import argparse


# Import ticker list from discovery file
from globalx_canada_discovery import ALL_TICKERS, CATEGORIES, get_etf_url


class GlobalXCanadaScraper:
    """Scraper for Global X Canada ETF data"""

    def __init__(self, delay: float = 1.0):
        """
        Initialize scraper

        Args:
            delay: Delay between requests in seconds (be respectful)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def _parse_percentage(self, text: str) -> Optional[float]:
        """Extract percentage value from text"""
        if not text:
            return None
        match = re.search(r'([-+]?\d+\.?\d*)%?', text.replace(',', ''))
        return float(match.group(1)) if match else None

    def _parse_currency(self, text: str) -> Optional[float]:
        """Extract currency value from text"""
        if not text:
            return None
        # Remove $, commas, and extract number
        match = re.search(r'\$?([-+]?\d+(?:,\d{3})*(?:\.\d+)?)', text.replace(',', ''))
        return float(match.group(1).replace(',', '')) if match else None

    def _parse_date(self, text: str) -> Optional[str]:
        """Parse date to ISO format"""
        if not text:
            return None
        try:
            # Try common formats
            for fmt in ['%B %d, %Y', '%b %d, %Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(text.strip(), fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        except Exception:
            pass
        return text.strip()

    def _extract_table_data(self, soup: BeautifulSoup, header_text: str) -> Dict[str, str]:
        """
        Extract data from a two-column table based on header text

        Args:
            soup: BeautifulSoup object
            header_text: Text to search for in headers/headings

        Returns:
            Dictionary of label: value pairs
        """
        data = {}

        # Find the section containing this header
        for header in soup.find_all(['h2', 'h3', 'h4']):
            if header_text.lower() in header.get_text().lower():
                # Look for table after this header
                table = header.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            label = cells[0].get_text(strip=True)
                            value = cells[1].get_text(strip=True)
                            data[label] = value
                break

        return data

    def scrape_etf(self, ticker: str) -> Dict[str, Any]:
        """
        Scrape complete ETF data for a given ticker

        Args:
            ticker: ETF ticker symbol

        Returns:
            Dictionary containing all ETF data
        """
        url = get_etf_url(ticker)
        print(f"Scraping {ticker} from {url}...")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching {ticker}: {e}")
            return {"ticker": ticker, "error": str(e)}

        soup = BeautifulSoup(response.content, 'html.parser')

        # Initialize data structure
        etf_data = {
            "ticker": ticker,
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "basic_info": {},
            "pricing": {},
            "metrics": {},
            "distributions": {},
            "holdings": [],
            "performance": {},
            "calendar_returns": {},
            "distribution_history": []
        }

        # Extract basic info
        etf_data["basic_info"] = self._extract_basic_info(soup)

        # Extract fund details table
        fund_details = self._extract_table_data(soup, "fund details")
        etf_data["basic_info"].update(fund_details)

        # Extract pricing (NAV, Price from top section)
        etf_data["pricing"] = self._extract_pricing(soup)

        # Extract metrics
        etf_data["metrics"] = self._extract_metrics(soup, fund_details)

        # Extract distribution info
        etf_data["distributions"] = self._extract_distributions(soup, fund_details)

        # Extract holdings
        etf_data["holdings"] = self._extract_holdings(soup)

        # Extract performance
        etf_data["performance"] = self._extract_performance(soup)

        # Extract calendar returns
        etf_data["calendar_returns"] = self._extract_calendar_returns(soup)

        # Extract distribution history
        etf_data["distribution_history"] = self._extract_distribution_history(soup)

        # Add delay before next request
        time.sleep(self.delay)

        return etf_data

    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract basic fund information"""
        info = {}

        # Product name - usually in h1 or prominent header
        h1 = soup.find('h1')
        if h1:
            info['name'] = h1.get_text(strip=True)

        # Try to find ticker in page
        # Often shown near the top or in a specific div
        ticker_patterns = [r'Ticker:\s*([A-Z]+\.?[A-Z]*)', r'Symbol:\s*([A-Z]+\.?[A-Z]*)']
        page_text = soup.get_text()
        for pattern in ticker_patterns:
            match = re.search(pattern, page_text)
            if match:
                info['ticker'] = match.group(1)
                break

        return info

    def _extract_pricing(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract NAV and pricing information"""
        pricing = {}

        # NAV is typically shown prominently at top
        # Look for text containing "NAV" followed by a price
        text = soup.get_text()
        nav_match = re.search(r'NAV[:\s]+\$?([\d,]+\.?\d*)', text)
        if nav_match:
            pricing['nav'] = self._parse_currency(nav_match.group(1))

        # Price
        price_match = re.search(r'Price[:\s]+\$?([\d,]+\.?\d*)', text)
        if price_match:
            pricing['price'] = self._parse_currency(price_match.group(1))

        # Date (as of)
        date_match = re.search(r'as of\s+([A-Z][a-z]+\s+\d{1,2},\s+\d{4})', text)
        if date_match:
            pricing['as_of_date'] = self._parse_date(date_match.group(1))

        return pricing

    def _extract_metrics(self, soup: BeautifulSoup, fund_details: Dict[str, str]) -> Dict[str, Any]:
        """Extract key metrics (MER, fees, AUM, etc.)"""
        metrics = {}

        # Parse from fund details table
        if 'Management Fee' in fund_details:
            metrics['management_fee'] = self._parse_percentage(fund_details['Management Fee'])

        if 'MER' in fund_details:
            metrics['mer'] = self._parse_percentage(fund_details['MER'])

        if 'TER' in fund_details:
            metrics['ter'] = self._parse_percentage(fund_details['TER'])

        if 'Net Assets' in fund_details:
            metrics['net_assets'] = self._parse_currency(fund_details['Net Assets'])

        # Distribution yield - often shown prominently
        text = soup.get_text()
        yield_match = re.search(r'(?:Annualized\s+)?Distribution\s+Yield[:\s]+([\d.]+)%', text, re.IGNORECASE)
        if yield_match:
            metrics['distribution_yield'] = float(yield_match.group(1))

        return metrics

    def _extract_distributions(self, soup: BeautifulSoup, fund_details: Dict[str, str]) -> Dict[str, Any]:
        """Extract distribution information"""
        distributions = {}

        if 'Distribution Frequency' in fund_details:
            distributions['frequency'] = fund_details['Distribution Frequency']

        if 'Most Recent Distribution' in fund_details:
            distributions['most_recent'] = self._parse_currency(fund_details['Most Recent Distribution'])

        if '12-Month Trailing Yield' in fund_details:
            distributions['trailing_12m_yield'] = self._parse_percentage(fund_details['12-Month Trailing Yield'])

        return distributions

    def _extract_holdings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract top holdings"""
        holdings = []

        # Look for holdings table
        for header in soup.find_all(['h2', 'h3', 'h4']):
            if 'holdings' in header.get_text().lower():
                table = header.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            holding = {
                                'security': cells[0].get_text(strip=True),
                                'weight': self._parse_percentage(cells[1].get_text(strip=True))
                            }
                            holdings.append(holding)
                break

        return holdings

    def _extract_performance(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """Extract annualized performance metrics"""
        performance = {}
        periods = ['1mo', '3mo', '6mo', 'YTD', '1yr', '3yr', '5yr', '10yr', 'Since Inception']

        # Look for performance table
        for header in soup.find_all(['h2', 'h3', 'h4']):
            if 'performance' in header.get_text().lower() and 'annualized' in header.get_text().lower():
                table = header.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            period = cells[0].get_text(strip=True)
                            value = self._parse_percentage(cells[1].get_text(strip=True))
                            # Normalize period names
                            for p in periods:
                                if p.lower() in period.lower():
                                    performance[p] = value
                                    break
                break

        return performance

    def _extract_calendar_returns(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """Extract calendar year returns"""
        returns = {}

        # Look for calendar year performance table
        for header in soup.find_all(['h2', 'h3', 'h4']):
            if 'calendar' in header.get_text().lower() and 'performance' in header.get_text().lower():
                table = header.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            year = cells[0].get_text(strip=True)
                            value = self._parse_percentage(cells[1].get_text(strip=True))
                            if re.match(r'^\d{4}$', year):  # Ensure it's a year
                                returns[year] = value
                break

        return returns

    def _extract_distribution_history(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract distribution payment history"""
        history = []

        # Look for distribution history table
        for header in soup.find_all(['h2', 'h3', 'h4']):
            if 'distribution' in header.get_text().lower() and 'history' in header.get_text().lower():
                table = header.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    # Get header to map columns
                    header_row = rows[0] if rows else None
                    headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])] if header_row else []

                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:
                            payment = {}
                            for i, cell in enumerate(cells):
                                text = cell.get_text(strip=True)
                                if i < len(headers):
                                    header_name = headers[i]
                                    if 'date' in header_name:
                                        payment[header_name] = self._parse_date(text)
                                    elif 'amount' in header_name or 'payment' in header_name:
                                        payment[header_name] = self._parse_currency(text)
                                    else:
                                        payment[header_name] = text
                            if payment:
                                history.append(payment)
                break

        return history

    def scrape_all(self, tickers: List[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape all ETFs

        Args:
            tickers: List of tickers to scrape. If None, scrape all.

        Returns:
            List of ETF data dictionaries
        """
        if tickers is None:
            tickers = ALL_TICKERS

        results = []
        total = len(tickers)

        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{total}] Processing {ticker}...")
            data = self.scrape_etf(ticker)
            results.append(data)

        return results

    def scrape_category(self, category_name: str) -> List[Dict[str, Any]]:
        """
        Scrape all ETFs in a specific category

        Args:
            category_name: Name of category from CATEGORIES dict

        Returns:
            List of ETF data dictionaries
        """
        if category_name not in CATEGORIES:
            raise ValueError(f"Category '{category_name}' not found. Available: {list(CATEGORIES.keys())}")

        tickers = CATEGORIES[category_name]
        return self.scrape_all(tickers)


def main():
    parser = argparse.ArgumentParser(description='Scrape Global X Canada ETF data')
    parser.add_argument('--ticker', type=str, help='Single ticker to scrape')
    parser.add_argument('--all', action='store_true', help='Scrape all ETFs')
    parser.add_argument('--category', type=str, help='Scrape specific category')
    parser.add_argument('--output', type=str, default='globalx_etf_data.json', help='Output JSON file')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')

    args = parser.parse_args()

    scraper = GlobalXCanadaScraper(delay=args.delay)

    if args.ticker:
        # Scrape single ticker
        data = scraper.scrape_etf(args.ticker.upper())
        results = [data]
    elif args.all:
        # Scrape all ETFs
        results = scraper.scrape_all()
    elif args.category:
        # Scrape category
        results = scraper.scrape_category(args.category)
    else:
        print("Please specify --ticker, --all, or --category")
        parser.print_help()
        return

    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n\nResults saved to {args.output}")
    print(f"Total ETFs scraped: {len(results)}")


if __name__ == "__main__":
    main()
