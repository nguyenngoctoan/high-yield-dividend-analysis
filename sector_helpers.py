"""
Helper functions for fetching and formatting sector data from FMP API.

Used by both populate_sector_data.py (backfill) and update_stock.py (ongoing updates).
"""

import requests
from time import sleep
from threading import Semaphore

# Module-level rate limiter
fmp_limiter = Semaphore(10)

def get_etf_sector_weightings(symbol, api_key):
    """
    Get sector weightings for an ETF from FMP.

    Args:
        symbol: Stock symbol
        api_key: FMP API key

    Returns:
        Dict of {sector: percentage} or None if not an ETF or no data
    """
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/etf-sector-weightings/{symbol}?apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            sector_data = {}
            for item in data:
                sector = item.get('sector', '').strip()
                weight = item.get('weightPercentage', 0)

                if sector and weight:
                    try:
                        weight_float = float(weight) if isinstance(weight, (int, float, str)) else 0
                        if weight_float > 0:
                            sector_data[sector] = weight_float
                    except (ValueError, TypeError):
                        pass

            return sector_data if sector_data else None

        return None
    except Exception:
        # ETF sector weightings may not exist for all symbols
        return None
    finally:
        fmp_limiter.release()
        sleep(0.05)  # Small delay


def get_company_sector(symbol, api_key):
    """
    Get sector for a regular stock from company profile.

    Args:
        symbol: Stock symbol
        api_key: FMP API key

    Returns:
        Sector string or None
    """
    fmp_limiter.acquire()
    try:
        url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={api_key}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and isinstance(data, list) and len(data) > 0:
            sector = data[0].get('sector', '').strip()
            return sector if sector else None

        return None
    except Exception:
        return None
    finally:
        fmp_limiter.release()
        sleep(0.05)


def format_sector_string(sector_data):
    """
    Format sector data as a string.

    Args:
        sector_data: Either a dict of {sector: percentage} or a single sector string

    Returns:
        Formatted string like "Technology (45.2%), Healthcare (30.1%)" or just "Technology"
    """
    if isinstance(sector_data, dict):
        # Multiple sectors with percentages (ETF)
        sorted_sectors = sorted(sector_data.items(), key=lambda x: -x[1])

        # Only include sectors with >=1% weight
        significant_sectors = [(sector, pct) for sector, pct in sorted_sectors if pct >= 1.0]

        if not significant_sectors:
            # If no significant sectors, take top 3
            significant_sectors = sorted_sectors[:3]

        if significant_sectors:
            formatted_parts = [f"{sector} ({pct:.1f}%)" for sector, pct in significant_sectors]
            return ", ".join(formatted_parts)

        return None

    elif isinstance(sector_data, str) and sector_data:
        # Single sector (regular stock)
        return sector_data

    return None


def get_sector_for_symbol(symbol, api_key):
    """
    Get formatted sector string for any symbol (stock or ETF).

    Strategy:
    1. Try ETF sector weightings first (works for ETFs, fails gracefully for stocks)
    2. Fall back to company profile sector (works for stocks)
    3. Format appropriately

    Args:
        symbol: Stock symbol
        api_key: FMP API key

    Returns:
        Formatted sector string or None

    Examples:
        - Stock: "Technology"
        - ETF: "Technology (45.2%), Healthcare (30.1%), Financial (24.7%)"
    """
    # Try ETF sector weightings first
    etf_sectors = get_etf_sector_weightings(symbol, api_key)
    if etf_sectors:
        return format_sector_string(etf_sectors)

    # Fall back to company profile
    company_sector = get_company_sector(symbol, api_key)
    if company_sector:
        return format_sector_string(company_sector)

    return None
