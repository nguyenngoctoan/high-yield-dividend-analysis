#!/usr/bin/env python3
"""
Hybrid Stock Data Update Script with Multiple Data Sources

This script implements a comprehensive hybrid approach for fetching stock and dividend data:
1. PRIMARY: FMP (Financial Modeling Prep) - Comprehensive historical data
2. SECONDARY: Alpha Vantage - NASDAQ official vendor, faster updates for new symbols  
3. FALLBACK: Yahoo Finance - Free, excellent coverage including newest ETFs

The hybrid approach ensures maximum data coverage and reliability.
"""

import os
import sys
import logging
import argparse
import requests
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
# Import Supabase helpers instead of PostgreSQL
from supabase_helpers import (
    get_supabase_client,
    test_supabase_connection,
    initialize_supabase_connection,
    supabase_select as pg_select,
    supabase_insert as pg_insert,
    supabase_upsert as pg_upsert,
    supabase_delete as pg_delete,
    supabase_update as pg_update,
    supabase_batch_upsert,
    get_excluded_symbols as fetch_excluded_symbols,
    get_existing_symbols as fetch_existing_symbols
)
from dotenv import load_dotenv
from sector_helpers import get_sector_for_symbol

# Load environment variables
load_dotenv()

# API Configuration
FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Rate limiters for different APIs - ULTIMATE PLAN OPTIMIZED
# FMP Ultimate Plan: 3,000 requests/min (50 req/sec)
# https://site.financialmodelingprep.com/pricing-plans
fmp_limiter = Semaphore(144)  # 18X from 8 to 144 for Ultimate plan (2X increase to utilize full capacity)
av_limiter = Semaphore(2)     # Alpha Vantage Premium - very conservative (2 concurrent)
yahoo_limiter = Semaphore(3)  # Yahoo Finance - extremely conservative (3 concurrent)

# Configuration
DEBUG_MODE = False
ENHANCED_HISTORICAL_DATA = True
PRICES_START_DATE = "1960-01-01"
DIVIDENDS_START_DATE = "1960-01-01"
# Control NASDAQ-only filtering via command line (--nasdaq-only flag)
NASDAQ_ONLY = False  # Controlled by command-line argument

# US and Canadian exchanges only (international markets removed)
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "BATS", "BTS", "BYX", "BZX", "CBOE",
    "EDGA", "EDGX", "PCX", "NGM",
    "OTCM", "OTCX",  # OTC markets for dividend stocks
    "TSX", "TSXV", "CSE", "TSE"  # Canadian exchanges
]

# Hybrid fetching configuration
USE_HYBRID_DIVIDENDS = True  # Enable hybrid dividend fetching
USE_HYBRID_PRICES = False    # Keep FMP primary for prices (excellent coverage)
FALLBACK_TO_YAHOO = True     # Enable Yahoo Finance fallback

# Database connection functions are imported from supabase_helpers
# All pg_* functions are aliased from the supabase_* equivalents
# This allows for seamless migration from PostgreSQL to Supabase

# Configure logging FIRST before any other operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_update.log', mode='w'),  # 'w' mode overwrites on each run
        logging.StreamHandler()
    ]
)

# Reduce HTTP request logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("yfinance").setLevel(logging.WARNING)

# Initialize logger BEFORE Supabase initialization
logger = logging.getLogger(__name__)

# Note: NASDAQ_ONLY is now controlled via command-line --nasdaq-only flag

# Initialize Supabase connection AFTER logger is ready
if not initialize_supabase_connection():
    logger.error("❌ Failed to initialize Supabase connection - exiting")
    sys.exit(1)

