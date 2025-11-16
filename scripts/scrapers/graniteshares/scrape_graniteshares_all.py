#!/usr/bin/env python3
"""
GraniteShares ETF Scraper (All Funds)

Scrapes comprehensive data from all GraniteShares ETF pages including:
- Performance data
- Fund overview
- Fund details (expense ratio, inception date, AUM, NAV)
- Distributions
- Holdings

All data stored as JSON in raw_etfs_graniteshares table.
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


# GraniteShares ETF Configuration (59 ETFs across 6 categories)
GRANITESHARES_ETFS = {
    # YieldBOOST (16)
    'AMYY': {
        'name': 'GraniteShares YieldBOOST AMD ETF',
        'category': 'YieldBOOST',
        'underlying': 'Advanced Micro Devices, Inc.',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/amyy/'
    },
    'AZYY': {
        'name': 'GraniteShares YieldBOOST AMZN ETF',
        'category': 'YieldBOOST',
        'underlying': 'Amazon',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/azyy/'
    },
    'BBYY': {
        'name': 'GraniteShares YieldBOOST BABA ETF',
        'category': 'YieldBOOST',
        'underlying': 'Alibaba Group Holding Limited',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/bbyy/'
    },
    'COYY': {
        'name': 'GraniteShares YieldBOOST COIN ETF',
        'category': 'YieldBOOST',
        'underlying': 'Coinbase Global, Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/coyy/'
    },
    'FBYY': {
        'name': 'GraniteShares YieldBOOST META ETF',
        'category': 'YieldBOOST',
        'underlying': 'Meta Platforms Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/fbyy/'
    },
    'HOYY': {
        'name': 'GraniteShares YieldBOOST HOOD ETF',
        'category': 'YieldBOOST',
        'underlying': 'Robinhood Markets, Inc. (HOOD)',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/hoyy/'
    },
    'IOYY': {
        'name': 'GraniteShares YieldBOOST IONQ ETF',
        'category': 'YieldBOOST',
        'underlying': 'IonQ Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/ioyy/'
    },
    'MAAY': {
        'name': 'GraniteShares YieldBOOST MARA ETF',
        'category': 'YieldBOOST',
        'underlying': 'MARA Holdings Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/maay/'
    },
    'MTYY': {
        'name': 'GraniteShares YieldBOOST MSTR ETF',
        'category': 'YieldBOOST',
        'underlying': 'MicroStrategy Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/mtyy/'
    },
    'NVYY': {
        'name': 'GraniteShares YieldBOOST NVDA ETF',
        'category': 'YieldBOOST',
        'underlying': 'NVIDIA Corp',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/nvyy/'
    },
    'PLYY': {
        'name': 'GraniteShares YieldBOOST PLTR ETF',
        'category': 'YieldBOOST',
        'underlying': 'Palantir Technologies Inc.',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/plyy/'
    },
    'SMYY': {
        'name': 'GraniteShares YieldBOOST SMCI ETF',
        'category': 'YieldBOOST',
        'underlying': 'Super Micro Computer Inc. (SMCI)',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/smyy/'
    },
    'TQQY': {
        'name': 'GraniteShares YieldBOOST QQQ ETF',
        'category': 'YieldBOOST',
        'underlying': 'Nasdaq-100 Index',
        'leverage': '3',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/tqqy/'
    },
    'TSYY': {
        'name': 'GraniteShares YieldBOOST TSLA ETF',
        'category': 'YieldBOOST',
        'underlying': 'Tesla Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/tsyy/'
    },
    'XBTY': {
        'name': 'GraniteShares YieldBOOST Bitcoin ETF',
        'category': 'YieldBOOST',
        'underlying': 'Bitcoin',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/xbty/'
    },
    'YSPY': {
        'name': 'GraniteShares YieldBOOST SPY ETF',
        'category': 'YieldBOOST',
        'underlying': 'S&P 500 Index',
        'leverage': '3',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/yspy/'
    },

    # Leveraged (38)
    'AAPB': {
        'name': 'GraniteShares 2x Long AAPL Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Apple',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/aapb/'
    },
    'AMDL': {
        'name': 'GraniteShares 2x Long AMD Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Advanced Micro Devices, Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/amdl/'
    },
    'AMZZ': {
        'name': 'GraniteShares 2x Long AMZN Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Amazon',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/amzz/'
    },
    'AVGU': {
        'name': 'GraniteShares 2x Long AVGO Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Broadcom Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/avgu/'
    },
    'BABX': {
        'name': 'GraniteShares 2x Long BABA Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Alibaba Group Holding Limited',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/babx/'
    },
    'BULX': {
        'name': 'GraniteShares 2x Long BULL Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Webull Corporation',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/bulx/'
    },
    'CONI': {
        'name': 'GraniteShares 2x Short COIN Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Coinbase Global Inc',
        'leverage': '-2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/coni/'
    },
    'CONL': {
        'name': 'GraniteShares 2x Long COIN Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Coinbase Global Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/conl/'
    },
    'CRWL': {
        'name': 'GraniteShares 2x Long CRWD Daily ETF',
        'category': 'Leveraged',
        'underlying': 'CrowdStrike Holdings Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/crwl/'
    },
    'DLLL': {
        'name': 'GraniteShares 2x Long DELL Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Dell Technologies Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/dlll/'
    },
    'ETRL': {
        'name': 'GraniteShares 2x Long ETOR Daily ETF',
        'category': 'Leveraged',
        'underlying': 'eToro Group Ltd',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/etrl/'
    },
    'FBL': {
        'name': 'GraniteShares 2x Long META Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Meta Platforms Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/fbl/'
    },
    'INTW': {
        'name': 'GraniteShares 2x Long INTC Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Intel Corp',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/intw/'
    },
    'IONL': {
        'name': 'GraniteShares 2x Long IONQ Daily ETF',
        'category': 'Leveraged',
        'underlying': 'IonQ Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/ionl/'
    },
    'ISUL': {
        'name': 'GraniteShares 2x Long ISRG Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Intuitive Surgical, Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/isul/'
    },
    'LCDL': {
        'name': 'GraniteShares 2x Long LCID Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Lucid Group Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/lcdl/'
    },
    'MRAL': {
        'name': 'GraniteShares 2x Long MARA Daily ETF',
        'category': 'Leveraged',
        'underlying': 'MARA Holdings Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/mral/'
    },
    'MSDD': {
        'name': 'GraniteShares 2x Short MSTR Daily ETF',
        'category': 'Leveraged',
        'underlying': 'MicroStrategy Inc',
        'leverage': '-2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/msdd/'
    },
    'MSFL': {
        'name': 'GraniteShares 2x Long MSFT Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Microsoft',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/msfl/'
    },
    'MSTP': {
        'name': 'GraniteShares 2x Long MSTR Daily ETF',
        'category': 'Leveraged',
        'underlying': 'MicroStrategy Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/mstp/'
    },
    'MULL': {
        'name': 'GraniteShares 2x Long MU Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Micron Technology Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/mull/'
    },
    'MVLL': {
        'name': 'GraniteShares 2x Long MRVL Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Marvell Technology, Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/mvll/'
    },
    'NBIL': {
        'name': 'GraniteShares 2x Long NBIS Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Nebius Group N.V',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/nbil/'
    },
    'NOWL': {
        'name': 'GraniteShares 2x Long NOW Daily ETF',
        'category': 'Leveraged',
        'underlying': 'ServiceNow Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/nowl/'
    },
    'NVD': {
        'name': 'GraniteShares 2x Short NVDA Daily ETF',
        'category': 'Leveraged',
        'underlying': 'NVIDIA Corp',
        'leverage': '-2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/nvd/'
    },
    'NVDL': {
        'name': 'GraniteShares 2x Long NVDA Daily ETF',
        'category': 'Leveraged',
        'underlying': 'NVIDIA Corp',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/nvdl/'
    },
    'PDDL': {
        'name': 'GraniteShares 2x Long PDD Daily ETF',
        'category': 'Leveraged',
        'underlying': 'PDD Holdings Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/pddl/'
    },
    'PTIR': {
        'name': 'GraniteShares 2x Long PLTR Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Palantir Technologies Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/ptir/'
    },
    'QCML': {
        'name': 'GraniteShares 2x Long QCOM Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Qualcomm Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/qcml/'
    },
    'RDTL': {
        'name': 'GraniteShares 2x Long RDDT Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Reddit Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/rdtl/'
    },
    'RVNL': {
        'name': 'GraniteShares 2x Long RIVN Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Rivian Automotive Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/rvnl/'
    },
    'SMCL': {
        'name': 'GraniteShares 2x Long SMCI Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Super Micro Computer Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/smcl/'
    },
    'TSDD': {
        'name': 'GraniteShares 2x Short TSLA Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Tesla Inc',
        'leverage': '-2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/tsdd/'
    },
    'TSL': {
        'name': 'GraniteShares 1.25x Long TSLA Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Tesla Inc',
        'leverage': '1.25',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/tsl/'
    },
    'TSLR': {
        'name': 'GraniteShares 2x Long TSLA Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Tesla Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/tslr/'
    },
    'TSMU': {
        'name': 'GraniteShares 2x Long TSM Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Taiwan Semiconductor Manufacturing Co Ltd',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/tsmu/'
    },
    'UBRL': {
        'name': 'GraniteShares 2x Long Uber Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Uber Technologies Inc',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/ubrl/'
    },
    'VRTL': {
        'name': 'GraniteShares 2x Long VRT Daily ETF',
        'category': 'Leveraged',
        'underlying': 'Vertiv Holdings Co',
        'leverage': '2',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/vrtl/'
    },

    # Commodities (2)
    'COMB': {
        'name': 'GraniteShares Bloomberg Commodity Broad Strategy No K-1 ETF',
        'category': 'Commodities',
        'underlying': 'Bloomberg Commodity Index',
        'leverage': '0',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/comb/'
    },
    'PLTM': {
        'name': 'GraniteShares Platinum Trust',
        'category': 'Commodities',
        'underlying': 'Spot Platinum',
        'leverage': '0',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/pltm/'
    },

    # Gold (1)
    'BAR': {
        'name': 'GraniteShares Gold Trust',
        'category': 'Gold',
        'underlying': 'Physical Gold',
        'leverage': '0',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/bar/'
    },

    # Equity (1)
    'DRUP': {
        'name': 'GraniteShares Nasdaq Select Disruptors ETF',
        'category': 'Equity',
        'underlying': '',
        'leverage': '0',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/drup/'
    },

    # Income (1)
    'HIPS': {
        'name': 'GraniteShares HIPS US High Income ETF',
        'category': 'Income',
        'underlying': 'EQM High Income Pass-Through Securities Index',
        'leverage': '0',
        'url': 'https://graniteshares.com/institutional/us/en-us/etfs/hips/'
    }
}


class GraniteSharesScraper:
    """Scraper for GraniteShares ETF data"""

    def __init__(self, ticker: str, fund_name: str, url: str, category: str = None, underlying: str = None, leverage: str = None):
        """
        Initialize the scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            url: GraniteShares ETF page URL
            category: ETF category
            underlying: Underlying security
            leverage: Leverage multiplier
        """
        self.ticker = ticker
        self.fund_name = fund_name
        self.url = url
        self.category = category
        self.underlying = underlying
        self.leverage = leverage

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
                'category': self.category,
                'underlying': self.underlying,
                'leverage': self.leverage,
                'scraped_at': datetime.now().isoformat(),
                'expense_ratio': self._extract_expense_ratio(soup),
                'inception_date': self._extract_inception_date(soup),
                'nav': self._extract_nav(soup),
                'aum': self._extract_aum(soup),
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

    def _extract_text_by_class(self, soup: BeautifulSoup, class_name: str) -> Optional[str]:
        """Helper to extract text by class name"""
        elem = soup.find(class_=class_name)
        if elem:
            return elem.get_text(strip=True)
        return None

    def _extract_expense_ratio(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract expense ratio from page"""
        # Look for elements with class or text containing "expense ratio"
        # GraniteShares uses various formats, check multiple possibilities
        value = self._extract_text_by_class(soup, 'pExpenseRatio')
        if value:
            logger.info(f"✅ Extracted expense ratio: {value}")
            return value

        # Fallback: search in all text
        keywords = ['expense ratio', 'net expense']
        for keyword in keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for elem in elements:
                parent = elem.parent
                if parent:
                    siblings = parent.find_next_siblings()
                    for sibling in siblings:
                        text = sibling.get_text(strip=True)
                        if '%' in text and re.search(r'\d', text):
                            logger.info(f"✅ Extracted expense ratio: {text}")
                            return text

        logger.warning("⚠️  No expense ratio found")
        return None

    def _extract_inception_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract inception date from page"""
        value = self._extract_text_by_class(soup, 'pInception')
        if value:
            logger.info(f"✅ Extracted inception date: {value}")
            return value

        logger.warning("⚠️  No inception date found")
        return None

    def _extract_nav(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract NAV from page"""
        value = self._extract_text_by_class(soup, 'pNav')
        if value:
            logger.info(f"✅ Extracted NAV: {value}")
            return value

        logger.warning("⚠️  No NAV found")
        return None

    def _extract_aum(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract AUM from page"""
        value = self._extract_text_by_class(soup, 'pAum')
        if value:
            logger.info(f"✅ Extracted AUM: {value}")
            return value

        logger.warning("⚠️  No AUM found")
        return None

    def _extract_market_price(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract market price from page"""
        value = self._extract_text_by_class(soup, 'pClose')
        if value:
            logger.info(f"✅ Extracted market price: {value}")
            return value

        logger.warning("⚠️  No market price found")
        return None

    def _extract_premium_discount(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract premium/discount from page"""
        value = self._extract_text_by_class(soup, 'pDisc')
        if value:
            logger.info(f"✅ Extracted premium/discount: {value}")
            return value

        logger.warning("⚠️  No premium/discount found")
        return None

    def _extract_fund_details(self, soup: BeautifulSoup) -> Optional[Dict[str, str]]:
        """Extract fund details from page"""
        try:
            fund_details = {}

            # Look for any table with fund details
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
        """Extract performance data from page"""
        try:
            # Look for performance table (class="etf-chart-details_content_performance-table")
            perf_table = soup.find('div', class_='etf-chart-details_content_performance-table')
            if not perf_table:
                logger.warning("⚠️  No performance data found")
                return None

            # Parse the table structure
            # GraniteShares uses spans in a grid layout
            spans = perf_table.find_all('span')
            if not spans:
                return None

            # Extract headers and data
            performance_data = {}
            # This will vary by page structure, best effort parsing
            logger.info(f"✅ Extracted performance data: {len(spans)} elements")
            return {'raw_data': [span.get_text(strip=True) for span in spans]}

        except Exception as e:
            logger.error(f"❌ Error extracting performance data: {e}")
            return None

    def _extract_distributions(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """Extract distribution data from page"""
        try:
            # Look for distribution calendar table (class="etf-chart-details_content_distribution-calendar-table")
            dist_table = soup.find('div', class_='etf-chart-details_content_distribution-calendar-table')
            if not dist_table:
                logger.warning("⚠️  No distributions found")
                return None

            # Parse the table structure
            spans = dist_table.find_all('span', class_='Mono2')
            if len(spans) < 4:
                return None

            # Headers: Ex Date, Record Date, Payment Date, Distribution
            distributions = []
            data_spans = dist_table.find_all('span', class_=lambda x: x != 'Mono2')

            # Group by 4 (one row = 4 cells)
            for i in range(0, len(data_spans), 4):
                if i + 3 < len(data_spans):
                    distributions.append({
                        'Ex Date': data_spans[i].get_text(strip=True),
                        'Record Date': data_spans[i+1].get_text(strip=True),
                        'Payment Date': data_spans[i+2].get_text(strip=True),
                        'Distribution': data_spans[i+3].get_text(strip=True)
                    })

            if distributions:
                logger.info(f"✅ Extracted distributions: {len(distributions)} records")
                return distributions

            return None

        except Exception as e:
            logger.error(f"❌ Error extracting distributions: {e}")
            return None

    def _extract_holdings(self, soup: BeautifulSoup) -> Optional[List[Dict[str, str]]]:
        """Extract holdings data from page"""
        try:
            # Look for fund allocation table (class="etf-chart-details_content_fund-allocation-table")
            holdings_table = soup.find('div', class_='etf-chart-details_content_fund-allocation-table')
            if not holdings_table:
                logger.warning("⚠️  No holdings found")
                return None

            # Parse the table structure
            holdings = []
            security_names = holdings_table.find_all('span', class_='security-name')

            for security in security_names:
                # Get siblings for share/par, value, allocation
                parent_row = security.parent
                if parent_row:
                    cells = parent_row.find_all('span')
                    if len(cells) >= 4:
                        holdings.append({
                            'Security': cells[0].get_text(strip=True),
                            'Share/Par': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                            'Value': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                            'Allocation': cells[3].get_text(strip=True) if len(cells) > 3 else ''
                        })

            if holdings:
                logger.info(f"✅ Extracted holdings: {len(holdings)} positions")
                return holdings

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
                'category': data.get('category'),
                'underlying': data.get('underlying'),
                'leverage': data.get('leverage'),
                'scraped_at': data['scraped_at'],
                'expense_ratio': data.get('expense_ratio'),
                'inception_date': data.get('inception_date'),
                'nav': data.get('nav'),
                'aum': data.get('aum'),
                'market_price': data.get('market_price'),
                'premium_discount': data.get('premium_discount'),
                'fund_details': data.get('fund_details'),
                'performance_data': data.get('performance_data'),
                'distributions': data.get('distributions'),
                'holdings': data.get('holdings')
            }

            # Upsert to database
            result = supabase_upsert('raw_etfs_graniteshares', [record])

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
    Scrape a single GraniteShares ETF

    Args:
        ticker: ETF ticker symbol

    Returns:
        True if successful, False otherwise
    """
    if ticker not in GRANITESHARES_ETFS:
        logger.error(f"❌ Unknown ticker: {ticker}")
        logger.info(f"Available tickers: {', '.join(GRANITESHARES_ETFS.keys())}")
        return False

    etf_info = GRANITESHARES_ETFS[ticker]
    scraper = GraniteSharesScraper(
        ticker,
        etf_info['name'],
        etf_info['url'],
        etf_info.get('category'),
        etf_info.get('underlying'),
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
    print(f"  • Underlying: {data.get('underlying') or '❌'}")
    print(f"  • Leverage: {data.get('leverage') or '❌'}")
    print(f"  • Expense Ratio: {data.get('expense_ratio') or '❌'}")
    print(f"  • Inception Date: {data.get('inception_date') or '❌'}")
    print(f"  • NAV: {data.get('nav') or '❌'}")
    print(f"  • AUM: {data.get('aum') or '❌'}")
    print(f"  • Market Price: {data.get('market_price') or '❌'}")
    print(f"  • Premium/Discount: {data.get('premium_discount') or '❌'}")

    details = data.get('fund_details') or {}
    print(f"  • Fund Details: {'✅' if details else '❌'} ({len(details)} fields)")

    performance = data.get('performance_data') or {}
    print(f"  • Performance Data: {'✅' if performance else '❌'}")

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

    for ticker, info in GRANITESHARES_ETFS.items():
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
        print(f"✅ All {len(GRANITESHARES_ETFS)} ETF URLs validated successfully!")
        print()

    return validation_results


def scrape_all_etfs(delay: int = 5, skip_validation: bool = False, category: str = None, limit: int = None) -> Dict[str, bool]:
    """
    Scrape all GraniteShares ETFs

    Args:
        delay: Seconds to wait between requests (default: 5)
        skip_validation: Skip URL validation step (default: False)
        category: Filter by category (default: None)
        limit: Limit number of ETFs to scrape (default: None)

    Returns:
        Dictionary mapping ticker to success status
    """
    # Filter by category if specified
    tickers_to_scrape = list(GRANITESHARES_ETFS.keys())
    if category:
        tickers_to_scrape = [
            ticker for ticker, info in GRANITESHARES_ETFS.items()
            if info.get('category', '').lower() == category.lower()
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

    print(f"🚀 Scraping {len(valid_tickers)} GraniteShares ETFs...")
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
    parser = argparse.ArgumentParser(description='Scrape GraniteShares ETF data')
    parser.add_argument('--ticker', '-t', type=str, help='Specific ticker to scrape (e.g., NVDL)')
    parser.add_argument('--all', '-a', action='store_true', help='Scrape all GraniteShares ETFs')
    parser.add_argument('--category', '-c', type=str,
                       help='Scrape by category (YieldBOOST, Leveraged, Commodities, Gold, Equity, Income)')
    parser.add_argument('--list', '-l', action='store_true', help='List available tickers')
    parser.add_argument('--delay', '-d', type=int, default=5,
                       help='Delay in seconds between requests when scraping all (default: 5)')
    parser.add_argument('--limit', type=int, help='Limit number of ETFs to scrape')
    parser.add_argument('--test', action='store_true', help='Test mode: scrape only 3 ETFs')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip URL validation before scraping (faster but may fail on invalid URLs)')

    args = parser.parse_args()

    print("=" * 80)
    print("🎯 GraniteShares ETF Scraper")
    print("=" * 80)
    print()

    # List available tickers
    if args.list:
        print(f"Available GraniteShares ETFs ({len(GRANITESHARES_ETFS)}):")
        print()

        # Group by category
        categories = {}
        for ticker, info in GRANITESHARES_ETFS.items():
            category = info.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append((ticker, info['name']))

        for category in ['YieldBOOST', 'Leveraged', 'Commodities', 'Gold', 'Equity', 'Income', 'Other']:
            if category in categories:
                print(f"{category} ({len(categories[category])}):")
                for ticker, name in sorted(categories[category]):
                    print(f"  {ticker:8s} - {name}")
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
