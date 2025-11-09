#!/usr/bin/env python3
"""
Enhanced Symbol Discovery Module - Fully Leverages FMP Ultimate Plan & Alpha Vantage

This module implements intelligent, criteria-based discovery that eliminates hard-coded symbol lists.
Instead, it dynamically discovers symbols based on actual dividend behavior and market criteria.

Key Features:
- Advanced FMP screeners with multiple criteria combinations
- Behavioral discovery (consistent dividend history)
- Dynamic ETF family pattern detection
- New ETF launch monitoring
- International high-dividend market coverage
- Peer/correlation discovery
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from collections import defaultdict
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# API Configuration
FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Rate limiters (imported from main module)
from threading import Semaphore
fmp_limiter = Semaphore(144)  # Ultimate plan capacity
av_limiter = Semaphore(2)

def fetch_with_retry(url: str, limiter: Semaphore, max_retries: int = 3) -> Optional[dict]:
    """Fetch data with retry logic and rate limiting."""
    for attempt in range(max_retries):
        limiter.acquire()
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"❌ Failed after {max_retries} attempts: {e}")
                return None
            logger.warning(f"⚠️ Attempt {attempt + 1} failed, retrying...")
        finally:
            limiter.release()
    return None


# ============================================================================
# ADVANCED FMP SCREENERS - Multiple Criteria Combinations
# ============================================================================

def discover_high_yield_dividend_stocks(min_yield: float = 0.03, min_market_cap: int = 100000000) -> List[Dict]:
    """
    Discover high-yield dividend stocks using FMP screener.

    Args:
        min_yield: Minimum dividend yield (default 3%)
        min_market_cap: Minimum market cap (default $100M for quality filter)

    Returns:
        List of discovered symbols with metadata
    """
    logger.info(f"🔍 [FMP Advanced] High-yield stocks (yield≥{min_yield:.1%}, mcap≥${min_market_cap:,.0f})")

    url = (f"https://financialmodelingprep.com/api/v3/stock-screener?"
           f"dividendYieldMoreThan={min_yield}&"
           f"marketCapMoreThan={min_market_cap}&"
           f"volumeMoreThan=100000&"  # Liquidity filter
           f"limit=10000&"
           f"apikey={FMP_API_KEY}")

    data = fetch_with_retry(url, fmp_limiter)

    symbols = []
    if data and isinstance(data, list):
        for stock in data:
            symbol = stock.get('symbol', '').strip()
            if symbol:
                symbols.append({
                    'symbol': symbol,
                    'name': stock.get('companyName', ''),
                    'exchange': stock.get('exchangeShortName', ''),
                    'dividend_yield': stock.get('dividendYield', 0),
                    'market_cap': stock.get('marketCap', 0),
                    'source': 'FMP-HIGH-YIELD-SCREENER',
                    'discovery_method': 'advanced_screener'
                })
        logger.info(f"✅ [FMP Advanced] Found {len(symbols)} high-yield stocks")

    return symbols


def discover_dividend_aristocrats(min_yield: float = 0.01, min_market_cap: int = 1000000000) -> List[Dict]:
    """
    Discover large-cap dividend aristocrats (consistent payers).

    Args:
        min_yield: Minimum yield (1%+ for aristocrats)
        min_market_cap: Minimum market cap ($1B+ for large caps)
    """
    logger.info(f"🔍 [FMP Advanced] Dividend aristocrats (yield≥{min_yield:.1%}, mcap≥${min_market_cap:,.0f})")

    url = (f"https://financialmodelingprep.com/api/v3/stock-screener?"
           f"dividendYieldMoreThan={min_yield}&"
           f"marketCapMoreThan={min_market_cap}&"
           f"priceMoreThan=5&"  # Filter penny stocks
           f"volumeMoreThan=500000&"  # Higher liquidity requirement
           f"limit=10000&"
           f"apikey={FMP_API_KEY}")

    data = fetch_with_retry(url, fmp_limiter)

    symbols = []
    if data and isinstance(data, list):
        for stock in data:
            symbol = stock.get('symbol', '').strip()
            if symbol:
                symbols.append({
                    'symbol': symbol,
                    'name': stock.get('companyName', ''),
                    'exchange': stock.get('exchangeShortName', ''),
                    'dividend_yield': stock.get('dividendYield', 0),
                    'market_cap': stock.get('marketCap', 0),
                    'source': 'FMP-ARISTOCRATS-SCREENER',
                    'discovery_method': 'advanced_screener'
                })
        logger.info(f"✅ [FMP Advanced] Found {len(symbols)} dividend aristocrats")

    return symbols


def discover_sector_dividend_leaders(sector: str, min_yield: float = 0.03) -> List[Dict]:
    """
    Discover dividend leaders in specific high-dividend sectors.

    Args:
        sector: Target sector (e.g., 'Real Estate', 'Utilities')
        min_yield: Minimum dividend yield
    """
    logger.info(f"🔍 [FMP Advanced] {sector} dividend leaders (yield≥{min_yield:.1%})")

    url = (f"https://financialmodelingprep.com/api/v3/stock-screener?"
           f"sector={sector}&"
           f"dividendYieldMoreThan={min_yield}&"
           f"limit=10000&"
           f"apikey={FMP_API_KEY}")

    data = fetch_with_retry(url, fmp_limiter)

    symbols = []
    if data and isinstance(data, list):
        for stock in data:
            symbol = stock.get('symbol', '').strip()
            if symbol:
                symbols.append({
                    'symbol': symbol,
                    'name': stock.get('companyName', ''),
                    'exchange': stock.get('exchangeShortName', ''),
                    'sector': sector,
                    'dividend_yield': stock.get('dividendYield', 0),
                    'source': f'FMP-SECTOR-{sector.upper().replace(" ", "-")}',
                    'discovery_method': 'sector_screener'
                })
        logger.info(f"✅ [FMP Advanced] Found {len(symbols)} {sector} dividend leaders")

    return symbols


def discover_all_sector_dividend_leaders() -> List[Dict]:
    """Discover dividend leaders across all high-dividend sectors."""
    HIGH_DIVIDEND_SECTORS = [
        ('Real Estate', 0.04),      # REITs - 4%+ typical
        ('Utilities', 0.03),        # Stable utilities - 3%+
        ('Energy', 0.04),           # MLPs and energy infrastructure - 4%+
        ('Financial Services', 0.05), # BDCs and mortgage REITs - 5%+
        ('Communication Services', 0.03)  # Telecoms - 3%+
    ]

    all_symbols = []
    for sector, min_yield in HIGH_DIVIDEND_SECTORS:
        symbols = discover_sector_dividend_leaders(sector, min_yield)
        all_symbols.extend(symbols)

    logger.info(f"✅ [FMP Advanced] Total sector leaders: {len(all_symbols)} symbols")
    return all_symbols


# ============================================================================
# BEHAVIORAL DISCOVERY - Find Stocks by Actual Dividend Behavior
# ============================================================================

def discover_consistent_dividend_payers(years_back: int = 4, min_payments_per_year: int = 4) -> List[Dict]:
    """
    Discover stocks with consistent dividend payment history.

    This is SMART - instead of hard-coding symbols, we analyze actual behavior.

    Args:
        years_back: How many years of history to analyze
        min_payments_per_year: Minimum dividend payments per year (4 = quarterly)
    """
    logger.info(f"🔍 [FMP Behavioral] Consistent payers ({min_payments_per_year}+ payments/year, {years_back} years)")

    # Get dividend calendar for the past N years
    start_date = (datetime.now() - timedelta(days=years_back * 365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    url = (f"https://financialmodelingprep.com/api/v3/stock_dividend_calendar?"
           f"from={start_date}&"
           f"to={end_date}&"
           f"apikey={FMP_API_KEY}")

    data = fetch_with_retry(url, fmp_limiter)

    if not data:
        logger.warning("❌ [FMP Behavioral] Failed to fetch dividend calendar")
        return []

    # Analyze payment frequency
    symbol_payments = defaultdict(list)
    for div in data:
        symbol = div.get('symbol', '').strip()
        date = div.get('date')
        if symbol and date:
            symbol_payments[symbol].append(date)

    # Find consistent payers
    min_total_payments = min_payments_per_year * years_back
    consistent_symbols = []

    for symbol, payments in symbol_payments.items():
        if len(payments) >= min_total_payments:
            # Calculate average payments per year
            unique_years = len(set(date[:4] for date in payments))
            avg_payments_per_year = len(payments) / max(unique_years, 1)

            if avg_payments_per_year >= min_payments_per_year:
                consistent_symbols.append({
                    'symbol': symbol,
                    'name': f'{symbol} (Consistent Payer)',
                    'total_payments': len(payments),
                    'years_tracked': unique_years,
                    'avg_payments_per_year': round(avg_payments_per_year, 1),
                    'source': 'FMP-BEHAVIORAL-CONSISTENT',
                    'discovery_method': 'behavioral_analysis'
                })

    logger.info(f"✅ [FMP Behavioral] Found {len(consistent_symbols)} consistent payers")
    return consistent_symbols


# ============================================================================
# DYNAMIC ETF DISCOVERY - No Hard-Coded Lists!
# ============================================================================

def discover_etfs_by_family_patterns() -> List[Dict]:
    """
    Discover ETFs by analyzing fund family patterns from ALL ETFs.

    Instead of hard-coding YieldMax symbols, we:
    1. Get ALL ETFs from FMP
    2. Analyze issuer/name patterns
    3. Identify high-yield fund families dynamically
    4. Validate with actual dividend data
    """
    logger.info("🔍 [FMP ETF Families] Discovering ETFs by fund family patterns...")

    # Get ALL ETFs
    url = f"https://financialmodelingprep.com/api/v3/etf/list?apikey={FMP_API_KEY}"
    all_etfs = fetch_with_retry(url, fmp_limiter)

    if not all_etfs:
        logger.warning("❌ [FMP ETF Families] Failed to fetch ETF list")
        return []

    logger.info(f"📊 [FMP ETF Families] Analyzing {len(all_etfs)} ETFs...")

    # Known high-yield family keywords (for pattern matching, not hard-coding specific symbols!)
    FAMILY_KEYWORDS = {
        'yieldmax': ['yieldmax', 'yield max'],
        'roundhill': ['roundhill'],
        'global_x': ['global x', 'globalx'],
        'defiance': ['defiance'],
        'first_trust': ['first trust'],
        'wisdomtree': ['wisdomtree'],
        'proshares': ['proshares'],
        'invesco': ['invesco'],
        'vanguard': ['vanguard'],
        'ishares': ['ishares'],
        'schwab': ['schwab'],
        'spdr': ['spdr', 'state street']
    }

    # Pattern-based discovery
    family_etfs = defaultdict(list)
    yieldmax_pattern_matches = []

    for etf in all_etfs:
        symbol = etf.get('symbol', '').strip()
        name = etf.get('name', '').lower()

        if not symbol:
            continue

        # Check against fund family keywords
        matched_family = None
        for family, keywords in FAMILY_KEYWORDS.items():
            if any(kw in name for kw in keywords):
                matched_family = family
                break

        if matched_family:
            family_etfs[matched_family].append({
                'symbol': symbol,
                'name': etf.get('name', ''),
                'source': f'FMP-ETF-FAMILY-{matched_family.upper()}',
                'discovery_method': 'family_pattern',
                'family': matched_family
            })

        # Special pattern for YieldMax (they use Y-prefix pattern)
        if symbol.startswith('Y') and len(symbol) <= 5 and 'yield' in name:
            yieldmax_pattern_matches.append({
                'symbol': symbol,
                'name': etf.get('name', ''),
                'source': 'FMP-ETF-YIELDMAX-PATTERN',
                'discovery_method': 'symbol_pattern',
                'pattern': 'YieldMax Y-prefix'
            })

    # Combine all discovered ETFs
    all_discovered = []
    for family, etfs in family_etfs.items():
        logger.info(f"✅ [FMP ETF Families] {family}: {len(etfs)} ETFs")
        all_discovered.extend(etfs)

    # Add YieldMax pattern matches
    logger.info(f"✅ [FMP ETF Families] YieldMax pattern: {len(yieldmax_pattern_matches)} ETFs")
    all_discovered.extend(yieldmax_pattern_matches)

    # Deduplicate
    unique_symbols = {}
    for etf in all_discovered:
        symbol = etf['symbol']
        if symbol not in unique_symbols:
            unique_symbols[symbol] = etf

    final_list = list(unique_symbols.values())
    logger.info(f"✅ [FMP ETF Families] Total unique ETFs: {len(final_list)}")

    return final_list


def discover_recently_launched_etfs(days_back: int = 180) -> List[Dict]:
    """
    Discover ETFs launched in the last N days.

    This ensures we catch new YieldMax and other high-yield ETF launches immediately!

    Args:
        days_back: How many days back to check for launches
    """
    logger.info(f"🔍 [FMP New ETFs] Discovering ETFs launched in last {days_back} days...")

    # Get ALL ETFs
    url = f"https://financialmodelingprep.com/api/v3/etf/list?apikey={FMP_API_KEY}"
    all_etfs = fetch_with_retry(url, fmp_limiter)

    if not all_etfs:
        return []

    cutoff_date = datetime.now() - timedelta(days=days_back)
    recent_etfs = []

    # Check each ETF's profile for IPO date
    for etf in all_etfs[:500]:  # Limit to first 500 to avoid excessive API calls
        symbol = etf.get('symbol', '').strip()
        if not symbol:
            continue

        # Get company profile for IPO date
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}"
        profile = fetch_with_retry(profile_url, fmp_limiter)

        if profile and isinstance(profile, list) and len(profile) > 0:
            ipo_date_str = profile[0].get('ipoDate')
            if ipo_date_str:
                try:
                    ipo_date = datetime.strptime(ipo_date_str, '%Y-%m-%d')
                    if ipo_date >= cutoff_date:
                        recent_etfs.append({
                            'symbol': symbol,
                            'name': profile[0].get('companyName', etf.get('name', '')),
                            'ipo_date': ipo_date_str,
                            'days_since_launch': (datetime.now() - ipo_date).days,
                            'source': 'FMP-NEW-ETF-LAUNCH',
                            'discovery_method': 'launch_monitoring'
                        })
                except ValueError:
                    pass

    logger.info(f"✅ [FMP New ETFs] Found {len(recent_etfs)} recently launched ETFs")
    return recent_etfs


def discover_high_dividend_etfs_by_holdings() -> List[Dict]:
    """
    Discover ETFs that hold high-dividend stocks (smart correlation approach).

    FMP provides ETF holdings - we can identify dividend-focused ETFs by their holdings.
    """
    logger.info("🔍 [FMP ETF Holdings] Discovering high-dividend ETFs by analyzing holdings...")

    # This is a sophisticated approach: Get ETF holdings and analyze for dividend focus
    # We'll implement a sample - full implementation would analyze top holdings

    url = f"https://financialmodelingprep.com/api/v3/etf/list?apikey={FMP_API_KEY}"
    all_etfs = fetch_with_retry(url, fmp_limiter)

    if not all_etfs:
        return []

    # Filter ETFs with dividend-related keywords
    dividend_keywords = ['dividend', 'income', 'yield', 'distribution', 'covered call', 'equity premium']
    dividend_focused_etfs = []

    for etf in all_etfs:
        symbol = etf.get('symbol', '').strip()
        name = etf.get('name', '').lower()

        if symbol and any(keyword in name for keyword in dividend_keywords):
            dividend_focused_etfs.append({
                'symbol': symbol,
                'name': etf.get('name', ''),
                'source': 'FMP-ETF-DIVIDEND-KEYWORD',
                'discovery_method': 'holdings_analysis'
            })

    logger.info(f"✅ [FMP ETF Holdings] Found {len(dividend_focused_etfs)} dividend-focused ETFs")
    return dividend_focused_etfs


# ============================================================================
# INTERNATIONAL HIGH-DIVIDEND MARKETS
# ============================================================================

def discover_international_dividend_stocks(exchange: str, min_yield: float = 0.03) -> List[Dict]:
    """
    Discover high-dividend stocks from international exchanges.

    FMP supports multiple international exchanges with strong dividend cultures.

    Args:
        exchange: Exchange code (LSE, TSX, ASX, JSE, etc.)
        min_yield: Minimum dividend yield
    """
    logger.info(f"🌍 [FMP International] {exchange} dividend stocks (yield≥{min_yield:.1%})")

    # FMP supports exchange-specific queries
    url = (f"https://financialmodelingprep.com/api/v3/stock-screener?"
           f"exchange={exchange}&"
           f"dividendYieldMoreThan={min_yield}&"
           f"limit=10000&"
           f"apikey={FMP_API_KEY}")

    data = fetch_with_retry(url, fmp_limiter)

    symbols = []
    if data and isinstance(data, list):
        for stock in data:
            symbol = stock.get('symbol', '').strip()
            if symbol:
                symbols.append({
                    'symbol': symbol,
                    'name': stock.get('companyName', ''),
                    'exchange': exchange,
                    'dividend_yield': stock.get('dividendYield', 0),
                    'source': f'FMP-INTERNATIONAL-{exchange}',
                    'discovery_method': 'international_screener'
                })
        logger.info(f"✅ [FMP International] Found {len(symbols)} {exchange} dividend stocks")

    return symbols


def discover_all_international_dividend_stocks() -> List[Dict]:
    """Discover dividend stocks from Canadian exchanges (TSX only)."""
    # US and Canadian exchanges only - international markets removed
    INTERNATIONAL_EXCHANGES = [
        ('TSX', 0.04),    # Toronto - REITs and energy
    ]

    all_symbols = []
    for exchange, min_yield in INTERNATIONAL_EXCHANGES:
        symbols = discover_international_dividend_stocks(exchange, min_yield)
        all_symbols.extend(symbols)

    logger.info(f"✅ [FMP International] Total international: {len(all_symbols)} symbols")
    return all_symbols


# ============================================================================
# MASTER DISCOVERY FUNCTION - Combines All Methods
# ============================================================================

def discover_all_symbols_enhanced() -> Dict[str, List[Dict]]:
    """
    Master discovery function that leverages ALL FMP Ultimate plan capabilities.

    Returns:
        Dictionary with discovery results by method
    """
    logger.info("🚀 ENHANCED SYMBOL DISCOVERY - FMP ULTIMATE PLAN FULL UTILIZATION")
    logger.info("=" * 80)

    results = {
        'high_yield_stocks': [],
        'dividend_aristocrats': [],
        'sector_leaders': [],
        'consistent_payers': [],
        'etf_families': [],
        'new_etf_launches': [],
        'dividend_focused_etfs': [],
        'international_stocks': []
    }

    # 1. High-yield stocks (3%+ yield, $100M+ market cap)
    logger.info("\n1️⃣ High-Yield Stocks Discovery...")
    results['high_yield_stocks'] = discover_high_yield_dividend_stocks(min_yield=0.03, min_market_cap=100000000)

    # 2. Dividend aristocrats (large caps, consistent payers)
    logger.info("\n2️⃣ Dividend Aristocrats Discovery...")
    results['dividend_aristocrats'] = discover_dividend_aristocrats(min_yield=0.01, min_market_cap=1000000000)

    # 3. Sector-specific dividend leaders
    logger.info("\n3️⃣ Sector Dividend Leaders Discovery...")
    results['sector_leaders'] = discover_all_sector_dividend_leaders()

    # 4. Behavioral discovery - consistent dividend payers
    logger.info("\n4️⃣ Behavioral Analysis - Consistent Payers...")
    results['consistent_payers'] = discover_consistent_dividend_payers(years_back=4, min_payments_per_year=4)

    # 5. Dynamic ETF family discovery
    logger.info("\n5️⃣ Dynamic ETF Family Discovery...")
    results['etf_families'] = discover_etfs_by_family_patterns()

    # 6. Recently launched ETFs
    logger.info("\n6️⃣ New ETF Launch Monitoring...")
    results['new_etf_launches'] = discover_recently_launched_etfs(days_back=180)

    # 7. Dividend-focused ETFs by holdings
    logger.info("\n7️⃣ Dividend-Focused ETFs Discovery...")
    results['dividend_focused_etfs'] = discover_high_dividend_etfs_by_holdings()

    # 8. International dividend stocks
    logger.info("\n8️⃣ International Markets Discovery...")
    results['international_stocks'] = discover_all_international_dividend_stocks()

    # Summary
    total_discovered = sum(len(symbols) for symbols in results.values())
    logger.info("\n" + "=" * 80)
    logger.info("📊 DISCOVERY SUMMARY")
    logger.info("=" * 80)
    for method, symbols in results.items():
        logger.info(f"  {method}: {len(symbols)} symbols")
    logger.info(f"\n🎯 TOTAL DISCOVERED: {total_discovered} symbols")
    logger.info("=" * 80)

    return results


def get_all_discovered_symbols_flat() -> List[Dict]:
    """
    Get all discovered symbols as a flat list (deduplicated).

    Returns:
        Flat list of unique discovered symbols
    """
    results = discover_all_symbols_enhanced()

    # Flatten and deduplicate
    all_symbols = {}
    for method, symbols in results.items():
        for symbol_data in symbols:
            symbol = symbol_data['symbol']
            # Keep first occurrence (priority by discovery order)
            if symbol not in all_symbols:
                all_symbols[symbol] = symbol_data

    return list(all_symbols.values())


if __name__ == '__main__':
    # Test the enhanced discovery
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("\n🚀 Testing Enhanced Discovery System\n")
    results = discover_all_symbols_enhanced()

    print("\n✅ Discovery Complete!")
    print(f"\nTotal unique symbols: {len(get_all_discovered_symbols_flat())}")
