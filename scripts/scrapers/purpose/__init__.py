"""
Purpose Investments ETF Scraper Package

A comprehensive scraper for all 81 Purpose Investments ETFs across 7 categories.

Features:
- NO Selenium required (uses requests + BeautifulSoup)
- Extracts embedded JSON from Next.js server-side rendering
- Supports all Purpose ETF categories:
  - Equity (Yield Shares US Tech, Yield Shares Canadian, Traditional)
  - Fixed Income
  - Cryptocurrency
  - Alternatives
  - Multi-Asset
  - Commodities
  - Cash Management

Version: 1.0.0
Created: 2025-11-16
"""

__version__ = '1.0.0'
__author__ = 'Purpose ETF Data Aggregator'
__description__ = 'Purpose Investments ETF scraper for high-yield dividend analysis'

from .scrape_purpose_all import (
    PurposeScraper,
    PURPOSE_ETFS,
    scrape_single_etf,
    scrape_all_etfs,
    validate_etf_urls
)

__all__ = [
    'PurposeScraper',
    'PURPOSE_ETFS',
    'scrape_single_etf',
    'scrape_all_etfs',
    'validate_etf_urls'
]