def fetch_with_adaptive_retry(url, limiter, max_retries=3, symbol=None):
    """Fetch data with adaptive retry logic and rate limiting."""
    for attempt in range(max_retries):
        try:
            limiter.acquire()
            try:
                response = requests.get(url, timeout=30)
            finally:
                limiter.release()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            elif response.status_code == 404:
                # 404 errors are expected for invalid/non-existent symbols - log at debug level
                symbol_info = f" for {symbol}" if symbol else ""
                logger.debug(f"Symbol not found (HTTP 404){symbol_info}: {url}")
                return None
            elif response.status_code == 401:
                # 401 errors indicate API key issues - log once and return None
                symbol_info = f" for {symbol}" if symbol else ""
                logger.warning(f"API authentication failed (HTTP 401){symbol_info}")
                return None
            else:
                symbol_info = f" for {symbol}" if symbol else ""
                logger.error(f"HTTP {response.status_code}{symbol_info}: {response.text}")
                
        except Exception as e:
            symbol_info = f" for {symbol}" if symbol else ""
            logger.error(f"Request failed (attempt {attempt + 1}){symbol_info}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None

def fetch_fmp_etf_info(symbol):
    """Fetch ETF company and detailed info from FMP."""
    try:
        url = f"https://financialmodelingprep.com/stable/etf/info?symbol={symbol}&apikey={FMP_API_KEY}"
        
        logger.debug(f"📊 [FMP ETF] Fetching ETF info for {symbol}")
        data = fetch_with_adaptive_retry(url, fmp_limiter, symbol=symbol)
        
        if data and isinstance(data, list) and len(data) > 0:
            etf_info = data[0]
            return {
                'source': 'FMP-ETF',
                'company_name': etf_info.get('etfCompany'),
                'name': etf_info.get('name'),
                'description': etf_info.get('description'),
                'expense_ratio': etf_info.get('expenseRatio'),
                'aum': etf_info.get('assetsUnderManagement'),
                'inception_date': etf_info.get('inceptionDate'),
                'holdings_count': etf_info.get('holdingsCount'),
                'website': etf_info.get('website'),
                'isin': etf_info.get('isin'),
                'domicile': etf_info.get('domicile')
            }
    except Exception as e:
        logger.error(f"FMP ETF info error for {symbol}: {e}")
    
    return None

def fetch_fmp_prices(symbol, from_date=None):
    """Fetch price data from FMP API with AUM for ETFs."""
    try:
        if from_date:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={from_date}&apikey={FMP_API_KEY}"
        else:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={PRICES_START_DATE}&apikey={FMP_API_KEY}"

        logger.debug(f"📊 [FMP] Fetching prices for {symbol}")
        data = fetch_with_adaptive_retry(url, fmp_limiter, symbol=symbol)

        if data and 'historical' in data and data['historical']:
            # Try to get current AUM from ETF metadata
            aum = None
            try:
                etf_metadata = fetch_fmp_etf_metadata(symbol)
                if etf_metadata and etf_metadata.get('aum'):
                    aum = etf_metadata['aum']
                    logger.debug(f"📊 [FMP] Found AUM for {symbol}: ${aum:,.0f}")
            except:
                pass  # Not an ETF or AUM not available

            # Only add AUM to the most recent (first) record - this is today's/latest data
            # Don't backfill AUM to historical records
            price_data = data['historical']
            if aum and len(price_data) > 0:
                # FMP returns newest first, so index 0 is the most recent
                price_data[0]['aum'] = aum

            return {
                'source': 'FMP',
                'data': price_data,
                'count': len(price_data),
                'aum': aum
            }
    except Exception as e:
        logger.error(f"FMP prices error for {symbol}: {e}")

    return None

def fetch_yahoo_prices(symbol):
    """Fetch price data from Yahoo Finance using yfinance."""
    if not FALLBACK_TO_YAHOO:
        return None

    try:
        yahoo_limiter.acquire()
        try:
            logger.debug(f"📊 [YAHOO] Fetching prices for {symbol}")
            ticker = yf.Ticker(symbol)

            # Get AUM (total assets) for ETFs - this is current value, will be same for all dates
            aum = None
            try:
                info = ticker.info
                aum = info.get('totalAssets')
                if aum:
                    logger.debug(f"📊 [YAHOO] Found AUM for {symbol}: ${aum:,.0f}")
            except:
                pass  # AUM not available for this symbol

            # Get historical prices
            hist = ticker.history(period="max")

            if not hist.empty:
                # Convert to format similar to FMP
                price_data = []
                for idx, (date, row) in enumerate(hist.iterrows()):
                    record = {
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'adjClose': float(row['Close']),  # Yahoo Finance history() already returns adjusted prices
                        'volume': int(row['Volume']) if not pd.isna(row['Volume']) else 0
                    }
                    # Add AUM to ALL records for daily AUM tracking (if available)
                    # Note: AUM represents current assets, but we record it daily to track growth over time
                    if aum:
                        record['aum'] = int(aum)
                    price_data.append(record)

                return {
                    'source': 'Yahoo Finance',
                    'data': price_data,
                    'count': len(price_data),
                    'aum': aum  # Also include AUM at top level
                }
        finally:
            yahoo_limiter.release()

    except Exception as e:
        logger.error(f"Yahoo prices error for {symbol}: {e}")

    return None

# =====================================
# COMPREHENSIVE SYMBOL DISCOVERY SYSTEM  
# =====================================

def discover_symbols_from_fmp(limit=None):
    """Discover symbols from FMP API."""
    logger.info(f"🔍 [FMP] Discovering symbols (limit: {'None - fetching ALL' if limit is None else limit})")
    
    symbols = []
    
    try:
        url = f"https://financialmodelingprep.com/api/v3/available-traded/list?apikey={FMP_API_KEY}"
        data = fetch_with_adaptive_retry(url, fmp_limiter)
        
        if data:
            items_to_process = data if limit is None else data[:limit]
            for item in items_to_process:
                symbol = item.get('symbol', '').strip()
                exchange = item.get('exchangeShortName', '')
                
                if symbol and exchange in ALLOWED_EXCHANGES:
                    symbols.append({
                        'symbol': symbol,
                        'name': item.get('name', ''),
                        'source': f'FMP-{exchange}',
                        'exchange': exchange,
                        'price': item.get('price'),
                        'type': 'STOCK'  # FMP doesn't distinguish clearly
                    })
            
            logger.info(f"✅ [FMP] Discovered {len(symbols)} symbols from allowed exchanges")
        else:
            logger.error(f"❌ [FMP] Failed to fetch symbol list")
            
    except Exception as e:
        logger.error(f"❌ [FMP] Discovery error: {e}")
    
    return symbols

def discover_all_etfs_from_fmp():
    """Discover ALL ETFs from FMP's comprehensive ETF list."""
    logger.info("🔍 [FMP] Discovering ALL ETFs from comprehensive list...")
    
    symbols = []
    
    try:
        url = f"https://financialmodelingprep.com/api/v3/etf/list?apikey={FMP_API_KEY}"
        data = fetch_with_adaptive_retry(url, fmp_limiter)
        
        if data and isinstance(data, list):
            logger.info(f"📊 [FMP] Found {len(data)} ETFs in comprehensive list")
            
            for etf in data:
                symbol = etf.get('symbol', '').strip()
                name = etf.get('name', '')
                
                if symbol and name:
                    symbols.append({
                        'symbol': symbol,
                        'name': name,
                        'source': 'FMP-ETF-LIST',
                        'type': 'ETF'
                    })
            
            logger.info(f"✅ [FMP] Discovered {len(symbols)} ETFs from comprehensive list")
        else:
            logger.warning("❌ [FMP] No ETF data returned from comprehensive list")
            
    except Exception as e:
        logger.error(f"❌ [FMP] ETF list discovery failed: {e}")
    
    return symbols

def discover_dividend_stocks_from_fmp(min_yield=0.01, limit=None):
    """Discover dividend-paying stocks from FMP screener."""
    logger.info(f"🔍 [FMP] Discovering dividend stocks (yield > {min_yield:.1%}, limit: {'None - fetching ALL' if limit is None else limit})")
    
    symbols = []
    
    try:
        # FMP API requires a limit parameter, use 10000 as a very high number if no limit specified
        api_limit = 10000 if limit is None else limit
        url = f"https://financialmodelingprep.com/api/v3/stock-screener?dividendYieldMoreThan={min_yield}&limit={api_limit}&apikey={FMP_API_KEY}"
        data = fetch_with_adaptive_retry(url, fmp_limiter)
        
        if data and isinstance(data, list):
            logger.info(f"📊 [FMP] Found {len(data)} dividend stocks")
            
            for stock in data:
                symbol = stock.get('symbol', '').strip()
                name = stock.get('companyName', '')
                exchange = stock.get('exchangeShortName', '')
                dividend_yield = stock.get('dividendYield', 0)
                
                if symbol and exchange in ALLOWED_EXCHANGES and dividend_yield > 0:
                    symbols.append({
                        'symbol': symbol,
                        'name': name,
                        'source': f'FMP-DIV-{exchange}',
                        'exchange': exchange,
                        'dividend_yield': dividend_yield
                    })
            
            logger.info(f"✅ [FMP] Discovered {len(symbols)} dividend stocks")
        else:
            logger.warning("❌ [FMP] No dividend stock data returned")
            
    except Exception as e:
        logger.error(f"❌ [FMP] Dividend screener failed: {e}")
    
    return symbols

def discover_symbols_from_alpha_vantage(limit=None):
    """Discover symbols from Alpha Vantage LISTING_STATUS endpoint."""
    logger.info(f"🔍 [Alpha Vantage] Discovering symbols from LISTING_STATUS (limit: {'None - fetching ALL' if limit is None else limit})")
    
    symbols = []
    
    try:
        # Use Alpha Vantage LISTING_STATUS endpoint to get comprehensive symbol list
        api_key = ALPHA_VANTAGE_API_KEY.strip().rstrip('%')  # Clean up any formatting issues
        url = f"https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={api_key}"
        
        av_limiter.acquire()
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Check if response is JSON (error) or CSV (success)
            if response.text.strip().startswith('{'):
                logger.warning(f"❌ [Alpha Vantage] API returned JSON error: {response.text[:100]}")
                raise Exception("API key issue or rate limit exceeded")
            
            # Parse CSV response
            import csv
            import io
            
            csv_data = io.StringIO(response.text)
            csv_reader = csv.DictReader(csv_data)
            
            count = 0
            exchange_map = {'NYSE ARCA': 'AMEX', 'NASDAQ': 'NASDAQ', 'NYSE': 'NYSE', 'BATS': 'BATS'}
            
            for row in csv_reader:
                if limit is not None and count >= limit:
                    break
                    
                symbol = row.get('symbol', '').strip()
                name = row.get('name', '').strip()
                exchange = row.get('exchange', '').strip()
                asset_type = row.get('assetType', '').strip()
                status = row.get('status', '').strip()
                
                # Map Alpha Vantage exchange names to our standard names
                mapped_exchange = exchange_map.get(exchange, exchange)
                
                # Filter for active stocks and ETFs on major exchanges
                if (symbol and status == 'Active' and 
                    asset_type in ['Stock', 'ETF'] and 
                    mapped_exchange in ALLOWED_EXCHANGES):
                    
                    symbols.append({
                        'symbol': symbol,
                        'name': name,
                        'source': f'AV-LISTING-{mapped_exchange}',
                        'exchange': mapped_exchange,
                        'asset_type': asset_type
                    })
                    count += 1
            
            logger.info(f"✅ [Alpha Vantage] Discovered {len(symbols)} symbols from LISTING_STATUS")
            
        finally:
            av_limiter.release()
        
    except Exception as e:
        logger.error(f"❌ [Alpha Vantage] LISTING_STATUS discovery failed: {e}")
        logger.warning("⚠️ [Alpha Vantage] API failed - returning empty list")
        logger.info("ℹ️ [Alpha Vantage] Enhanced discovery will provide comprehensive coverage")
        # Return empty - enhanced discovery methods will cover all symbols dynamically

    return symbols

def discover_symbols_from_yahoo_screener(min_yield=2.0, limit=None):
    """
    Yahoo Finance discovery - DEPRECATED.

    This function has been replaced by enhanced_discovery.py which provides:
    - Dynamic ETF family pattern detection (no hard-coded lists)
    - Behavioral analysis for consistent dividend payers
    - International market coverage
    - FMP Ultimate plan full utilization

    Returning empty list - enhanced discovery provides comprehensive coverage.
    """
    logger.info("ℹ️ [Yahoo] Disabled - enhanced discovery provides superior coverage")
    logger.info("ℹ️ [Yahoo] See enhanced_discovery.py for dynamic, criteria-based discovery")
    return []

def discover_symbols_from_yahoo_search_original(search_terms=None, max_results_per_term=25):
    """Discover symbols using Yahoo Finance search (original method)."""
    if search_terms is None:
        search_terms = [
            # Core dividend terms
            'dividend ETF', 'high yield ETF', 'dividend stocks', 'income ETF',
            'monthly dividend', 'quarterly dividend', 'dividend aristocrat', 'dividend king',
            
            # Specific dividend strategies
            'YieldMax', 'Roundhill', 'option income ETF', 'covered call ETF',
            'weekly pay ETF', 'income strategy ETF', 'enhanced dividend ETF',
            
            # Major dividend-focused issuers
            'Defiance ETF', 'Amplify ETF', 'Global X ETF', 'First Trust ETF',
            'Invesco dividend', 'Schwab dividend', 'Vanguard dividend', 
            'iShares dividend', 'SPDR dividend',
            
            # Asset classes with high dividend yields
            'REIT ETF', 'utility stocks', 'energy dividend', 'financial dividend',
            'MLP ETF', 'BDC ETF', 'preferred stock', 'high yield bond',
            
            # Geographic dividend focus
            'international dividend', 'emerging markets dividend', 'European dividend',
            
            # Sector ETFs (often dividend-heavy)
            'utility ETF', 'energy ETF', 'financial ETF', 'consumer staples ETF',
            'telecom ETF', 'materials ETF'
        ]
    
    logger.info(f"🔍 [Yahoo] Discovering symbols via search ({len(search_terms)} terms)")
    
    symbols = []
    discovered_symbols = set()
    
    for term in search_terms:
        try:
            yahoo_limiter.acquire()
            try:
                # Use yfinance Search functionality
                search = yf.Search(term, max_results=max_results_per_term)
                results = search.quotes
                
                for result in results:
                    symbol = result.get('symbol', '').strip()
                    if symbol and symbol not in discovered_symbols:
                        symbols.append({
                            'symbol': symbol,
                            'name': result.get('shortname') or result.get('longname', ''),
                            'source': f'YAHOO-SEARCH',
                            'type': result.get('quoteType', 'UNKNOWN'),
                            'exchange': result.get('exchange', 'Unknown')
                        })
                        discovered_symbols.add(symbol)
                
                logger.debug(f"  [Yahoo] '{term}': Found {len(results)} symbols")
                
            finally:
                yahoo_limiter.release()
                
        except Exception as e:
            logger.error(f"❌ [Yahoo] Search failed for '{term}': {e}")
    
    # Hard-coded ETF list REMOVED - enhanced discovery provides dynamic coverage
    # See enhanced_discovery.py for:
    # - Dynamic ETF family pattern detection (discovers all YieldMax, Roundhill, etc.)
    # - Behavioral analysis for consistent dividend payers
    # - No manual maintenance required

    logger.info(f"✅ [Yahoo] Discovered {len(symbols)} unique symbols from search")
    logger.info("ℹ️ [Yahoo] Hard-coded symbol lists removed - see enhanced_discovery.py")
    return symbols

def discover_symbols_from_nasdaq_api(limit=None):
    """Discover symbols from NASDAQ public API."""
    logger.info(f"🔍 [NASDAQ API] Discovering symbols (limit: {'None - fetching ALL' if limit is None else limit})")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    symbols = []
    
    try:
        # Get ETFs from NASDAQ
        etf_url = 'https://api.nasdaq.com/api/screener/etf'
        params = {'tableonly': 'true', 'limit': 5000 if limit is None else limit // 2, 'offset': 0}
        
        response = requests.get(etf_url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            etf_rows = data.get('data', {}).get('table', {}).get('rows', [])
            
            for row in etf_rows:
                symbol = row.get('symbol', '').strip()
                if symbol:
                    symbols.append({
                        'symbol': symbol,
                        'name': row.get('name', ''),
                        'type': 'ETF',
                        'source': 'NASDAQ-API',
                        'exchange': 'NASDAQ'
                    })
            
            logger.info(f"✅ [NASDAQ API] Found {len(etf_rows)} ETFs")
        
        # Get stocks from major exchanges
        exchanges = ['NYSE', 'NASDAQ', 'AMEX']
        for exchange in exchanges:
            try:
                stock_url = 'https://api.nasdaq.com/api/screener/stocks'
                params = {
                    'tableonly': 'true', 
                    'limit': 300 if limit is None else min(limit // len(exchanges) // 2, 300),
                    'offset': 0,
                    'exchange': exchange
                }
                
                response = requests.get(stock_url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    stock_rows = data.get('data', {}).get('table', {}).get('rows', [])
                    
                    for row in stock_rows:
                        symbol = row.get('symbol', '').strip()
                        if symbol and not any(s['symbol'] == symbol for s in symbols):
                            symbols.append({
                                'symbol': symbol,
                                'name': row.get('name', ''),
                                'type': 'STOCK',
                                'source': f'NASDAQ-API-{exchange}',
                                'exchange': exchange
                            })
                    
                    logger.info(f"✅ [NASDAQ API] Found {len(stock_rows)} stocks from {exchange}")
                    
            except Exception as e:
                logger.error(f"❌ [NASDAQ API] {exchange} discovery failed: {e}")
        
    except Exception as e:
        logger.error(f"❌ [NASDAQ API] Discovery error: {e}")
    
    logger.info(f"✅ [NASDAQ API] Total discovered: {len(symbols)} symbols")
    return symbols

def discover_etfs_by_company(limit=None):
    """
    Company-based ETF discovery - DEPRECATED.

    This function contained hard-coded lists of:
    - YieldMax ETFs (23 hard-coded symbols)
    - Roundhill ETFs (15 hard-coded symbols)
    - Global X ETFs (16 hard-coded symbols)
    - And 6 other fund families (68 total hard-coded symbols)

    REPLACED BY: enhanced_discovery.py -> discover_etfs_by_family_patterns()

    The new implementation:
    - Gets ALL 13,288 ETFs from FMP dynamically
    - Analyzes fund family patterns (no hard-coding!)
    - Discovers ALL ETFs from 12+ fund families automatically
    - Found 5,052 ETFs vs 68 hard-coded (74X improvement!)
    - Automatically discovers new launches (e.g., new YieldMax ETFs)

    Example: YieldMax discovery
    - OLD: 23 hard-coded symbols (goes stale immediately)
    - NEW: 58 ETFs discovered dynamically by pattern matching

    Returning empty list - enhanced discovery provides comprehensive coverage.
    """
    logger.info("ℹ️ [COMPANY ETF] Disabled - enhanced discovery provides superior coverage")
    logger.info("ℹ️ [COMPANY ETF] Enhanced discovery found 5,052 ETFs (vs 68 hard-coded)")
    logger.info("ℹ️ [COMPANY ETF] See enhanced_discovery.py -> discover_etfs_by_family_patterns()")
    return []

def validate_discovered_symbol(symbol_data, disable_yahoo=True):
    """Validate a discovered symbol to determine if it meets criteria.

    Validation checks:
    1. Must have recent price data (within 7 days) OR dividend history (within 365 days)
    2. Excludes mutual funds
    """
    symbol = symbol_data['symbol']

    # Yahoo validation disabled by default (unreliable API with auth errors)
    # Use FMP API for validation instead
    if disable_yahoo or True:  # Always skip Yahoo validation
        try:
            # Check for recent price activity using FMP
            from datetime import datetime, timedelta
            today = datetime.now().date()
            seven_days_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            one_year_ago = (today - timedelta(days=365)).strftime('%Y-%m-%d')

            has_recent_price = False
            has_recent_dividend = False
            exclusion_reason = None

            # Try to fetch recent price data from FMP
            try:
                fmp_limiter.acquire()
                try:
                    price_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={seven_days_ago}&apikey={FMP_API_KEY}"
                    response = requests.get(price_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('historical') and len(data['historical']) > 0:
                            has_recent_price = True
                            logger.debug(f"✅ {symbol}: Has recent price data ({len(data['historical'])} records)")
                finally:
                    fmp_limiter.release()
            except Exception as e:
                logger.debug(f"⚠️ {symbol}: Could not check recent prices - {e}")

            # Try to fetch recent dividend data from FMP
            try:
                fmp_limiter.acquire()
                try:
                    dividend_url = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{symbol}?from={one_year_ago}&apikey={FMP_API_KEY}"
                    response = requests.get(dividend_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('historical') and len(data['historical']) > 0:
                            has_recent_dividend = True
                            logger.debug(f"✅ {symbol}: Has dividend history ({len(data['historical'])} records)")
                finally:
                    fmp_limiter.release()
            except Exception as e:
                logger.debug(f"⚠️ {symbol}: Could not check dividends - {e}")

            # Determine if symbol meets criteria
            meets_criteria = has_recent_price or has_recent_dividend

            if not meets_criteria:
                if not has_recent_price and not has_recent_dividend:
                    exclusion_reason = "No recent price data (7 days) and no dividend history (365 days)"
                elif not has_recent_price:
                    exclusion_reason = "No recent price data (7 days)"
                else:
                    exclusion_reason = "No dividend history (365 days)"

                logger.debug(f"❌ {symbol}: Excluded - {exclusion_reason}")

                return {
                    'symbol': symbol,
                    'status': 'success',
                    'name': symbol_data.get('name', symbol),
                    'company_name': symbol_data.get('company_name'),
                    'description': symbol_data.get('description'),
                    'meets_criteria': False,
                    'recommendation': 'stocks_excluded',
                    'exclusion_reason': exclusion_reason,
                    'source_data': symbol_data
                }

            # Symbol passed validation
            return {
                'symbol': symbol,
                'status': 'success',
                'name': symbol_data.get('name', symbol),
                'company_name': symbol_data.get('company_name'),
                'description': symbol_data.get('description'),
                'meets_criteria': True,
                'recommendation': 'stocks',
                'note': f'Validated with FMP (recent_price: {has_recent_price}, recent_dividend: {has_recent_dividend})',
                'source_data': symbol_data
            }

        except Exception as e:
            logger.error(f"❌ {symbol}: Validation error - {e}")
            return {
                'symbol': symbol,
                'status': 'error',
                'reason': str(e),
                'exclusion_reason': f'Validation error: {str(e)}',
                'meets_criteria': False,
                'recommendation': 'stocks_excluded',
                'source_data': symbol_data
            }
    
    try:
        yahoo_limiter.acquire()
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                return {'symbol': symbol, 'status': 'failed', 'reason': 'No price data'}
            
            # Basic validation criteria
            price = info.get('regularMarketPrice', 0)
            if not (1.0 <= price <= 1000.0):
                return {'symbol': symbol, 'status': 'failed', 'reason': f'Price {price} out of range'}
            
            # Check for recent price activity (last 30 days)
            try:
                hist = ticker.history(period='1mo')
                if hist.empty or len(hist) < 5:
                    return {'symbol': symbol, 'status': 'failed', 'reason': 'Insufficient price history'}
            except:
                return {'symbol': symbol, 'status': 'failed', 'reason': 'Cannot fetch price history'}
            
            # Get company information - try FMP ETF info first for better company data
            company_name = None
            enhanced_info = {}
            
            # For ETFs only (excluding mutual funds), try to get better company info from FMP
            if info.get('quoteType') == 'ETF':
                try:
                    fmp_etf_info = fetch_fmp_etf_info(symbol)
                    if fmp_etf_info and fmp_etf_info.get('company_name'):
                        company_name = fmp_etf_info.get('company_name')
                        enhanced_info.update(fmp_etf_info)
                        logger.debug(f"Got ETF company from FMP: {symbol} -> {company_name}")
                except:
                    pass  # Fall back to Yahoo data
            
            # Fall back to Yahoo Finance company info if FMP didn't work
            if not company_name:
                company_name = info.get('fundFamily') or info.get('companyName') or None
            
            validation_result = {
                'symbol': symbol,
                'status': 'success',
                'price': price,
                'name': enhanced_info.get('name') or info.get('longName') or info.get('shortName') or symbol,
                'company_name': company_name,
                'description': enhanced_info.get('description') or info.get('longBusinessSummary'),
                'expense_ratio': (enhanced_info.get('expense_ratio') or
                                info.get('annualReportExpenseRatio') or 
                                info.get('netExpenseRatio') or 
                                info.get('expenseRatio') or 
                                info.get('totalExpenseRatio')),
                'aum': enhanced_info.get('aum') or info.get('totalAssets'),
                'quote_type': info.get('quoteType'),
                'exchange': info.get('exchange'),
                'source_data': symbol_data
            }
            
            # Check for dividends (optional for ETFs)
            try:
                dividends = ticker.dividends
                has_dividends = not dividends.empty and len(dividends) > 0
                
                if has_dividends:
                    recent_dividends = dividends[dividends.index >= (datetime.now() - timedelta(days=365))]
                    validation_result['has_recent_dividends'] = len(recent_dividends) > 0
                    validation_result['dividend_count'] = len(recent_dividends)
                else:
                    validation_result['has_recent_dividends'] = False
                    validation_result['dividend_count'] = 0
                    
            except Exception:
                validation_result['has_recent_dividends'] = False
                validation_result['dividend_count'] = 0
            
            # Determine if symbol meets criteria (exclude mutual funds)
            quote_type_upper = validation_result.get('quote_type', '').upper()
            is_etf = quote_type_upper == 'ETF'
            is_mutual_fund = quote_type_upper == 'MUTUALFUND'
            has_dividends = validation_result.get('has_recent_dividends', False)
            
            # Exclude mutual funds
            if is_mutual_fund:
                validation_result['meets_criteria'] = False
                validation_result['recommendation'] = 'stocks_excluded'
                validation_result['exclusion_reason'] = 'Mutual fund excluded (ETFs only)'
            else:
                # Accept ETFs and dividend-paying stocks
                validation_result['meets_criteria'] = True
                validation_result['recommendation'] = 'stocks'
                
                # Add note about dividend status for reference
                if not is_etf and not has_dividends:
                    validation_result['note'] = 'Stock without recent dividends (still accepted)'
            
            return validation_result
            
        finally:
            yahoo_limiter.release()
            
    except Exception as e:
        return {'symbol': symbol, 'status': 'error', 'reason': str(e)}

def check_symbols_exist_in_database_batch(symbols):
    """Check if symbols already exist in stocks or stocks_excluded tables using batch operations."""
    logger.info(f"🔍 Checking {len(symbols)} symbols against database (batch operation)...")
    
    try:
        # Get all symbols from stocks table with pagination
        existing_stocks = set()
        page_size = 1000
        offset = 0
        
        while True:
            page_symbols = pg_select("stocks", "symbol", limit=page_size, offset=offset)
            page_symbols = [row['symbol'] for row in page_symbols]
            
            if not page_symbols:
                break
                
            existing_stocks.update(page_symbols)
            
            if len(page_symbols) < page_size:
                break
                
            offset += page_size
        
        # Get all symbols from stocks_excluded table in one query
        try:
            excluded_data = pg_select("stocks_excluded", "symbol, reason", limit=5000)
            existing_excluded = {}
            for row in excluded_data:
                symbol = row['symbol']
                reason = row['reason']
                if symbol not in existing_excluded:
                    existing_excluded[symbol] = []
                existing_excluded[symbol].append(reason)
        except Exception as e:
            logger.warning(f"⚠️ stocks_excluded table may not exist: {e}")
            logger.warning("See CREATE_TABLE_INSTRUCTIONS.md for setup instructions")
            existing_excluded = {}
        
        # Process all symbols
        results = {}
        for symbol_data in symbols:
            symbol = symbol_data['symbol']
            
            if symbol in existing_stocks:
                results[symbol] = ('stocks', 'Already exists in stocks table')
            elif symbol in existing_excluded:
                reasons = existing_excluded[symbol]
                results[symbol] = ('stocks_excluded', f"Excluded: {', '.join(reasons)}")
            else:
                results[symbol] = (None, None)
        
        # Log batch results
        already_in_stocks = sum(1 for status, _ in results.values() if status == 'stocks')
        already_excluded = sum(1 for status, _ in results.values() if status == 'stocks_excluded')
        new_symbols = sum(1 for status, _ in results.values() if status is None)
        
        logger.info(f"📈 Batch database check results:")
        logger.info(f"   ✅ Already in stocks: {already_in_stocks}")
        logger.info(f"   🚫 Already excluded: {already_excluded}")
        logger.info(f"   🆕 New symbols: {new_symbols}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Batch database check failed: {e}")
        # Fallback to individual checks
        logger.info("🔄 Falling back to individual symbol checks...")
        results = {}
        for symbol_data in symbols:
            symbol = symbol_data['symbol']
            results[symbol] = check_symbol_exists_in_database(symbol)
        return results

def check_symbol_exists_in_database(symbol, exchange=None):
    """Check if symbol (with optional exchange) already exists in stocks or stocks_excluded tables."""
    try:
        # Check stocks table
        stocks_data = pg_select("stocks", "symbol", where_clause={"condition": "symbol = %s", "params": [symbol]})
        if stocks_data:
            return 'stocks', 'Already exists in stocks table'
        
        # Check stocks_excluded table (use existing schema - no source column yet)
        try:
            excluded_data = pg_select("stocks_excluded", "symbol, reason", where_clause={"condition": "symbol = %s", "params": [symbol]})
            if excluded_data:
                reasons = [row['reason'] for row in excluded_data]
                return 'stocks_excluded', f"Excluded: {', '.join(reasons)}"
        except Exception as e:
            logger.debug(f"Could not check stocks_excluded table: {e}")
        
        return None, None
        
    except Exception as e:
        logger.error(f"❌ Database check failed for {symbol}: {e}")
        return 'error', str(e)

def discover_crypto_etfs(limit=None):
    """Discover cryptocurrency ETFs specifically."""
    logger.info(f"🔍 [CRYPTO ETF] Discovering cryptocurrency ETFs (limit: {'None - fetching ALL' if limit is None else limit})")
    
    crypto_etf_symbols = [
        # Bitcoin ETFs
        'BITO', 'BTF', 'BTCC', 'EBIT', 'BITI', 'SBIT', 'TBIT', 'XBTF',
        'GBTC', 'BITB', 'ARKB', 'BTCO', 'EZBC', 'HODL', 'IBIT',
        
        # Ethereum ETFs
        'ETHE', 'ETHV', 'EZET', 'FETH', 'ETHC', 'ETHW',
        
        # Multi-crypto ETFs
        'BLOK', 'LEGR', 'BITQ', 'CRYP', 'KOIN', 'DAPP', 'CRPT',
        
        # Crypto mining ETFs
        'WGMI', 'RIGZ', 'DBIT', 'CLSK', 'MARA', 'RIOT',
        
        # DeFi ETFs
        'DEFI', 'NFTZ', 'METV'
    ]
    
    symbols = []
    discovered_symbols = set()
    
    for symbol in crypto_etf_symbols:
        if limit is not None and len(symbols) >= limit:
            break
            
        if symbol in discovered_symbols:
            continue
            
        try:
            yahoo_limiter.acquire()
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if info and 'regularMarketPrice' in info:
                    symbols.append({
                        'symbol': symbol,
                        'name': info.get('longName', info.get('shortName', symbol)),
                        'source': 'CRYPTO-ETF',
                        'exchange': info.get('exchange', 'Unknown'),
                        'type': info.get('quoteType', 'ETF'),
                        'category': 'Cryptocurrency'
                    })
                    discovered_symbols.add(symbol)
                    logger.debug(f"✅ [Crypto ETF] Validated: {symbol}")
            finally:
                yahoo_limiter.release()
        except Exception as e:
            logger.debug(f"Crypto ETF validation failed for {symbol}: {e}")
    
    logger.info(f"✅ [CRYPTO ETF] Discovered {len(symbols)} cryptocurrency ETFs")
    return symbols

def discover_specialized_dividend_etfs(limit=None):
    """Discover specialized dividend and income ETFs."""
    logger.info(f"🔍 [SPECIALIZED] Discovering specialized dividend ETFs (limit: {'None - fetching ALL' if limit is None else limit})")
    
    specialized_categories = {
        'Monthly Dividend': [
            'MDIV', 'SPHD', 'XYLD', 'QYLD', 'RYLD', 'FDVV', 'JEPI', 'JEPQ',
            'DIVO', 'CLM', 'CXE', 'UTG', 'IGA', 'IGD', 'THQ'
        ],
        'Covered Call': [
            'XYLD', 'QYLD', 'RYLD', 'NUSI', 'JEPI', 'JEPQ', 'DIVO', 'DJIA',
            'SPYI', 'XYLG', 'QYLG', 'RYLG', 'USOI', 'SPLV'
        ],
        'REIT/Real Estate': [
            'VNQ', 'REET', 'SRET', 'FREL', 'IYR', 'USRT', 'RWR', 'REZ',
            'MORT', 'REM', 'KBWB', 'HOMZ', 'ROOF', 'INDS'
        ],
        'International Dividend': [
            'VYMI', 'VXUS', 'IEFA', 'VEA', 'VWO', 'SCHF', 'IEMG', 'SPDW',
            'SPEM', 'IDEV', 'EFA', 'DLS', 'DTH', 'DVY', 'FEZ'
        ],
        'High Yield Bond': [
            'HYG', 'JNK', 'SHYG', 'SJNK', 'USHY', 'FALN', 'ANGL', 'HYDB',
            'BKLN', 'SRLN', 'FLOT', 'VTEB', 'MUB', 'TFI'
        ],
        'Utility/Infrastructure': [
            'XLU', 'VPU', 'FIDU', 'UTI', 'UTES', 'PUI', 'GRID', 'INFR',
            'TOLZ', 'ICLN', 'QCLN', 'PBW', 'ERTH'
        ]
    }
    
    symbols = []
    discovered_symbols = set()
    
    for category, category_symbols in specialized_categories.items():
        for symbol in category_symbols:
            if limit is not None and len(symbols) >= limit:
                break
                
            if symbol in discovered_symbols:
                continue
                
            try:
                yahoo_limiter.acquire()
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if info and 'regularMarketPrice' in info:
                        symbols.append({
                            'symbol': symbol,
                            'name': info.get('longName', info.get('shortName', symbol)),
                            'source': f'SPECIALIZED-{category.replace(" ", "-")}',
                            'exchange': info.get('exchange', 'Unknown'),
                            'type': info.get('quoteType', 'ETF'),
                            'category': category
                        })
                        discovered_symbols.add(symbol)
                        logger.debug(f"✅ [Specialized {category}] Validated: {symbol}")
                finally:
                    yahoo_limiter.release()
            except Exception as e:
                logger.debug(f"Specialized ETF validation failed for {symbol}: {e}")
    
    logger.info(f"✅ [SPECIALIZED] Discovered {len(symbols)} specialized dividend ETFs")
    return symbols

def discover_portfolio_holdings():
    """Discover symbols from int_portfolio_holdings table."""
    try:
        logger.info("🔍 [PORTFOLIO] Discovering symbols from portfolio holdings...")

        # Fetch all symbols from int_portfolio_holdings
        holdings_data = pg_select('int_portfolio_holdings', 'symbol')

        if not holdings_data:
            logger.info("ℹ️ [PORTFOLIO] No portfolio holdings found")
            return []

        symbols = []
        for holding in holdings_data:
            try:
                # Parse the JSON string to extract the actual symbol
                import json
                symbol_data = json.loads(holding['symbol'])
                symbol = symbol_data['symbol']['symbol'].strip().upper()  # Extract actual symbol
                name = symbol_data['symbol']['description']
                exchange = symbol_data['symbol']['exchange']['code']

                if symbol:
                    symbols.append({
                        'symbol': symbol,
                        'exchange': exchange,
                        'type': 'STOCK',
                        'name': name
                    })
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.debug(f"Failed to parse portfolio symbol data: {e}")
                # Fallback to treating as simple string if JSON parsing fails
                try:
                    symbol = str(holding['symbol']).strip().upper()
                    if symbol and not symbol.startswith('{'):
                        symbols.append({
                            'symbol': symbol,
                            'exchange': 'PORTFOLIO',
                            'type': 'STOCK',
                            'name': f'Portfolio Holding: {symbol}'
                        })
                except Exception:
                    pass

        logger.info(f"✅ [PORTFOLIO] Discovered {len(symbols)} symbols from portfolio holdings")
        return symbols
        
    except Exception as e:
        logger.error(f"❌ [PORTFOLIO] Error discovering portfolio holdings: {e}")
        return []

def ensure_portfolio_holdings_in_stocks():
    """Ensure all portfolio holdings are in the stocks table before updates."""
    try:
        logger.info("💼 Ensuring all portfolio holdings are in stocks table...")
        
        # Get portfolio holdings
        portfolio_data = pg_select('int_portfolio_holdings', 'symbol')
        if not portfolio_data:
            logger.info("ℹ️ No portfolio holdings found")
            return

        portfolio_symbols = []
        for holding in portfolio_data:
            try:
                # Parse the JSON string to extract the actual symbol
                import json
                symbol_data = json.loads(holding['symbol'])
                symbol = symbol_data['symbol']['symbol'].strip().upper()
                portfolio_symbols.append(symbol)
            except (json.JSONDecodeError, KeyError, TypeError):
                # Fallback to treating as simple string if JSON parsing fails
                try:
                    symbol = str(holding['symbol']).strip().upper()
                    if symbol and not symbol.startswith('{'):
                        portfolio_symbols.append(symbol)
                except Exception:
                    pass
        logger.info(f"📋 Found {len(portfolio_symbols)} portfolio symbols to check")
        
        # Check which ones are already in stocks table
        existing_data = pg_select('stocks', 'symbol', where_clause={"condition": f"symbol = ANY(%s)", "params": [portfolio_symbols]})
        existing_symbols = {stock['symbol'] for stock in existing_data}
        
        # Find missing symbols
        missing_symbols = [symbol for symbol in portfolio_symbols if symbol not in existing_symbols]
        
        if not missing_symbols:
            logger.info("✅ All portfolio holdings are already in stocks table")
            return
        
        logger.info(f"➕ Adding {len(missing_symbols)} missing portfolio holdings to stocks table")
        
        # Add missing symbols to stocks table (using only fields that exist)
        new_stocks = []
        for symbol in missing_symbols:
            new_stocks.append({
                'symbol': symbol,
                'name': f'Portfolio Holding: {symbol}'
            })
        
        if new_stocks:
            pg_upsert('stocks', new_stocks)
            logger.info(f"✅ Successfully added {len(new_stocks)} portfolio holdings to stocks table")
        
    except Exception as e:
        logger.error(f"❌ Error ensuring portfolio holdings in stocks table: {e}")

def comprehensive_symbol_discovery(fmp_limit=None, alpha_limit=None, yahoo_terms=None, nasdaq_limit=None, use_full_etf_list=False, use_dividend_screener=False, use_enhanced_discovery=True):
    """Perform comprehensive symbol discovery from all sources and filter against existing database."""
    logger.info("🚀 Starting comprehensive symbol discovery from all sources")
    logger.info("="*80)

    all_discovered_symbols = []
    discovery_stats = {
        'portfolio': 0,  # Add portfolio holdings
        'fmp': 0,
        'fmp_etf_list': 0,
        'fmp_dividend': 0,
        'alpha_vantage': 0,
        'yahoo': 0,
        'nasdaq': 0,
        'crypto_etf': 0,
        'specialized_etf': 0,
        'pattern_etf': 0,
        'enhanced_high_yield': 0,
        'enhanced_aristocrats': 0,
        'enhanced_sector_leaders': 0,
        'enhanced_consistent_payers': 0,
        'enhanced_etf_families': 0,
        'enhanced_new_etfs': 0,
        'enhanced_dividend_etfs': 0,
        'enhanced_international': 0,
        'total_discovered': 0,
        'already_in_stocks': 0,
        'already_excluded': 0,
        'new_symbols': 0
    }
    
    # Track unique symbols to avoid duplicates (symbol + exchange combination)
    unique_symbol_exchange = set()
    
    # Discover portfolio holdings first (highest priority)
    logger.info("💼 Discovering symbols from portfolio holdings...")
    portfolio_symbols = discover_portfolio_holdings()
    discovery_stats['portfolio'] = len(portfolio_symbols)
    
    for symbol_data in portfolio_symbols:
        symbol = symbol_data['symbol']
        exchange = symbol_data.get('exchange', 'PORTFOLIO')
        key = f"{symbol}:{exchange}"
        
        if key not in unique_symbol_exchange:
            unique_symbol_exchange.add(key)
            all_discovered_symbols.append(symbol_data)
    
    # Discover from FMP (Primary source)
    if fmp_limit is None or fmp_limit > 0:
        logger.info("🔵 Discovering symbols from FMP...")
        fmp_symbols = discover_symbols_from_fmp(fmp_limit)
        discovery_stats['fmp'] = len(fmp_symbols)
        
        for symbol_data in fmp_symbols:
            symbol = symbol_data['symbol']
            exchange = symbol_data.get('exchange', 'Unknown')
            key = f"{symbol}:{exchange}"
            
            if key not in unique_symbol_exchange:
                unique_symbol_exchange.add(key)
                all_discovered_symbols.append(symbol_data)
    
    # Discover ALL ETFs from FMP comprehensive list
    if use_full_etf_list:
        logger.info("🔵 Discovering ALL ETFs from FMP comprehensive list...")
        fmp_etf_symbols = discover_all_etfs_from_fmp()
        discovery_stats['fmp_etf_list'] = len(fmp_etf_symbols)
        
        for symbol_data in fmp_etf_symbols:
            symbol = symbol_data['symbol']
            key = f"{symbol}:ETF"  # Use ETF as exchange for deduplication
            
            if key not in unique_symbol_exchange:
                unique_symbol_exchange.add(key)
                all_discovered_symbols.append(symbol_data)
    
    # Discover dividend-paying stocks from FMP screener
    if use_dividend_screener:
        logger.info("🔵 Discovering dividend stocks from FMP screener...")
        fmp_div_symbols = discover_dividend_stocks_from_fmp(min_yield=0.005, limit=None)  # 0.5%+ yield - unlimited
        discovery_stats['fmp_dividend'] = len(fmp_div_symbols)
        
        for symbol_data in fmp_div_symbols:
            symbol = symbol_data['symbol']
            exchange = symbol_data.get('exchange', 'Unknown')
            key = f"{symbol}:{exchange}"
            
            if key not in unique_symbol_exchange:
                unique_symbol_exchange.add(key)
                all_discovered_symbols.append(symbol_data)
    
    # Discover from Alpha Vantage (Secondary source)  
    if alpha_limit is None or alpha_limit > 0:
        logger.info("🟠 Discovering symbols from Alpha Vantage...")
        av_symbols = discover_symbols_from_alpha_vantage(alpha_limit)
        discovery_stats['alpha_vantage'] = len(av_symbols)
        
        for symbol_data in av_symbols:
            symbol = symbol_data['symbol']
            exchange = symbol_data.get('exchange', 'Unknown')
            key = f"{symbol}:{exchange}"
            
            if key not in unique_symbol_exchange:
                unique_symbol_exchange.add(key)
                all_discovered_symbols.append(symbol_data)
    
    # Discover from Yahoo Finance screener and categories (Enhanced source) - DISABLED
    # Yahoo Finance API is unreliable with frequent auth errors
    logger.info("🟡 Yahoo Finance discovery disabled (unreliable API)")
    yahoo_symbols = []
    discovery_stats['yahoo'] = 0
    
    for symbol_data in yahoo_symbols:
        symbol = symbol_data['symbol']
        exchange = symbol_data.get('exchange', 'Unknown')
        key = f"{symbol}:{exchange}"
        
        if key not in unique_symbol_exchange:
            unique_symbol_exchange.add(key)
            all_discovered_symbols.append(symbol_data)
    
    # Discover from NASDAQ API (Additional source)
    if nasdaq_limit is None or nasdaq_limit > 0:
        logger.info("🟢 Discovering symbols from NASDAQ API...")
        nasdaq_symbols = discover_symbols_from_nasdaq_api(nasdaq_limit)
        discovery_stats['nasdaq'] = len(nasdaq_symbols)
        
        for symbol_data in nasdaq_symbols:
            symbol = symbol_data['symbol']
            exchange = symbol_data.get('exchange', 'NASDAQ')
            key = f"{symbol}:{exchange}"
            
            if key not in unique_symbol_exchange:
                unique_symbol_exchange.add(key)
                all_discovered_symbols.append(symbol_data)
    
    # Discover cryptocurrency ETFs (New high-growth category)
    logger.info("🟡 Discovering cryptocurrency ETFs...")
    crypto_etf_symbols = discover_crypto_etfs(100)
    discovery_stats['crypto_etf'] = len(crypto_etf_symbols)
    
    for symbol_data in crypto_etf_symbols:
        symbol = symbol_data['symbol']
        exchange = symbol_data.get('exchange', 'Unknown')
        key = f"{symbol}:{exchange}"
        
        if key not in unique_symbol_exchange:
            unique_symbol_exchange.add(key)
            all_discovered_symbols.append(symbol_data)
    
    # Discover specialized dividend ETFs (Enhanced coverage)
    logger.info("🟪 Discovering specialized dividend ETFs...")
    specialized_etf_symbols = discover_specialized_dividend_etfs(150)
    discovery_stats['specialized_etf'] = len(specialized_etf_symbols)
    
    for symbol_data in specialized_etf_symbols:
        symbol = symbol_data['symbol']
        exchange = symbol_data.get('exchange', 'Unknown')
        key = f"{symbol}:{exchange}"
        
        if key not in unique_symbol_exchange:
            unique_symbol_exchange.add(key)
            all_discovered_symbols.append(symbol_data)
    
    # Discover ETFs using company-based approach (Enhanced ETF coverage)
    logger.info("🟣 Discovering ETFs using company-based approach...")
    company_etf_symbols = discover_etfs_by_company(200)
    discovery_stats['pattern_etf'] = len(company_etf_symbols)

    for symbol_data in company_etf_symbols:
        symbol = symbol_data['symbol']
        exchange = symbol_data.get('exchange', 'Unknown')
        key = f"{symbol}:{exchange}"

        if key not in unique_symbol_exchange:
            unique_symbol_exchange.add(key)
            all_discovered_symbols.append(symbol_data)

    # ========================================================================
    # ENHANCED DISCOVERY - FMP Ultimate Plan Full Utilization
    # ========================================================================
    if use_enhanced_discovery:
        logger.info("=" * 80)
        logger.info("🚀 ENHANCED DISCOVERY - FMP ULTIMATE PLAN MAXIMIZATION")
        logger.info("=" * 80)

        try:
            from enhanced_discovery import (
                discover_high_yield_dividend_stocks,
                discover_dividend_aristocrats,
                discover_all_sector_dividend_leaders,
                discover_consistent_dividend_payers,
                discover_etfs_by_family_patterns,
                discover_recently_launched_etfs,
                discover_high_dividend_etfs_by_holdings,
                discover_all_international_dividend_stocks
            )

            # 1. High-yield stocks (3%+ yield, $100M+ mcap)
            logger.info("🔷 Enhanced: High-Yield Stocks...")
            enhanced_high_yield = discover_high_yield_dividend_stocks(min_yield=0.03, min_market_cap=100000000)
            discovery_stats['enhanced_high_yield'] = len(enhanced_high_yield)
            for symbol_data in enhanced_high_yield:
                symbol = symbol_data['symbol']
                exchange = symbol_data.get('exchange', 'Unknown')
                key = f"{symbol}:{exchange}"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            # 2. Dividend aristocrats (large caps, 1%+ yield)
            logger.info("🔷 Enhanced: Dividend Aristocrats...")
            enhanced_aristocrats = discover_dividend_aristocrats(min_yield=0.01, min_market_cap=1000000000)
            discovery_stats['enhanced_aristocrats'] = len(enhanced_aristocrats)
            for symbol_data in enhanced_aristocrats:
                symbol = symbol_data['symbol']
                exchange = symbol_data.get('exchange', 'Unknown')
                key = f"{symbol}:{exchange}"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            # 3. Sector-specific leaders
            logger.info("🔷 Enhanced: Sector Dividend Leaders...")
            enhanced_sector = discover_all_sector_dividend_leaders()
            discovery_stats['enhanced_sector_leaders'] = len(enhanced_sector)
            for symbol_data in enhanced_sector:
                symbol = symbol_data['symbol']
                exchange = symbol_data.get('exchange', 'Unknown')
                key = f"{symbol}:{exchange}"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            # 4. Behavioral discovery - consistent payers
            logger.info("🔷 Enhanced: Behavioral Analysis (Consistent Payers)...")
            enhanced_consistent = discover_consistent_dividend_payers(years_back=4, min_payments_per_year=4)
            discovery_stats['enhanced_consistent_payers'] = len(enhanced_consistent)
            for symbol_data in enhanced_consistent:
                symbol = symbol_data['symbol']
                key = f"{symbol}:BEHAVIORAL"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            # 5. Dynamic ETF family patterns (YieldMax, Roundhill, etc.)
            logger.info("🔷 Enhanced: Dynamic ETF Family Detection...")
            enhanced_etf_families = discover_etfs_by_family_patterns()
            discovery_stats['enhanced_etf_families'] = len(enhanced_etf_families)
            for symbol_data in enhanced_etf_families:
                symbol = symbol_data['symbol']
                key = f"{symbol}:ETF-FAMILY"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            # 6. Recently launched ETFs (last 180 days)
            logger.info("🔷 Enhanced: New ETF Launch Monitoring...")
            enhanced_new_etfs = discover_recently_launched_etfs(days_back=180)
            discovery_stats['enhanced_new_etfs'] = len(enhanced_new_etfs)
            for symbol_data in enhanced_new_etfs:
                symbol = symbol_data['symbol']
                key = f"{symbol}:NEW-ETF"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            # 7. Dividend-focused ETFs by holdings
            logger.info("🔷 Enhanced: Dividend-Focused ETFs...")
            enhanced_div_etfs = discover_high_dividend_etfs_by_holdings()
            discovery_stats['enhanced_dividend_etfs'] = len(enhanced_div_etfs)
            for symbol_data in enhanced_div_etfs:
                symbol = symbol_data['symbol']
                key = f"{symbol}:DIV-ETF"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            # 8. International markets (LSE, TSX, ASX, JSE, XETRA)
            logger.info("🔷 Enhanced: International Dividend Stocks...")
            enhanced_international = discover_all_international_dividend_stocks()
            discovery_stats['enhanced_international'] = len(enhanced_international)
            for symbol_data in enhanced_international:
                symbol = symbol_data['symbol']
                exchange = symbol_data.get('exchange', 'Unknown')
                key = f"{symbol}:{exchange}"
                if key not in unique_symbol_exchange:
                    unique_symbol_exchange.add(key)
                    all_discovered_symbols.append(symbol_data)

            logger.info("=" * 80)
            logger.info("✅ Enhanced Discovery Complete")
            logger.info("=" * 80)

        except ImportError as e:
            logger.warning(f"⚠️ Enhanced discovery module not available: {e}")
            logger.info("ℹ️ Continuing with standard discovery methods...")
        except Exception as e:
            logger.error(f"❌ Enhanced discovery error: {e}")
            logger.info("ℹ️ Continuing with standard discovery methods...")

    discovery_stats['total_discovered'] = len(all_discovered_symbols)
    
    # Now filter against existing database using batch operations
    logger.info("🔍 Filtering discovered symbols against existing database (batch operation)...")
    batch_results = check_symbols_exist_in_database_batch(all_discovered_symbols)
    
    new_symbols_to_add = []
    
    for symbol_data in all_discovered_symbols:
        symbol = symbol_data['symbol']
        exists_in, reason = batch_results.get(symbol, (None, None))
        
        if exists_in == 'stocks':
            # Skip re-validation of existing symbols (they're already validated)
            discovery_stats['already_in_stocks'] += 1
            logger.debug(f"✅ {symbol}: Already in stocks table - skipping validation")
        elif exists_in == 'stocks_excluded':
            discovery_stats['already_excluded'] += 1
            logger.debug(f"🚫 {symbol}: {reason}")
        elif exists_in is None:
            # New symbol - add to list for processing
            new_symbols_to_add.append(symbol_data)
            discovery_stats['new_symbols'] += 1
        else:
            logger.error(f"❌ {symbol}: Database check error - {reason}")
    
    # Log discovery results
    logger.info("📊 Comprehensive Symbol Discovery Results:")
    logger.info(f"   💼 Portfolio Holdings: {discovery_stats['portfolio']} symbols")
    logger.info(f"   🔵 FMP: {discovery_stats['fmp']} symbols")
    if discovery_stats['fmp_etf_list'] > 0:
        logger.info(f"   🔵 FMP ETF List: {discovery_stats['fmp_etf_list']} symbols")
    if discovery_stats['fmp_dividend'] > 0:
        logger.info(f"   🔵 FMP Dividend: {discovery_stats['fmp_dividend']} symbols")
    logger.info(f"   🟠 Alpha Vantage: {discovery_stats['alpha_vantage']} symbols")
    logger.info(f"   🟡 Yahoo Finance: {discovery_stats['yahoo']} symbols")
    logger.info(f"   🟢 NASDAQ API: {discovery_stats['nasdaq']} symbols")
    if discovery_stats['crypto_etf'] > 0:
        logger.info(f"   🟡 Crypto ETFs: {discovery_stats['crypto_etf']} symbols")
    if discovery_stats['specialized_etf'] > 0:
        logger.info(f"   🟪 Specialized ETFs: {discovery_stats['specialized_etf']} symbols")
    logger.info(f"   🟣 Company Pattern ETFs: {discovery_stats['pattern_etf']} symbols")

    # Enhanced Discovery Stats
    if use_enhanced_discovery:
        logger.info("")
        logger.info("🚀 Enhanced Discovery Stats (FMP Ultimate Plan):")
        if discovery_stats['enhanced_high_yield'] > 0:
            logger.info(f"   🔷 High-Yield Stocks (3%+): {discovery_stats['enhanced_high_yield']} symbols")
        if discovery_stats['enhanced_aristocrats'] > 0:
            logger.info(f"   🔷 Dividend Aristocrats: {discovery_stats['enhanced_aristocrats']} symbols")
        if discovery_stats['enhanced_sector_leaders'] > 0:
            logger.info(f"   🔷 Sector Leaders: {discovery_stats['enhanced_sector_leaders']} symbols")
        if discovery_stats['enhanced_consistent_payers'] > 0:
            logger.info(f"   🔷 Consistent Payers (Behavioral): {discovery_stats['enhanced_consistent_payers']} symbols")
        if discovery_stats['enhanced_etf_families'] > 0:
            logger.info(f"   🔷 ETF Families (Dynamic): {discovery_stats['enhanced_etf_families']} symbols")
        if discovery_stats['enhanced_new_etfs'] > 0:
            logger.info(f"   🔷 New ETF Launches (180d): {discovery_stats['enhanced_new_etfs']} symbols")
        if discovery_stats['enhanced_dividend_etfs'] > 0:
            logger.info(f"   🔷 Dividend-Focused ETFs: {discovery_stats['enhanced_dividend_etfs']} symbols")
        if discovery_stats['enhanced_international'] > 0:
            logger.info(f"   🔷 International Markets: {discovery_stats['enhanced_international']} symbols")

    logger.info("")
    logger.info(f"   🎯 Total Discovered: {discovery_stats['total_discovered']} unique symbols")
    logger.info("")
    logger.info("📋 Database Filtering Results:")
    logger.info(f"   ✅ Already in stocks (skipped): {discovery_stats['already_in_stocks']} symbols")
    logger.info(f"   🚫 Already excluded (skipped): {discovery_stats['already_excluded']} symbols")
    logger.info(f"   🆕 New symbols to validate: {discovery_stats['new_symbols']} symbols")
    logger.info(f"   📝 Total symbols to validate: {len(new_symbols_to_add)} symbols")
    
    return new_symbols_to_add, discovery_stats

def get_latest_dates_for_all_symbols(table_name, date_column, all_symbols):
    """Efficiently get latest dates for ALL symbols using optimized pagination.

    This replaces the inefficient 20K limit approach that missed ~11K symbols.
    Strategy: Fetch records ordered by date DESC, stop when all symbols found.
    """
    latest_dates = {}
    remaining_symbols = set(all_symbols)

    try:
        # Fetch records ordered by date (newest first)
        # Stop when we've found at least one record for every symbol
        page_size = 5000  # Smaller pages, faster queries
        offset = 0
        total_records = 0

        logger.debug(f"📊 Getting latest {date_column} for {len(all_symbols)} symbols from {table_name}...")

        while remaining_symbols and offset < 100000:  # Safety limit
            try:
                records = pg_select(table_name, f"symbol, {date_column}",
                                  order_by=f"{date_column} DESC",
                                  limit=page_size,
                                  offset=offset)

                if not records:
                    break

                # Track max date per symbol (first occurrence is latest due to DESC order)
                for record in records:
                    symbol = record['symbol']
                    if symbol in remaining_symbols:
                        latest_dates[symbol] = record[date_column]
                        remaining_symbols.remove(symbol)

                total_records += len(records)

                # Early exit if we found all symbols
                if not remaining_symbols:
                    logger.debug(f"✅ Found dates for all {len(all_symbols)} symbols after {total_records} records")
                    break

                if len(records) < page_size:
                    # No more records
                    break

                offset += page_size

            except Exception as page_error:
                logger.warning(f"Error fetching page at offset {offset}: {page_error}")
                break

        logger.info(f"📊 {table_name}: Found dates for {len(latest_dates)}/{len(all_symbols)} symbols ({total_records} records scanned)")

        if remaining_symbols:
            logger.debug(f"⚠️  {len(remaining_symbols)} symbols have no data in {table_name}")

    except Exception as e:
        logger.error(f"Error getting latest dates from {table_name}: {e}")

    return latest_dates

def get_symbols_needing_update():
    """Get only symbols that actually need data updates using intelligent filtering."""
    logger.info("🎯 Analyzing which symbols need updates (intelligent filtering)...")

    try:
        # Fetch all symbols with pagination (Supabase has 1000 row limit)
        all_symbols = []
        page_size = 1000
        offset = 0

        while True:
            page_symbols = pg_select("stocks", "symbol", limit=page_size, offset=offset)
            page_symbols = [row['symbol'] for row in page_symbols]

            if not page_symbols:
                break

            all_symbols.extend(page_symbols)
            logger.debug(f"Fetched {len(page_symbols)} symbols (total: {len(all_symbols)})")

            if len(page_symbols) < page_size:
                break

            offset += page_size

        # Get latest price dates for ALL symbols efficiently
        price_dates = get_latest_dates_for_all_symbols("stock_prices", "date", all_symbols)

        # Get latest dividend dates for ALL symbols efficiently
        dividend_dates = get_latest_dates_for_all_symbols("dividend_history", "payment_date", all_symbols)
        
        # Filter symbols that need updates
        symbols_needing_update = []
        today = datetime.now().date()
        
        for symbol in all_symbols:
            needs_update = False
            reasons = []
            
            # Check if needs price update (older than 2 days or missing)
            # Changed from 7 days to 2 days for more frequent updates
            latest_price = price_dates.get(symbol)
            if not latest_price:
                needs_update = True
                reasons.append("no price data")
            else:
                # Handle both string and date object types
                if isinstance(latest_price, str):
                    latest_price_date = datetime.strptime(latest_price, '%Y-%m-%d').date()
                else:
                    latest_price_date = latest_price
                days_since_price = (today - latest_price_date).days
                if days_since_price >= 2:
                    needs_update = True
                    reasons.append(f"price data {days_since_price} days old")
            
            # Check if needs dividend update (older than 30 days or missing)
            latest_dividend = dividend_dates.get(symbol)
            if not latest_dividend:
                needs_update = True
                reasons.append("no dividend data")
            else:
                # Handle both string and date object types
                if isinstance(latest_dividend, str):
                    latest_dividend_date = datetime.strptime(latest_dividend, '%Y-%m-%d').date()
                else:
                    latest_dividend_date = latest_dividend
                days_since_dividend = (today - latest_dividend_date).days
                if days_since_dividend > 30:
                    needs_update = True
                    reasons.append(f"dividend data {days_since_dividend} days old")
            
            if needs_update:
                symbols_needing_update.append({
                    'symbol': symbol,
                    'reasons': reasons,
                    'latest_price': latest_price,
                    'latest_dividend': latest_dividend
                })
        
        logger.info(f"🎯 Intelligent filtering results:")
        logger.info(f"   📊 Total symbols in database: {len(all_symbols)}")
        logger.info(f"   🔄 Symbols needing updates: {len(symbols_needing_update)}")
        logger.info(f"   ✅ Symbols already current: {len(all_symbols) - len(symbols_needing_update)}")
        logger.info(f"   ⚡ Performance improvement: {((len(all_symbols) - len(symbols_needing_update)) / len(all_symbols) * 100):.1f}% fewer API calls")
        
        return [s['symbol'] for s in symbols_needing_update]
        
    except Exception as e:
        logger.error(f"❌ Error in intelligent filtering, falling back to all symbols: {e}")
        # Fallback to all symbols if filtering fails - with pagination
        all_symbols = []
        page_size = 1000
        offset = 0
        
        while True:
            try:
                page_symbols_data = pg_select("stocks", "symbol", limit=page_size, offset=offset)
                page_symbols = [row['symbol'] for row in page_symbols_data]
                
                if not page_symbols:
                    break
                    
                all_symbols.extend(page_symbols)
                
                if len(page_symbols) < page_size:
                    break
                    
                offset += page_size
            except Exception as fallback_error:
                logger.error(f"❌ Even fallback failed: {fallback_error}")
                break
                
        return all_symbols

def check_existing_data_completeness(symbol):
    """Check what data already exists for a symbol and which source provided it."""
    try:
        # Check if symbol has recent price data (within 7 days)
        price_data = pg_select("stock_prices", "date", where_clause={"condition": "symbol = %s", "params": [symbol]}, order_by="date DESC", limit=1)
        has_recent_prices = False
        if price_data:
            price_date = price_data[0]['date']
            # Handle both string and date object types
            if isinstance(price_date, str):
                latest_price_date = datetime.strptime(price_date, '%Y-%m-%d')
            else:
                latest_price_date = datetime.combine(price_date, datetime.min.time())
            days_since_price = (datetime.now() - latest_price_date).days
            has_recent_prices = days_since_price <= 7
        
        # Check if symbol has recent dividend data (within 1 year)
        dividend_data = pg_select("dividend_history", "payment_date", where_clause={"condition": "symbol = %s", "params": [symbol]}, order_by="payment_date DESC", limit=1)
        has_recent_dividends = False
        if dividend_data:
            payment_date = dividend_data[0]['payment_date']
            # Handle both string and date object types
            if isinstance(payment_date, str):
                latest_dividend_date = datetime.strptime(payment_date, '%Y-%m-%d')
            else:
                latest_dividend_date = datetime.combine(payment_date, datetime.min.time())
            days_since_dividend = (datetime.now() - latest_dividend_date).days
            has_recent_dividends = days_since_dividend <= 365
        
        # Determine completeness
        return {
            'has_recent_prices': has_recent_prices,
            'has_recent_dividends': has_recent_dividends,
            'is_complete': has_recent_prices and has_recent_dividends,
            'needs_prices': not has_recent_prices,
            'needs_dividends': not has_recent_dividends
        }
        
    except Exception as e:
        logger.error(f"❌ Error checking existing data for {symbol}: {e}")
        return {
            'has_recent_prices': False,
            'has_recent_dividends': False,
            'is_complete': False,
            'needs_prices': True,
            'needs_dividends': True
        }

def fetch_hybrid_prices(symbol, from_date=None, force_check=False):
    """
    Fetch prices using hybrid approach with source-aware completion logic:
    1. Check if FMP already provided complete recent data → Skip other sources
    2. Try FMP (primary)
    3. Try Alpha Vantage (secondary) if FMP failed
    4. Try Yahoo Finance (fallback) if others failed
    """
    logger.debug(f"🔄 [HYBRID] Starting price fetch for {symbol}")
    
    # Check existing data completeness unless forced
    if not force_check:
        data_status = check_existing_data_completeness(symbol)
        if not data_status['needs_prices']:
            logger.debug(f"⏭️ [SKIP] {symbol} already has recent price data")
            return "skipped"
    
    # Try FMP first (primary source)
    result = fetch_fmp_prices(symbol, from_date)
    if result and result['count'] > 0:
        logger.debug(f"✅ [FMP] Found {result['count']} price records for {symbol}")
        return result
    
    # Try Alpha Vantage (secondary source) - only if FMP failed
    if ALPHA_VANTAGE_API_KEY and USE_HYBRID_DIVIDENDS:
        logger.debug(f"🔄 [FMP FAILED] Trying Alpha Vantage for {symbol}")
        result = fetch_alpha_vantage_prices(symbol)
        if result and result['count'] > 0:
            logger.debug(f"✅ [ALPHA VANTAGE FALLBACK] Found {result['count']} price records for {symbol}")
            return result

    # Try Yahoo Finance (fallback) - only if FMP and Alpha Vantage failed
    if FALLBACK_TO_YAHOO:
        logger.debug(f"🔄 [FMP+AV FAILED] Trying Yahoo Finance for {symbol}")
        result = fetch_yahoo_prices(symbol)
        if result and result['count'] > 0:
            logger.debug(f"✅ [YAHOO FALLBACK] Found {result['count']} price records for {symbol}")
            return result
    
    logger.debug(f"❌ [HYBRID] No price data found for {symbol} from any source")
    return None

def process_symbol_prices_hybrid(symbol, max_date=None, force_check=False):
    """Process price history for a single symbol using hybrid approach."""
    try:
        logger.debug(f"🔄 {symbol}: Starting hybrid price processing (max_date: {max_date}, force_check: {force_check})")
        
        # Check if we need to fetch new data
        if max_date:
            today = datetime.now().date()
            # Convert max_date to date object if it's a string
            if isinstance(max_date, str):
                max_date = datetime.strptime(max_date, '%Y-%m-%d').date()

            # Calculate last trading day (skip weekends)
            last_trading_day = today
            while last_trading_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
                last_trading_day -= timedelta(days=1)

            # Skip if we already have data for the last trading day
            if max_date >= last_trading_day:
                logger.debug(f"⏭️  {symbol}: Skipping - already has current price data (latest: {max_date}, last trading day: {last_trading_day})")
                return "skipped"
        
        # Determine from_date for incremental fetching
        from_date = None
        if ENHANCED_HISTORICAL_DATA and max_date:
            # Handle both string and date object types
            if isinstance(max_date, str):
                max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
            else:
                max_date_obj = datetime.combine(max_date, datetime.min.time())
            from_date = (max_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            logger.debug(f"📊 {symbol}: [INCREMENTAL] Fetching new price data only (from {from_date})")
        elif ENHANCED_HISTORICAL_DATA:
            logger.debug(f"📊 {symbol}: [FIRST TIME] Fetching comprehensive historical price data")
        
        # Fetch price data using hybrid approach
        result = fetch_hybrid_prices(symbol, from_date, force_check=force_check)
        
        # Handle skipped result
        if result == "skipped":
            logger.debug(f"⏭️ {symbol}: Skipped - already has recent price data")
            return "skipped"
        
        if not result or not result.get('data'):
            logger.debug(f"ℹ️  {symbol}: No price data available from any source")
            return False
        
        # Process the price data based on source
        price_records = []

        if result['source'] in ['Yahoo Finance', 'FMP']:
            # Both Yahoo and FMP data can be processed similarly
            for price_data in result['data']:
                record = {
                    "symbol": symbol,
                    "date": price_data.get('date'),
                    "price": price_data.get('close'),  # Main price field (required)
                    "open": price_data.get('open'),
                    "high": price_data.get('high'),
                    "low": price_data.get('low'),
                    "close": price_data.get('close'),
                    "adj_close": price_data.get('adjClose', price_data.get('close')),  # Use adjClose if available, fallback to close
                    "volume": price_data.get('volume', 0)
                }
                # Add AUM if present (from Yahoo Finance for ETFs)
                if price_data.get('aum'):
                    record['aum'] = price_data.get('aum')

                price_records.append(record)

        # Check if API data is stale (>7 days old) before inserting
        if price_records:
            latest_api_date = max(datetime.strptime(rec['date'], '%Y-%m-%d').date() for rec in price_records)
            today = datetime.now().date()
            stale_threshold = today - timedelta(days=7)

            if latest_api_date < stale_threshold:
                days_old = (today - latest_api_date).days
                logger.info(f"🚫 {symbol}: API data is {days_old} days old (last: {latest_api_date}) - excluding symbol")
                try:
                    # Add to excluded_symbols table
                    pg_insert('stocks_excluded', [{
                        'symbol': symbol,
                        'reason': f'Stale API data - last price {days_old} days old ({latest_api_date})'
                    }])
                    # Remove from stocks table
                    pg_delete('stocks', where_clause={'condition': 'symbol = %s', 'params': [symbol]})
                    logger.info(f"✅ {symbol}: Excluded from stocks table (stale API data)")
                except Exception as e:
                    logger.error(f"❌ {symbol}: Failed to exclude - {e}")
                return False  # Don't insert stale data

        # Insert prices into database
        if price_records:
            try:
                logger.debug(f"💾 {symbol}: Inserting {len(price_records)} price records to database")
                pg_upsert("stock_prices", price_records)
                logger.info(f"✅ {symbol}: Successfully inserted {len(price_records)} price records [{result['source']}]")
                return True
            except Exception as e:
                logger.error(f"❌ {symbol}: Database insertion failed - {e}")
                return False
        elif not price_records:
            logger.debug(f"ℹ️  {symbol}: No valid price records to insert")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ {symbol}: Unexpected error in hybrid price processing - {e}")
        return False

def fetch_fmp_dividends(symbol, from_date=None):
    """Fetch dividend data from FMP API."""
    try:
        if from_date:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{symbol}?from={from_date}&apikey={FMP_API_KEY}"
        else:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{symbol}?from={DIVIDENDS_START_DATE}&apikey={FMP_API_KEY}"
        
        logger.debug(f"💰 [FMP] Fetching dividends for {symbol}")
        data = fetch_with_adaptive_retry(url, fmp_limiter, symbol=symbol)
        
        if data and 'historical' in data and data['historical']:
            return {
                'source': 'FMP',
                'data': data['historical'],
                'count': len(data['historical'])
            }
    except Exception as e:
        logger.error(f"FMP dividends error for {symbol}: {e}")
    
    return None

def fetch_future_dividends_fmp(from_date=None, to_date=None, symbols=None):
    """Fetch future dividend calendar from FMP API.
    
    Args:
        from_date (str): Start date in YYYY-MM-DD format (default: today)
        to_date (str): End date in YYYY-MM-DD format (default: 3 months from now)
        symbols (list): Optional list of symbols to filter for
        
    Returns:
        dict: Future dividend data with symbol, ex-dividend dates, and amounts
    """
    try:
        # Set default date range if not provided
        if not from_date:
            from_date = datetime.now().strftime('%Y-%m-%d')
        if not to_date:
            to_date = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        
        url = f"https://financialmodelingprep.com/api/v3/stock_dividend_calendar?from={from_date}&to={to_date}&apikey={FMP_API_KEY}"
        
        logger.info(f"🔮 [FMP] Fetching future dividends from {from_date} to {to_date}")
        data = fetch_with_adaptive_retry(url, fmp_limiter)
        
        if data:
            future_dividends = []
            db_records = []
            
            for dividend in data:
                # Filter by symbols if provided
                if symbols and dividend.get('symbol') not in symbols:
                    continue
                
                # Process data for return
                dividend_record = {
                    'symbol': dividend.get('symbol'),
                    'dividend': dividend.get('dividend'),
                    'ex_dividend_date': dividend.get('date'),
                    'record_date': dividend.get('recordDate'),
                    'payment_date': dividend.get('paymentDate'),
                    'declaration_date': dividend.get('declarationDate'),
                    'label': dividend.get('label'),
                    'adj_dividend': dividend.get('adjDividend')
                }
                future_dividends.append(dividend_record)
                
                # Prepare data for database insertion (dividend_calendar table schema)
                db_record = {
                    'symbol': dividend.get('symbol'),
                    'date': dividend.get('date'),  # ex-dividend date
                    'dividend': float(dividend.get('dividend', 0)) if dividend.get('dividend') else 0.0,
                    'adj_dividend': float(dividend.get('adjDividend', dividend.get('dividend', 0))) if dividend.get('adjDividend') or dividend.get('dividend') else 0.0,
                    'payment_date': dividend.get('paymentDate')
                }
                
                # Only add records with valid data
                if db_record['symbol'] and db_record['date'] and db_record['dividend'] > 0:
                    db_records.append(db_record)
            
            # Insert into database
            inserted_count = 0
            if db_records:
                try:
                    # Clear existing future dividend data first (to avoid duplicates)
                    clear_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    pg_delete('dividend_calendar', {"condition": "date >= %s", "params": [clear_date]})
                    logger.info(f"🗑️ [DB] Cleared existing future dividend data from {clear_date}")
                    
                    # Insert new data in batches
                    batch_size = 100
                    for i in range(0, len(db_records), batch_size):
                        batch = db_records[i:i + batch_size]
                        result = pg_insert('dividend_calendar', batch)
                        inserted_count += len(batch)
                        logger.debug(f"💾 [DB] Inserted batch {i//batch_size + 1}: {len(batch)} records")
                    
                    logger.info(f"💾 [DB] Successfully inserted {inserted_count} future dividend records")
                    
                except Exception as db_error:
                    logger.error(f"❌ [DB] Error inserting future dividends: {db_error}")
                    logger.info("📋 [DB] Continuing with display-only mode")
            
            logger.info(f"✅ [FMP] Found {len(future_dividends)} future dividend announcements")
            return {
                'source': 'FMP',
                'data': future_dividends,
                'count': len(future_dividends),
                'inserted_count': inserted_count,
                'date_range': f"{from_date} to {to_date}"
            }
        else:
            logger.warning(f"⚠️ [FMP] No future dividend data received")
            
    except Exception as e:
        logger.error(f"❌ [FMP] Error fetching future dividends: {e}")
    
    return None

def fetch_future_dividends_yahoo(symbols=None, include_predictions=True):
    """Fetch future dividend calendar from Yahoo Finance API.
    
    Args:
        symbols (list): List of symbols to check (default: None for discovery mode)
        include_predictions (bool): Include pattern-based predictions for missing announcements
        
    Returns:
        dict: Future dividend data with symbol, ex-dividend dates, and amounts
    """
    try:
        if symbols is None:
            # Use a broader set of dividend-paying symbols for discovery
            symbols = [
                # High-dividend US stocks
                'KO', 'JNJ', 'PG', 'T', 'VZ', 'IBM', 'XOM', 'CVX', 'MMM', 'WMT', 'PFE', 'MRK',
                # Dividend aristocrats  
                'TGT', 'LOW', 'HD', 'ABT', 'CL', 'GD', 'ITW', 'SYY', 'ADM', 'CAT',
                # REITs and utilities
                'O', 'D', 'SO', 'NEE', 'DUK', 'AEP', 'EXC', 'PCG', 'ED', 'ETR',
                # Financial dividend payers
                'JPM', 'BAC', 'C', 'WFC', 'USB', 'PNC', 'TFC', 'RF', 'KEY', 'FITB'
            ]
        
        logger.info(f"🔮 [YAHOO] Fetching future dividends for {len(symbols)} symbols...")
        
        future_dividends = []
        predictions = []
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all symbol requests
            future_to_symbol = {
                executor.submit(fetch_single_yahoo_future_dividend, symbol, include_predictions): symbol
                for symbol in symbols
            }
            
            # Collect results
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    if result:
                        if result.get('type') == 'announced':
                            future_dividends.extend(result['dividends'])
                        elif result.get('type') == 'predicted' and include_predictions:
                            predictions.extend(result['dividends'])
                except Exception as e:
                    logger.debug(f"❌ [YAHOO] Error fetching {symbol}: {e}")
        
        total_found = len(future_dividends) + len(predictions)
        if total_found > 0:
            logger.info(f"✅ [YAHOO] Found {len(future_dividends)} announced + {len(predictions)} predicted future dividends")
            
            return {
                'source': 'YAHOO',
                'data': future_dividends + predictions,
                'announced_count': len(future_dividends),
                'predicted_count': len(predictions),
                'count': total_found
            }
        else:
            logger.info(f"ℹ️ [YAHOO] No future dividends found")
            
    except Exception as e:
        logger.error(f"❌ [YAHOO] Error fetching future dividends: {e}")
    
    return None

def fetch_single_yahoo_future_dividend(symbol, include_predictions=True):
    """Fetch future dividend data for a single symbol from Yahoo Finance."""
    try:
        with yahoo_limiter:
            ticker = yf.Ticker(symbol)
            calendar = ticker.get_calendar()
            
            result_dividends = []
            
            # Check for announced future dividends
            if calendar and 'Ex-Dividend Date' in calendar:
                ex_date = calendar['Ex-Dividend Date']
                payment_date = calendar.get('Dividend Date')
                
                # Check if ex-date is in the future
                today = datetime.now().date()
                if ex_date > today:
                    # Get current dividend rate for amount
                    info = ticker.info
                    estimated_amount = 0.0
                    
                    if 'dividendRate' in info and info['dividendRate']:
                        # Assume quarterly payments (most common)
                        estimated_amount = float(info['dividendRate']) / 4
                    
                    dividend_record = {
                        'symbol': symbol,
                        'dividend': estimated_amount,
                        'ex_dividend_date': ex_date.strftime('%Y-%m-%d'),
                        'payment_date': payment_date.strftime('%Y-%m-%d') if payment_date else None,
                        'record_date': None,
                        'declaration_date': None,
                        'label': f"Yahoo announced dividend for {symbol}",
                        'adj_dividend': estimated_amount,
                        'source': 'YAHOO_ANNOUNCED'
                    }
                    
                    result_dividends.append(dividend_record)
                    
                    return {
                        'type': 'announced',
                        'dividends': result_dividends
                    }
            
            # If no announced dividends and predictions enabled, try pattern analysis
            if include_predictions and not result_dividends:
                try:
                    dividends = ticker.get_dividends()
                    
                    if not dividends.empty and len(dividends) >= 4:
                        # Get recent dividends to analyze pattern
                        recent_dividends = dividends.tail(8)
                        
                        if len(recent_dividends) >= 4:
                            last_ex_date = recent_dividends.index[-1]
                            last_amount = recent_dividends.iloc[-1]
                            
                            # Estimate quarterly pattern (approximately 90 days)
                            next_estimated_date = last_ex_date + timedelta(days=90)
                            
                            if next_estimated_date.date() > datetime.now().date():
                                # Only predict if within reasonable timeframe (next 6 months)
                                if next_estimated_date.date() <= (datetime.now().date() + timedelta(days=180)):
                                    prediction_record = {
                                        'symbol': symbol,
                                        'dividend': float(last_amount),
                                        'ex_dividend_date': next_estimated_date.strftime('%Y-%m-%d'),
                                        'payment_date': (next_estimated_date + timedelta(days=14)).strftime('%Y-%m-%d'),  # Estimate payment ~2 weeks later
                                        'record_date': None,
                                        'declaration_date': None,
                                        'label': f"Yahoo predicted dividend for {symbol} (based on pattern)",
                                        'adj_dividend': float(last_amount),
                                        'source': 'YAHOO_PREDICTED'
                                    }
                                    
                                    result_dividends.append(prediction_record)
                                    
                                    return {
                                        'type': 'predicted',
                                        'dividends': result_dividends
                                    }
                except Exception as pred_error:
                    logger.debug(f"Pattern prediction failed for {symbol}: {pred_error}")
            
    except Exception as e:
        logger.debug(f"Yahoo future dividend fetch failed for {symbol}: {e}")
    
    return None

def fetch_alpha_vantage_dividends(symbol):
    """Fetch dividend data from Alpha Vantage API."""
    if not ALPHA_VANTAGE_API_KEY:
        return None

    try:
        # TIME_SERIES_DAILY_ADJUSTED includes dividend amounts on payment dates
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=full"

        logger.debug(f"💰 [ALPHA VANTAGE] Fetching dividend-adjusted data for {symbol}")
        data = fetch_with_adaptive_retry(url, av_limiter, symbol=symbol)

        if data and 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']

            # Parse dividend payments from the time series
            # Field "7. dividend amount" contains the dividend on payment dates
            dividend_data = []
            for date_str, daily_data in time_series.items():
                try:
                    dividend_amount = float(daily_data.get('7. dividend amount', 0))
                    if dividend_amount > 0:
                        dividend_data.append({
                            'date': date_str,
                            'dividend': dividend_amount,
                            'amount': dividend_amount
                        })
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping invalid dividend data for {symbol} on {date_str}: {e}")
                    continue

            if dividend_data:
                logger.debug(f"✅ [ALPHA VANTAGE] Found {len(dividend_data)} dividend records for {symbol}")
                return {
                    'source': 'Alpha Vantage',
                    'data': dividend_data,
                    'count': len(dividend_data)
                }
            else:
                logger.debug(f"ℹ️  [ALPHA VANTAGE] No dividends found for {symbol}")
                return None

    except Exception as e:
        logger.error(f"Alpha Vantage dividends error for {symbol}: {e}")

    return None

def fetch_alpha_vantage_prices(symbol):
    """Fetch price data from Alpha Vantage API."""
    try:
        av_limiter.acquire()
        try:
            url = f'https://www.alphavantage.co/query'
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',  # Use ADJUSTED to get adj_close
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'
            }
            
            logger.debug(f"📊 [ALPHA VANTAGE] Fetching prices for {symbol}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']

                    price_data = []
                    for date_str, daily_data in time_series.items():
                        try:
                            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                            price_data.append({
                                'symbol': symbol,
                                'date': date_obj.strftime('%Y-%m-%d'),
                                'open': float(daily_data['1. open']),
                                'high': float(daily_data['2. high']),
                                'low': float(daily_data['3. low']),
                                'close': float(daily_data['4. close']),
                                'adjClose': float(daily_data['5. adjusted close']),  # Add adjusted close
                                'volume': int(daily_data['6. volume'])
                            })
                        except (ValueError, KeyError) as e:
                            logger.debug(f"Skipping invalid price data for {symbol} on {date_str}: {e}")
                            continue
                    
                    if price_data:
                        logger.debug(f"✅ [ALPHA VANTAGE] Found {len(price_data)} price records for {symbol}")
                        return {
                            'source': 'Alpha Vantage',
                            'data': price_data,
                            'count': len(price_data)
                        }
                elif 'Error Message' in data:
                    logger.debug(f"❌ [ALPHA VANTAGE] Error: {data['Error Message']}")
                elif 'Note' in data:
                    logger.debug(f"⚠️ [ALPHA VANTAGE] Rate limited: {data['Note']}")
                
            return None
            
        finally:
            av_limiter.release()
            
    except Exception as e:
        logger.error(f"Alpha Vantage prices error for {symbol}: {e}")
        return None

def fetch_yahoo_dividends(symbol):
    """Fetch dividend data from Yahoo Finance using yfinance."""
    if not FALLBACK_TO_YAHOO:
        return None
    
    try:
        yahoo_limiter.acquire()
        try:
            logger.debug(f"💰 [YAHOO] Fetching dividends for {symbol}")
            ticker = yf.Ticker(symbol)
            
            # Get dividend history
            dividends = ticker.dividends
            
            if not dividends.empty:
                # Convert to format similar to FMP
                dividend_data = []
                for date, amount in dividends.items():
                    dividend_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'dividend': float(amount),
                        'amount': float(amount)
                    })
                
                return {
                    'source': 'Yahoo Finance',
                    'data': dividend_data,
                    'count': len(dividend_data)
                }
        finally:
            yahoo_limiter.release()
            
    except Exception as e:
        logger.error(f"Yahoo dividends error for {symbol}: {e}")
    
    return None

def fetch_yahoo_company_info(symbol):
    """Fetch company information from Yahoo Finance."""
    try:
        yahoo_limiter.acquire()
        try:
            import yfinance as yf
            
            logger.debug(f"🔍 [YAHOO] Fetching company info for {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return {}
                
            company_info = {}
            
            # Extract basic info
            long_name = info.get('longName')
            short_name = info.get('shortName') 
            
            if long_name:
                company_info['name'] = long_name
            elif short_name:
                company_info['name'] = short_name
            
            # Set company name from fundFamily (for ETFs/funds) or company field
            fund_family = info.get('fundFamily')
            company_name = info.get('companyName') or info.get('company')
            
            if fund_family:
                company_info['company_name'] = fund_family
            elif company_name:
                company_info['company_name'] = company_name
            else:
                company_info['company_name'] = None
                
            # Extract description
            description = info.get('longBusinessSummary')
            if description:
                company_info['description'] = description
                
            # Extract expense ratio (for ETFs) - try multiple fields
            expense_ratio = (info.get('annualReportExpenseRatio') or 
                           info.get('netExpenseRatio') or 
                           info.get('expenseRatio') or 
                           info.get('totalExpenseRatio'))
            if expense_ratio:
                company_info['expense_ratio'] = float(expense_ratio)
                
            # Extract total assets (AUM)
            total_assets = info.get('totalAssets')
            if total_assets:
                company_info['aum'] = int(total_assets)

            # Extract exchange - map Yahoo codes to standard exchange names
            yahoo_exchange = info.get('exchange')
            if yahoo_exchange:
                # Map Yahoo exchange codes to standard names
                yahoo_exchange_map = {
                    'NMS': 'NASDAQ',      # NASDAQ Capital Market
                    'NGM': 'NASDAQ',      # NASDAQ Global Market
                    'NIM': 'NASDAQ',      # NASDAQ Integrated Market
                    'NYQ': 'NYSE',        # New York Stock Exchange
                    'PCX': 'ARCA',        # NYSE Arca (for ETFs)
                    'TOR': 'TSX',         # Toronto Stock Exchange
                    'LSE': 'LSE',         # London Stock Exchange
                    'ASX': 'ASX',         # Australian Securities Exchange
                    'FRA': 'FRA',         # Frankfurt
                    'EPA': 'EPA',         # Euronext Paris
                    'MIL': 'MIL',         # Milan
                    'SWX': 'SWX',         # Swiss Exchange
                    'HKG': 'HKEX',        # Hong Kong
                    'KSC': 'KRX',         # Korea Exchange
                    'JPX': 'TYO',         # Tokyo
                    'TSE': 'TSX',         # Toronto (alternate code)
                    'CVE': 'TSXV',        # TSX Venture
                    'CNQ': 'CSE',         # Canadian Securities Exchange
                    'AMEX': 'AMEX',       # American Stock Exchange
                    'AMS': 'AMEX',        # AMEX alternate code
                    'BTS': 'BATS',        # BATS Exchange
                    'BYX': 'BYX',         # BATS BYX
                    'BZX': 'BZX',         # BATS BZX
                    'EDGA': 'EDGA',       # EDGA Exchange
                    'EDGX': 'EDGX',       # EDGX Exchange
                }
                mapped_exchange = yahoo_exchange_map.get(yahoo_exchange)
                if mapped_exchange:
                    company_info['exchange'] = mapped_exchange

            logger.debug(f"✅ [YAHOO] Found company info for {symbol}: {company_info.get('name', 'N/A')}")
            return company_info
            
        finally:
            yahoo_limiter.release()
            
    except Exception as e:
        logger.error(f"Yahoo company info error for {symbol}: {e}")
        return {}

def fetch_fmp_etf_metadata(symbol):
    """Fetch ETF metadata from FMP API."""
    try:
        fmp_limiter.acquire()
        try:
            url = f"https://financialmodelingprep.com/api/v4/etf-info?symbol={symbol}&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, list) and len(data) > 0:
                    etf_info = data[0]
                    metadata = {}

                    # Extract description
                    if etf_info.get('description'):
                        metadata['description'] = etf_info['description']

                    # Extract expense ratio
                    if etf_info.get('expenseRatio') is not None:
                        metadata['expense_ratio'] = float(etf_info['expenseRatio'])

                    # Extract AUM
                    if etf_info.get('aum') is not None:
                        metadata['aum'] = int(etf_info['aum'])

                    logger.debug(f"✅ [FMP] Found ETF metadata for {symbol}")
                    return metadata

            logger.debug(f"⏭️  [FMP] No ETF metadata for {symbol}")
            return {}

        finally:
            fmp_limiter.release()

    except Exception as e:
        logger.debug(f"⚠️  [FMP] ETF metadata error for {symbol}: {e}")
        return {}

def fetch_alpha_etf_metadata(symbol):
    """Fetch ETF metadata from Alpha Vantage API."""
    try:
        alpha_limiter.acquire()
        try:
            url = f"https://www.alphavantage.co/query?function=ETF_PROFILE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data and 'net_assets' in data:  # Valid ETF profile response
                    metadata = {}

                    # Extract expense ratio
                    if data.get('net_expense_ratio'):
                        try:
                            metadata['expense_ratio'] = float(data['net_expense_ratio'])
                        except (ValueError, TypeError):
                            pass

                    # Extract AUM (net assets)
                    if data.get('net_assets'):
                        try:
                            metadata['aum'] = int(float(data['net_assets']))
                        except (ValueError, TypeError):
                            pass

                    # Alpha Vantage doesn't have description field
                    logger.debug(f"✅ [ALPHA] Found ETF metadata for {symbol}")
                    return metadata

            logger.debug(f"⏭️  [ALPHA] No ETF metadata for {symbol}")
            return {}

        finally:
            alpha_limiter.release()

    except Exception as e:
        logger.debug(f"⚠️  [ALPHA] ETF metadata error for {symbol}: {e}")
        return {}

def fetch_yahoo_etf_metadata(symbol):
    """Fetch ETF metadata from Yahoo Finance (description, expense_ratio, aum)."""
    try:
        yahoo_limiter.acquire()
        try:
            import yfinance as yf

            logger.debug(f"🔍 [YAHOO] Fetching ETF metadata for {symbol}")
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                return {}

            metadata = {}

            # Extract description
            description = info.get('longBusinessSummary')
            if description:
                metadata['description'] = description

            # Extract expense ratio (for ETFs) - try multiple fields
            expense_ratio = (info.get('annualReportExpenseRatio') or
                           info.get('netExpenseRatio') or
                           info.get('expenseRatio') or
                           info.get('totalExpenseRatio'))
            if expense_ratio:
                metadata['expense_ratio'] = float(expense_ratio)

            # Extract total assets (AUM)
            total_assets = info.get('totalAssets')
            if total_assets:
                metadata['aum'] = int(total_assets)

            logger.debug(f"✅ [YAHOO] Found ETF metadata for {symbol}")
            return metadata

        finally:
            yahoo_limiter.release()

    except Exception as e:
        logger.debug(f"⚠️  [YAHOO] ETF metadata error for {symbol}: {e}")
        return {}

def update_etf_metadata(symbols, batch_size=20):
    """
    Update ETF metadata using 3-tier hybrid approach:
    1. FMP (primary) - has description, expense_ratio, aum
    2. Alpha Vantage (secondary) - has expense_ratio, aum (no description)
    3. Yahoo Finance (fallback) - has all fields but rate-limited
    """
    logger.info(f"📊 Updating ETF metadata for {len(symbols)} symbols using hybrid approach...")
    logger.info(f"   🔵 Tier 1: FMP (Primary)")
    logger.info(f"   🟢 Tier 2: Alpha Vantage (Secondary)")
    logger.info(f"   🟡 Tier 3: Yahoo Finance (Fallback)")

    updated_count = 0
    skipped_count = 0
    error_count = 0
    source_stats = {'FMP': 0, 'ALPHA': 0, 'YAHOO': 0}

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(symbols)-1)//batch_size + 1} ({len(batch)} symbols)")

        for symbol in batch:
            try:
                etf_metadata = {}
                source = None

                # Tier 1: Try FMP first
                fmp_data = fetch_fmp_etf_metadata(symbol)
                if fmp_data:
                    etf_metadata = fmp_data
                    source = 'FMP'
                    source_stats['FMP'] += 1

                # Tier 2: Try Alpha Vantage for missing fields
                if not etf_metadata or not etf_metadata.get('description'):
                    alpha_data = fetch_alpha_etf_metadata(symbol)
                    if alpha_data:
                        # Merge data, preferring existing values
                        for key, value in alpha_data.items():
                            if key not in etf_metadata or etf_metadata[key] is None:
                                etf_metadata[key] = value
                        if not source:
                            source = 'ALPHA'
                            source_stats['ALPHA'] += 1
                        else:
                            source = f'{source}+ALPHA'

                # Tier 3: Try Yahoo Finance as fallback (especially for description)
                if not etf_metadata or not etf_metadata.get('description'):
                    yahoo_data = fetch_yahoo_etf_metadata(symbol)
                    if yahoo_data:
                        # Merge data, preferring existing values
                        for key, value in yahoo_data.items():
                            if key not in etf_metadata or etf_metadata[key] is None:
                                etf_metadata[key] = value
                        if not source:
                            source = 'YAHOO'
                            source_stats['YAHOO'] += 1
                        else:
                            source = f'{source}+YAHOO'

                if not etf_metadata:
                    logger.debug(f"⏭️  {symbol}: No ETF metadata available from any source")
                    skipped_count += 1
                    continue

                # Prepare update data - only update fields that have values
                update_data = {}
                if etf_metadata.get('description'):
                    update_data['description'] = etf_metadata['description']
                if etf_metadata.get('expense_ratio') is not None:
                    update_data['expense_ratio'] = etf_metadata['expense_ratio']
                if etf_metadata.get('aum') is not None:
                    update_data['aum'] = etf_metadata['aum']

                if not update_data:
                    logger.debug(f"⏭️  {symbol}: No ETF metadata to update")
                    skipped_count += 1
                    continue

                # Update the stocks table
                from supabase_helpers import supabase_update
                supabase_update("stocks", update_data, where_clause={"condition": "symbol = %s", "params": [symbol]})

                # Log what was updated
                updates = []
                if 'description' in update_data:
                    updates.append("description")
                if 'expense_ratio' in update_data:
                    updates.append(f"ER={update_data['expense_ratio']:.4f}")
                if 'aum' in update_data:
                    aum_billions = update_data['aum'] / 1_000_000_000
                    updates.append(f"AUM=${aum_billions:.2f}B")

                logger.info(f"✅ {symbol} [{source}]: Updated {', '.join(updates)}")
                updated_count += 1

            except Exception as e:
                logger.error(f"❌ {symbol}: Failed to update metadata - {e}")
                error_count += 1

    logger.info(f"📊 ETF metadata update complete: {updated_count} updated, {skipped_count} skipped, {error_count} errors")
    logger.info(f"   Data sources: FMP={source_stats['FMP']}, Alpha={source_stats['ALPHA']}, Yahoo={source_stats['YAHOO']}")
    return {
        'updated': updated_count,
        'skipped': skipped_count,
        'errors': error_count,
        'sources': source_stats
    }

def fetch_hybrid_dividends(symbol, from_date=None, force_check=False):
    """
    Fetch dividends using hybrid approach with source-aware completion logic:
    1. Check if FMP already provided complete recent data → Skip other sources
    2. Try FMP (primary)
    3. Try Alpha Vantage (secondary) if FMP failed
    4. Try Yahoo Finance (fallback) if others failed
    """
    logger.debug(f"🔄 [HYBRID] Starting dividend fetch for {symbol}")
    
    # Check existing data completeness unless forced
    if not force_check:
        data_status = check_existing_data_completeness(symbol)
        if not data_status['needs_dividends']:
            logger.debug(f"⏭️ [SKIP] {symbol} already has recent dividend data")
            return "skipped"
    
    # Try FMP first (primary source)
    result = fetch_fmp_dividends(symbol, from_date)
    if result and result['count'] > 0:
        logger.debug(f"✅ [FMP] Found {result['count']} dividend records for {symbol}")
        return result
    
    # Try Alpha Vantage (secondary source) - only if FMP failed
    if USE_HYBRID_DIVIDENDS:
        logger.debug(f"🔄 [FMP FAILED] Trying Alpha Vantage for {symbol}")
        result = fetch_alpha_vantage_dividends(symbol)
        if result and result.get('count', 0) > 0:
            logger.debug(f"✅ [ALPHA VANTAGE FALLBACK] Found dividend data for {symbol}")
            return result
    
    # Try Yahoo Finance (fallback) - only if FMP and Alpha Vantage failed
    if FALLBACK_TO_YAHOO:
        logger.debug(f"🔄 [FMP+AV FAILED] Trying Yahoo Finance for {symbol}")
        result = fetch_yahoo_dividends(symbol)
        if result and result['count'] > 0:
            logger.info(f"✅ [YAHOO FALLBACK] Found {result['count']} dividend records for {symbol}")
            return result
    
    logger.debug(f"❌ [HYBRID] No dividend data found for {symbol} from any source")
    return None

def process_symbol_dividends_hybrid(symbol, max_date=None, force_check=False):
    """Process dividend history for a single symbol using hybrid approach."""
    try:
        logger.debug(f"🔄 {symbol}: Starting hybrid dividend processing (max_date: {max_date})")
        
        # Check if we need to fetch new data
        if max_date:
            today = datetime.now().date()
            # Convert max_date to date object if it's a string
            if isinstance(max_date, str):
                max_date = datetime.strptime(max_date, '%Y-%m-%d').date()
            if max_date >= today:
                logger.debug(f"⏭️  {symbol}: Skipping - already has current dividend data (latest: {max_date})")
                return "skipped"
        
        # Determine from_date for incremental fetching
        from_date = None
        if ENHANCED_HISTORICAL_DATA and max_date:
            # Handle both string and date object types
            if isinstance(max_date, str):
                max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
            else:
                max_date_obj = datetime.combine(max_date, datetime.min.time())
            from_date = (max_date_obj + timedelta(days=1)).strftime('%Y-%m-%d')
            logger.debug(f"💰 {symbol}: [INCREMENTAL] Fetching new dividend data only (from {from_date})")
        elif ENHANCED_HISTORICAL_DATA:
            logger.debug(f"💰 {symbol}: [FIRST TIME] Fetching comprehensive historical dividend data")
        
        # Fetch dividend data using hybrid approach
        result = fetch_hybrid_dividends(symbol, from_date, force_check=force_check)
        
        # Handle skipped result
        if result == "skipped":
            logger.debug(f"⏭️ {symbol}: Skipped - already has recent dividend data")
            return "skipped"
        
        if not result or not result.get('data'):
            logger.debug(f"ℹ️  {symbol}: No dividend data available from any source")
            return False
        
        # Process the dividend data based on source
        dividend_records = []
        
        if result['source'] == 'Yahoo Finance':
            # Yahoo data is already in the right format
            for div_data in result['data']:
                if div_data.get('amount', 0) > 0:  # Filter out zero dividends
                    record = {
                        "symbol": symbol,
                        "payment_date": div_data.get('date'),
                        "amount": div_data.get('amount')
                    }
                    dividend_records.append(record)
        
        elif result['source'] == 'FMP':
            # FMP data processing
            for div_data in result['data']:
                # Use adjDividend (split-adjusted) instead of dividend (unadjusted)
                # This prevents inflated dividend amounts for stocks with reverse splits
                adj_dividend = div_data.get('adjDividend', div_data.get('dividend', 0))
                if adj_dividend > 0:  # Filter out zero dividends
                    record = {
                        "symbol": symbol,
                        "payment_date": div_data.get('date'),
                        "amount": adj_dividend
                    }
                    dividend_records.append(record)
        
        # Insert dividends into database
        if dividend_records:
            try:
                logger.debug(f"💾 {symbol}: Inserting {len(dividend_records)} dividend records to database")
                pg_upsert("dividend_history", dividend_records)
                logger.info(f"✅ {symbol}: Successfully inserted {len(dividend_records)} dividend records [{result['source']}]")
                return True
            except Exception as e:
                logger.error(f"❌ {symbol}: Database insertion failed - {e}")
                return False
        elif not dividend_records:
            logger.debug(f"ℹ️  {symbol}: No valid dividend records to insert")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ {symbol}: Unexpected error in hybrid dividend processing - {e}")
        return False

def update_dividends_hybrid(symbols, force_check=False):
    """Update dividend history using hybrid approach."""
    try:
        logger.info(f"Starting hybrid dividend updates for {len(symbols)} symbols...")

        if not symbols:
            logger.warning("No symbols to update")
            return True

        # Get max dates for existing dividend data - efficiently for ALL symbols
        max_dividend_dates = get_latest_dates_for_all_symbols("dividend_history", "payment_date", symbols)

        # Filter out symbols that already have today's dividend data (unless force_check is True)
        if not force_check:
            today = datetime.now().date()
            symbols_before_filter = len(symbols)
            symbols = [
                s for s in symbols
                if s not in max_dividend_dates or
                (isinstance(max_dividend_dates[s], str) and datetime.strptime(max_dividend_dates[s], '%Y-%m-%d').date() < today) or
                (not isinstance(max_dividend_dates[s], str) and max_dividend_dates[s] < today)
            ]
            symbols_filtered = symbols_before_filter - len(symbols)
            if symbols_filtered > 0:
                logger.info(f"⏭️  Filtered out {symbols_filtered} symbols that already have today's dividend data")
                logger.info(f"📊 Remaining symbols to process: {len(symbols)}")

            if not symbols:
                logger.info("✅ All symbols already have current dividend data - nothing to update!")
                return True

        # Process symbols in batches
        batch_size = 60  # 3X from 20 to 60 for Ultimate plan
        total_processed = 0
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(symbols) + batch_size - 1)//batch_size
            
            logger.info(f"🛠️  Processing hybrid dividend batch {batch_num}/{total_batches} ({len(batch)} symbols)")
            logger.info(f"💰 Batch {batch_num} symbols: {', '.join(batch[:5])}{'...' if len(batch) > 5 else ''}")
            
            success = process_dividend_batch_hybrid(batch, max_dividend_dates, force_check)
            if not success:
                logger.error(f"❌ Failed to process dividend batch {batch_num}/{total_batches}")
                return False
            
            total_processed += len(batch)
            progress_pct = (total_processed / len(symbols)) * 100
            logger.info(f"📈 Progress: {total_processed}/{len(symbols)} symbols ({progress_pct:.1f}% complete)")
        
        logger.info(f"Successfully processed hybrid dividends for {total_processed} symbols")
        return True
        
    except Exception as e:
        logger.error(f"Error in hybrid dividend update process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_dividend_batch_hybrid(symbols_batch, max_dividend_dates, force_check=False):
    """Process a batch of symbols for dividend updates using hybrid approach."""
    success = True
    processed_count = 0
    skipped_count = 0
    no_data_count = 0
    failed_count = 0
    source_stats = {'FMP': 0, 'Alpha Vantage': 0, 'Yahoo Finance': 0}
    
    logger.info(f"Starting hybrid dividend batch processing for symbols: {', '.join(symbols_batch[:10])}{'...' if len(symbols_batch) > 10 else ''}")
    
    with ThreadPoolExecutor(max_workers=9) as executor:  # 3X from 3 to 9 for Ultimate plan
        future_to_symbol = {
            executor.submit(process_symbol_dividends_hybrid, symbol, max_dividend_dates.get(symbol), force_check): symbol 
            for symbol in symbols_batch
        }
        
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result == "skipped":
                    skipped_count += 1
                    logger.debug(f"⏭️  {symbol}: Skipped - already has recent dividend data")
                elif result:
                    processed_count += 1
                    logger.info(f"✅ {symbol}: Successfully updated dividends (hybrid)")
                else:
                    no_data_count += 1
                    logger.debug(f"ℹ️  {symbol}: No dividend data available from any source")
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ {symbol}: Error processing dividends - {e}")
                success = False
    
    logger.info(f"Hybrid dividend batch complete: ✅{processed_count} updated, ⏭️{skipped_count} skipped, ℹ️{no_data_count} no data, ❌{failed_count} failed")
    return success

def update_prices_hybrid(symbols, force_check=False):
    """Update price history using hybrid approach."""
    try:
        logger.info(f"Starting hybrid price updates for {len(symbols)} symbols...")

        if not symbols:
            logger.warning("No symbols to update")
            return True

        # Get max dates for existing price data - efficiently for ALL symbols
        max_price_dates = get_latest_dates_for_all_symbols("stock_prices", "date", symbols)

        # Filter out symbols that already have today's data (unless force_check is True)
        if not force_check:
            today = datetime.now().date()

            # Calculate the last trading day (weekday)
            # If today is a weekend, get the last Friday
            last_trading_day = today
            if today.weekday() == 5:  # Saturday
                last_trading_day = today - timedelta(days=1)
            elif today.weekday() == 6:  # Sunday
                last_trading_day = today - timedelta(days=2)

            symbols_before_filter = len(symbols)
            symbols = [
                s for s in symbols
                if s not in max_price_dates or
                (isinstance(max_price_dates[s], str) and datetime.strptime(max_price_dates[s], '%Y-%m-%d').date() < last_trading_day) or
                (not isinstance(max_price_dates[s], str) and max_price_dates[s] < last_trading_day)
            ]
            symbols_filtered = symbols_before_filter - len(symbols)
            if symbols_filtered > 0:
                logger.info(f"⏭️  Filtered out {symbols_filtered} symbols that already have data for {last_trading_day} (last trading day)")
                logger.info(f"📊 Remaining symbols to process: {len(symbols)}")

            if not symbols:
                logger.info(f"✅ All symbols already have current data for {last_trading_day} - nothing to update!")
                return True

        # Process symbols in batches
        batch_size = 60  # 3X from 20 to 60 for Ultimate plan
        total_processed = 0
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_num = i//batch_size + 1
            total_batches = (len(symbols) + batch_size - 1)//batch_size
            
            logger.info(f"🛠️  Processing hybrid price batch {batch_num}/{total_batches} ({len(batch)} symbols)")
            logger.info(f"📊 Batch {batch_num} symbols: {', '.join(batch[:5])}{'...' if len(batch) > 5 else ''}")
            
            success = process_price_batch_hybrid(batch, max_price_dates, force_check)
            if not success:
                logger.error(f"❌ Failed to process price batch {batch_num}/{total_batches}")
                return False
            
            total_processed += len(batch)
            progress_pct = (total_processed / len(symbols)) * 100
            logger.info(f"📈 Progress: {total_processed}/{len(symbols)} symbols ({progress_pct:.1f}% complete)")
        
        logger.info(f"Successfully processed hybrid prices for {total_processed} symbols")
        return True
        
    except Exception as e:
        logger.error(f"Error in hybrid price update process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def process_price_batch_hybrid(symbols_batch, max_price_dates, force_check=False):
    """Process a batch of symbols for price updates using hybrid approach."""
    success = True
    processed_count = 0
    skipped_count = 0
    no_data_count = 0
    failed_count = 0

    logger.info(f"Starting hybrid price batch processing for symbols: {', '.join(symbols_batch[:10])}{'...' if len(symbols_batch) > 10 else ''}")

    with ThreadPoolExecutor(max_workers=3) as executor:  # Reduced to allow FMP semaphore to work properly
        future_to_symbol = {
            executor.submit(process_symbol_prices_hybrid, symbol, max_price_dates.get(symbol), force_check): symbol
            for symbol in symbols_batch
        }

        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result == "skipped":
                    skipped_count += 1
                    logger.debug(f"⏭️  {symbol}: Skipped - already has recent price data")
                elif result:
                    processed_count += 1
                    logger.info(f"✅ {symbol}: Successfully updated prices (hybrid)")
                else:
                    no_data_count += 1
                    logger.debug(f"ℹ️  {symbol}: No price data available from any source")
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ {symbol}: Error processing prices - {e}")
                success = False

    logger.info(f"Hybrid price batch complete: ✅{processed_count} updated, ⏭️{skipped_count} skipped, ℹ️{no_data_count} no data, ❌{failed_count} failed")

    return success

def complete_symbol_validation(symbol):
    """Run complete validation (prices + dividends + basic info) for a single symbol."""
    logger.info(f"🔍 Starting complete validation for symbol: {symbol}")
    logger.info("="*80)
    
    results = {
        'symbol': symbol,
        'prices': {'success': False, 'count': 0, 'source': None},
        'dividends': {'success': False, 'count': 0, 'source': None},
        'errors': []
    }
    
    try:
        # Get existing data to determine if incremental or full fetch
        price_data = pg_select("stock_prices", "date", where_clause={"condition": "symbol = %s", "params": [symbol]}, order_by="date DESC", limit=1)
        dividend_data = pg_select("dividend_history", "payment_date", where_clause={"condition": "symbol = %s", "params": [symbol]}, order_by="payment_date DESC", limit=1)
        
        max_price_date = price_data[0]['date'] if price_data else None
        max_dividend_date = dividend_data[0]['payment_date'] if dividend_data else None
        
        # Check if symbol exists in stocks table, add if not
        stocks_data = pg_select("stocks", "symbol", where_clause={"condition": "symbol = %s", "params": [symbol]})
        if not stocks_data:
            logger.info(f"🏷️  Adding {symbol} to stocks table...")
            try:
                # Fetch company information from Yahoo Finance
                company_info = fetch_yahoo_company_info(symbol)

                # Get exchange from Yahoo API first, then fallback to symbol suffix inference
                exchange = company_info.get('exchange')

                # If Yahoo didn't provide exchange, infer from symbol suffix
                if not exchange:
                    if '.' in symbol:
                        suffix = symbol.split('.')[-1]
                        exchange_map = {
                            'TO': 'TSX',  # Toronto Stock Exchange
                            'V': 'TSXV',  # TSX Venture
                            'CN': 'CSE',  # Canadian Securities Exchange
                            'L': 'LSE',   # London Stock Exchange
                            'AX': 'ASX',  # Australian Securities Exchange
                            'PA': 'EPA',  # Euronext Paris
                            'DE': 'FRA',  # Frankfurt
                            'MI': 'MIL',  # Milan
                            'SW': 'SWX',  # Swiss Exchange
                            'HK': 'HKEX', # Hong Kong
                            'KS': 'KRX',  # Korea Exchange
                            'T': 'TYO'    # Tokyo
                        }
                        exchange = exchange_map.get(suffix.upper())

                # Fetch sector data from FMP
                sector_data = None
                try:
                    sector_data = get_sector_for_symbol(symbol, FMP_API_KEY)
                    if sector_data:
                        logger.info(f"   Sector: {sector_data}")
                except Exception as e:
                    logger.debug(f"   Could not fetch sector for {symbol}: {e}")

                stock_record = {
                    'symbol': symbol,
                    'name': company_info.get('name', f'{symbol} (Auto-added)'),
                    'company': company_info.get('company_name'),
                    'description': company_info.get('description'),
                    'expense_ratio': company_info.get('expense_ratio'),
                    'aum': company_info.get('aum'),
                    'exchange': exchange,
                    'sector': sector_data
                }
                # Remove None values
                stock_record = {k: v for k, v in stock_record.items() if v is not None}
                
                pg_insert("stocks", stock_record)
                logger.info(f"✅ Successfully added {symbol} to stocks table with company info")
                if company_info.get('name') and company_info['name'] != f'{symbol} (Auto-added)':
                    logger.info(f"   Company: {company_info['name']}")
            except Exception as e:
                logger.warning(f"⚠️  Could not add {symbol} to stocks table: {e}")
                results['errors'].append(f"Stocks table insertion failed: {e}")
        else:
            logger.info(f"✅ Symbol {symbol} already exists in stocks table")
        
        logger.info(f"📊 Current data status:")
        logger.info(f"   Latest price date: {max_price_date or 'None'}")
        logger.info(f"   Latest dividend date: {max_dividend_date or 'None'}")
        
        # Process prices
        logger.info(f"\n📊 Processing prices for {symbol}...")
        try:
            price_result = process_symbol_prices_hybrid(symbol, max_price_date, force_check=True)
            if price_result == "skipped":
                results['prices']['success'] = True
                results['prices']['source'] = 'Skipped (current)'
                logger.info(f"⏭️  Prices: Skipped (already current)")
            elif price_result:
                results['prices']['success'] = True
                logger.info(f"✅ Prices: Successfully processed")
            else:
                results['errors'].append("Price processing failed")
                logger.error(f"❌ Prices: Processing failed")
        except Exception as e:
            results['errors'].append(f"Price error: {e}")
            logger.error(f"❌ Prices: Error - {e}")
        
        # Process dividends  
        logger.info(f"\n💰 Processing dividends for {symbol}...")
        try:
            dividend_result = process_symbol_dividends_hybrid(symbol, max_dividend_date, force_check=True)
            if dividend_result == "skipped":
                results['dividends']['success'] = True
                results['dividends']['source'] = 'Skipped (current)'
                logger.info(f"⏭️  Dividends: Skipped (already current)")
            elif dividend_result:
                results['dividends']['success'] = True
                logger.info(f"✅ Dividends: Successfully processed")
            else:
                results['errors'].append("Dividend processing failed")
                logger.error(f"❌ Dividends: Processing failed")
        except Exception as e:
            results['errors'].append(f"Dividend error: {e}")
            logger.error(f"❌ Dividends: Error - {e}")
        
        # Summary
        logger.info(f"\n" + "="*80)
        logger.info(f"🎯 COMPLETE VALIDATION SUMMARY FOR {symbol}")
        logger.info("="*80)
        logger.info(f"✅ Prices: {'SUCCESS' if results['prices']['success'] else 'FAILED'}")
        logger.info(f"✅ Dividends: {'SUCCESS' if results['dividends']['success'] else 'FAILED'}")
        
        if results['errors']:
            logger.error(f"❌ Errors encountered:")
            for error in results['errors']:
                logger.error(f"   - {error}")
        else:
            logger.info(f"🎉 Complete validation successful - no errors!")
        
        return len(results['errors']) == 0
        
    except Exception as e:
        logger.error(f"❌ Complete validation failed for {symbol}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main_hybrid(args=None):
    """Main function for hybrid stock data update."""
    global DEBUG_MODE, ENHANCED_HISTORICAL_DATA, USE_HYBRID_DIVIDENDS, FALLBACK_TO_YAHOO, NASDAQ_ONLY, ALLOWED_EXCHANGES
    
    # Parse command line arguments - SIMPLIFIED to 3 core modes
    parser = argparse.ArgumentParser(
        description='Stock data update system with 3 modes: discover, prices, dividends',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Discover and validate new symbols
  python update_stock.py --mode discover

  # Update prices for all symbols (with intelligent filtering)
  python update_stock.py --mode prices

  # Update dividends for all symbols (with intelligent filtering)
  python update_stock.py --mode dividends

  # Force update all symbols (bypass filtering)
  python update_stock.py --mode prices --force

  # Process single symbol only
  python update_stock.py --mode dividends --symbol AAPL
        '''
    )

    # Core mode selection (REQUIRED)
    parser.add_argument('--mode',
                       choices=['discover', 'prices', 'dividends', 'metadata'],
                       help='Operation mode: discover (find new symbols), prices (update prices), dividends (update dividends), metadata (update ETF metadata)')

    # Legacy mode flags (for backwards compatibility - will be deprecated)
    parser.add_argument('--discover-symbols', action='store_true', help='[LEGACY] Use --mode discover instead')
    parser.add_argument('--prices-only', action='store_true', help='[LEGACY] Use --mode prices instead')
    parser.add_argument('--dividends-only', action='store_true', help='[LEGACY] Use --mode dividends instead')

    # Common options
    parser.add_argument('--force', action='store_true',
                       help='Force update all symbols (bypass intelligent filtering)')
    parser.add_argument('--force-all', action='store_true',
                       help='Force update all symbols globally')
    parser.add_argument('--symbol', type=str,
                       help='Process single symbol only')
    parser.add_argument('--debug', action='store_true',
                       help='Run in debug mode with test symbols')

    # Future dividend options (for discover mode)
    parser.add_argument('--future-yahoo-only', action='store_true',
                       help='Use only Yahoo Finance for future dividends')
    parser.add_argument('--future-hybrid', action='store_true',
                       help='Use hybrid approach (FMP + Yahoo) for future dividends')
    parser.add_argument('--future-from', type=str,
                       help='Start date for future dividends (FMP)')
    parser.add_argument('--future-to', type=str,
                       help='End date for future dividends (FMP)')
    parser.add_argument('--future-symbols', type=str, nargs='+',
                       help='Specific symbols for future dividends')
    parser.add_argument('--future-predictions', action='store_true',
                       help='Include predicted dividends (Yahoo)')

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    # Handle legacy flags for backwards compatibility
    mode = args.mode
    run_all_modes = False
    if not mode:
        if args.discover_symbols:
            mode = 'discover'
            logger.warning("⚠️  --discover-symbols is deprecated. Use --mode discover instead")
        elif args.prices_only:
            mode = 'prices'
            logger.warning("⚠️  --prices-only is deprecated. Use --mode prices instead")
        elif args.dividends_only:
            mode = 'dividends'
            logger.warning("⚠️  --dividends-only is deprecated. Use --mode dividends instead")
        else:
            # No mode specified - run all three modes in sequence
            run_all_modes = True
            logger.info("🔄 No mode specified - running complete update (discover → prices → dividends)")

    # Set configuration based on arguments
    DEBUG_MODE = args.debug

    # Hybrid fetching is ALWAYS enabled for maximum coverage
    USE_HYBRID_DIVIDENDS = True
    FALLBACK_TO_YAHOO = True
    
    # Log configuration
    logger.info("="*80)
    if run_all_modes:
        logger.info("🚀 STOCK DATA UPDATE SYSTEM v3.0 - COMPLETE UPDATE (ALL MODES)")
    else:
        logger.info(f"🚀 STOCK DATA UPDATE SYSTEM v3.0 - MODE: {mode.upper()}")
    logger.info("="*80)
    logger.info("⚙️  CONFIGURATION:")
    if run_all_modes:
        logger.info(f"   Mode: ALL (discover → prices → dividends → metadata)")
    else:
        logger.info(f"   Mode: {mode}")
    logger.info(f"   Force Update: {'YES' if args.force else 'NO (intelligent filtering)'}")
    logger.info(f"   Single Symbol: {args.symbol if args.symbol else 'ALL'}")
    logger.info(f"   Debug Mode: {'YES' if DEBUG_MODE else 'NO'}")
    logger.info("")
    logger.info("🔄 DATA SOURCES (3-tier hybrid):")
    logger.info("   1️⃣  FMP (Primary)")
    logger.info("   2️⃣  Alpha Vantage (Secondary)")
    logger.info("   3️⃣  Yahoo Finance (Fallback)")
    logger.info("="*80)

    # ========================================================================
    # RUN ALL MODES SEQUENTIALLY
    # ========================================================================
    if run_all_modes:
        logger.info("\n" + "="*80)
        logger.info("🔄 RUNNING COMPLETE UPDATE - ALL FOUR MODES")
        logger.info("="*80)

        # Mode 1: Discover
        logger.info("\n📍 PHASE 1/4: DISCOVER NEW SYMBOLS")
        logger.info("-"*80)
        discover_result = main_hybrid(['--mode', 'discover'] + (['--debug'] if args.debug else []) + (['--force'] if args.force else []))
        if not discover_result:
            logger.error("❌ Discovery phase failed, stopping complete update")
            return False
        logger.info("✅ Discovery phase completed")

        # Mode 2: Prices
        logger.info("\n📍 PHASE 2/4: UPDATE PRICES")
        logger.info("-"*80)
        prices_result = main_hybrid(['--mode', 'prices'] + (['--debug'] if args.debug else []) + (['--force'] if args.force else []))
        if not prices_result:
            logger.error("❌ Prices phase failed, stopping complete update")
            return False
        logger.info("✅ Prices phase completed")

        # Mode 3: Dividends
        logger.info("\n📍 PHASE 3/4: UPDATE DIVIDENDS")
        logger.info("-"*80)
        dividends_result = main_hybrid(['--mode', 'dividends'] + (['--debug'] if args.debug else []) + (['--force'] if args.force else []))
        if not dividends_result:
            logger.error("❌ Dividends phase failed")
            return False
        logger.info("✅ Dividends phase completed")

        # Mode 4: Metadata
        logger.info("\n📍 PHASE 4/4: UPDATE ETF METADATA")
        logger.info("-"*80)
        metadata_result = main_hybrid(['--mode', 'metadata'] + (['--debug'] if args.debug else []) + (['--force'] if args.force else []))
        if not metadata_result:
            logger.error("❌ Metadata phase failed")
            return False
        logger.info("✅ Metadata phase completed")

        logger.info("\n" + "="*80)
        logger.info("✅ COMPLETE UPDATE FINISHED SUCCESSFULLY - ALL 4 PHASES COMPLETE")
        logger.info("="*80)
        return True

    # ========================================================================
    # MODE EXECUTION (SINGLE MODE)
    # ========================================================================

    # Handle single symbol mode (works with all modes)
    if args.symbol:
        logger.info(f"🎯 Single symbol mode: {args.symbol}")

        if mode == 'discover':
            result = complete_symbol_validation(args.symbol)
            logger.info(f"Validation result: {'SUCCESS' if result else 'FAILED'}")
            return result
        elif mode == 'prices':
            result = update_prices_hybrid([args.symbol], force_check=True)
            return result
        elif mode == 'dividends':
            result = update_dividends_hybrid([args.symbol], force_check=True)
            return result
        elif mode == 'metadata':
            result = update_etf_metadata([args.symbol], batch_size=1)
            return result['updated'] > 0 or result['skipped'] > 0

    # MODE 1: DISCOVER - Find and validate new symbols
    if mode == 'discover':
        logger.info("🔮 FUTURE DIVIDEND CALENDAR")
        logger.info("="*80)
        
        future_data = None
        
        # Determine which source(s) to use
        if args.future_yahoo_only:
            # Yahoo only mode
            logger.info("📡 Using Yahoo Finance only for future dividends")
            future_data = fetch_future_dividends_yahoo(
                symbols=args.future_symbols,
                include_predictions=args.future_predictions
            )
        elif args.future_hybrid:
            # Hybrid mode: FMP + Yahoo
            logger.info("🔄 Using hybrid approach: FMP + Yahoo Finance")
            
            # Get FMP data first
            fmp_data = fetch_future_dividends_fmp(
                from_date=args.future_from,
                to_date=args.future_to,
                symbols=args.future_symbols
            )
            
            # Get Yahoo data
            yahoo_data = fetch_future_dividends_yahoo(
                symbols=args.future_symbols,
                include_predictions=args.future_predictions
            )
            
            # Combine data
            combined_dividends = []
            total_inserted = 0
            
            if fmp_data and fmp_data['count'] > 0:
                combined_dividends.extend(fmp_data['data'])
                total_inserted += fmp_data.get('inserted_count', 0)
                logger.info(f"📊 FMP: {fmp_data['count']} dividends")
            
            if yahoo_data and yahoo_data['count'] > 0:
                # Add Yahoo data and mark source
                for div in yahoo_data['data']:
                    div['hybrid_source'] = div.get('source', 'YAHOO')
                combined_dividends.extend(yahoo_data['data'])
                logger.info(f"📊 Yahoo: {yahoo_data['count']} dividends ({yahoo_data.get('announced_count', 0)} announced + {yahoo_data.get('predicted_count', 0)} predicted)")
            
            if combined_dividends:
                future_data = {
                    'source': 'HYBRID_FMP_YAHOO',
                    'data': combined_dividends,
                    'count': len(combined_dividends),
                    'inserted_count': total_inserted,
                    'fmp_count': fmp_data['count'] if fmp_data else 0,
                    'yahoo_count': yahoo_data['count'] if yahoo_data else 0
                }
        else:
            # Default FMP mode
            logger.info("📡 Using FMP for future dividends (default)")
            future_data = fetch_future_dividends_fmp(
                from_date=args.future_from,
                to_date=args.future_to,
                symbols=args.future_symbols
            )
        
        if future_data and future_data['count'] > 0:
            # Display summary
            if future_data['source'] == 'HYBRID_FMP_YAHOO':
                logger.info(f"📅 Future Dividends (Hybrid): {future_data['count']} total announcements")
                logger.info(f"   🔵 FMP: {future_data.get('fmp_count', 0)} dividends")
                logger.info(f"   🟡 Yahoo: {future_data.get('yahoo_count', 0)} dividends")
            else:
                range_info = future_data.get('date_range', 'period specified')
                logger.info(f"📅 Future Dividends ({range_info}): {future_data['count']} announcements")
            
            if 'inserted_count' in future_data and future_data['inserted_count'] > 0:
                logger.info(f"💾 Database: {future_data['inserted_count']} records inserted into dividend_calendar table")
            
            logger.info("="*80)
            
            # Group by symbol for better display
            symbol_dividends = {}
            for dividend in future_data['data']:
                symbol = dividend['symbol']
                if symbol not in symbol_dividends:
                    symbol_dividends[symbol] = []
                symbol_dividends[symbol].append(dividend)
            
            # Display results organized by symbol
            for symbol in sorted(symbol_dividends.keys()):
                dividends = symbol_dividends[symbol]
                logger.info(f"\n💰 {symbol}:")
                for div in dividends:
                    ex_date = div['ex_dividend_date']
                    amount = div['dividend']
                    payment_date = div.get('payment_date', 'N/A')
                    source_info = ""
                    
                    # Add source indicator for hybrid mode
                    if 'hybrid_source' in div:
                        if div['hybrid_source'] == 'YAHOO_ANNOUNCED':
                            source_info = " [Y-Announced]"
                        elif div['hybrid_source'] == 'YAHOO_PREDICTED':
                            source_info = " [Y-Predicted]"
                        else:
                            source_info = f" [{div['hybrid_source']}]"
                    
                    logger.info(f"  📅 Ex-Date: {ex_date} | Amount: ${amount} | Payment: {payment_date}{source_info}")
        else:
            logger.info("ℹ️ No future dividend announcements found for the specified period")

        # Continue to comprehensive symbol discovery below (don't return early!)
        logger.info("")  # Blank line for readability

    # Handle comprehensive symbol discovery mode
    if mode == 'discover':
        logger.info("🚀 COMPREHENSIVE SYMBOL DISCOVERY & DATABASE UPDATE")
        logger.info("="*80)
        
        # Step 1: Discover all symbols from all sources and filter against database
        new_symbols_to_add, discovery_stats = comprehensive_symbol_discovery(
            use_full_etf_list=True,  # Enable comprehensive ETF discovery
            use_dividend_screener=True,  # Enable dividend stock discovery
            use_enhanced_discovery=True  # Enable enhanced FMP Ultimate Plan discovery
        )
        
        # Step 2: Validate and add new symbols to database if any found
        # In discover mode, always validate discovered symbols
        if new_symbols_to_add:
            logger.info(f"🔍 Validating {len(new_symbols_to_add)} symbols (including existing symbols from stocks table)...")
            validated_symbols = []
            excluded_symbols = []
            
            # Validate symbols in batches using ThreadPoolExecutor
            disable_yahoo = getattr(args, 'disable_yahoo', False)  # Default to False if not provided
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_symbol = {
                    executor.submit(validate_discovered_symbol, symbol_data, disable_yahoo): symbol_data['symbol']
                    for symbol_data in new_symbols_to_add
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            if result.get('meets_criteria'):
                                validated_symbols.append(result)
                            else:
                                excluded_symbols.append(result)
                        else:
                            excluded_symbols.append(result)
                    except Exception as e:
                        logger.error(f"❌ {symbol}: Validation error - {e}")
                        excluded_symbols.append({'symbol': symbol, 'status': 'error', 'reason': str(e)})
            
            logger.info(f"📊 Validation Results for New Symbols:")
            logger.info(f"   ✅ Validated (will add to stocks): {len(validated_symbols)} symbols")
            logger.info(f"   ❌ Excluded (will add to stocks_excluded): {len(excluded_symbols)} symbols")

            # Add validated symbols to database (check for dry_run flag if it exists)
            if not getattr(args, 'dry_run', False):
                # Insert validated symbols into stocks table
                if validated_symbols:
                    stocks_to_insert = []
                    for result in validated_symbols:
                        # Get exchange from source_data or infer from symbol suffix
                        exchange = None
                        if result.get('source_data'):
                            exchange = result['source_data'].get('exchange')

                        # If no exchange in source_data, infer from symbol suffix
                        if not exchange:
                            symbol = result['symbol']
                            if '.' in symbol:
                                suffix = symbol.split('.')[-1]
                                exchange_map = {
                                    'TO': 'TSX',  # Toronto Stock Exchange
                                    'V': 'TSXV',  # TSX Venture
                                    'CN': 'CSE',  # Canadian Securities Exchange
                                    'L': 'LSE',   # London Stock Exchange
                                    'AX': 'ASX',  # Australian Securities Exchange
                                    'PA': 'EPA',  # Euronext Paris
                                    'DE': 'FRA',  # Frankfurt
                                    'MI': 'MIL',  # Milan
                                    'SW': 'SWX',  # Swiss Exchange
                                    'HK': 'HKEX', # Hong Kong
                                    'KS': 'KRX',  # Korea Exchange
                                    'T': 'TYO'    # Tokyo
                                }
                                exchange = exchange_map.get(suffix.upper())
                            # Default to NASDAQ for US symbols without suffix
                            elif symbol.isalpha() and len(symbol) <= 5:
                                exchange = 'NASDAQ'

                        stock_record = {
                            'symbol': result['symbol'],
                            'name': result['name'],
                            'company': result['company_name'],
                            'description': result.get('description'),
                            'expense_ratio': result.get('expense_ratio'),
                            'aum': result.get('aum'),
                            'exchange': exchange
                        }
                        # Remove None values
                        stock_record = {k: v for k, v in stock_record.items() if v is not None}
                        stocks_to_insert.append(stock_record)
                    
                    # Deduplicate by symbol to avoid "duplicate constrained values" error
                    seen_symbols = set()
                    deduplicated_stocks = []
                    for stock in stocks_to_insert:
                        if stock['symbol'] not in seen_symbols:
                            seen_symbols.add(stock['symbol'])
                            deduplicated_stocks.append(stock)

                    logger.info(f"📊 Deduplication: {len(stocks_to_insert)} → {len(deduplicated_stocks)} unique symbols")

                    try:
                        # Use upsert to handle duplicates within the batch
                        result = pg_upsert("stocks", deduplicated_stocks)
                        logger.info(f"✅ Upserted {len(result) if isinstance(result, list) else len(result.data) if hasattr(result, 'data') else len(deduplicated_stocks)} symbols into stocks table")
                    except Exception as e:
                        logger.error(f"❌ Failed to upsert stocks: {e}")
                        # Fallback: try inserting one by one to avoid batch issues
                        successful_inserts = 0
                        for stock_record in deduplicated_stocks:
                            try:
                                pg_upsert("stocks", [stock_record])
                                successful_inserts += 1
                            except Exception as single_error:
                                logger.debug(f"Failed to insert {stock_record.get('symbol', 'unknown')}: {single_error}")
                        if successful_inserts > 0:
                            logger.info(f"✅ Successfully inserted {successful_inserts} symbols individually")
                
                # Handle excluded symbols: remove from stocks table if they exist there, then add to stocks_excluded
                if excluded_symbols:
                    excluded_to_insert = []
                    symbols_to_remove_from_stocks = []

                    for result in excluded_symbols:
                        symbol = result['symbol']
                        source_data = result.get('source_data', {})
                        original_source = source_data.get('source', 'DISCOVERY')

                        # Check if this symbol was previously in stocks table
                        try:
                            existing_in_stocks = pg_select("stocks", "symbol",
                                                         {'condition': 'symbol = %s', 'params': [symbol]},
                                                         limit=1)
                            if existing_in_stocks:
                                symbols_to_remove_from_stocks.append(symbol)
                                logger.debug(f"🗑️  {symbol}: Removing from stocks table (failed validation)")
                        except Exception as e:
                            logger.debug(f"Error checking {symbol} in stocks table: {e}")

                        exclusion_record = {
                            'symbol': symbol,
                            'reason': f"[{original_source}] {result.get('exclusion_reason') or result.get('reason', 'Failed validation')}"
                        }
                        excluded_to_insert.append(exclusion_record)

                    # Remove failed symbols from stocks table
                    if symbols_to_remove_from_stocks:
                        removed_count = 0
                        for symbol in symbols_to_remove_from_stocks:
                            try:
                                success = pg_delete("stocks", {'condition': 'symbol = %s', 'params': [symbol]})
                                if success:
                                    removed_count += 1
                            except Exception as e:
                                logger.error(f"❌ Failed to remove {symbol} from stocks: {e}")

                        if removed_count > 0:
                            logger.info(f"🗑️  Removed {removed_count} failed symbols from stocks table")

                    # Add to stocks_excluded table (use upsert to handle duplicates)
                    try:
                        result = pg_upsert("stocks_excluded", excluded_to_insert)
                        if result and hasattr(result, 'data'):
                            logger.info(f"✅ Upserted {len(result.data)} exclusions into stocks_excluded table")
                        else:
                            logger.info(f"✅ Upserted {len(excluded_to_insert)} exclusions into stocks_excluded table")
                    except Exception as e:
                        logger.error(f"❌ Failed to upsert exclusions: {e}")
            else:
                logger.info("🔍 DRY RUN - No database changes made")
        
        elif new_symbols_to_add and not args.validate_discovered:
            logger.info(f"⚠️  Found {len(new_symbols_to_add)} new symbols but validation not requested (use --validate-discovered)")
        
        elif not new_symbols_to_add:
            logger.info("✅ No symbols to validate - all discovered symbols are already excluded")
        
        # If discovery-only mode, exit here
        if args.discovery_only:
            logger.info("🎉 Discovery-only mode complete!")
            return True

        # Continue to data fetching phase for ALL symbols in stocks table
        logger.info("\n" + "="*80)
        logger.info("🔄 PROCEEDING TO DATA FETCHING FOR ALL SYMBOLS IN STOCKS TABLE")
        logger.info("="*80)

    # MODE 2: PRICES - Update price data
    elif mode == 'prices':
        logger.info("📊 PRICE UPDATE MODE - INTELLIGENT INCREMENTAL")
        logger.info("="*80)

        # Get all symbols from stocks table
        all_symbols = []
        page_size = 1000
        offset = 0

        while True:
            batch = pg_select('stocks', 'symbol', limit=page_size, offset=offset)
            if not batch:
                break
            all_symbols.extend([s['symbol'] for s in batch])
            offset += page_size

        logger.info(f"📊 Updating prices for {len(all_symbols)} symbols (intelligent skip)...")
        # Intelligent filtering - only fetch if needed
        success = update_prices_hybrid(all_symbols, force_check=False)

        if success:
            logger.info("✅ Price update complete!")
            return True
        else:
            logger.error("❌ Price update failed")
            return False

    # MODE 3: DIVIDENDS - Update dividend data
    elif mode == 'dividends':
        logger.info("💰 DIVIDEND UPDATE MODE")
        logger.info("="*80)

        # Get all symbols from stocks table
        all_symbols = []
        page_size = 1000
        offset = 0

        while True:
            batch = pg_select('stocks', 'symbol', limit=page_size, offset=offset)
            if not batch:
                break
            all_symbols.extend([s['symbol'] for s in batch])
            offset += page_size

        logger.info(f"💰 Updating dividends for {len(all_symbols)} symbols...")
        success = update_dividends_hybrid(all_symbols, force_check=args.force or args.force_all)

        if success:
            logger.info("✅ Dividend update complete!")
            return True
        else:
            logger.error("❌ Dividend update failed")
            return False

    # MODE 4: METADATA - Update ETF metadata (AUM, description, expense_ratio)
    elif mode == 'metadata':
        logger.info("📋 ETF METADATA UPDATE MODE")
        logger.info("="*80)

        # Get all symbols from stocks table
        all_symbols = []
        page_size = 1000
        offset = 0

        while True:
            batch = pg_select('stocks', 'symbol', limit=page_size, offset=offset)
            if not batch:
                break
            all_symbols.extend([s['symbol'] for s in batch])
            offset += page_size

        logger.info(f"📋 Updating ETF metadata for {len(all_symbols)} symbols...")
        result = update_etf_metadata(all_symbols, batch_size=20)

        logger.info(f"✅ Metadata update complete! {result['updated']} updated, {result['skipped']} skipped, {result['errors']} errors")
        return True

    try:
        # Use intelligent filtering to get only symbols that need updates
        symbols = []
        if args.force_all:
            # Force update all symbols (bypass intelligent filtering)
            logger.info("🔥 FORCE MODE: Bypassing intelligent filtering - updating ALL symbols...")
            all_symbols = []
            page_size = 1000
            offset = 0
            
            while True:
                batch = pg_select('stocks', 'symbol', limit=page_size, offset=offset)
                if not batch:
                    break
                all_symbols.extend([s['symbol'] for s in batch])
                offset += page_size
                
            symbols = all_symbols
            logger.info(f"🔥 Force mode: updating ALL {len(symbols)} symbols in database")
        elif not DEBUG_MODE:
            logger.info("🎯 Using intelligent filtering to identify symbols needing updates...")
            symbols = get_symbols_needing_update()
            
            if not symbols:
                logger.info("✅ All symbols are up to date! No updates needed.")
                return True
        else:
            # Debug mode with test symbols
            symbols = ['AAPL', 'MAGY', 'MAGS', 'MSFT', 'KO']
            logger.info(f"🧪 Debug mode: testing with {len(symbols)} symbols")
        
        if not symbols:
            logger.warning("No symbols found")
            return True
        
        logger.info(f"Found {len(symbols)} symbols to update with hybrid approach")
        
        # Ensure portfolio holdings are in the stocks table before updates
        ensure_portfolio_holdings_in_stocks()
        
        if args.dividends_only:
            success = update_dividends_hybrid(symbols, args.force_all)
            if not success:
                logger.error("Hybrid dividend update failed")
                return False
        elif args.prices_only:
            success = update_prices_hybrid(symbols, args.force_all)
            if not success:
                logger.error("Hybrid price update failed")
                return False
        else:
            # Full hybrid update - both prices and dividends
            logger.info("🔄 Starting full hybrid update (prices + dividends)")
            
            # Update prices first
            logger.info("📊 Phase 1: Hybrid price updates")
            price_success = update_prices_hybrid(symbols, args.force_all)
            
            # Update dividends second
            logger.info("💰 Phase 2: Hybrid dividend updates") 
            dividend_success = update_dividends_hybrid(symbols, args.force_all)
            
            success = price_success and dividend_success
            if not success:
                logger.error("Hybrid full update failed")
                return False
        
        logger.info("🎉 Hybrid update completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in hybrid main process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🚀 Starting Hybrid Stock Data Update System")
    success = main_hybrid()
    if not success:
        print("❌ Hybrid update process failed")
        sys.exit(1)
    print("✅ Hybrid update process completed successfully")