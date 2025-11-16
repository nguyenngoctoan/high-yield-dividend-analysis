#!/usr/bin/env python3
"""
Global X Canada ETF Scraper (All Funds)

Scrapes comprehensive data from all 107 Global X Canada ETF pages including:
- Fund overview and metrics (NAV, AUM, fees, yields)
- Covered call specific metrics (coverage, moneyness, option yield)
- Portfolio holdings and allocations
- Distribution history
- Performance data (annualized and calendar year)
- Sector and geographic allocations

Uses standard HTML parsing - NO Selenium needed!
All data is in static HTML tables that can be scraped with requests + BeautifulSoup.

Supports 13 categories:
1. Cash & Fixed Income (19 ETFs)
2. Corporate Class (8 ETFs)
3. Thematic (16 ETFs)
4. Enhanced Growth (6 ETFs) - 25% leveraged
5. Equity Essentials (12 ETFs)
6. Covered Call - Index (9 ETFs)
7. Covered Call - Sector (2 ETFs)
8. Enhanced Covered Call (9 ETFs) - 25% leveraged
9. Commodities - Covered Call (5 ETFs)
10. Cryptocurrency - Covered Call (4 ETFs)
11. Precious Metals (7 ETFs)
12. Asset Allocation (8 ETFs)
13. BetaPro - Leveraged/Inverse (7 ETFs) - 2x

All data stored as JSON in raw_etfs_globalx table.
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


# Global X Canada ETF Configuration (107 ETFs across 13 categories)
GLOBALX_ETFS = {
    # ========================================
    # CASH & FIXED INCOME (19 ETFs)
    # ========================================
    'CASH': {
        'name': 'Global X High Interest Savings ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Money Market'
    },
    'CBIL': {
        'name': 'Global X 0-3 Month T-Bill ETF',
        'category': 'Cash & Fixed Income',
        'type': 'T-Bill'
    },
    'CBIL.U': {
        'name': 'Global X 0-3 Month T-Bill ETF (USD)',
        'category': 'Cash & Fixed Income',
        'type': 'T-Bill'
    },
    'HBB': {
        'name': 'Global X Canadian Select Universe Bond Index Corporate Class ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Bond'
    },
    'PAYS': {
        'name': 'Global X Short-Term Government Bond Premium Yield ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'SPAY': {
        'name': 'Global X Short-Term U.S. Treasury Premium Yield ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'SPAY.U': {
        'name': 'Global X Short-Term U.S. Treasury Premium Yield ETF (USD)',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'PAYM': {
        'name': 'Global X Mid-Term Government Bond Premium Yield ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'MPAY': {
        'name': 'Global X Mid-Term U.S. Treasury Premium Yield ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'MPAY.U': {
        'name': 'Global X Mid-Term U.S. Treasury Premium Yield ETF (USD)',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'PAYL': {
        'name': 'Global X Long-Term Government Bond Premium Yield ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'LPAY': {
        'name': 'Global X Long-Term U.S. Treasury Premium Yield ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'LPAY.U': {
        'name': 'Global X Long-Term U.S. Treasury Premium Yield ETF (USD)',
        'category': 'Cash & Fixed Income',
        'type': 'Premium Yield'
    },
    'TSTX': {
        'name': 'Global X 1-3 Year U.S. Treasury Bond Index ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Treasury'
    },
    'TSTX.U': {
        'name': 'Global X 1-3 Year U.S. Treasury Bond Index ETF (USD)',
        'category': 'Cash & Fixed Income',
        'type': 'Treasury'
    },
    'TSTX.F': {
        'name': 'Global X 1-3 Year U.S. Treasury Bond Index ETF (CAD-hedged)',
        'category': 'Cash & Fixed Income',
        'type': 'Treasury'
    },
    'TLTX': {
        'name': 'Global X 20+ Year U.S. Treasury Bond Index ETF',
        'category': 'Cash & Fixed Income',
        'type': 'Treasury'
    },
    'TLTX.U': {
        'name': 'Global X 20+ Year U.S. Treasury Bond Index ETF (USD)',
        'category': 'Cash & Fixed Income',
        'type': 'Treasury'
    },
    'TLTX.F': {
        'name': 'Global X 20+ Year U.S. Treasury Bond Index ETF (CAD-hedged)',
        'category': 'Cash & Fixed Income',
        'type': 'Treasury'
    },

    # ========================================
    # CORPORATE CLASS (8 ETFs)
    # ========================================
    'HXS': {
        'name': 'Global X S&P 500 Index Corporate Class ETF',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Equity Index'
    },
    'HXS.U': {
        'name': 'Global X S&P 500 Index Corporate Class ETF (USD)',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Equity Index'
    },
    'HXT': {
        'name': 'Global X S&P/TSX 60 Index Corporate Class ETF',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Equity Index'
    },
    'HXT.U': {
        'name': 'Global X S&P/TSX 60 Index Corporate Class ETF (USD)',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Equity Index'
    },
    'HXQ': {
        'name': 'Global X Nasdaq-100 Index Corporate Class ETF',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Equity Index'
    },
    'HXQ.U': {
        'name': 'Global X NASDAQ-100 Index Corporate Class ETF (USD)',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Equity Index'
    },
    'HXCN': {
        'name': 'Global X S&P/TSX Capped Composite Index Corporate Class ETF',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Equity Index'
    },
    'HSAV': {
        'name': 'Global X Cash Maximizer Corporate Class ETF',
        'category': 'Corporate Class (Tax-Efficient)',
        'type': 'Cash'
    },

    # ========================================
    # THEMATIC (16 ETFs)
    # ========================================
    'CHQQ': {
        'name': 'Global X China Hang Seng TECH Index ETF',
        'category': 'Thematic',
        'type': 'China Tech'
    },
    'MEDX': {
        'name': 'Global X Equal Weight Global Healthcare Index ETF',
        'category': 'Thematic',
        'type': 'Healthcare'
    },
    'SHLD': {
        'name': 'Global X Defence Tech Index ETF',
        'category': 'Thematic',
        'type': 'Defence Tech'
    },
    'MTRX': {
        'name': 'Global X Artificial Intelligence Infrastructure Index ETF',
        'category': 'Thematic',
        'type': 'AI Infrastructure'
    },
    'AIGO': {
        'name': 'Global X Artificial Intelligence & Technology Index ETF',
        'category': 'Thematic',
        'type': 'AI & Technology'
    },
    'TTTX': {
        'name': 'Global X Innovative Bluechip Top 10 Index ETF',
        'category': 'Thematic',
        'type': 'Innovation'
    },
    'CHPS': {
        'name': 'Global X Artificial Intelligence Semiconductor Index ETF',
        'category': 'Thematic',
        'type': 'AI Semiconductors'
    },
    'CHPS.U': {
        'name': 'Global X Artificial Intelligence Semiconductor Index ETF (USD)',
        'category': 'Thematic',
        'type': 'AI Semiconductors'
    },
    'FOUR': {
        'name': 'Global X Industry 4.0 Index ETF',
        'category': 'Thematic',
        'type': 'Industry 4.0'
    },
    'HBGD': {
        'name': 'Global X Big Data & Hardware Index ETF',
        'category': 'Thematic',
        'type': 'Big Data'
    },
    'HBGD.U': {
        'name': 'Global X Big Data & Hardware Index ETF (USD)',
        'category': 'Thematic',
        'type': 'Big Data'
    },
    'HLIT': {
        'name': 'Global X Lithium Producers Index ETF',
        'category': 'Thematic',
        'type': 'Lithium'
    },
    'HMMJ': {
        'name': 'Global X Marijuana Life Sciences Index ETF',
        'category': 'Thematic',
        'type': 'Cannabis'
    },
    'HMMJ.U': {
        'name': 'Global X Marijuana Life Sciences Index ETF (USD)',
        'category': 'Thematic',
        'type': 'Cannabis'
    },
    'RBOT': {
        'name': 'Global X Robotics & AI Index ETF',
        'category': 'Thematic',
        'type': 'Robotics & AI'
    },
    'RBOT.U': {
        'name': 'Global X Robotics & AI Index ETF (USD)',
        'category': 'Thematic',
        'type': 'Robotics & AI'
    },

    # ========================================
    # ENHANCED GROWTH (6 ETFs) - 25% Leveraged
    # ========================================
    'CANL': {
        'name': 'Global X Enhanced S&P/TSX 60 Index ETF',
        'category': 'Enhanced Growth (25% Leveraged)',
        'type': 'Canadian Equity',
        'leverage': '1.25x'
    },
    'BNKL': {
        'name': 'Global X Enhanced Equal Weight Banks Index ETF',
        'category': 'Enhanced Growth (25% Leveraged)',
        'type': 'Canadian Banks',
        'leverage': '1.25x'
    },
    'USSL': {
        'name': 'Global X Enhanced S&P 500 Index ETF',
        'category': 'Enhanced Growth (25% Leveraged)',
        'type': 'US Equity',
        'leverage': '1.25x'
    },
    'QQQL': {
        'name': 'Global X Enhanced NASDAQ-100 Index ETF',
        'category': 'Enhanced Growth (25% Leveraged)',
        'type': 'Tech',
        'leverage': '1.25x'
    },
    'EAFL': {
        'name': 'Global X Enhanced MSCI EAFE Index ETF',
        'category': 'Enhanced Growth (25% Leveraged)',
        'type': 'International',
        'leverage': '1.25x'
    },
    'EMML': {
        'name': 'Global X Enhanced MSCI Emerging Markets Index ETF',
        'category': 'Enhanced Growth (25% Leveraged)',
        'type': 'Emerging Markets',
        'leverage': '1.25x'
    },

    # ========================================
    # EQUITY ESSENTIALS (12 ETFs)
    # ========================================
    'CNDX': {
        'name': 'Global X S&P/TSX 60 Index ETF',
        'category': 'Equity Essentials - Core',
        'type': 'Canadian Equity'
    },
    'HBNK': {
        'name': 'Global X Equal Weight Canadian Banks Index ETF',
        'category': 'Equity Essentials - Core',
        'type': 'Canadian Banks'
    },
    'USSX': {
        'name': 'Global X S&P 500 Index ETF',
        'category': 'Equity Essentials - Core',
        'type': 'US Equity'
    },
    'USSX.U': {
        'name': 'Global X S&P 500 Index ETF (USD)',
        'category': 'Equity Essentials - Core',
        'type': 'US Equity'
    },
    'RSSX': {
        'name': 'Global X Russell 2000 Index ETF',
        'category': 'Equity Essentials - Core',
        'type': 'US Small Cap'
    },
    'RSSX.U': {
        'name': 'Global X Russell 2000 Index ETF (USD)',
        'category': 'Equity Essentials - Core',
        'type': 'US Small Cap'
    },
    'QQQX': {
        'name': 'Global X Nasdaq-100 Index ETF',
        'category': 'Equity Essentials - Core',
        'type': 'Tech'
    },
    'QQQX.U': {
        'name': 'Global X Nasdaq-100 Index ETF (USD)',
        'category': 'Equity Essentials - Core',
        'type': 'Tech'
    },
    'EAFX': {
        'name': 'Global X MSCI EAFE Index ETF',
        'category': 'Equity Essentials - Core',
        'type': 'International'
    },
    'EAFX.U': {
        'name': 'Global X MSCI EAFE Index ETF (USD)',
        'category': 'Equity Essentials - Core',
        'type': 'International'
    },
    'EMMX': {
        'name': 'Global X MSCI Emerging Markets Index ETF',
        'category': 'Equity Essentials - Core',
        'type': 'Emerging Markets'
    },
    'EMMX.U': {
        'name': 'Global X MSCI Emerging Markets Index ETF (USD)',
        'category': 'Equity Essentials - Core',
        'type': 'Emerging Markets'
    },

    # ========================================
    # COVERED CALL - INDEX (9 ETFs)
    # ========================================
    'CNCC': {
        'name': 'Global X S&P/TSX 60 Covered Call ETF',
        'category': 'Covered Call - Index',
        'type': 'Canadian Equity'
    },
    'USCC': {
        'name': 'Global X S&P 500 Covered Call ETF',
        'category': 'Covered Call - Index',
        'type': 'US Equity'
    },
    'USCC.U': {
        'name': 'Global X S&P 500 Covered Call ETF (USD)',
        'category': 'Covered Call - Index',
        'type': 'US Equity'
    },
    'QQCC': {
        'name': 'Global X NASDAQ-100 Covered Call ETF',
        'category': 'Covered Call - Index',
        'type': 'Tech'
    },
    'QQCC.U': {
        'name': 'Global X Nasdaq-100 Covered Call ETF (USD)',
        'category': 'Covered Call - Index',
        'type': 'Tech'
    },
    'RSCC': {
        'name': 'Global X Russell 2000 Covered Call ETF',
        'category': 'Covered Call - Index',
        'type': 'US Small Cap'
    },
    'RSCC.U': {
        'name': 'Global X Russell 2000 Covered Call ETF (USD)',
        'category': 'Covered Call - Index',
        'type': 'US Small Cap'
    },
    'EACC': {
        'name': 'Global X MSCI EAFE Covered Call ETF',
        'category': 'Covered Call - Index',
        'type': 'International'
    },
    'EMCC': {
        'name': 'Global X MSCI Emerging Markets Covered Call ETF',
        'category': 'Covered Call - Index',
        'type': 'Emerging Markets'
    },

    # ========================================
    # COVERED CALL - SECTOR (2 ETFs)
    # ========================================
    'BKCC': {
        'name': 'Global X Equal Weight Canadian Bank Covered Call ETF',
        'category': 'Covered Call - Sector',
        'type': 'Canadian Banks'
    },
    'RNCC': {
        'name': 'Global X Equal Weight Canadian Telecommunications Covered Call ETF',
        'category': 'Covered Call - Sector',
        'type': 'Canadian Telecom'
    },

    # ========================================
    # ENHANCED COVERED CALL (9 ETFs) - 25% Leveraged
    # ========================================
    'CNCL': {
        'name': 'Global X Enhanced S&P/TSX 60 Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'Canadian Equity',
        'leverage': '1.25x'
    },
    'BKCL': {
        'name': 'Global X Enhanced Equal Weight Canadian Banks Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'Canadian Banks',
        'leverage': '1.25x'
    },
    'USCL': {
        'name': 'Global X Enhanced S&P 500 Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'US Equity',
        'leverage': '1.25x'
    },
    'QQCL': {
        'name': 'Global X Enhanced NASDAQ-100 Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'Tech',
        'leverage': '1.25x'
    },
    'RSCL': {
        'name': 'Global X Enhanced Russell 2000 Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'US Small Cap',
        'leverage': '1.25x'
    },
    'EACL': {
        'name': 'Global X Enhanced MSCI EAFE Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'International',
        'leverage': '1.25x'
    },
    'EMCL': {
        'name': 'Global X Enhanced MSCI Emerging Markets Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'Emerging Markets',
        'leverage': '1.25x'
    },
    'RNCL': {
        'name': 'Global X Enhanced Equal Weight Canadian Telecommunications Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'Canadian Telecom',
        'leverage': '1.25x'
    },
    'ENCL': {
        'name': 'Global X Enhanced Canadian Oil And Gas Equity Covered Call ETF',
        'category': 'Enhanced Covered Call (25% Leveraged)',
        'type': 'Energy',
        'leverage': '1.25x'
    },

    # ========================================
    # COMMODITIES - COVERED CALL (5 ETFs)
    # ========================================
    'ENCC': {
        'name': 'Global X Canadian Oil and Gas Equity Covered Call ETF',
        'category': 'Commodities - Covered Call',
        'type': 'Energy'
    },
    'GLCC': {
        'name': 'Global X Gold Producer Equity Covered Call ETF',
        'category': 'Commodities - Covered Call',
        'type': 'Gold'
    },
    'GLCL': {
        'name': 'Global X Enhanced Gold Producer Equity Covered Call ETF',
        'category': 'Commodities - Covered Call',
        'type': 'Gold',
        'leverage': '1.25x'
    },
    'AGCC': {
        'name': 'Global X Silver Covered Call ETF',
        'category': 'Commodities - Covered Call',
        'type': 'Silver'
    },
    'HGY': {
        'name': 'Global X Gold Yield ETF',
        'category': 'Commodities - Covered Call',
        'type': 'Gold'
    },

    # ========================================
    # CRYPTOCURRENCY - COVERED CALL (4 ETFs)
    # ========================================
    'BCCC': {
        'name': 'Global X Bitcoin Covered Call ETF',
        'category': 'Cryptocurrency - Covered Call',
        'type': 'Bitcoin'
    },
    'BCCC.U': {
        'name': 'Global X Bitcoin Covered Call ETF (USD)',
        'category': 'Cryptocurrency - Covered Call',
        'type': 'Bitcoin'
    },
    'BCCL': {
        'name': 'Global X Enhanced Bitcoin Covered Call ETF',
        'category': 'Cryptocurrency - Covered Call',
        'type': 'Bitcoin',
        'leverage': '1.25x'
    },
    'BCCL.U': {
        'name': 'Global X Enhanced Bitcoin Covered Call ETF (USD)',
        'category': 'Cryptocurrency - Covered Call',
        'type': 'Bitcoin',
        'leverage': '1.25x'
    },

    # ========================================
    # PRECIOUS METALS (7 ETFs)
    # ========================================
    'HUG': {
        'name': 'Global X Gold ETF',
        'category': 'Precious Metals',
        'type': 'Gold Bullion'
    },
    'HUZ': {
        'name': 'Global X Silver ETF',
        'category': 'Precious Metals',
        'type': 'Silver Bullion'
    },
    'GLDX': {
        'name': 'Global X Gold Producers Index ETF',
        'category': 'Precious Metals',
        'type': 'Gold Equity'
    },

    # ========================================
    # ASSET ALLOCATION (8 ETFs)
    # ========================================
    'HCON': {
        'name': 'Global X Conservative Asset Allocation ETF',
        'category': 'Asset Allocation',
        'type': 'Conservative'
    },
    'HBAL': {
        'name': 'Global X Balanced Asset Allocation ETF',
        'category': 'Asset Allocation',
        'type': 'Balanced'
    },
    'HGRW': {
        'name': 'Global X Growth Asset Allocation ETF',
        'category': 'Asset Allocation',
        'type': 'Growth'
    },
    'HEQT': {
        'name': 'Global X All-Equity Asset Allocation ETF',
        'category': 'Asset Allocation',
        'type': 'All-Equity'
    },
    'HEQL': {
        'name': 'Global X Enhanced All-Equity Asset Allocation ETF',
        'category': 'Asset Allocation',
        'type': 'All-Equity',
        'leverage': '1.25x'
    },
    'GRCC': {
        'name': 'Global X Growth Asset Allocation Covered Call ETF',
        'category': 'Asset Allocation',
        'type': 'Growth Covered Call'
    },
    'EQCC': {
        'name': 'Global X All-Equity Asset Allocation Covered Call ETF',
        'category': 'Asset Allocation',
        'type': 'All-Equity Covered Call'
    },
    'EQCL': {
        'name': 'Global X Enhanced All-Equity Asset Allocation Covered Call ETF',
        'category': 'Asset Allocation',
        'type': 'All-Equity Covered Call',
        'leverage': '1.25x'
    },

    # ========================================
    # BETAPRO (7 ETFs) - 2x Leveraged/Inverse
    # ========================================
    'HQU': {
        'name': 'BetaPro NASDAQ-100® 2x Daily Bull ETF',
        'category': 'BetaPro (Leveraged/Inverse)',
        'type': 'Tech',
        'leverage': '2x'
    },
    'HSU': {
        'name': 'BetaPro S&P 500® 2x Daily Bull ETF',
        'category': 'BetaPro (Leveraged/Inverse)',
        'type': 'US Equity',
        'leverage': '2x'
    },
    'HNU': {
        'name': 'BetaPro Natural Gas Leveraged Daily Bull ETF',
        'category': 'BetaPro (Leveraged/Inverse)',
        'type': 'Natural Gas',
        'leverage': '2x'
    },
    'HND': {
        'name': 'BetaPro Natural Gas Inverse Leveraged Daily Bear ETF',
        'category': 'BetaPro (Leveraged/Inverse)',
        'type': 'Natural Gas',
        'leverage': '-2x'
    },
    'HGU': {
        'name': 'BetaPro Canadian Gold Miners 2x Daily Bull ETF',
        'category': 'BetaPro (Leveraged/Inverse)',
        'type': 'Gold Miners',
        'leverage': '2x'
    },
    'HOU': {
        'name': 'BetaPro Crude Oil Leveraged Daily Bull ETF',
        'category': 'BetaPro (Leveraged/Inverse)',
        'type': 'Crude Oil',
        'leverage': '2x'
    },
    'HZU': {
        'name': 'BetaPro Silver 2x Daily Bull ETF',
        'category': 'BetaPro (Leveraged/Inverse)',
        'type': 'Silver',
        'leverage': '2x'
    }
}


class GlobalXScraper:
    """Scraper for Global X Canada ETF data using requests + BeautifulSoup"""

    BASE_URL = "https://www.globalx.ca"

    def __init__(self, ticker: str, fund_name: str, category: str = None, fund_type: str = None, leverage: str = None):
        """
        Initialize the scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            category: ETF category
            fund_type: Fund type/strategy
            leverage: Leverage ratio (if applicable)
        """
        self.ticker = ticker
        self.fund_name = fund_name
        self.category = category
        self.fund_type = fund_type
        self.leverage = leverage

        # Remove currency suffixes (.U, .F) for URL
        base_ticker = ticker.split('.')[0].lower()
        self.url = f"{self.BASE_URL}/product/{base_ticker}"

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Global X ETF Data Aggregator (research purposes)'
        })

    def scrape_data(self) -> Optional[Dict[str, Any]]:
        """
        Scrape all data from the ETF page using requests + BeautifulSoup

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

            # Extract all data sections
            data = {
                'ticker': self.ticker,
                'fund_name': self.fund_name,
                'url': self.url,
                'scraped_at': datetime.now().isoformat(),
                'category': self.category,
                'leverage_ratio': self.leverage
            }

            # Extract fund details table
            fund_details = self._extract_fund_details(soup)
            data.update(fund_details)

            # Extract covered call metrics (if applicable)
            if 'Covered Call' in (self.category or ''):
                cc_metrics = self._extract_covered_call_metrics(soup)
                data.update(cc_metrics)

            # Extract holdings
            holdings = self._extract_holdings(soup)
            if holdings:
                data['holdings'] = holdings

            # Extract distributions
            distributions = self._extract_distributions(soup)
            if distributions:
                data['distributions'] = distributions

            # Extract performance data
            performance = self._extract_performance(soup)
            if performance:
                data['performance_data'] = performance

            # Extract sector allocation
            sector_allocation = self._extract_sector_allocation(soup)
            if sector_allocation:
                data['sector_allocation'] = sector_allocation

            # Extract geographic allocation
            geographic_allocation = self._extract_geographic_allocation(soup)
            if geographic_allocation:
                data['geographic_allocation'] = geographic_allocation

            # Extract additional fund details for JSONB
            additional_details = self._extract_additional_details(soup)
            if additional_details:
                data['fund_details'] = additional_details

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

    def _extract_fund_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract fund details from main table"""
        details = {}

        try:
            # Find all tables with class wp-block-table
            tables = soup.find_all('table', class_='wp-block-table')

            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)

                        # Map labels to database fields
                        if 'CUSIP' in label:
                            details['cusip'] = value
                        elif 'Inception' in label:
                            details['inception_date'] = value
                        elif 'Net Assets' in label or 'AUM' in label:
                            details['net_assets'] = value
                        elif 'Management Fee' in label:
                            details['management_fee'] = value
                        elif 'MER' in label:
                            details['mer'] = value
                        elif 'TER' in label or 'Trading Expense' in label:
                            details['ter'] = value
                        elif 'Benchmark' in label:
                            details['benchmark_index'] = value
                        elif 'Distribution Frequency' in label:
                            details['distribution_frequency'] = value
                        elif 'Most Recent Distribution' in label:
                            details['most_recent_distribution'] = value
                        elif '12-Month' in label and 'Yield' in label:
                            details['trailing_yield_12m'] = value

            # Extract NAV and market price from page text
            text = soup.get_text()

            # NAV pattern
            nav_match = re.search(r'NAV[:\s]+\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
            if nav_match:
                details['nav'] = nav_match.group(1)

            # Market price pattern
            price_match = re.search(r'(?:Market\s+)?Price[:\s]+\$?([\d,]+\.?\d*)', text, re.IGNORECASE)
            if price_match:
                details['market_price'] = price_match.group(1)

            # Distribution yield pattern
            yield_match = re.search(r'(?:Annualized\s+)?Distribution\s+Yield[:\s]+([\d.]+%)', text, re.IGNORECASE)
            if yield_match:
                details['distribution_yield'] = yield_match.group(1)

        except Exception as e:
            logger.warning(f"Error extracting fund details: {e}")

        return details

    def _extract_covered_call_metrics(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract covered call specific metrics (Portfolio Investment Metrics section)"""
        metrics = {}

        try:
            text = soup.get_text()

            # Average Coverage
            coverage_match = re.search(r'Average\s+Coverage[:\s]+([\d.]+%)', text, re.IGNORECASE)
            if coverage_match:
                metrics['average_coverage'] = coverage_match.group(1)

            # Average Moneyness
            moneyness_match = re.search(r'Average\s+Moneyness[:\s]+([\d.]+%)', text, re.IGNORECASE)
            if moneyness_match:
                metrics['moneyness'] = moneyness_match.group(1)

            # Option Annualized Yield
            option_yield_match = re.search(r'Option\s+Annualized\s+Yield[:\s]+([\d.]+%)', text, re.IGNORECASE)
            if option_yield_match:
                metrics['option_yield'] = option_yield_match.group(1)

            # Dividend Yield
            div_yield_match = re.search(r'Dividend\s+Yield[:\s]+([\d.]+%)', text, re.IGNORECASE)
            if div_yield_match:
                metrics['dividend_yield'] = div_yield_match.group(1)

        except Exception as e:
            logger.warning(f"Error extracting covered call metrics: {e}")

        return metrics

    def _extract_holdings(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract top 10 holdings"""
        holdings_data = {'top_holdings': []}

        try:
            # Find holdings section by looking for "Holdings" or "Top Holdings" heading
            for header in soup.find_all(['h2', 'h3', 'h4']):
                if 'holdings' in header.get_text().lower():
                    # Find next table
                    table = header.find_next('table')
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header
                        for row in rows[:10]:  # Top 10
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                holdings_data['top_holdings'].append({
                                    'security': cells[0].get_text(strip=True),
                                    'weight': cells[1].get_text(strip=True)
                                })
                        break
        except Exception as e:
            logger.warning(f"Error extracting holdings: {e}")

        return holdings_data if holdings_data['top_holdings'] else None

    def _extract_distributions(self, soup: BeautifulSoup) -> Optional[List[Dict]]:
        """Extract distribution history"""
        distributions = []

        try:
            # Find distribution history table
            for header in soup.find_all(['h2', 'h3', 'h4']):
                if 'distribution' in header.get_text().lower() and 'history' in header.get_text().lower():
                    table = header.find_next('table')
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 4:
                                distributions.append({
                                    'ex_dividend_date': cells[0].get_text(strip=True),
                                    'record_date': cells[1].get_text(strip=True),
                                    'payment_date': cells[2].get_text(strip=True),
                                    'amount': cells[3].get_text(strip=True),
                                    'period': cells[4].get_text(strip=True) if len(cells) > 4 else None
                                })
                        break
        except Exception as e:
            logger.warning(f"Error extracting distributions: {e}")

        return distributions if distributions else None

    def _extract_performance(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract performance data (annualized and calendar year)"""
        performance = {
            'annualized': {},
            'calendar_year': {}
        }

        try:
            # Find performance tables
            for header in soup.find_all(['h2', 'h3', 'h4']):
                header_text = header.get_text().lower()

                # Annualized performance
                if 'annualized' in header_text and 'performance' in header_text:
                    table = header.find_next('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                period = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                performance['annualized'][period] = value

                # Calendar year performance
                elif 'calendar' in header_text or 'annual' in header_text:
                    table = header.find_next('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                year = cells[0].get_text(strip=True)
                                value = cells[1].get_text(strip=True)
                                if year.isdigit():
                                    performance['calendar_year'][year] = value
        except Exception as e:
            logger.warning(f"Error extracting performance: {e}")

        return performance if (performance['annualized'] or performance['calendar_year']) else None

    def _extract_sector_allocation(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract sector allocation breakdown"""
        sector_data = {}

        try:
            for header in soup.find_all(['h2', 'h3', 'h4']):
                if 'sector' in header.get_text().lower():
                    table = header.find_next('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                sector = cells[0].get_text(strip=True)
                                weight = cells[1].get_text(strip=True)
                                sector_data[sector] = weight
                        break
        except Exception as e:
            logger.warning(f"Error extracting sector allocation: {e}")

        return sector_data if sector_data else None

    def _extract_geographic_allocation(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract geographic allocation breakdown"""
        geo_data = {}

        try:
            for header in soup.find_all(['h2', 'h3', 'h4']):
                if 'geographic' in header.get_text().lower() or 'geography' in header.get_text().lower():
                    table = header.find_next('table')
                    if table:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= 2:
                                region = cells[0].get_text(strip=True)
                                weight = cells[1].get_text(strip=True)
                                geo_data[region] = weight
                        break
        except Exception as e:
            logger.warning(f"Error extracting geographic allocation: {e}")

        return geo_data if geo_data else None

    def _extract_additional_details(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract additional fund details for JSONB storage"""
        details = {}

        try:
            text = soup.get_text()

            # Investment objective
            obj_match = re.search(r'Investment Objective[:\s]+(.+?)(?:\n\n|Risk Rating)', text, re.IGNORECASE | re.DOTALL)
            if obj_match:
                details['investment_objective'] = obj_match.group(1).strip()

            # Risk rating
            risk_match = re.search(r'Risk Rating[:\s]+(\w+(?:\s+to\s+\w+)?)', text, re.IGNORECASE)
            if risk_match:
                details['risk_rating'] = risk_match.group(1).strip()

            # Reasons to consider (usually 3-4 bullet points)
            reasons = []
            for header in soup.find_all(['h2', 'h3', 'h4']):
                if 'reasons' in header.get_text().lower() and 'consider' in header.get_text().lower():
                    next_elem = header.find_next(['ul', 'ol'])
                    if next_elem:
                        for li in next_elem.find_all('li'):
                            reasons.append(li.get_text(strip=True))
                    break
            if reasons:
                details['reasons_to_consider'] = reasons

        except Exception as e:
            logger.warning(f"Error extracting additional details: {e}")

        return details if details else None

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
                'category': data.get('category'),
                'cusip': data.get('cusip'),
                'inception_date': data.get('inception_date'),
                'nav': data.get('nav'),
                'market_price': data.get('market_price'),
                'premium_discount': data.get('premium_discount'),
                'management_fee': data.get('management_fee'),
                'mer': data.get('mer'),
                'ter': data.get('ter'),
                'net_assets': data.get('net_assets'),
                'distribution_yield': data.get('distribution_yield'),
                'distribution_frequency': data.get('distribution_frequency'),
                'average_coverage': data.get('average_coverage'),
                'moneyness': data.get('moneyness'),
                'option_yield': data.get('option_yield'),
                'dividend_yield': data.get('dividend_yield'),
                'benchmark_index': data.get('benchmark_index'),
                'most_recent_distribution': data.get('most_recent_distribution'),
                'trailing_yield_12m': data.get('trailing_yield_12m'),
                'leverage_ratio': data.get('leverage_ratio'),
                'fund_details': data.get('fund_details'),
                'holdings': data.get('holdings'),
                'distributions': data.get('distributions'),
                'performance_data': data.get('performance_data'),
                'sector_allocation': data.get('sector_allocation'),
                'geographic_allocation': data.get('geographic_allocation')
            }

            # Upsert to database
            result = supabase_upsert('raw_etfs_globalx', [record])

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
    Scrape a single Global X Canada ETF

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if successful, False otherwise
    """
    if ticker not in GLOBALX_ETFS:
        logger.error(f"❌ Unknown ticker: {ticker}")
        logger.info(f"Available tickers: {', '.join(sorted(GLOBALX_ETFS.keys()))}")
        return False

    etf_info = GLOBALX_ETFS[ticker]
    scraper = GlobalXScraper(
        ticker,
        etf_info['name'],
        etf_info.get('category'),
        etf_info.get('type'),
        etf_info.get('leverage')
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
    print(f"  • NAV: {data.get('nav') or '❌'}")
    print(f"  • Market Price: {data.get('market_price') or '❌'}")
    print(f"  • Distribution Yield: {data.get('distribution_yield') or 'N/A'}")
    print(f"  • Net Assets: {data.get('net_assets') or '❌'}")
    print(f"  • Management Fee: {data.get('management_fee') or '❌'}")
    print(f"  • MER: {data.get('mer') or '❌'}")

    if data.get('leverage_ratio'):
        print(f"  • Leverage: {data['leverage_ratio']}")

    if data.get('average_coverage'):
        print(f"\n  Covered Call Metrics:")
        print(f"  • Average Coverage: {data.get('average_coverage')}")
        print(f"  • Moneyness: {data.get('moneyness')}")
        print(f"  • Option Yield: {data.get('option_yield')}")
        print(f"  • Dividend Yield: {data.get('dividend_yield')}")

    holdings = data.get('holdings') or {}
    print(f"\n  • Holdings: {'✅' if holdings.get('top_holdings') else '❌'}")
    if holdings.get('top_holdings'):
        print(f"    - Top Holdings: {len(holdings['top_holdings'])} positions")

    distributions = data.get('distributions') or []
    print(f"  • Distributions: {'✅' if distributions else '❌'} ({len(distributions)} records)")

    performance = data.get('performance_data') or {}
    print(f"  • Performance Data: {'✅' if performance else '❌'}")

    sector = data.get('sector_allocation') or {}
    print(f"  • Sector Allocation: {'✅' if sector else '❌'}")

    geo = data.get('geographic_allocation') or {}
    print(f"  • Geographic Allocation: {'✅' if geo else '❌'}")
    print()

    # Save to database
    return scraper.save_to_database(data)


def scrape_all_etfs(delay: float = 1.5, category: str = None, limit: int = None, test: bool = False) -> Dict[str, bool]:
    """
    Scrape all Global X Canada ETFs

    Args:
        delay: Seconds to wait between requests (default: 1.5)
        category: Filter by category (default: None)
        limit: Limit number of ETFs to scrape (default: None)
        test: Test mode - scrape only 3 ETFs (default: False)

    Returns:
        Dictionary mapping ticker to success status
    """
    # Filter by category if specified
    tickers_to_scrape = list(GLOBALX_ETFS.keys())
    if category:
        tickers_to_scrape = [
            ticker for ticker, info in GLOBALX_ETFS.items()
            if category.lower() in info.get('category', '').lower()
        ]
        if not tickers_to_scrape:
            print(f"❌ No ETFs found for category: {category}")
            return {}

    # Test mode
    if test:
        limit = 3

    # Apply limit if specified
    if limit and limit > 0:
        tickers_to_scrape = tickers_to_scrape[:limit]

    results = {}

    print(f"🚀 Scraping {len(tickers_to_scrape)} Global X Canada ETFs...")
    print(f"⏱️  Delay between requests: {delay} seconds")
    print()

    for i, ticker in enumerate(tickers_to_scrape, 1):
        print("=" * 80)
        print(f"[{i}/{len(tickers_to_scrape)}] {ticker}")
        print("=" * 80)

        success = scrape_single_etf(ticker)
        results[ticker] = success

        if success:
            print(f"✅ {ticker} complete")
        else:
            print(f"❌ {ticker} failed")
        print()

        # Delay between requests to be respectful
        if i < len(tickers_to_scrape):
            logger.info(f"⏳ Waiting {delay} seconds before next scrape...")
            time.sleep(delay)

    return results


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Scrape Global X Canada ETF data')
    parser.add_argument('--ticker', '-t', type=str, help='Specific ticker to scrape (e.g., ENCC, CNDX)')
    parser.add_argument('--all', '-a', action='store_true', help='Scrape all Global X Canada ETFs')
    parser.add_argument('--category', '-c', type=str,
                       help='Scrape by category (e.g., "Covered Call", "Thematic", "BetaPro")')
    parser.add_argument('--list', '-l', action='store_true', help='List available tickers by category')
    parser.add_argument('--delay', '-d', type=float, default=1.5,
                       help='Delay in seconds between requests (default: 1.5)')
    parser.add_argument('--limit', type=int, help='Limit number of ETFs to scrape')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only 3 ETFs')

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 Global X Canada ETF Scraper")
    print("=" * 80)
    print()

    # List available tickers
    if args.list:
        print(f"Available Global X Canada ETFs ({len(GLOBALX_ETFS)}):")
        print()

        # Group by category
        categories = {}
        for ticker, info in GLOBALX_ETFS.items():
            category = info.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append((ticker, info['name']))

        category_order = [
            'Cash & Fixed Income',
            'Corporate Class (Tax-Efficient)',
            'Thematic',
            'Enhanced Growth (25% Leveraged)',
            'Equity Essentials - Core',
            'Covered Call - Index',
            'Covered Call - Sector',
            'Enhanced Covered Call (25% Leveraged)',
            'Commodities - Covered Call',
            'Cryptocurrency - Covered Call',
            'Precious Metals',
            'Asset Allocation',
            'BetaPro (Leveraged/Inverse)',
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

    # Scrape all ETFs or by category
    if args.all or args.category:
        results = scrape_all_etfs(
            delay=args.delay,
            category=args.category,
            limit=args.limit,
            test=args.test
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
