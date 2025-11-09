#!/usr/bin/env python3
"""
Comprehensive Stock Data Update Script with Multiple Data Sources

This script fetches ALL stocks and ETFs from multiple sources:
1. FMP (Financial Modeling Prep) - Primary source
2. Alpha Vantage - Secondary source
3. Yahoo Finance - Tertiary source
4. NASDAQ - Additional source

Requirements: Recent data within 7 days
"""

import os
import sys
import logging
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
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comprehensive_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# API Configuration
FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

# Rate limiters for different APIs
fmp_limiter = Semaphore(10)    # FMP can handle more concurrent requests
av_limiter = Semaphore(5)       # Alpha Vantage - conservative for free tier
yahoo_limiter = Semaphore(25)   # Yahoo is more lenient
nasdaq_limiter = Semaphore(10)  # NASDAQ rate limiting

# Configuration
BATCH_SIZE = 50
MAX_WORKERS = 20
RECENT_DATA_DAYS = 7
MIN_PRICE = 0.01
MIN_VOLUME = 100

# Allowed exchanges - Original list as specified by user
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "TSX", "BATS", "BTS", "BYX", "BZX", "CBOE", "TSE",
    "EDGA", "EDGX", "PCX", "NGM",
    "OTCM", "OTCX",  # OTC markets for dividend stocks
    "LSE", "ASX", "JSE"  # International high-dividend markets
]

# Excluded types - More specific
EXCLUDED_TYPES = ['mutual fund', 'fund', 'mutualfund', 'index', 'note']

# High-dividend sectors to focus on
HIGH_DIVIDEND_SECTORS = [
    'REIT', 'Utilities', 'Energy', 'Telecommunications', 'Consumer Defensive',
    'Financial Services', 'Basic Materials', 'Healthcare'
]

# PostgreSQL connection functions
def get_postgres_connection():
    """Get PostgreSQL connection with proper configuration."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'dividend_tracker_native'),
        user=os.getenv('POSTGRES_USER', 'toan'),
        password=os.getenv('POSTGRES_PASSWORD', '')
    )

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

def truncate_excluded_table():
    """Truncate the stocks_excluded table to start fresh."""
    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("TRUNCATE TABLE stocks_excluded CASCADE")
                conn.commit()
                logger.info("✅ Truncated stocks_excluded table")
                return True
    except Exception as e:
        logger.error(f"❌ Error truncating stocks_excluded table: {e}")
        return False

def get_existing_symbols():
    """Get all existing symbols from the stocks table."""
    try:
        with get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT symbol FROM stocks")
                results = cursor.fetchall()
                return set(row['symbol'] for row in results)
    except Exception as e:
        logger.error(f"Error fetching existing symbols: {e}")
        return set()

def save_symbols_batch(symbols_data):
    """Save a batch of symbols to the database."""
    if not symbols_data:
        return 0

    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare data for insertion
                insert_data = []
                for symbol_info in symbols_data:
                    insert_data.append((
                        symbol_info['symbol'],
                        symbol_info.get('name', ''),
                        symbol_info.get('price', 0),
                        symbol_info.get('last_updated', datetime.now())
                    ))

                # Use ON CONFLICT to handle duplicates
                query = """
                    INSERT INTO stocks (symbol, name, price, last_updated)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (symbol) DO UPDATE SET
                        name = EXCLUDED.name,
                        price = EXCLUDED.price,
                        last_updated = EXCLUDED.last_updated
                """

                execute_batch(cursor, query, insert_data, page_size=100)
                conn.commit()

                logger.info(f"✅ Saved {len(insert_data)} symbols to database")
                return len(insert_data)

    except Exception as e:
        logger.error(f"Error saving symbols batch: {e}")
        return 0

def get_portfolio_symbols():
    """Get all symbols from portfolio holdings."""
    portfolio_symbols = set()

    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Get symbols from int_portfolio_holdings table
                cursor.execute("SELECT DISTINCT symbol FROM int_portfolio_holdings WHERE symbol IS NOT NULL")
                holdings_symbols = set(row[0].strip().upper() for row in cursor.fetchall() if row[0] and row[0].strip())
                portfolio_symbols.update(holdings_symbols)

                # Get symbols from portfolios table (JSON field)
                cursor.execute("SELECT stocks FROM portfolios WHERE stocks IS NOT NULL")
                for row in cursor.fetchall():
                    try:
                        stocks_data = row[0]
                        if isinstance(stocks_data, str):
                            stocks_data = json.loads(stocks_data)
                        if isinstance(stocks_data, list):
                            for stock in stocks_data:
                                if isinstance(stock, dict) and 'symbol' in stock:
                                    symbol = stock['symbol'].strip().upper()
                                    if symbol:
                                        portfolio_symbols.add(symbol)
                    except (json.JSONDecodeError, KeyError, AttributeError) as e:
                        logger.debug(f"Error parsing portfolio stocks JSON: {e}")
                        continue

                logger.info(f"💼 Found {len(portfolio_symbols)} symbols in portfolios")
                return portfolio_symbols

    except Exception as e:
        logger.error(f"Error fetching portfolio symbols: {e}")
        return set()

def add_to_excluded(symbol, reason):
    """Add a symbol to the excluded table, but protect portfolio symbols."""
    try:
        # Check if symbol is in any portfolio - if so, don't exclude it
        portfolio_symbols = get_portfolio_symbols()
        if symbol.upper() in portfolio_symbols:
            logger.info(f"🛡️ Protected portfolio symbol {symbol} from exclusion (reason would have been: {reason})")
            return

        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO stocks_excluded (symbol, reason, excluded_at)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (symbol) DO UPDATE SET
                           reason = EXCLUDED.reason,
                           excluded_at = EXCLUDED.excluded_at""",
                    (symbol, reason, datetime.now())
                )
                conn.commit()
    except Exception as e:
        logger.error(f"Error adding {symbol} to excluded: {e}")

