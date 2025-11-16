"""
Global X Canada ETF Scraper Package

Comprehensive web scraper for all 107 Global X Canada ETF products.
Extracts fund metrics, covered call statistics, holdings, distributions,
and performance data.

Supports 13 ETF categories:
1. Cash & Fixed Income (19 ETFs)
2. Corporate Class (8 ETFs) - Tax-efficient structures
3. Thematic (16 ETFs) - AI, semiconductors, defence, healthcare, etc.
4. Enhanced Growth (6 ETFs) - 25% leveraged
5. Equity Essentials (12 ETFs) - Core index tracking
6. Covered Call - Index (9 ETFs)
7. Covered Call - Sector (2 ETFs)
8. Enhanced Covered Call (9 ETFs) - 25% leveraged
9. Commodities - Covered Call (5 ETFs)
10. Cryptocurrency - Covered Call (4 ETFs)
11. Precious Metals (7 ETFs)
12. Asset Allocation (8 ETFs)
13. BetaPro (7 ETFs) - 2x leveraged/inverse

Key Features:
- Static HTML parsing - NO Selenium needed
- Covered call metrics for 30+ ETFs
- Complete holdings and distribution history
- Performance data (annualized + calendar year)
- Automatic currency variant handling (.U, .F suffixes)

Usage:
    from scrape_globalx_all import scrape_single_etf, scrape_all_etfs

    # Scrape single ETF
    success = scrape_single_etf('ENCC')

    # Scrape all ETFs
    results = scrape_all_etfs(delay=1.5)

    # Scrape by category
    results = scrape_all_etfs(category='Covered Call')

Database:
    Table: raw_etfs_globalx
    View: v_globalx_latest (latest record per ticker)
    Migration: supabase/migrations/20251116_add_globalx_etf_data.sql

Author: High Yield Dividend Analysis Project
Version: 1.0.0
Date: 2025-11-16
"""

__version__ = '1.0.0'
__author__ = 'High Yield Dividend Analysis Project'
__date__ = '2025-11-16'

# Total ETF count
TOTAL_ETFS = 107
TOTAL_CATEGORIES = 13

# Category breakdown
CATEGORY_COUNTS = {
    'Cash & Fixed Income': 19,
    'Corporate Class (Tax-Efficient)': 8,
    'Thematic': 16,
    'Enhanced Growth (25% Leveraged)': 6,
    'Equity Essentials - Core': 12,
    'Covered Call - Index': 9,
    'Covered Call - Sector': 2,
    'Enhanced Covered Call (25% Leveraged)': 9,
    'Commodities - Covered Call': 5,
    'Cryptocurrency - Covered Call': 4,
    'Precious Metals': 7,
    'Asset Allocation': 8,
    'BetaPro (Leveraged/Inverse)': 7
}

# Export main classes and functions
from .scrape_globalx_all import (
    GlobalXScraper,
    scrape_single_etf,
    scrape_all_etfs,
    GLOBALX_ETFS
)

__all__ = [
    'GlobalXScraper',
    'scrape_single_etf',
    'scrape_all_etfs',
    'GLOBALX_ETFS',
    'TOTAL_ETFS',
    'TOTAL_CATEGORIES',
    'CATEGORY_COUNTS'
]
