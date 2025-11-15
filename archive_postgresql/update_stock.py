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
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Rate limiters for different APIs - OPTIMIZED
fmp_limiter = Semaphore(8)   # FMP can handle more concurrent requests
av_limiter = Semaphore(5)    # Alpha Vantage - keep conservative for free tier
yahoo_limiter = Semaphore(20) # Yahoo is more lenient, increase for better performance

# Configuration
DEBUG_MODE = False
ENHANCED_HISTORICAL_DATA = True
PRICES_START_DATE = "1960-01-01"
DIVIDENDS_START_DATE = "1960-01-01"
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "TSX", "BATS", "BTS", "BYX", "BZX", "CBOE", "TSE", 
    "EDGA", "EDGX", "PCX", "NGM",
    "OTCM", "OTCX",  # OTC markets for dividend stocks
    "LSE", "ASX", "JSE"  # International high-dividend markets
]

# Hybrid fetching configuration
USE_HYBRID_DIVIDENDS = True  # Enable hybrid dividend fetching
USE_HYBRID_PRICES = False    # Keep FMP primary for prices (excellent coverage)
FALLBACK_TO_YAHOO = True     # Enable Yahoo Finance fallback

# PostgreSQL connection functions
def test_postgres_connection():
    """Test PostgreSQL connection and return success status."""
    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 LIMIT 1")
                cursor.fetchone()
        logger.info("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False

def get_postgres_connection():
    """Get PostgreSQL connection with proper configuration."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'dividend_tracker_native'),
        user=os.getenv('POSTGRES_USER', 'toan'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )

def initialize_postgres_connection():
    """Initialize and test PostgreSQL connection."""
    try:
        if not test_postgres_connection():
            raise Exception("PostgreSQL connection test failed")
        
        logger.info("✅ PostgreSQL connection initialized and tested successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing PostgreSQL connection: {e}")
        return False

# PostgreSQL helper functions to replace Supabase operations
def pg_select(table, columns="*", where_clause=None, limit=None, offset=None, order_by=None):
    """Execute SELECT query on PostgreSQL."""
    with get_postgres_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = f"SELECT {columns} FROM {table}"
            params = []
            
            if where_clause:
                query += f" WHERE {where_clause['condition']}"
                if 'params' in where_clause:
                    params.extend(where_clause['params'])
            
            if order_by:
                query += f" ORDER BY {order_by}"
            
            if limit:
                query += f" LIMIT %s"
                params.append(limit)
            
            if offset:
                query += f" OFFSET %s"
                params.append(offset)
            
            cursor.execute(query, params)
            return cursor.fetchall()

def pg_insert(table, data, on_conflict=None):
    """Execute INSERT query on PostgreSQL."""
    if not data:
        return []
    
    if isinstance(data, dict):
        data = [data]
    
    with get_postgres_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if data:
                columns = list(data[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
                
                if on_conflict:
                    query += f" ON CONFLICT {on_conflict}"
                
                query += " RETURNING *"
                
                values = [[row[col] for col in columns] for row in data]
                
                if len(data) == 1:
                    cursor.execute(query, values[0])
                    return cursor.fetchall()
                else:
                    execute_batch(cursor, query, values)
                    conn.commit()
                    return data

def pg_upsert(table, data):
    """Execute UPSERT (INSERT ... ON CONFLICT DO UPDATE) on PostgreSQL."""
    if not data:
        return []
    
    if isinstance(data, dict):
        data = [data]
    
    with get_postgres_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            if data:
                columns = list(data[0].keys())
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                
                # Determine the appropriate conflict target based on table
                if table == 'stock_prices':
                    conflict_target = '(symbol, date)'
                    update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['symbol', 'date']])
                elif table == 'dividend_history':
                    conflict_target = '(symbol, payment_date)'
                    update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['symbol', 'payment_date']])
                else:
                    # Default to symbol for other tables
                    conflict_target = '(symbol)'
                    update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'symbol'])
                
                query = f"""
                INSERT INTO {table} ({columns_str}) VALUES ({placeholders})
                ON CONFLICT {conflict_target} DO UPDATE SET {update_clause}
                RETURNING *
                """
                
                values = [[row[col] for col in columns] for row in data]
                
                if len(data) == 1:
                    cursor.execute(query, values[0])
                    return cursor.fetchall()
                else:
                    execute_batch(cursor, query, values)
                    conn.commit()
                    return data

def pg_delete(table, where_clause):
    """Execute DELETE query on PostgreSQL."""
    with get_postgres_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = f"DELETE FROM {table} WHERE {where_clause['condition']} RETURNING *"
            params = where_clause.get('params', [])
            cursor.execute(query, params)
            return cursor.fetchall()

def pg_update(table, data, where_clause):
    """Execute UPDATE query on PostgreSQL."""
    with get_postgres_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause['condition']} RETURNING *"
            
            params = list(data.values()) + where_clause.get('params', [])
            cursor.execute(query, params)
            return cursor.fetchall()

# Configure logging FIRST before any other operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_update.log'),
        logging.StreamHandler()
    ]
)

# Reduce HTTP request logging noise
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("yfinance").setLevel(logging.WARNING)

# Initialize logger BEFORE PostgreSQL initialization
logger = logging.getLogger(__name__)

# Initialize PostgreSQL connection AFTER logger is ready
if not initialize_postgres_connection():
    logger.error("❌ Failed to initialize PostgreSQL connection - exiting")
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
    """Fetch price data from FMP API."""
    try:
        if from_date:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={from_date}&apikey={FMP_API_KEY}"
        else:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={PRICES_START_DATE}&apikey={FMP_API_KEY}"
        
        logger.debug(f"📊 [FMP] Fetching prices for {symbol}")
        data = fetch_with_adaptive_retry(url, fmp_limiter, symbol=symbol)
        
        if data and 'historical' in data and data['historical']:
            return {
                'source': 'FMP',
                'data': data['historical'],
                'count': len(data['historical'])
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
            
            # Get historical prices
            hist = ticker.history(period="max")
            
            if not hist.empty:
                # Convert to format similar to FMP
                price_data = []
                for date, row in hist.iterrows():
                    price_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume']) if not pd.isna(row['Volume']) else 0
                    })
                
                return {
                    'source': 'Yahoo Finance',
                    'data': price_data,
                    'count': len(price_data)
                }
        finally:
            yahoo_limiter.release()
            
    except Exception as e:
        logger.error(f"Yahoo prices error for {symbol}: {e}")
    
    return None

# =====================================
# COMPREHENSIVE SYMBOL DISCOVERY SYSTEM  
# =====================================

def discover_symbols_from_fmp(limit=5000):
    """Discover symbols from FMP API."""
    logger.info(f"🔍 [FMP] Discovering symbols (limit: {limit})")
    
    symbols = []
    
    try:
        url = f"https://financialmodelingprep.com/api/v3/available-traded/list?apikey={FMP_API_KEY}"
        data = fetch_with_adaptive_retry(url, fmp_limiter)
        
        if data:
            for item in data[:limit]:
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

def discover_dividend_stocks_from_fmp(min_yield=0.01, limit=1000):
    """Discover dividend-paying stocks from FMP screener."""
    logger.info(f"🔍 [FMP] Discovering dividend stocks (yield > {min_yield:.1%}, limit: {limit})")
    
    symbols = []
    
    try:
        url = f"https://financialmodelingprep.com/api/v3/stock-screener?dividendYieldMoreThan={min_yield}&limit={limit}&apikey={FMP_API_KEY}"
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

def discover_symbols_from_alpha_vantage(limit=1000):
    """Discover symbols from Alpha Vantage LISTING_STATUS endpoint."""
    logger.info(f"🔍 [Alpha Vantage] Discovering symbols from LISTING_STATUS (limit: {limit})")
    
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
                if count >= limit:
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
        
        # Fallback to curated list if API fails
        logger.info("🔄 [Alpha Vantage] Falling back to curated symbol list")
        popular_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK.B', 'JNJ',
            'V', 'WMT', 'PG', 'UNH', 'DIS', 'HD', 'BAC', 'MA', 'PFE', 'KO',
            # Popular ETFs
            'SPY', 'QQQ', 'VTI', 'IWM', 'VTV', 'VUG', 'VEA', 'VWO', 'AGG', 'BND',
            'XLK', 'XLF', 'XLV', 'XLE', 'XLI', 'XLB', 'XLRE', 'XLU', 'XLP', 'XLY'
        ]
        
        for symbol in popular_symbols[:min(limit, len(popular_symbols))]:
            symbols.append({
                'symbol': symbol,
                'name': f'{symbol} (Alpha Vantage)',
                'source': 'AV-FALLBACK',
                'exchange': 'Unknown'
            })
    
    return symbols

def discover_symbols_from_yahoo_screener(min_yield=2.0, limit=200):
    """Enhanced Yahoo Finance discovery using direct yfinance methods."""
    logger.info(f"🔍 [Yahoo Enhanced] Discovering dividend stocks (min yield: {min_yield}%, limit: {limit})")
    
    symbols = []
    
    # Popular high-yield dividend ETFs and REITs to validate
    high_yield_targets = [
        # YieldMax ETFs
        'PLTW', 'JEPY', 'DIVO', 'XYLD', 'XRMI', 'APLY', 'NUSI', 'YMAX', 'YMAG', 'YBIT',
        'YNDX', 'YTEK', 'YSEM', 'YGEN', 'YQQQ', 'AAPL', 'TSLY', 'NVDY',
        
        # Core dividend ETFs
        'FDVV', 'SCHD', 'HDV', 'VYM', 'SPHD', 'SPYD', 'JEPI', 'QYLD', 'RYLD', 'NUSI',
        
        # Roundhill ETFs
        'MAGS', 'MAGY', 'TMDV', 'METV', 'RNDR', 'BITO', 'WUGI', 'CHAT',
        
        # Global X dividend ETFs
        'SDIV', 'DIV', 'SDEM', 'HDIV', 'PFFD', 'SRET',
        
        # High-yield REITs
        'O', 'STAG', 'MPW', 'VICI', 'EPR', 'WPC', 'STORE', 'NNN', 'MAIN', 'GAIN',
        'GLAD', 'ARCC', 'HTGC', 'PSEC', 'NEWT', 'SACH', 'TSLX',
        
        # International dividend ETFs
        'VYMI', 'VXUS', 'IEFA', 'VEA', 'VWO', 'SCHF', 'IEMG',
        
        # Sector dividend leaders
        'XLU', 'VPU', 'FIDU', 'XLE', 'VDE', 'FENY', 'XLF', 'VFH', 'FNCL'
    ]
    
    discovered_symbols = set()
    
    for symbol in high_yield_targets:
        if len(symbols) >= limit:
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
                        'source': 'YAHOO-ENHANCED',
                        'type': info.get('quoteType', 'UNKNOWN'),
                        'exchange': info.get('exchange', 'Unknown')
                    })
                    discovered_symbols.add(symbol)
                    logger.debug(f"✅ [Yahoo Enhanced] Validated: {symbol}")
            finally:
                yahoo_limiter.release()
        except Exception as e:
            logger.debug(f"Yahoo enhanced validation failed for {symbol}: {e}")
    
    # Add search-based discovery as backup
    if len(symbols) < limit:
        remaining_limit = limit - len(symbols)
        search_symbols = discover_symbols_from_yahoo_search_original(max_results_per_term=remaining_limit//10)
        
        for symbol_data in search_symbols:
            if symbol_data['symbol'] not in discovered_symbols:
                symbols.append(symbol_data)
                discovered_symbols.add(symbol_data['symbol'])
    
    logger.info(f"✅ [Yahoo Enhanced] Discovered {len(symbols)} symbols")
    return symbols

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
    
    # Add specific high-yield ETFs that might not be found through search
    high_yield_etfs = [
        'PLTW', 'JEPY', 'DIVO', 'XYLD', 'XRMI', 'APLY', 'NUSI', 'YMAX',
        'FDVV', 'SCHD', 'HDV', 'VYM', 'SPHD', 'SPYD'
    ]
    
    for symbol in high_yield_etfs:
        if symbol not in discovered_symbols:
            try:
                # Quick validation that symbol exists
                yahoo_limiter.acquire()
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if info and 'regularMarketPrice' in info:
                        symbols.append({
                            'symbol': symbol,
                            'name': info.get('longName') or info.get('shortName', ''),
                            'source': 'YAHOO-MANUAL',
                            'type': info.get('quoteType', 'UNKNOWN'),
                            'exchange': info.get('exchange', 'Unknown')
                        })
                        discovered_symbols.add(symbol)
                        logger.debug(f"  [Yahoo] Added manual ETF: {symbol}")
                finally:
                    yahoo_limiter.release()
            except Exception as e:
                logger.debug(f"  [Yahoo] Manual ETF {symbol} failed: {e}")
    
    logger.info(f"✅ [Yahoo] Discovered {len(symbols)} unique symbols from search")
    return symbols

def discover_symbols_from_nasdaq_api(limit=1000):
    """Discover symbols from NASDAQ public API."""
    logger.info(f"🔍 [NASDAQ API] Discovering symbols (limit: {limit})")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    symbols = []
    
    try:
        # Get ETFs from NASDAQ
        etf_url = 'https://api.nasdaq.com/api/screener/etf'
        params = {'tableonly': 'true', 'limit': limit // 2, 'offset': 0}
        
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
                    'limit': min(limit // len(exchanges) // 2, 300),
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

def discover_etfs_by_company(limit=200):
    """Discover ETFs using known successful patterns and company relationships."""
    logger.info(f"🔍 [COMPANY ETF] Discovering ETFs by company patterns (limit: {limit})")
    
    symbols = []
    
    # Known high-yield ETF patterns to search for systematically
    etf_patterns = {
        'YieldMax': [
            'YMAX', 'YMAG', 'YBIT', 'YNDX', 'YTEK', 'YSEM', 'YGEN', 'YQQQ', 
            'TSLY', 'NVDY', 'OARK', 'YSPY', 'YSML', 'YBTC', 'YETH', 'YAMD',
            'YGOG', 'YMSF', 'YCOL', 'YCRM', 'YAMA', 'YNVS', 'YLDV'
        ],
        'Roundhill': [
            'MAGS', 'MAGY', 'TMDV', 'METV', 'RNDR', 'BITO', 'WUGI', 'CHAT',
            'MVPS', 'NERD', 'ESPO', 'MEME', 'LIVE', 'RPAR', 'ISPY'
        ],
        'Global X': [
            'SDIV', 'DIV', 'SDEM', 'HDIV', 'PFFD', 'SRET', 'MLPA', 'CHIQ',
            'ASHR', 'CHIH', 'EDOC', 'FINX', 'GNOM', 'HERO', 'SNSR', 'SOCL'
        ],
        'Defiance': [
            'QTUM', 'FIVG', 'NFTZ', 'MAGS', 'KLNE', 'FNCL', 'PRAY', 'AUGR'
        ],
        'First Trust': [
            'FDN', 'FYT', 'FEX', 'FDNI', 'FCOM', 'FREL', 'FTSL', 'FTSM',
            'FDVV', 'FTCS', 'FDTS', 'FDEM', 'FDRR', 'FDWM'
        ],
        'ProShares': [
            'NOBL', 'SRET', 'REET', 'TQQQ', 'SQQQ', 'UPRO', 'SPXU',
            'SSO', 'SDS', 'QLD', 'QID', 'VIXY', 'SVXY'
        ],
        'VanEck': [
            'GDXJ', 'GDXJ', 'SLV', 'PDBC', 'REMX', 'MOO', 'PICK',
            'CPER', 'JJG', 'CORN', 'WEAT', 'NIB'
        ],
        'ARK': [
            'ARKK', 'ARKQ', 'ARKW', 'ARKG', 'ARKF', 'ARKX', 'PRNT', 'IZRL'
        ],
        'Amplify': [
            'DIVO', 'IDVO', 'CWS', 'BATT', 'IBUY', 'HACK', 'BLOK', 'DTEC'
        ]
    }
    
    discovered_symbols = set()
    
    for company, pattern_symbols in etf_patterns.items():
        for symbol in pattern_symbols:
            if len(symbols) >= limit:
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
                            'source': f'PATTERN-{company}',
                            'exchange': info.get('exchange', 'Unknown'),
                            'company_pattern': company,
                            'type': info.get('quoteType', 'ETF')
                        })
                        discovered_symbols.add(symbol)
                        logger.debug(f"✅ [Pattern {company}] Validated: {symbol}")
                finally:
                    yahoo_limiter.release()
            except Exception as e:
                logger.debug(f"Pattern validation failed for {symbol}: {e}")
    
    logger.info(f"✅ [COMPANY ETF] Discovered {len(symbols)} ETFs using company patterns")
    return symbols

def validate_discovered_symbol(symbol_data):
    """Validate a discovered symbol using Yahoo Finance to determine if it meets criteria."""
    symbol = symbol_data['symbol']
    
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
        # Get all symbols from raw_stocks table with pagination
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
        excluded_data = pg_select("stocks_excluded", "symbol, reason", limit=5000)
        existing_excluded = {}
        for row in excluded_data:
            symbol = row['symbol']
            reason = row['reason']
            if symbol not in existing_excluded:
                existing_excluded[symbol] = []
            existing_excluded[symbol].append(reason)
        
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
        excluded_data = pg_select("stocks_excluded", "symbol, reason", where_clause={"condition": "symbol = %s", "params": [symbol]})
        if excluded_data:
            reasons = [row['reason'] for row in excluded_data] 
            return 'stocks_excluded', f"Excluded: {', '.join(reasons)}"
        
        return None, None
        
    except Exception as e:
        logger.error(f"❌ Database check failed for {symbol}: {e}")
        return 'error', str(e)

def discover_crypto_etfs(limit=50):
    """Discover cryptocurrency ETFs specifically."""
    logger.info(f"🔍 [CRYPTO ETF] Discovering cryptocurrency ETFs (limit: {limit})")
    
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
        if len(symbols) >= limit:
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

def discover_specialized_dividend_etfs(limit=100):
    """Discover specialized dividend and income ETFs."""
    logger.info(f"🔍 [SPECIALIZED] Discovering specialized dividend ETFs (limit: {limit})")
    
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
            if len(symbols) >= limit:
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
            symbol = holding['symbol'].strip().upper()
            if symbol:
                symbols.append({
                    'symbol': symbol,
                    'exchange': 'PORTFOLIO',  # Special exchange marker for portfolio symbols
                    'type': 'STOCK',
                    'name': f'Portfolio Holding: {symbol}'
                })
        
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
        
        portfolio_symbols = [holding['symbol'].strip().upper() for holding in portfolio_data if holding['symbol'].strip()]
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

def comprehensive_symbol_discovery(fmp_limit=5000, alpha_limit=1000, yahoo_terms=None, nasdaq_limit=1000, use_full_etf_list=False, use_dividend_screener=False):
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
    if fmp_limit > 0:
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
        fmp_div_symbols = discover_dividend_stocks_from_fmp(min_yield=0.005, limit=2000)  # 0.5%+ yield
        discovery_stats['fmp_dividend'] = len(fmp_div_symbols)
        
        for symbol_data in fmp_div_symbols:
            symbol = symbol_data['symbol']
            exchange = symbol_data.get('exchange', 'Unknown')
            key = f"{symbol}:{exchange}"
            
            if key not in unique_symbol_exchange:
                unique_symbol_exchange.add(key)
                all_discovered_symbols.append(symbol_data)
    
    # Discover from Alpha Vantage (Secondary source)  
    if alpha_limit > 0:
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
    
    # Discover from Yahoo Finance screener and categories (Enhanced source)
    logger.info("🟡 Discovering symbols from Yahoo Finance enhanced methods...")
    yahoo_symbols = discover_symbols_from_yahoo_screener(min_yield=1.0, limit=300)
    discovery_stats['yahoo'] = len(yahoo_symbols)
    
    for symbol_data in yahoo_symbols:
        symbol = symbol_data['symbol']
        exchange = symbol_data.get('exchange', 'Unknown')
        key = f"{symbol}:{exchange}"
        
        if key not in unique_symbol_exchange:
            unique_symbol_exchange.add(key)
            all_discovered_symbols.append(symbol_data)
    
    # Discover from NASDAQ API (Additional source)
    if nasdaq_limit > 0:
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
    
    discovery_stats['total_discovered'] = len(all_discovered_symbols)
    
    # Now filter against existing database using batch operations
    logger.info("🔍 Filtering discovered symbols against existing database (batch operation)...")
    batch_results = check_symbols_exist_in_database_batch(all_discovered_symbols)
    
    new_symbols_to_add = []
    
    for symbol_data in all_discovered_symbols:
        symbol = symbol_data['symbol']
        exists_in, reason = batch_results.get(symbol, (None, None))
        
        if exists_in == 'stocks':
            discovery_stats['already_in_stocks'] += 1
            logger.debug(f"⏭️  {symbol}: Already in stocks table")
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
    logger.info(f"   🎯 Total Discovered: {discovery_stats['total_discovered']} unique symbols")
    logger.info("")
    logger.info("📋 Database Filtering Results:")
    logger.info(f"   ✅ Already in stocks: {discovery_stats['already_in_stocks']} symbols")
    logger.info(f"   🚫 Already excluded: {discovery_stats['already_excluded']} symbols")
    logger.info(f"   🆕 New symbols to process: {discovery_stats['new_symbols']} symbols")
    
    return new_symbols_to_add, discovery_stats

def get_symbols_needing_update():
    """Get only symbols that actually need data updates using intelligent filtering."""
    logger.info("🎯 Analyzing which symbols need updates (intelligent filtering)...")
    
    try:
        # Get all symbols from raw_stocks table with their latest data timestamps
        symbols_query = """
        SELECT 
            s.symbol,
            p.last_price_date,
            d.last_dividend_date
        FROM raw_stocks s
        LEFT JOIN (
            SELECT symbol, MAX(date) as last_price_date
            FROM raw_stock_prices 
            GROUP BY symbol
        ) p ON s.symbol = p.symbol
        LEFT JOIN (
            SELECT symbol, MAX(payment_date) as last_dividend_date  
            FROM raw_dividends
            GROUP BY symbol
        ) d ON s.symbol = d.symbol
        """
        
        # Since Supabase doesn't support complex joins directly, we'll do this in steps
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
        
        # Get latest price dates for all symbols
        price_dates = {}
        try:
            prices_data = pg_select("stock_prices", "symbol, date", order_by="date DESC", limit=20000)
            for record in prices_data:
                symbol = record['symbol']
                date = record['date']
                if symbol not in price_dates or date > price_dates[symbol]:
                    price_dates[symbol] = date
        except Exception as e:
            logger.warning(f"Could not fetch price dates: {e}")
        
        # Get latest dividend dates for all symbols
        dividend_dates = {}
        try:
            dividends_data = pg_select("dividend_history", "symbol, payment_date", order_by="payment_date DESC", limit=20000)
            for record in dividends_data:
                symbol = record['symbol']
                date = record['payment_date']
                if symbol not in dividend_dates or date > dividend_dates[symbol]:
                    dividend_dates[symbol] = date
        except Exception as e:
            logger.warning(f"Could not fetch dividend dates: {e}")
        
        # Filter symbols that need updates
        symbols_needing_update = []
        today = datetime.now().date()
        
        for symbol in all_symbols:
            needs_update = False
            reasons = []
            
            # Check if needs price update (older than 7 days or missing)
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
                if days_since_price > 7:
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
            logger.info(f"✅ [ALPHA VANTAGE FALLBACK] Found {result['count']} price records for {symbol}")
            return result
    
    # Try Yahoo Finance (fallback) - only if FMP and Alpha Vantage failed
    if FALLBACK_TO_YAHOO:
        logger.debug(f"🔄 [FMP+AV FAILED] Trying Yahoo Finance for {symbol}")
        result = fetch_yahoo_prices(symbol)
        if result and result['count'] > 0:
            logger.info(f"✅ [YAHOO FALLBACK] Found {result['count']} price records for {symbol}")
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
            if max_date >= today:
                logger.debug(f"⏭️  {symbol}: Skipping - already has current price data (latest: {max_date})")
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
                    "open_price": price_data.get('open'),
                    "highest_price": price_data.get('high'),
                    "lowest_price": price_data.get('low'), 
                    "close_price": price_data.get('close'),
                    "volume": price_data.get('volume', 0)
                }
                price_records.append(record)
        
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
        # Try TIME_SERIES_DAILY_ADJUSTED which includes dividend info
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=full"
        
        logger.debug(f"💰 [ALPHA VANTAGE] Fetching dividend-adjusted data for {symbol}")
        data = fetch_with_adaptive_retry(url, av_limiter, symbol=symbol)
        
        if data and 'Time Series (Daily)' in data:
            # Alpha Vantage includes dividend info in adjusted data
            # We'd need to parse this for actual dividend dates/amounts
            # For now, return indication that data exists
            return {
                'source': 'Alpha Vantage',
                'data': None,  # Would need parsing logic
                'count': 0,
                'note': 'Has dividend-adjusted data, needs parsing'
            }
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
                'function': 'TIME_SERIES_DAILY',
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
                                'volume': int(daily_data['5. volume'])
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
                company_info['total_assets'] = int(total_assets)
                
            logger.debug(f"✅ [YAHOO] Found company info for {symbol}: {company_info.get('name', 'N/A')}")
            return company_info
            
        finally:
            yahoo_limiter.release()
            
    except Exception as e:
        logger.error(f"Yahoo company info error for {symbol}: {e}")
        return {}

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
        if result:
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
                if div_data.get('dividend', 0) > 0:  # Filter out zero dividends
                    record = {
                        "symbol": symbol,
                        "payment_date": div_data.get('date'),
                        "amount": div_data.get('dividend')
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
        
        # Get max dates for existing dividend data
        max_dividend_dates = {}
        try:
            dividends_data = pg_select("dividend_history", "symbol, payment_date", order_by="payment_date DESC", limit=20000)
            for record in dividends_data:
                symbol = record['symbol']
                date = record['payment_date']
                if symbol not in max_dividend_dates or date > max_dividend_dates[symbol]:
                    max_dividend_dates[symbol] = date
            logger.info(f"Found max dates for {len(max_dividend_dates)} symbols in dividends")
        except Exception as e:
            logger.warning(f"Could not fetch max dates: {e}")
        
        # Process symbols in batches
        batch_size = 20  # Smaller batches for hybrid processing
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
    
    with ThreadPoolExecutor(max_workers=3) as executor:  # Conservative for hybrid processing
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
        
        # Get max dates for existing price data
        max_price_dates = {}
        try:
            prices_data = pg_select("stock_prices", "symbol, date", order_by="date DESC", limit=20000)
            for record in prices_data:
                symbol = record['symbol']
                date = record['date']
                if symbol not in max_price_dates or date > max_price_dates[symbol]:
                    max_price_dates[symbol] = date
            logger.info(f"Found max dates for {len(max_price_dates)} symbols in prices")
        except Exception as e:
            logger.warning(f"Could not fetch max dates: {e}")
        
        # Process symbols in batches
        batch_size = 20  # Smaller batches for hybrid processing
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
    
    with ThreadPoolExecutor(max_workers=3) as executor:  # Conservative for hybrid processing
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
                
                # Create stock record with proper company information
                stock_record = {
                    'symbol': symbol,
                    'name': company_info.get('name', f'{symbol} (Auto-added)'),
                    'company_name': company_info.get('company_name', f'{symbol} (Auto-added)'),
                    'description': company_info.get('description'),
                    'expense_ratio': company_info.get('expense_ratio'),
                    'aum': company_info.get('total_assets')
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
    global DEBUG_MODE, ENHANCED_HISTORICAL_DATA, USE_HYBRID_DIVIDENDS, FALLBACK_TO_YAHOO
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hybrid stock data update with multiple data sources')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode with test symbols')
    parser.add_argument('--force-all', action='store_true', help='Force update all symbols (bypass intelligent filtering)')
    parser.add_argument('--dividends-only', action='store_true', help='Only update dividends using hybrid approach')
    parser.add_argument('--prices-only', action='store_true', help='Only update prices using hybrid approach')
    parser.add_argument('--symbol', type=str, help='Run complete validation (prices + dividends) for a single symbol')
    parser.add_argument('--disable-hybrid', action='store_true', help='Disable hybrid fetching (FMP only)')
    parser.add_argument('--disable-yahoo', action='store_true', help='Disable Yahoo Finance fallback')
    parser.add_argument('--test-symbol', type=str, help='Test hybrid fetching on a single symbol (deprecated, use --symbol)')
    parser.add_argument('--full-hybrid', action='store_true', help='Enable full 3-tier hybrid passes (FMP → Alpha Vantage → Yahoo)')
    parser.add_argument('--discover-symbols', action='store_true', help='Discover new symbols from all sources before data fetching')
    parser.add_argument('--discovery-only', action='store_true', help='Only discover symbols, do not fetch data')
    parser.add_argument('--validate-discovered', action='store_true', help='Validate discovered symbols and add to database')
    parser.add_argument('--fmp-limit', type=int, default=5000, help='Limit for FMP symbol discovery (default: 5000)')
    parser.add_argument('--alpha-limit', type=int, default=1000, help='Limit for Alpha Vantage symbol discovery (default: 1000)')
    parser.add_argument('--nasdaq-limit', type=int, default=1000, help='Limit for NASDAQ API symbol discovery (default: 1000)')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run (no database updates for discovered symbols)')
    parser.add_argument('--future-dividends', action='store_true', help='Fetch and display future dividend calendar (3 months ahead)')
    parser.add_argument('--future-from', type=str, help='Start date for future dividends in YYYY-MM-DD format (default: today)')
    parser.add_argument('--future-to', type=str, help='End date for future dividends in YYYY-MM-DD format (default: 3 months)')
    parser.add_argument('--future-symbols', type=str, nargs='+', help='Filter future dividends by specific symbols')
    parser.add_argument('--future-yahoo-only', action='store_true', help='Use only Yahoo Finance for future dividends')
    parser.add_argument('--future-hybrid', action='store_true', help='Use both FMP and Yahoo Finance for comprehensive future dividend coverage')
    parser.add_argument('--future-predictions', action='store_true', help='Include pattern-based dividend predictions from Yahoo Finance')
    
    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)
    
    # Set configuration based on arguments
    DEBUG_MODE = args.debug
    if args.disable_hybrid:
        USE_HYBRID_DIVIDENDS = False
    if args.disable_yahoo:
        FALLBACK_TO_YAHOO = False
    if args.full_hybrid:
        USE_HYBRID_DIVIDENDS = True
        FALLBACK_TO_YAHOO = True
        logger.info("🚀 Full hybrid mode enabled - all data sources active")
    
    # Log comprehensive configuration
    logger.info("="*80)
    logger.info("🚀 ENHANCED HYBRID STOCK DATA UPDATE SYSTEM v2.0")
    logger.info("="*80)
    logger.info("🛠️  CONFIGURATION:")
    logger.info(f"   Debug Mode: {DEBUG_MODE}")
    logger.info(f"   Enhanced Historical Data: {'ENABLED' if ENHANCED_HISTORICAL_DATA else 'DISABLED'}")
    logger.info(f"   Hybrid Dividends: {'ENABLED' if USE_HYBRID_DIVIDENDS else 'DISABLED'}")
    logger.info(f"   Yahoo Fallback: {'ENABLED' if FALLBACK_TO_YAHOO else 'DISABLED'}")
    logger.info(f"   Intelligent Filtering: ENABLED (up to 70% fewer API calls)")
    logger.info("")
    logger.info("🔍 DISCOVERY SOURCES:")
    logger.info("   🔵 FMP: Primary source (8 concurrent requests)")
    logger.info("   🟠 Alpha Vantage: Secondary source (5 concurrent requests)")
    logger.info("   🟡 Yahoo Finance: Fallback source (20 concurrent requests)")
    logger.info("   🟢 NASDAQ API: Additional coverage")
    logger.info("   🟡 Crypto ETFs: Bitcoin, Ethereum, DeFi coverage")
    logger.info("   🟪 Specialized ETFs: Monthly dividend, covered call, REIT")
    logger.info("   🟣 Pattern ETFs: YieldMax, Roundhill, Global X, etc.")
    logger.info("")
    logger.info("🌍 EXCHANGE COVERAGE:")
    logger.info(f"   {', '.join(ALLOWED_EXCHANGES[:8])}")
    logger.info(f"   {', '.join(ALLOWED_EXCHANGES[8:])}")
    logger.info("="*80)
    
    # Handle single symbol complete validation mode
    if args.symbol:
        logger.info(f"🎯 Running complete validation for symbol: {args.symbol}")
        result = complete_symbol_validation(args.symbol)
        logger.info(f"Complete validation result: {'SUCCESS' if result else 'FAILED'}")
        return result
    
    # Handle test symbol mode (deprecated)
    if args.test_symbol:
        logger.info(f"🧪 Testing hybrid fetching for symbol: {args.test_symbol}")
        result = process_symbol_dividends_hybrid(args.test_symbol)
        logger.info(f"Test result: {'SUCCESS' if result else 'FAILED'}")
        return True
    
    # Handle future dividends mode
    if args.future_dividends:
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
        
        return True
    
    # Handle comprehensive symbol discovery mode
    if args.discover_symbols or args.discovery_only:
        logger.info("🚀 COMPREHENSIVE SYMBOL DISCOVERY & DATABASE UPDATE")
        logger.info("="*80)
        
        # Step 1: Discover all symbols from all sources and filter against database
        new_symbols_to_add, discovery_stats = comprehensive_symbol_discovery(
            fmp_limit=args.fmp_limit,
            alpha_limit=args.alpha_limit,
            nasdaq_limit=args.nasdaq_limit,
            use_full_etf_list=True,  # Enable comprehensive ETF discovery
            use_dividend_screener=True  # Enable dividend stock discovery
        )
        
        # Step 2: Validate and add new symbols to database if any found
        if new_symbols_to_add and args.validate_discovered:
            logger.info(f"🔍 Validating {len(new_symbols_to_add)} new symbols...")
            validated_symbols = []
            excluded_symbols = []
            
            # Validate symbols in batches using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_symbol = {
                    executor.submit(validate_discovered_symbol, symbol_data): symbol_data['symbol']
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
            
            # Add validated symbols to database if not dry run
            if not args.dry_run:
                # Insert validated symbols into stocks table
                if validated_symbols:
                    stocks_to_insert = []
                    for result in validated_symbols:
                        stock_record = {
                            'symbol': result['symbol'],
                            'name': result['name'],
                            'company_name': result['company_name'],
                            'description': result.get('description'),
                            'expense_ratio': result.get('expense_ratio'),
                            'aum': result.get('aum')
                        }
                        # Remove None values
                        stock_record = {k: v for k, v in stock_record.items() if v is not None}
                        stocks_to_insert.append(stock_record)
                    
                    try:
                        result = pg_insert("stocks", stocks_to_insert)
                        logger.info(f"✅ Inserted {len(result.data)} new symbols into stocks table")
                    except Exception as e:
                        logger.error(f"❌ Failed to insert stocks: {e}")
                
                # Add excluded symbols to stocks_excluded table with source tracking
                if excluded_symbols:
                    excluded_to_insert = []
                    for result in excluded_symbols:
                        source_data = result.get('source_data', {})
                        original_source = source_data.get('source', 'DISCOVERY')
                        
                        exclusion_record = {
                            'symbol': result['symbol'],
                            'reason': f"[{original_source}] {result.get('exclusion_reason') or result.get('reason', 'Failed validation')}"
                        }
                        excluded_to_insert.append(exclusion_record)
                    
                    try:
                        result = pg_insert("stocks_excluded", excluded_to_insert)
                        logger.info(f"✅ Inserted {len(result.data)} exclusions into stocks_excluded table")
                    except Exception as e:
                        logger.error(f"❌ Failed to insert exclusions: {e}")
            else:
                logger.info("🔍 DRY RUN - No database changes made")
        
        elif new_symbols_to_add and not args.validate_discovered:
            logger.info(f"⚠️  Found {len(new_symbols_to_add)} new symbols but validation not requested (use --validate-discovered)")
        
        elif not new_symbols_to_add:
            logger.info("✅ No new symbols found - all discovered symbols already exist in database")
        
        # If discovery-only mode, exit here
        if args.discovery_only:
            logger.info("🎉 Discovery-only mode complete!")
            return True
        
        # Continue to data fetching phase for ALL symbols in stocks table
        logger.info("\n" + "="*80)
        logger.info("🔄 PROCEEDING TO DATA FETCHING FOR ALL SYMBOLS IN STOCKS TABLE")
        logger.info("="*80)
    
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