def remove_portfolio_symbols_from_exclusions():
    """Remove any portfolio symbols from the exclusion list to override exclusion rules."""
    try:
        portfolio_symbols = get_portfolio_symbols()
        if not portfolio_symbols:
            return 0

        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Remove portfolio symbols from exclusion list
                placeholders = ','.join(['%s'] * len(portfolio_symbols))
                cursor.execute(f"""
                    DELETE FROM stocks_excluded
                    WHERE symbol IN ({placeholders})
                """, list(portfolio_symbols))

                removed_count = cursor.rowcount
                conn.commit()

                if removed_count > 0:
                    logger.info(f"🔄 Overrode exclusions: Removed {removed_count} portfolio symbols from exclusion list")

                return removed_count

    except Exception as e:
        logger.error(f"Error removing portfolio symbols from exclusions: {e}")
        return 0

def get_excluded_symbols():
    """Get all excluded symbols from the stocks_excluded table."""
    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT symbol FROM stocks_excluded")
                excluded = set(row[0] for row in cursor.fetchall())
                logger.info(f"📋 Loaded {len(excluded)} excluded symbols from database")
                return excluded
    except Exception as e:
        logger.error(f"Error fetching excluded symbols: {e}")
        return set()

def cleanup_stale_stocks():
    """Remove stocks from the stocks table that are in the excluded list, but protect portfolio symbols."""
    try:
        portfolio_symbols = get_portfolio_symbols()

        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Delete stocks that are in the excluded list, but exclude portfolio symbols
                if portfolio_symbols:
                    placeholders = ','.join(['%s'] * len(portfolio_symbols))
                    cursor.execute(f"""
                        DELETE FROM stocks
                        WHERE symbol IN (
                            SELECT symbol FROM stocks_excluded
                        )
                        AND symbol NOT IN ({placeholders})
                    """, list(portfolio_symbols))
                else:
                    # If no portfolio symbols, use original query
                    cursor.execute("""
                        DELETE FROM stocks
                        WHERE symbol IN (
                            SELECT symbol FROM stocks_excluded
                        )
                    """)

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"🧹 Removed {deleted_count} stale symbols from stocks table (protected {len(portfolio_symbols)} portfolio symbols)")
                return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up stale stocks: {e}")
        return 0

