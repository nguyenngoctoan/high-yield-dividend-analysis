"""
Defiance ETF Scrapers

This package contains scrapers for Defiance ETF data.

Defiance ETFs offer:
- Thematic investing (quantum, AI, fintech, 5G/6G)
- Leveraged exposure (2X daily long/short single stocks)
- Enhanced income (1.75X leverage + covered calls)
- Income generation (0DTE options, covered calls, weekly distributions)

Modules:
- scrape_defiance_all: Universal scraper for all 57 Defiance ETFs

Usage:
    from scripts.scrapers.defiance.scrape_defiance_all import scrape_single_etf, scrape_all_etfs

    # Scrape single ETF
    scrape_single_etf('QQQY')

    # Scrape all ETFs
    scrape_all_etfs(delay=5)
"""

__version__ = '1.0.0'
__author__ = 'Dividend Analysis Team'
