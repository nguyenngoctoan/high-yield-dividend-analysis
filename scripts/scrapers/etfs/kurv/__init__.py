"""
Kurv ETF Scrapers

This package contains scrapers for Kurv ETF data.

Kurv ETFs offer:
- Growth & Income strategies (technology titans, high income)
- Precious Metals Income (gold and silver with enhanced yield)
- Single Stock Income (yield premium strategy on FAANG+ stocks)

Modules:
- scrape_kurv_all: Universal scraper for all 10 Kurv ETFs

Usage:
    from scripts.scrapers.kurv.scrape_kurv_all import scrape_single_etf, scrape_all_etfs

    # Scrape single ETF
    scrape_single_etf('KQQQ')

    # Scrape all ETFs
    scrape_all_etfs(delay=5)
"""

__version__ = '1.0.0'
__author__ = 'Dividend Analysis Team'