# FMP Data Source Functions
def fetch_fmp_all_symbols(excluded_symbols=None):
    """Fetch all available symbols from FMP."""
    logger.info("🔍 Fetching all symbols from FMP...")

    if excluded_symbols is None:
        excluded_symbols = set()

    try:
        # Get stock list
        stock_url = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={FMP_API_KEY}"
        response = requests.get(stock_url, timeout=30)

        if response.status_code == 200:
            stocks = response.json()
            logger.info(f"✅ Found {len(stocks)} stocks from FMP")

            # Get ETF list
            etf_url = f"https://financialmodelingprep.com/api/v3/etf/list?apikey={FMP_API_KEY}"
            etf_response = requests.get(etf_url, timeout=30)

            if etf_response.status_code == 200:
                etfs = etf_response.json()
                logger.info(f"✅ Found {len(etfs)} ETFs from FMP")

                # Additional endpoints for more symbol discovery
                additional_stocks = []

                # Get available traded symbols
                try:
                    traded_url = f"https://financialmodelingprep.com/api/v3/available-traded/list?apikey={FMP_API_KEY}"
                    traded_response = requests.get(traded_url, timeout=30)
                    if traded_response.status_code == 200:
                        traded = traded_response.json()
                        logger.info(f"✅ Found {len(traded)} traded symbols from FMP")
                        additional_stocks.extend(traded)
                except Exception as e:
                    logger.debug(f"Could not fetch traded symbols: {e}")

                # Get symbols with financial statements (quality companies)
                try:
                    financial_url = f"https://financialmodelingprep.com/api/v3/financial-statement-symbol-lists?apikey={FMP_API_KEY}"
                    financial_response = requests.get(financial_url, timeout=30)
                    if financial_response.status_code == 200:
                        financial = financial_response.json()
                        logger.info(f"✅ Found {len(financial)} symbols with financials from FMP")
                        # Convert to dict format
                        for symbol in financial[:1000]:  # Limit to avoid overwhelming
                            additional_stocks.append({'symbol': symbol, 'price': 0})
                except Exception as e:
                    logger.debug(f"Could not fetch financial symbols: {e}")

                # Get dividend calendar symbols (guaranteed dividend payers)
                try:
                    dividend_url = f"https://financialmodelingprep.com/api/v3/stock_dividend_calendar?apikey={FMP_API_KEY}"
                    dividend_response = requests.get(dividend_url, timeout=30)
                    if dividend_response.status_code == 200:
                        dividends = dividend_response.json()
                        logger.info(f"✅ Found {len(dividends)} dividend-paying symbols from FMP")
                        for div in dividends[:500]:  # Recent dividend payers
                            if 'symbol' in div:
                                additional_stocks.append({'symbol': div['symbol'], 'price': 0})
                except Exception as e:
                    logger.debug(f"Could not fetch dividend symbols: {e}")

                # Get IPO calendar symbols (new listings)
                try:
                    ipo_url = f"https://financialmodelingprep.com/api/v3/ipo_calendar?apikey={FMP_API_KEY}"
                    ipo_response = requests.get(ipo_url, timeout=30)
                    if ipo_response.status_code == 200:
                        ipos = ipo_response.json()
                        logger.info(f"✅ Found {len(ipos)} IPO symbols from FMP")
                        for ipo in ipos[:200]:  # Recent IPOs
                            if 'symbol' in ipo:
                                additional_stocks.append({'symbol': ipo['symbol'], 'price': ipo.get('priceRange', 0)})
                except Exception as e:
                    logger.debug(f"Could not fetch IPO symbols: {e}")

                # Get earnings calendar symbols (active companies)
                try:
                    earnings_url = f"https://financialmodelingprep.com/api/v3/earnings_calendar?apikey={FMP_API_KEY}"
                    earnings_response = requests.get(earnings_url, timeout=30)
                    if earnings_response.status_code == 200:
                        earnings = earnings_response.json()
                        logger.info(f"✅ Found {len(earnings)} earnings symbols from FMP")
                        for earning in earnings[:500]:  # Companies with earnings
                            if 'symbol' in earning:
                                additional_stocks.append({'symbol': earning['symbol'], 'price': 0})
                except Exception as e:
                    logger.debug(f"Could not fetch earnings symbols: {e}")

                # Get institutional holdings symbols
                try:
                    institutional_url = f"https://financialmodelingprep.com/api/v3/institutional-holder/symbol-ownership?apikey={FMP_API_KEY}"
                    inst_response = requests.get(institutional_url, timeout=30)
                    if inst_response.status_code == 200:
                        institutions = inst_response.json()
                        logger.info(f"✅ Found {len(institutions)} institutional holding symbols from FMP")
                        for inst in institutions[:500]:
                            if 'symbol' in inst:
                                additional_stocks.append({'symbol': inst['symbol'], 'price': 0})
                except Exception as e:
                    logger.debug(f"Could not fetch institutional symbols: {e}")

                # Get symbols from screener (high dividend yield stocks)
                try:
                    screener_url = f"https://financialmodelingprep.com/api/v3/stock-screener?dividendMoreThan=0&apikey={FMP_API_KEY}&limit=1000"
                    screener_response = requests.get(screener_url, timeout=30)
                    if screener_response.status_code == 200:
                        screened = screener_response.json()
                        logger.info(f"✅ Found {len(screened)} dividend stocks from screener")
                        for stock in screened:
                            if 'symbol' in stock:
                                additional_stocks.append({'symbol': stock['symbol'], 'price': stock.get('price', 0)})
                except Exception as e:
                    logger.debug(f"Could not fetch screener symbols: {e}")

                # Get sector performers (to catch sector-specific dividend stocks)
                sectors = ['REIT', 'Utilities', 'Financial Services', 'Energy', 'Consumer Defensive']
                for sector in sectors:
                    try:
                        sector_url = f"https://financialmodelingprep.com/api/v3/stock-screener?sector={sector}&apikey={FMP_API_KEY}&limit=500"
                        sector_response = requests.get(sector_url, timeout=15)
                        if sector_response.status_code == 200:
                            sector_stocks = sector_response.json()
                            logger.info(f"✅ Found {len(sector_stocks)} stocks in {sector} sector")
                            for stock in sector_stocks[:200]:  # Limit per sector
                                if 'symbol' in stock:
                                    additional_stocks.append({'symbol': stock['symbol'], 'price': stock.get('price', 0)})
                    except Exception as e:
                        logger.debug(f"Could not fetch {sector} sector symbols: {e}")

                # Get most active stocks
                try:
                    active_url = f"https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={FMP_API_KEY}"
                    active_response = requests.get(active_url, timeout=30)
                    if active_response.status_code == 200:
                        actives = active_response.json()
                        logger.info(f"✅ Found {len(actives)} most active symbols")
                        for active in actives:
                            if 'symbol' in active:
                                additional_stocks.append({'symbol': active['symbol'], 'price': active.get('price', 0)})
                except Exception as e:
                    logger.debug(f"Could not fetch most active symbols: {e}")

                # Get gainers and losers (active trading symbols)
                try:
                    gainers_url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={FMP_API_KEY}"
                    gainers_response = requests.get(gainers_url, timeout=30)
                    if gainers_response.status_code == 200:
                        gainers = gainers_response.json()
                        logger.info(f"✅ Found {len(gainers)} gainer symbols")
                        for gainer in gainers:
                            if 'symbol' in gainer:
                                additional_stocks.append({'symbol': gainer['symbol'], 'price': gainer.get('price', 0)})
                except Exception as e:
                    logger.debug(f"Could not fetch gainer symbols: {e}")

                # Combine all sources
                all_items = stocks + etfs + additional_stocks

                # Deduplicate by symbol
                seen_symbols = set()
                unique_items = []
                for item in all_items:
                    if item.get('symbol') and item['symbol'] not in seen_symbols:
                        seen_symbols.add(item['symbol'])
                        unique_items.append(item)

                logger.info(f"Total unique symbols from FMP: {len(unique_items)}")

                # Filter and format
                all_symbols = []
                filtered_count = 0
                excluded_count = 0

                for item in unique_items:
                    # Skip if no symbol or price too low
                    if not item.get('symbol') or not item.get('price'):
                        continue

                    symbol = item['symbol']

                    # Skip if symbol is in excluded list
                    if symbol in excluded_symbols:
                        excluded_count += 1
                        continue

                    try:
                        price = float(item.get('price', 0))
                    except (ValueError, TypeError):
                        continue

                    if price <= MIN_PRICE:
                        continue

                    # Check exchange filter
                    exchange = item.get('exchange', '')
                    if exchange:
                        exchange = exchange.upper()
                        if exchange not in ALLOWED_EXCHANGES:
                            filtered_count += 1
                            continue

                    # Check if it's a mutual fund (exclude)
                    item_type = item.get('type', '').lower()
                    name = item.get('name', '').lower()

                    if any(excluded in item_type for excluded in EXCLUDED_TYPES):
                        filtered_count += 1
                        continue

                    if any(excluded in name for excluded in ['mutual fund', 'fund of funds']):
                        filtered_count += 1
                        continue

                    all_symbols.append({
                        'symbol': item['symbol'],
                        'name': item.get('name', ''),
                        'exchange_name': exchange,
                        'type': 'etf' if item in etfs else 'stock',
                        'price': price,
                        'volume': item.get('volume', 0)
                    })

                logger.info(f"✅ Kept {len(all_symbols)} symbols after filtering (filtered out {filtered_count}, excluded {excluded_count})")
                return all_symbols

    except Exception as e:
        logger.error(f"Error fetching FMP symbols: {e}")

    return []

