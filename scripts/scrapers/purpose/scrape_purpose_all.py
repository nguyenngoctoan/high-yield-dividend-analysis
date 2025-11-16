#!/usr/bin/env python3
"""
Purpose Investments ETF Scraper (All Funds)

Scrapes comprehensive data from all 81 Purpose Investments ETF pages including:
- Fund overview and metrics
- NAV, AUM, management fees, MER
- Yield Shares option statistics
- Portfolio holdings and allocations
- Distribution history
- Performance data

Uses server-side rendered data from Next.js - NO Selenium needed!
All data extracted from embedded JSON in __NEXT_DATA__ script tag.

All data stored as JSON in raw_purpose_etf_data table.
"""

import sys
import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import time
import requests
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


# Purpose ETF Configuration (81 ETFs across 7 categories)
PURPOSE_ETFS = {
    # ========================================
    # EQUITY - Yield Shares US Tech (16 ETFs)
    # ========================================
    'MSFY': {
        'name': 'Microsoft (MSFT) Yield Shares Purpose ETF',
        'slug': 'microsoft-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Microsoft (MSFT)'
    },
    'YTSL': {
        'name': 'Tesla (TSLA) Yield Shares Purpose ETF',
        'slug': 'tesla-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Tesla (TSLA)'
    },
    'APLY': {
        'name': 'Apple (AAPL) Yield Shares Purpose ETF',
        'slug': 'apple-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Apple (AAPL)'
    },
    'YNVD': {
        'name': 'NVIDIA (NVDA) Yield Shares Purpose ETF',
        'slug': 'nvidia-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'NVIDIA (NVDA)'
    },
    'YGOG': {
        'name': 'Alphabet (GOOGL) Yield Shares Purpose ETF',
        'slug': 'alphabet-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Alphabet (GOOGL)'
    },
    'YMET': {
        'name': 'Meta (META) Yield Shares Purpose ETF',
        'slug': 'meta-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Meta (META)'
    },
    'YAMD': {
        'name': 'AMD (AMD) Yield Shares Purpose ETF',
        'slug': 'amd-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'AMD (AMD)'
    },
    'YAMZ': {
        'name': 'Amazon (AMZN) Yield Shares Purpose ETF',
        'slug': 'amazon-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Amazon (AMZN)'
    },
    'BRKY': {
        'name': 'Berkshire Hathaway (BRK) Yield Shares Purpose ETF',
        'slug': 'berkshire-hathaway-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Berkshire Hathaway (BRK)'
    },
    'YCST': {
        'name': 'Costco (COST) Yield Shares Purpose ETF',
        'slug': 'costco-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Costco (COST)'
    },
    'YNET': {
        'name': 'Netflix (NFLX) Yield Shares Purpose ETF',
        'slug': 'netflix-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Netflix (NFLX)'
    },
    'YAVG': {
        'name': 'Broadcom (AVGO) Yield Shares Purpose ETF',
        'slug': 'broadcom-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Broadcom (AVGO)'
    },
    'YCON': {
        'name': 'Coinbase (COIN) Yield Shares Purpose ETF',
        'slug': 'coinbase-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Coinbase (COIN)'
    },
    'YUNH': {
        'name': 'UnitedHealth Group (UNH) Yield Shares Purpose ETF',
        'slug': 'unitedhealth-group-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'UnitedHealth Group (UNH)'
    },
    'YPLT': {
        'name': 'Palantir (PLTR) Yield Shares Purpose ETF',
        'slug': 'palantir-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Palantir (PLTR)'
    },
    'YMAG': {
        'name': 'Tech Innovators Yield Shares Purpose ETF',
        'slug': 'tech-innovators-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares US Tech',
        'underlying': 'Tech Basket'
    },

    # ========================================
    # EQUITY - Yield Shares Canadian (10 ETFs)
    # ========================================
    'TDY': {
        'name': 'Purpose TD (TD) Yield Shares ETF',
        'slug': 'purpose-td-yield-shares-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'TD Bank (TD)'
    },
    'CNQY': {
        'name': 'Canadian Natural Resources (CNQ) Yield Shares ETF',
        'slug': 'canadian-natural-resources-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Canadian Natural Resources (CNQ)'
    },
    'BNSY': {
        'name': 'Scotiabank (BNS) Yield Shares ETF',
        'slug': 'scotiabank-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Scotiabank (BNS)'
    },
    'RBCY': {
        'name': 'RBC (RY) Yield Shares ETF',
        'slug': 'rbc-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Royal Bank (RY)'
    },
    'ATDY': {
        'name': 'Couche-Tard (ATD) Yield Shares ETF',
        'slug': 'couche-tard-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Alimentation Couche-Tard (ATD)'
    },
    'DOLY': {
        'name': 'Dollarama (DOL) Yield Shares ETF',
        'slug': 'dollarama-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Dollarama (DOL)'
    },
    'SHPY': {
        'name': 'Shopify (SHOP) Yield Shares ETF',
        'slug': 'shopify-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Shopify (SHOP)'
    },
    'ENBY': {
        'name': 'Enbridge (ENB) Yield Shares ETF',
        'slug': 'enbridge-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Enbridge (ENB)'
    },
    'BNY': {
        'name': 'Brookfield (BN) Yield Shares ETF',
        'slug': 'brookfield-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Brookfield (BN)'
    },
    'TY': {
        'name': 'Telus (T) Yield Shares ETF',
        'slug': 'telus-yield-shares-purpose-etf',
        'category': 'Equity - Yield Shares Canadian',
        'underlying': 'Telus (T)'
    },

    # ========================================
    # EQUITY - Traditional (12 ETFs)
    # ========================================
    'PBI': {
        'name': 'Purpose Best Ideas Fund',
        'slug': 'purpose-best-ideas-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'PINV': {
        'name': 'Purpose Global Innovators Fund',
        'slug': 'purpose-global-innovators-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'REDRGI': {
        'name': 'Purpose Global Resource Fund',
        'slug': 'purpose-global-resource-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'PHR': {
        'name': 'Purpose Real Estate Income Fund',
        'slug': 'purpose-real-estate-income-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'RDE': {
        'name': 'Purpose Core Equity Income Fund',
        'slug': 'purpose-core-equity-income-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'PDF': {
        'name': 'Purpose Core Dividend Fund',
        'slug': 'purpose-core-dividend-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'BNC': {
        'name': 'Purpose Canadian Financial Income Fund',
        'slug': 'purpose-canadian-financial-income-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'PDIV': {
        'name': 'Purpose Enhanced Dividend Fund',
        'slug': 'purpose-enhanced-dividend-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'PRP': {
        'name': 'Purpose Conservative Income Fund',
        'slug': 'purpose-conservative-income-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'PID': {
        'name': 'Purpose International Dividend Fund',
        'slug': 'purpose-international-dividend-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'REM': {
        'name': 'Purpose Emerging Markets Dividend Fund',
        'slug': 'purpose-emerging-markets-dividend-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },
    'RTT': {
        'name': 'Purpose Tactical Thematic Fund',
        'slug': 'purpose-tactical-thematic-fund',
        'category': 'Equity - Traditional',
        'underlying': None
    },

    # ========================================
    # FIXED INCOME (7 ETFs)
    # ========================================
    'IGB': {
        'name': 'Purpose Global Bond Class',
        'slug': 'purpose-global-bond-class',
        'category': 'Fixed Income',
        'underlying': None
    },
    'RPS': {
        'name': 'Purpose Canadian Preferred Share Fund',
        'slug': 'purpose-canadian-preferred-share-fund',
        'category': 'Fixed Income',
        'underlying': None
    },
    'SYLD': {
        'name': 'Purpose Strategic Yield Fund',
        'slug': 'purpose-strategic-yield-fund',
        'category': 'Fixed Income',
        'underlying': None
    },
    'BND': {
        'name': 'Purpose Global Bond Fund',
        'slug': 'purpose-global-bond-fund',
        'category': 'Fixed Income',
        'underlying': None
    },
    'FLX': {
        'name': 'Purpose Global Flexible Credit Fund',
        'slug': 'purpose-global-flexible-credit-fund',
        'category': 'Fixed Income',
        'underlying': None
    },
    'RPU': {
        'name': 'Purpose US Preferred Share Fund',
        'slug': 'purpose-us-preferred-share-fund',
        'category': 'Fixed Income',
        'underlying': None
    },
    'PBD': {
        'name': 'Purpose Total Return Bond Fund',
        'slug': 'purpose-total-return-bond-fund',
        'category': 'Fixed Income',
        'underlying': None
    },

    # ========================================
    # CRYPTOCURRENCY (9 ETFs - counting unique slugs)
    # ========================================
    'BTCC': {
        'name': 'Purpose Bitcoin ETF',
        'slug': 'purpose-bitcoin-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Bitcoin'
    },
    'ETHH': {
        'name': 'Purpose Ether ETF',
        'slug': 'purpose-ether-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Ethereum'
    },
    'ETHY': {
        'name': 'Purpose Ether Yield ETF',
        'slug': 'purpose-ether-yield-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Ethereum'
    },
    'BTCY': {
        'name': 'Purpose Bitcoin Yield ETF',
        'slug': 'purpose-bitcoin-yield-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Bitcoin'
    },
    'ETHO.B': {
        'name': 'Purpose Core Ether ETF',
        'slug': 'purpose-core-ether-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Ethereum'
    },
    'BTCO.B': {
        'name': 'Purpose Core Bitcoin ETF',
        'slug': 'purpose-core-bitcoin-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Bitcoin'
    },
    'XRPP': {
        'name': 'Purpose XRP ETF',
        'slug': 'purpose-xrp-etf',
        'category': 'Cryptocurrency',
        'underlying': 'XRP'
    },
    'SOLL': {
        'name': 'Purpose Solana ETF',
        'slug': 'purpose-solana-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Solana'
    },
    'ETHC.B': {
        'name': 'Purpose Ether Staking Corp. ETF',
        'slug': 'purpose-ether-staking-corp-etf',
        'category': 'Cryptocurrency',
        'underlying': 'Ethereum'
    },

    # ========================================
    # ALTERNATIVES (12 ETFs - counting unique slugs, CROP has variants)
    # ========================================
    'CROP': {
        'name': 'Purpose Credit Opportunities Fund',
        'slug': 'purpose-credit-opportunities-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PHW': {
        'name': 'Purpose International Enhanced Equity Income Fund',
        'slug': 'purpose-international-enhanced-equity-income-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PSY2': {
        'name': 'Purpose Structured Equity Yield Fund',
        'slug': 'purpose-structured-equity-yield-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PAYF': {
        'name': 'Purpose Enhanced Premium Yield Fund',
        'slug': 'purpose-enhanced-premium-yield-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PYF': {
        'name': 'Purpose Premium Yield Fund',
        'slug': 'purpose-premium-yield-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PSG': {
        'name': 'Purpose Structured Equity Growth Fund',
        'slug': 'purpose-structured-equity-growth-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PSYL': {
        'name': 'Purpose Structured Equity Yield Plus Fund',
        'slug': 'purpose-structured-equity-yield-plus-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PHE': {
        'name': 'Purpose Tactical Hedged Equity Fund',
        'slug': 'purpose-tactical-hedged-equity-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'PMM': {
        'name': 'Purpose Multi-Strategy Market Neutral Fund',
        'slug': 'purpose-multi-strategy-market-neutral-fund',
        'category': 'Alternatives',
        'underlying': None
    },
    'BNK': {
        'name': 'Big Banc Split Corp',
        'slug': 'big-banc-split-corp',
        'category': 'Alternatives',
        'underlying': None
    },

    # ========================================
    # MULTI-ASSET (8 ETFs)
    # ========================================
    'RTA': {
        'name': 'Purpose Tactical Asset Allocation Fund',
        'slug': 'purpose-tactical-asset-allocation-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },
    'PABF': {
        'name': 'Purpose Active Balanced Fund',
        'slug': 'purpose-active-balanced-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },
    'PACF': {
        'name': 'Purpose Active Conservative Fund',
        'slug': 'purpose-active-conservative-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },
    'PAGF': {
        'name': 'Purpose Active Growth Fund',
        'slug': 'purpose-active-growth-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },
    'PINC': {
        'name': 'Purpose Multi-Asset Income Fund',
        'slug': 'purpose-multi-asset-income-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },
    'PIN': {
        'name': 'Purpose Monthly Income Fund',
        'slug': 'purpose-monthly-income-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },
    'PRA': {
        'name': 'Purpose Diversified Real Asset Fund',
        'slug': 'purpose-diversified-real-asset-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },
    'LPF': {
        'name': 'Longevity Pension Fund',
        'slug': 'longevity-pension-fund',
        'category': 'Multi-Asset',
        'underlying': None
    },

    # ========================================
    # COMMODITIES (2 ETFs)
    # ========================================
    'KILO': {
        'name': 'Purpose Gold Bullion Fund',
        'slug': 'purpose-gold-bullion-fund',
        'category': 'Commodities',
        'underlying': 'Gold'
    },
    'SBT': {
        'name': 'Purpose Silver Bullion Fund',
        'slug': 'purpose-silver-bullion-fund',
        'category': 'Commodities',
        'underlying': 'Silver'
    },

    # ========================================
    # CASH MANAGEMENT (5 ETFs)
    # ========================================
    'MNY': {
        'name': 'Purpose Cash Management Fund',
        'slug': 'purpose-cash-management-fund',
        'category': 'Cash Management',
        'underlying': None
    },
    'MNU.U': {
        'name': 'Purpose USD Cash Management Fund',
        'slug': 'purpose-usd-cash-management-fund',
        'category': 'Cash Management',
        'underlying': None
    },
    'PSA': {
        'name': 'Purpose High Interest Savings Fund',
        'slug': 'purpose-high-interest-savings-fund',
        'category': 'Cash Management',
        'underlying': None
    },
    'PSU.U': {
        'name': 'Purpose US Cash Fund',
        'slug': 'purpose-us-cash-fund',
        'category': 'Cash Management',
        'underlying': None
    },
    'PMR': {
        'name': 'Purpose Premium Money Market Fund',
        'slug': 'purpose-premium-money-market-fund',
        'category': 'Cash Management',
        'underlying': None
    }
}


class PurposeScraper:
    """Scraper for Purpose Investments ETF data using embedded JSON extraction"""

    BASE_URL = "https://www.purposeinvest.com"

    def __init__(self, ticker: str, fund_name: str, slug: str, category: str = None, underlying: str = None):
        """
        Initialize the scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            slug: Fund URL slug
            category: ETF category
            underlying: Underlying security (for Yield Shares)
        """
        self.ticker = ticker
        self.fund_name = fund_name
        self.slug = slug
        self.url = f"{self.BASE_URL}/funds/{slug}"
        self.category = category
        self.underlying = underlying
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Purpose ETF Data Aggregator (research purposes)'
        })

    def scrape_data(self) -> Optional[Dict[str, Any]]:
        """
        Scrape all data from the ETF page using requests + BeautifulSoup
        NO Selenium needed - all data is server-side rendered!

        Returns:
            Dictionary containing all scraped data or None if error
        """
        try:
            logger.info(f"📊 Fetching page: {self.url}")

            # Make HTTP request
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract embedded JSON from __NEXT_DATA__ script tag
            fund_data = self._extract_next_data(soup)
            if not fund_data:
                logger.error(f"❌ Failed to extract fund data for {self.ticker}")
                return None

            # Parse fund data into structured format
            data = self._parse_fund_data(fund_data)
            data['url'] = self.url
            data['category'] = self.category

            logger.info("✅ Data extraction complete")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ HTTP request failed for {self.ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error scraping {self.ticker}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_next_data(self, soup: BeautifulSoup) -> Optional[Dict]:
        """
        Extract embedded JSON data from Next.js __NEXT_DATA__ script tag

        Args:
            soup: BeautifulSoup parsed HTML

        Returns:
            fundData object or None if extraction failed
        """
        try:
            # Find the __NEXT_DATA__ script tag
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

            if not script_tag or not script_tag.string:
                logger.error("❌ Could not find __NEXT_DATA__ script tag")
                return None

            # Parse JSON
            next_data = json.loads(script_tag.string)

            # Navigate to fundData: props.pageProps.fundData
            fund_data = (next_data
                        .get('props', {})
                        .get('pageProps', {})
                        .get('fundData', {}))

            if not fund_data:
                logger.error("❌ No fundData found in __NEXT_DATA__")
                return None

            logger.info(f"✅ Successfully extracted fundData for {fund_data.get('code', 'UNKNOWN')}")
            return fund_data

        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error extracting __NEXT_DATA__: {e}")
            return None

    def _parse_fund_data(self, fund_data: Dict) -> Dict[str, Any]:
        """
        Parse fund data from JSON into structured format

        Args:
            fund_data: Raw fund data from __NEXT_DATA__

        Returns:
            Structured fund data dictionary
        """
        # Extract basic info
        ticker = fund_data.get('code', self.ticker)
        name = fund_data.get('name', self.fund_name)

        # Get ETF series details (most common series)
        series = 'ETF'
        series_data = fund_data.get('series', {})
        details_list = fund_data.get('details', {}).get(series, [])
        details = details_list[0] if details_list else {}

        # Extract key metrics
        parsed_data = {
            'ticker': ticker,
            'fund_name': name,
            'series': series,
            'scraped_at': datetime.now().isoformat(),
            'underlying': self.underlying,

            # Core fund metrics
            'nav': self._safe_get(details, 'nav'),
            'current_yield': self._safe_get(details, 'current_yield'),
            'aum': self._safe_get_aum(details),
            'management_fee': self._safe_get(details, 'mgmt_fee'),
            'mer': self._safe_get(details, 'mer'),
            'fund_structure': self._safe_get(details, 'fund_structure'),
            'cusip': self._safe_get(details, 'cusip'),
            'exchange': self._safe_get(details, 'exchange'),
            'distribution_frequency': self._safe_get(details, 'distribution_frequency'),
            'currency_hedged': self._safe_get(details, 'curr_hedged'),
            'settlement': self._safe_get(details, 'settlement_date'),

            # Fixed income specific fields
            'duration': self._safe_get(details, 'duration'),
            'coupon': self._safe_get(details, 'coupon'),
            'maturity_yield': self._safe_get(details, 'maturity_yield'),
        }

        # Extract portfolio data (JSONB)
        portfolio = fund_data.get('portfolio', {})
        if portfolio:
            parsed_data['portfolio_data'] = self._parse_portfolio(portfolio)

        # Extract distribution data (JSONB)
        distributions = fund_data.get('distributions', {}).get(series, [])
        if distributions:
            parsed_data['distributions'] = distributions

        # Extract eligibilities (JSONB)
        eligibilities = fund_data.get('eligibilities', {}).get(series, {})
        if eligibilities:
            parsed_data['eligibilities'] = eligibilities

        # Extract returns/performance data (JSONB)
        returns = fund_data.get('returns', {}).get(series, {})
        if returns:
            sorted_dates = sorted(returns.keys(), reverse=True)
            parsed_data['performance_data'] = {
                'latest_nav_date': sorted_dates[0] if sorted_dates else None,
                'inception_date': min(returns.keys()) if returns else None,
                'total_data_points': len(returns),
                'latest_nav': returns.get(sorted_dates[0]) if sorted_dates else None
            }

        # Extract fund details (JSONB) - additional metadata
        parsed_data['fund_details'] = {
            'series_available': list(series_data.keys()),
            'code': ticker,
            'name': name
        }

        return parsed_data

    def _safe_get(self, data: Dict, key: str) -> Optional[str]:
        """Safely get value from dict and convert to string"""
        value = data.get(key)
        if value is None:
            return None
        if isinstance(value, bool):
            return value  # Return boolean as-is for BOOLEAN fields
        return str(value) if value else None

    def _safe_get_aum(self, details: Dict) -> Optional[str]:
        """Safely extract AUM (can be object or string)"""
        aum = details.get('aum')
        if aum is None:
            return None
        if isinstance(aum, dict):
            # Return CAD value if available, otherwise USD
            return aum.get('cad') or aum.get('usd')
        return str(aum)

    def _parse_portfolio(self, portfolio: Dict) -> Dict:
        """
        Parse portfolio holdings and allocation data

        Args:
            portfolio: Raw portfolio data from fundData

        Returns:
            Structured portfolio dictionary
        """
        parsed = {
            'date': portfolio.get('dt'),
            'asset_allocation': {},
            'sector_allocation': {},
            'top_holdings': [],
            'credit_profile': {},
            'option_statistics': {}
        }

        # Level 1: Asset class breakdown
        level1 = portfolio.get('Level1', {})
        if 'asset_class' in level1:
            parsed['asset_allocation'] = level1['asset_class']

        # Level 2: Sector/credit profile/option stats
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
                'series': data.get('series'),
                'nav': data.get('nav'),
                'aum': data.get('aum'),
                'management_fee': data.get('management_fee'),
                'mer': data.get('mer'),
                'distribution_frequency': data.get('distribution_frequency'),
                'category': data.get('category'),
                'current_yield': data.get('current_yield'),
                'fund_structure': data.get('fund_structure'),
                'cusip': data.get('cusip'),
                'exchange': data.get('exchange'),
                'currency_hedged': data.get('currency_hedged'),
                'settlement': data.get('settlement'),
                'duration': data.get('duration'),
                'coupon': data.get('coupon'),
                'maturity_yield': data.get('maturity_yield'),
                'underlying': data.get('underlying'),
                'fund_details': data.get('fund_details'),
                'portfolio_data': data.get('portfolio_data'),
                'distributions': data.get('distributions'),
                'performance_data': data.get('performance_data'),
                'eligibilities': data.get('eligibilities')
            }

            # Upsert to database
            result = supabase_upsert('raw_purpose_etf_data', [record])

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
    Scrape a single Purpose ETF

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if successful, False otherwise
    """
    if ticker not in PURPOSE_ETFS:
        logger.error(f"❌ Unknown ticker: {ticker}")
        logger.info(f"Available tickers: {', '.join(sorted(PURPOSE_ETFS.keys()))}")
        return False

    etf_info = PURPOSE_ETFS[ticker]
    scraper = PurposeScraper(
        ticker,
        etf_info['name'],
        etf_info['slug'],
        etf_info.get('category'),
        etf_info.get('underlying')
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
    print(f"  • Category: {data.get('category') or '❌'}")
    print(f"  • Underlying: {data.get('underlying') or 'N/A'}")
    print(f"  • Series: {data.get('series') or '❌'}")
    print(f"  • NAV: {data.get('nav') or '❌'}")
    print(f"  • Current Yield: {data.get('current_yield') or 'N/A'}")
    print(f"  • AUM: {data.get('aum') or '❌'}")
    print(f"  • Management Fee: {data.get('management_fee') or '❌'}")
    print(f"  • MER: {data.get('mer') or '❌'}")
    print(f"  • Distribution Frequency: {data.get('distribution_frequency') or '❌'}")

    portfolio = data.get('portfolio_data') or {}
    print(f"  • Portfolio Data: {'✅' if portfolio else '❌'}")
    if portfolio:
        holdings = portfolio.get('top_holdings', [])
        print(f"    - Top Holdings: {len(holdings)} positions")
        if 'option_statistics' in portfolio and portfolio['option_statistics']:
            print(f"    - Option Statistics: ✅ (Yield Shares)")

    distributions = data.get('distributions') or []
    print(f"  • Distributions: {'✅' if distributions else '❌'} ({len(distributions)} records)")

    performance = data.get('performance_data') or {}
    print(f"  • Performance Data: {'✅' if performance else '❌'}")
    if performance:
        print(f"    - Total Data Points: {performance.get('total_data_points', 0)}")

    eligibilities = data.get('eligibilities') or {}
    print(f"  • Eligibilities: {'✅' if eligibilities else '❌'}")
    print()

    # Save to database
    return scraper.save_to_database(data)


def validate_etf_urls() -> Dict[str, bool]:
    """
    Validate all ETF URLs before scraping

    Returns:
        Dictionary mapping ticker to availability status (True if accessible)
    """
    print("🔍 Validating ETF URLs...")
    print()

    validation_results = {}
    invalid_tickers = []

    for ticker, info in PURPOSE_ETFS.items():
        try:
            url = f"https://www.purposeinvest.com/funds/{info['slug']}"
            response = requests.head(url, timeout=10, allow_redirects=True)
            is_valid = response.status_code == 200
            validation_results[ticker] = is_valid

            if is_valid:
                print(f"  ✅ {ticker:8s} - OK")
            else:
                print(f"  ❌ {ticker:8s} - HTTP {response.status_code}")
                invalid_tickers.append(ticker)
                logger.warning(f"URL validation failed for {ticker}: HTTP {response.status_code}")

        except Exception as e:
            validation_results[ticker] = False
            print(f"  ❌ {ticker:8s} - {str(e)[:50]}")
            invalid_tickers.append(ticker)
            logger.error(f"URL validation error for {ticker}: {e}")

    print()
    if invalid_tickers:
        print(f"⚠️  {len(invalid_tickers)} invalid URLs found: {', '.join(invalid_tickers)}")
        print("   These tickers will be skipped during scraping")
        print()
    else:
        print(f"✅ All {len(PURPOSE_ETFS)} ETF URLs validated successfully!")
        print()

    return validation_results


def scrape_all_etfs(delay: int = 2, skip_validation: bool = False, category: str = None, limit: int = None) -> Dict[str, bool]:
    """
    Scrape all Purpose ETFs

    Args:
        delay: Seconds to wait between requests (default: 2)
        skip_validation: Skip URL validation step (default: False)
        category: Filter by category (default: None)
        limit: Limit number of ETFs to scrape (default: None)

    Returns:
        Dictionary mapping ticker to success status
    """
    # Filter by category if specified
    tickers_to_scrape = list(PURPOSE_ETFS.keys())
    if category:
        tickers_to_scrape = [
            ticker for ticker, info in PURPOSE_ETFS.items()
            if category.lower() in info.get('category', '').lower()
        ]
        if not tickers_to_scrape:
            print(f"❌ No ETFs found for category: {category}")
            return {}

    # Apply limit if specified
    if limit and limit > 0:
        tickers_to_scrape = tickers_to_scrape[:limit]

    # Validate URLs first unless skipped
    valid_tickers = tickers_to_scrape
    if not skip_validation:
        validation_results = validate_etf_urls()
        valid_tickers = [ticker for ticker in tickers_to_scrape if validation_results.get(ticker, False)]

        if len(valid_tickers) < len(tickers_to_scrape):
            invalid_count = len(tickers_to_scrape) - len(valid_tickers)
            print(f"⏭️  Skipping {invalid_count} invalid ticker(s)")
            print()

    results = {}

    print(f"🚀 Scraping {len(valid_tickers)} Purpose ETFs...")
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
    parser = argparse.ArgumentParser(description='Scrape Purpose Investments ETF data')
    parser.add_argument('--ticker', '-t', type=str, help='Specific ticker to scrape (e.g., YTSL, BTCC)')
    parser.add_argument('--all', '-a', action='store_true', help='Scrape all Purpose ETFs')
    parser.add_argument('--category', '-c', type=str,
                       help='Scrape by category (Equity, Fixed Income, Cryptocurrency, etc.)')
    parser.add_argument('--list', '-l', action='store_true', help='List available tickers')
    parser.add_argument('--delay', '-d', type=int, default=2,
                       help='Delay in seconds between requests when scraping all (default: 2)')
    parser.add_argument('--limit', type=int, help='Limit number of ETFs to scrape')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only 3 ETFs')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip URL validation before scraping (faster but may fail on invalid URLs)')

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 Purpose Investments ETF Scraper")
    print("=" * 80)
    print()

    # List available tickers
    if args.list:
        print(f"Available Purpose ETFs ({len(PURPOSE_ETFS)}):")
        print()

        # Group by category
        categories = {}
        for ticker, info in PURPOSE_ETFS.items():
            category = info.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append((ticker, info['name']))

        category_order = [
            'Equity - Yield Shares US Tech',
            'Equity - Yield Shares Canadian',
            'Equity - Traditional',
            'Fixed Income',
            'Cryptocurrency',
            'Alternatives',
            'Multi-Asset',
            'Commodities',
            'Cash Management',
            'Other'
        ]

        for category in category_order:
            if category in categories:
                print(f"{category} ({len(categories[category])}):")
                for ticker, name in sorted(categories[category]):
                    print(f"  {ticker:10s} - {name}")
                print()

        print("=" * 80)
        return 0

    # Test mode
    if args.test:
        args.limit = 3
        args.all = True

    # Scrape all ETFs
    if args.all or args.category:
        results = scrape_all_etfs(
            delay=args.delay,
            skip_validation=args.skip_validation,
            category=args.category,
            limit=args.limit
        )

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
