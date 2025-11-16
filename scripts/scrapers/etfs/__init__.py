#!/usr/bin/env python3
"""
ETF Scraper Package

Unified package for all ETF data scrapers with shared utilities.

Providers:
- YieldMax: 57 ETFs (covered call strategies)
- Roundhill: 15+ ETFs (options income)
- Neos: 10+ ETFs (enhanced income)
- Kurv: 12+ ETFs (yield enhancement)
- GraniteShares: 25+ ETFs (leveraged income)
- Defiance: 20+ ETFs (thematic income)
- Global X Canada: 30+ ETFs (Canadian covered calls)
- Purpose: 40+ ETFs (monthly income, Yield Shares)
"""

from .common import (
    setup_logging,
    get_chrome_options,
    create_chrome_driver,
    safe_find_element,
    safe_find_elements,
    save_to_database,
    scrape_with_retry,
    BaseETFScraper,
    batch_scrape_etfs,
)

__all__ = [
    'setup_logging',
    'get_chrome_options',
    'create_chrome_driver',
    'safe_find_element',
    'safe_find_elements',
    'save_to_database',
    'scrape_with_retry',
    'BaseETFScraper',
    'batch_scrape_etfs',
]

__version__ = '1.0.0'