def validate_fmp_symbol(symbol):
    """Validate if a symbol has recent data from FMP."""
    with fmp_limiter:
        try:
            # Get recent price data
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'historical' in data and data['historical']:
                    latest_date = datetime.strptime(data['historical'][0]['date'], '%Y-%m-%d')
                    days_old = (datetime.now() - latest_date).days

                    if days_old <= RECENT_DATA_DAYS:
                        return True, None
                    else:
                        return False, f"Data is {days_old} days old"

        except Exception as e:
            logger.debug(f"Error validating {symbol} with FMP: {e}")

    return False, "No recent data"

# Alpha Vantage Data Source Functions
def fetch_alpha_vantage_symbols():
    """Fetch symbols from Alpha Vantage."""
    logger.info("🔍 Fetching symbols from Alpha Vantage...")

    try:
        # Alpha Vantage doesn't have a direct symbol list endpoint
        # We'll use their search endpoint for common tickers
        # In practice, you might want to maintain a list of symbols to check

        # For now, we'll return empty and rely on other sources
        # You could implement a more sophisticated approach here
        logger.info("⚠️ Alpha Vantage requires specific symbol queries")
        return []

    except Exception as e:
        logger.error(f"Error with Alpha Vantage: {e}")
        return []

def validate_alpha_vantage_symbol(symbol):
    """Validate if a symbol has recent data from Alpha Vantage."""
    if not ALPHA_VANTAGE_API_KEY:
        return False, "No API key"

    with av_limiter:
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY,
                'outputsize': 'compact'
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if 'Time Series (Daily)' in data:
                    dates = list(data['Time Series (Daily)'].keys())
                    if dates:
                        latest_date = datetime.strptime(dates[0], '%Y-%m-%d')
                        days_old = (datetime.now() - latest_date).days

                        if days_old <= RECENT_DATA_DAYS:
                            return True, None
                        else:
                            return False, f"Data is {days_old} days old"

        except Exception as e:
            logger.debug(f"Error validating {symbol} with Alpha Vantage: {e}")

    return False, "No recent data"

# Yahoo Finance Data Source Functions
def fetch_yahoo_symbols(excluded_symbols=None):
    """Fetch popular symbols from Yahoo Finance screener."""
    logger.info("🔍 Fetching symbols from Yahoo Finance...")

    if excluded_symbols is None:
        excluded_symbols = set()

    try:
        # Yahoo doesn't provide a full symbol list API
        # We'll use multiple sources to get comprehensive coverage
        symbols = []

        # Get S&P 500 symbols
        try:
            sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(sp500_url)
            sp500_symbols = tables[0]['Symbol'].tolist()

            for symbol in sp500_symbols:
                symbols.append({
                    'symbol': symbol,
                    'name': '',
                    'type': 'stock',
                    'exchange_name': 'US',
                    'price': 0,
                    'volume': 0
                })

            logger.info(f"✅ Found {len(symbols)} S&P 500 symbols from Yahoo Finance")
        except Exception as e:
            logger.warning(f"Could not fetch S&P 500 list: {e}")

        # Get Russell 2000 symbols (small cap)
        try:
            russell_url = "https://en.wikipedia.org/wiki/Russell_2000_Index"
            tables = pd.read_html(russell_url)
            if tables and len(tables) > 0:
                russell_symbols = tables[0]['Symbol'].tolist() if 'Symbol' in tables[0].columns else []
                for symbol in russell_symbols[:500]:  # Limit to avoid too many
                    symbols.append({
                        'symbol': symbol,
                        'name': '',
                        'type': 'stock',
                        'exchange_name': 'US',
                        'price': 0,
                        'volume': 0
                    })
                logger.info(f"✅ Found {len(russell_symbols)} Russell 2000 symbols")
        except Exception as e:
            logger.debug(f"Could not fetch Russell 2000 list: {e}")

        # Get FTSE 100 symbols (LSE)
        try:
            ftse_url = "https://en.wikipedia.org/wiki/FTSE_100_Index"
            tables = pd.read_html(ftse_url)
            if tables and len(tables) > 0:
                ftse_symbols = tables[0]['Ticker'].tolist() if 'Ticker' in tables[0].columns else []
                for symbol in ftse_symbols:
                    # Add .L suffix for LSE symbols
                    symbols.append({
                        'symbol': f"{symbol}.L",
                        'name': '',
                        'type': 'stock',
                        'exchange_name': 'LSE',
                        'price': 0,
                        'volume': 0
                    })
                logger.info(f"✅ Found {len(ftse_symbols)} FTSE 100 symbols")
        except Exception as e:
            logger.debug(f"Could not fetch FTSE 100 list: {e}")

        # Get ASX 200 symbols (Australia)
        try:
            asx_url = "https://en.wikipedia.org/wiki/S%26P/ASX_200"
            tables = pd.read_html(asx_url)
            if tables and len(tables) > 0:
                asx_symbols = tables[0]['Code'].tolist() if 'Code' in tables[0].columns else []
                for symbol in asx_symbols:
                    # Add .AX suffix for ASX symbols
                    symbols.append({
                        'symbol': f"{symbol}.AX",
                        'name': '',
                        'type': 'stock',
                        'exchange_name': 'ASX',
                        'price': 0,
                        'volume': 0
                    })
                logger.info(f"✅ Found {len(asx_symbols)} ASX 200 symbols")
        except Exception as e:
            logger.debug(f"Could not fetch ASX 200 list: {e}")

        # Get TSX Composite symbols (Canada)
        try:
            tsx_url = "https://en.wikipedia.org/wiki/S%26P/TSX_Composite_Index"
            tables = pd.read_html(tsx_url)
            if tables and len(tables) > 0:
                tsx_symbols = tables[0]['Symbol'].tolist() if 'Symbol' in tables[0].columns else []
                for symbol in tsx_symbols:
                    # Add .TO suffix for TSX symbols
                    symbols.append({
                        'symbol': f"{symbol}.TO",
                        'name': '',
                        'type': 'stock',
                        'exchange_name': 'TSX',
                        'price': 0,
                        'volume': 0
                    })
                logger.info(f"✅ Found {len(tsx_symbols)} TSX Composite symbols")
        except Exception as e:
            logger.debug(f"Could not fetch TSX Composite list: {e}")

        # Get high dividend ETFs
        dividend_etfs = ['VYM', 'HDV', 'SCHD', 'DVY', 'SDY', 'VIG', 'NOBL', 'DGRO', 'DGRW', 'SPHD',
                        'SPYD', 'FDL', 'FVD', 'VTI', 'VOO', 'SPY', 'IVV', 'QQQ', 'DIA', 'IWM']
        for etf in dividend_etfs:
            symbols.append({
                'symbol': etf,
                'name': '',
                'type': 'etf',
                'exchange_name': 'US',
                'price': 0,
                'volume': 0
            })
        logger.info(f"✅ Added {len(dividend_etfs)} high dividend ETFs")

        # Deduplicate symbols and filter excluded
        seen = set()
        unique_symbols = []
        excluded_count = 0
        for sym in symbols:
            if sym['symbol'] in excluded_symbols:
                excluded_count += 1
                continue
            if sym['symbol'] not in seen:
                seen.add(sym['symbol'])
                unique_symbols.append(sym)

        logger.info(f"Total unique Yahoo symbols: {len(unique_symbols)}")
        return unique_symbols

    except Exception as e:
        logger.error(f"Error fetching Yahoo symbols: {e}")
        return []

def validate_yahoo_symbol(symbol):
    """Validate if a symbol has recent data from Yahoo Finance."""
    with yahoo_limiter:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")

            if not hist.empty:
                latest_date = hist.index[-1].to_pydatetime()
                days_old = (datetime.now() - latest_date).days

                if days_old <= RECENT_DATA_DAYS:
                    # Get additional info
                    info = ticker.info
                    return True, {
                        'name': info.get('longName', ''),
                        'exchange': info.get('exchange', ''),
                        'price': info.get('currentPrice', hist['Close'].iloc[-1]),
                        'volume': info.get('volume', hist['Volume'].iloc[-1])
                    }
                else:
                    return False, f"Data is {days_old} days old"

        except Exception as e:
            logger.debug(f"Error validating {symbol} with Yahoo: {e}")

    return False, "No recent data"

# NASDAQ Data Source Functions
def fetch_nasdaq_symbols(excluded_symbols=None):
    """Fetch symbols from NASDAQ."""
    logger.info("🔍 Fetching symbols from NASDAQ...")

    if excluded_symbols is None:
        excluded_symbols = set()

    try:
        # Download NASDAQ traded symbols file
        url = "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25000&offset=0"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            data = response.json()

            if 'data' in data and 'table' in data['data'] and 'rows' in data['data']['table']:
                rows = data['data']['table']['rows']
                symbols = []
                filtered_count = 0
                excluded_count = 0

                for row in rows:
                    if not row.get('symbol'):
                        continue

                    # Skip if symbol is in excluded list
                    if row['symbol'] in excluded_symbols:
                        excluded_count += 1
                        continue

                    # Check exchange filter
                    exchange = row.get('exchange', 'NASDAQ').upper()
                    if exchange not in ALLOWED_EXCHANGES:
                        filtered_count += 1
                        continue

                    # Parse price and volume
                    try:
                        price_str = row.get('lastsale', '0').replace('$', '').replace(',', '')
                        price = float(price_str) if price_str else 0

                        if price <= MIN_PRICE:
                            continue

                        volume_str = row.get('volume', '0').replace(',', '')
                        volume = int(volume_str) if volume_str else 0
                    except (ValueError, TypeError):
                        continue

                    # Check if it's a mutual fund (exclude)
                    name = row.get('name', '').lower()
                    if any(excluded in name for excluded in ['mutual fund', 'fund of funds']):
                        filtered_count += 1
                        continue

                    symbols.append({
                        'symbol': row['symbol'],
                        'name': row.get('name', ''),
                        'exchange_name': exchange,
                        'type': 'stock',
                        'price': price,
                        'volume': volume
                    })

                logger.info(f"✅ Found {len(symbols)} symbols from NASDAQ after filtering (filtered out {filtered_count}, excluded {excluded_count})")
                return symbols

    except Exception as e:
        logger.error(f"Error fetching NASDAQ symbols: {e}")

    return []

def process_symbol_validation(symbol, source_priority=['fmp', 'alpha_vantage', 'yahoo']):
    """Validate a symbol across multiple sources."""

    for source in source_priority:
        if source == 'fmp':
            valid, reason = validate_fmp_symbol(symbol)
            if valid:
                return True, source, None

        elif source == 'alpha_vantage' and ALPHA_VANTAGE_API_KEY:
            valid, reason = validate_alpha_vantage_symbol(symbol)
            if valid:
                return True, source, None

        elif source == 'yahoo':
            valid, info = validate_yahoo_symbol(symbol)
            if valid:
                return True, source, info

    return False, None, "No recent data from any source"

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Starting Comprehensive Stock Update Process")
    logger.info("=" * 80)

    # Test database connection
    if not test_postgres_connection():
        logger.error("Cannot proceed without database connection")
        return

    # First, remove any portfolio symbols from exclusions to override exclusion rules
    remove_portfolio_symbols_from_exclusions()

    # Get excluded symbols (after removing portfolio symbols)
    excluded_symbols = get_excluded_symbols()

    # Get portfolio symbols to override exclusions during filtering
    portfolio_symbols = get_portfolio_symbols()

    # Create effective excluded set (excluded symbols minus portfolio symbols)
    effective_excluded = excluded_symbols - portfolio_symbols

    if len(excluded_symbols) != len(effective_excluded):
        logger.info(f"🔄 Portfolio override: {len(excluded_symbols) - len(effective_excluded)} portfolio symbols will bypass exclusions")

    # Get existing symbols
    existing_symbols = get_existing_symbols()
    logger.info(f"📊 Found {len(existing_symbols)} existing symbols in database")

    all_symbols = {}

    # Phase 1: Fetch from FMP
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 1: FMP Data Collection")
    logger.info("=" * 50)

    fmp_symbols = fetch_fmp_all_symbols(effective_excluded)
    for sym in fmp_symbols:
        all_symbols[sym['symbol']] = sym

    # Phase 2: Fetch from NASDAQ
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 2: NASDAQ Data Collection")
    logger.info("=" * 50)

    nasdaq_symbols = fetch_nasdaq_symbols(effective_excluded)
    for sym in nasdaq_symbols:
        if sym['symbol'] not in all_symbols:
            all_symbols[sym['symbol']] = sym

    # Phase 3: Fetch from Yahoo (S&P 500 as sample)
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 3: Yahoo Finance Data Collection")
    logger.info("=" * 50)

    yahoo_symbols = fetch_yahoo_symbols(effective_excluded)
    for sym in yahoo_symbols:
        if sym.get('symbol') and sym['symbol'] not in all_symbols:
            all_symbols[sym['symbol']] = sym

    logger.info(f"\n📊 Total unique symbols collected: {len(all_symbols)}")

    # Phase 4: Validate symbols for recent data
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 4: Symbol Validation")
    logger.info("=" * 50)

    validated_symbols = []
    excluded_count = 0

    # Process in batches
    symbol_list = list(all_symbols.keys())
    total_batches = (len(symbol_list) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num in range(0, len(symbol_list), BATCH_SIZE):
        batch = symbol_list[batch_num:batch_num + BATCH_SIZE]
        current_batch = (batch_num // BATCH_SIZE) + 1

        logger.info(f"\n📦 Processing batch {current_batch}/{total_batches} ({len(batch)} symbols)")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}

            for symbol in batch:
                future = executor.submit(process_symbol_validation, symbol)
                futures[future] = symbol

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    valid, source, info = future.result(timeout=30)

                    if valid:
                        symbol_data = all_symbols[symbol].copy()

                        # Update with fresh info if available
                        if info and isinstance(info, dict):
                            symbol_data.update(info)

                        symbol_data['last_updated'] = datetime.now()
                        validated_symbols.append(symbol_data)

                        logger.info(f"✅ {symbol}: Valid (source: {source})")
                    else:
                        add_to_excluded(symbol, info or "No recent data")
                        excluded_count += 1
                        logger.debug(f"❌ {symbol}: Excluded - {info}")

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    add_to_excluded(symbol, str(e))
                    excluded_count += 1

        # Save validated symbols in batches
        if validated_symbols and len(validated_symbols) >= BATCH_SIZE:
            saved = save_symbols_batch(validated_symbols)
            validated_symbols = []

    # Save remaining symbols
    if validated_symbols:
        saved = save_symbols_batch(validated_symbols)

    # Phase 5: Cleanup stale stocks
    logger.info("\n" + "=" * 50)
    logger.info("PHASE 5: Cleanup Stale Stocks")
    logger.info("=" * 50)

    deleted_count = cleanup_stale_stocks()

    # Final statistics
    logger.info("\n" + "=" * 80)
    logger.info("PROCESS COMPLETE")
    logger.info("=" * 80)

    with get_postgres_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM stocks")
            total_stocks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) as count FROM stocks_excluded")
            total_excluded = cursor.fetchone()[0]

    logger.info(f"✅ Total symbols in database: {total_stocks}")
    logger.info(f"❌ Total excluded symbols: {total_excluded}")
    logger.info(f"🧹 Removed {deleted_count} stale symbols")
    logger.info(f"📊 Success rate: {(total_stocks / (total_stocks + total_excluded) * 100):.1f}%")

if __name__ == "__main__":
    main()