#!/usr/bin/env python3
"""
Fetch historical prices and dividends for all stocks in the database.

This script fetches comprehensive historical data for all symbols in the stocks table:
- Historical prices (daily)
- Dividend history
- Uses FMP as primary source with fallback to Yahoo Finance
"""

import os
import sys
import logging
import requests
import yfinance as yf
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from dotenv import load_dotenv
from decimal import Decimal
import warnings

# Suppress yfinance warnings and errors
warnings.filterwarnings("ignore", category=FutureWarning)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fetch_prices_dividends.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Reduce yfinance logging level to suppress its ERROR messages
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# API Configuration
FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')

# Rate limiters
fmp_limiter = Semaphore(10)    # FMP can handle more concurrent requests
yahoo_limiter = Semaphore(25)   # Yahoo is more lenient
alpha_limiter = Semaphore(75)   # Premium Alpha Vantage allows 75 requests/minute

# Configuration
BATCH_SIZE = 50
MAX_WORKERS = 20
PRICES_START_DATE = "2020-01-01"  # Get 5 years of price data
DIVIDENDS_START_DATE = "2015-01-01"  # Get 10 years of dividend data

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

def create_tables_if_not_exist():
    """Create prices and dividends tables if they don't exist."""
    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Create prices table if it doesn't exist (DO NOT DROP)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS stock_prices (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(20) NOT NULL,
                        date DATE NOT NULL,
                        open DECIMAL(12,4),
                        high DECIMAL(12,4),
                        low DECIMAL(12,4),
                        close DECIMAL(12,4),
                        volume BIGINT,
                        adjusted_close DECIMAL(12,4),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, date)
                    );
                    CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol ON stock_prices(symbol);
                    CREATE INDEX IF NOT EXISTS idx_stock_prices_date ON stock_prices(date);
                """)

                # No need to create stock_dividends table - we only use dividend_history
                # The dividend_history table should already exist in the database

                conn.commit()
                logger.info("✅ Database tables ready")
                return True

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

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

def add_to_excluded(symbol, reason):
    """Add a symbol to the excluded table and remove from raw_stocks table, but protect portfolio symbols."""
    try:
        # Check if symbol is in any portfolio - if so, don't exclude it
        portfolio_symbols = get_portfolio_symbols()
        if symbol.upper() in portfolio_symbols:
            logger.info(f"🛡️ Protected portfolio symbol {symbol} from exclusion (reason would have been: {reason})")
            return

        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Add to excluded list
                cursor.execute(
                    """INSERT INTO stocks_excluded (symbol, reason, excluded_at)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (symbol) DO UPDATE SET
                           reason = EXCLUDED.reason,
                           excluded_at = EXCLUDED.excluded_at""",
                    (symbol, reason, datetime.now())
                )

                # Remove from raw_stocks table
                cursor.execute("DELETE FROM raw_stocks WHERE symbol = %s", (symbol,))

                conn.commit()
                logger.debug(f"Added {symbol} to excluded list and removed from raw_stocks: {reason}")
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

def get_all_symbols():
    """Get all symbols from the stocks table, excluding those in stocks_excluded, but including portfolio symbols."""
    try:
        # First, remove any portfolio symbols from exclusions to override exclusion rules
        remove_portfolio_symbols_from_exclusions()

        portfolio_symbols = get_portfolio_symbols()

        with get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if portfolio_symbols:
                    # Get symbols that are NOT in excluded list OR are portfolio symbols
                    placeholders = ','.join(['%s'] * len(portfolio_symbols))
                    cursor.execute(f"""
                        SELECT symbol FROM raw_stocks
                        WHERE (
                            symbol NOT IN (
                                SELECT symbol FROM stocks_excluded
                            )
                            OR symbol IN ({placeholders})
                        )
                        ORDER BY symbol
                    """, list(portfolio_symbols))
                else:
                    # No portfolio symbols, use original query
                    cursor.execute("""
                        SELECT symbol FROM raw_stocks
                        WHERE symbol NOT IN (
                            SELECT symbol FROM stocks_excluded
                        )
                        ORDER BY symbol
                    """)

                results = cursor.fetchall()
                symbols = [row['symbol'] for row in results]

                # Count portfolio symbols that were included despite being in exclusions
                if portfolio_symbols:
                    portfolio_count = len([s for s in symbols if s.upper() in portfolio_symbols])
                    if portfolio_count > 0:
                        logger.info(f"📊 Found {len(symbols)} active symbols (including {portfolio_count} portfolio symbols that override exclusions)")
                    else:
                        logger.info(f"📊 Found {len(symbols)} active symbols (excluded ones filtered out)")
                else:
                    logger.info(f"📊 Found {len(symbols)} active symbols (excluded ones filtered out)")

                return symbols
    except Exception as e:
        logger.error(f"Error fetching symbols: {e}")
        return []

def get_latest_dates(symbol):
    """Get the latest price and dividend dates for a symbol from the database."""
    try:
        with get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get latest price date
                cursor.execute("""
                    SELECT MAX(date) as latest_price_date
                    FROM raw_stock_prices
                    WHERE symbol = %s
                """, (symbol,))
                price_result = cursor.fetchone()

                # Get latest dividend date
                cursor.execute("""
                    SELECT MAX(ex_date) as latest_dividend_date
                    FROM stock_dividends
                    WHERE symbol = %s
                """, (symbol,))
                div_result = cursor.fetchone()

                latest_price_date = price_result['latest_price_date'] if price_result and price_result['latest_price_date'] else None
                latest_div_date = div_result['latest_dividend_date'] if div_result and div_result['latest_dividend_date'] else None

                return latest_price_date, latest_div_date
    except Exception as e:
        logger.debug(f"Error getting latest dates for {symbol}: {e}")
        return None, None

def fetch_fmp_prices(symbol, start_date=None):
    """Fetch historical prices from FMP."""
    with fmp_limiter:
        try:
            # Use provided start date or default to PRICES_START_DATE
            from_date = start_date if start_date else PRICES_START_DATE

            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
            params = {
                'apikey': FMP_API_KEY,
                'from': from_date
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'historical' in data and data['historical']:
                    prices = []
                    for item in data['historical']:
                        prices.append({
                            'symbol': symbol,
                            'date': item['date'],
                            'open': item.get('open'),
                            'high': item.get('high'),
                            'low': item.get('low'),
                            'close': item.get('close'),
                            'volume': item.get('volume'),
                            'adjusted_close': item.get('adjClose', item.get('close'))
                        })
                    if prices:  # Only return if we have data
                        return prices, 'fmp'
                    else:
                        logger.debug(f"{symbol}: No new prices from FMP after {start_date}")

        except Exception as e:
            logger.debug(f"Error fetching FMP prices for {symbol}: {e}")

    return None, None

def fetch_yahoo_prices(symbol, start_date=None):
    """Fetch historical prices from Yahoo Finance."""
    with yahoo_limiter:
        try:
            # Use provided start date or default to PRICES_START_DATE
            from_date = start_date if start_date else PRICES_START_DATE

            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=from_date)

            if not hist.empty:
                prices = []
                for date, row in hist.iterrows():
                    date_str = date.strftime('%Y-%m-%d')
                    # Only include if the date is actually newer than start_date
                    if date_str >= from_date:
                        prices.append({
                            'symbol': symbol,
                            'date': date_str,
                            'open': row['Open'],
                            'high': row['High'],
                            'low': row['Low'],
                            'close': row['Close'],
                            'volume': row['Volume'],
                            'adjusted_close': row['Close']
                        })
                if prices:  # Only return if we have genuinely new data
                    return prices, 'yahoo'
                else:
                    logger.debug(f"{symbol}: Yahoo returned old data, no updates after {from_date}")
            else:
                # Only log as possibly delisted if we're looking for historical data (not just today's update)
                from datetime import datetime
                start_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
                days_diff = (datetime.now() - start_date_obj).days

                if days_diff > 7:
                    logger.debug(f"{symbol}: No data found for {days_diff} days, possibly delisted")
                else:
                    logger.debug(f"{symbol}: No new data available (checking from {from_date})")

        except Exception as e:
            logger.debug(f"Error fetching Yahoo prices for {symbol}: {e}")

    return None, None

def fetch_alpha_vantage_prices(symbol, start_date=None):
    """Fetch historical prices from Alpha Vantage."""
    with alpha_limiter:
        try:
            # Use provided start date or default to PRICES_START_DATE
            from_date = start_date if start_date else PRICES_START_DATE

            # Alpha Vantage TIME_SERIES_DAILY_ADJUSTED endpoint
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY,
                'outputsize': 'full'  # Get full historical data
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Check for error messages
                if 'Error Message' in data or 'Note' in data:
                    logger.debug(f"Alpha Vantage API issue for {symbol}: {data.get('Error Message', data.get('Note'))}")
                    return None, None

                if 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']
                    prices = []

                    for date_str, values in time_series.items():
                        # Filter by start date
                        if date_str >= from_date:
                            prices.append({
                                'symbol': symbol,
                                'date': date_str,
                                'open': float(values.get('1. open', 0)),
                                'high': float(values.get('2. high', 0)),
                                'low': float(values.get('3. low', 0)),
                                'close': float(values.get('4. close', 0)),
                                'volume': int(values.get('6. volume', 0)),
                                'adjusted_close': float(values.get('5. adjusted close', values.get('4. close', 0)))
                            })

                    if prices:
                        # Sort by date ascending
                        prices.sort(key=lambda x: x['date'])
                        return prices, 'alpha_vantage'
                    else:
                        logger.debug(f"{symbol}: No new prices from Alpha Vantage after {start_date}")

        except Exception as e:
            logger.debug(f"Error fetching Alpha Vantage prices for {symbol}: {e}")

    return None, None

def fetch_alpha_vantage_dividends(symbol, start_date=None):
    """Fetch dividend history from Alpha Vantage."""
    with alpha_limiter:
        try:
            # Use provided start date or default to DIVIDENDS_START_DATE
            from_date = start_date if start_date else DIVIDENDS_START_DATE

            # Alpha Vantage doesn't have a dedicated dividend endpoint
            # We need to use the adjusted close data to infer dividends
            # For now, we'll return None and rely on other sources for dividends

            # Alternative: Use the TIME_SERIES_MONTHLY_ADJUSTED which includes dividend data
            url = 'https://www.alphavantage.co/query'
            params = {
                'function': 'TIME_SERIES_MONTHLY_ADJUSTED',
                'symbol': symbol,
                'apikey': ALPHA_VANTAGE_API_KEY
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if 'Monthly Adjusted Time Series' in data:
                    time_series = data['Monthly Adjusted Time Series']
                    dividends = []

                    for date_str, values in time_series.items():
                        dividend_amount = float(values.get('7. dividend amount', 0))

                        # Only include if there's a dividend and it's after start date
                        if dividend_amount > 0 and date_str >= from_date:
                            dividends.append({
                                'symbol': symbol,
                                'ex_date': date_str,
                                'payment_date': None,
                                'record_date': None,
                                'declaration_date': None,
                                'amount': dividend_amount,
                                'currency': 'USD',
                                'frequency': 'Unknown'
                            })

                    if dividends:
                        # Sort by date ascending
                        dividends.sort(key=lambda x: x['ex_date'])
                        return dividends, 'alpha_vantage'

        except Exception as e:
            logger.debug(f"Error fetching Alpha Vantage dividends for {symbol}: {e}")

    return None, None

def fetch_fmp_dividends(symbol, start_date=None):
    """Fetch dividend history from FMP."""
    with fmp_limiter:
        try:
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{symbol}"
            params = {'apikey': FMP_API_KEY}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'historical' in data and data['historical']:
                    # Use provided start date or default to DIVIDENDS_START_DATE
                    from_date = start_date if start_date else DIVIDENDS_START_DATE

                    dividends = []
                    for item in data['historical']:
                        # Filter by date
                        if item.get('date') and item['date'] >= from_date:
                            dividends.append({
                                'symbol': symbol,
                                'ex_date': item['date'],
                                'payment_date': item.get('paymentDate'),
                                'record_date': item.get('recordDate'),
                                'declaration_date': item.get('declarationDate'),
                                'amount': item.get('dividend', 0),
                                'currency': 'USD',
                                'frequency': item.get('frequency', 'Quarterly')
                            })
                    return dividends, 'fmp'

        except Exception as e:
            logger.debug(f"Error fetching FMP dividends for {symbol}: {e}")

    return None, None

def fetch_yahoo_dividends(symbol, start_date=None):
    """Fetch dividend history from Yahoo Finance."""
    with yahoo_limiter:
        try:
            # Use provided start date or default to DIVIDENDS_START_DATE
            from_date = start_date if start_date else DIVIDENDS_START_DATE

            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends

            if not dividends.empty:
                # Filter by date
                dividends = dividends[dividends.index >= from_date]

                if not dividends.empty:
                    divs = []
                    for date, amount in dividends.items():
                        divs.append({
                            'symbol': symbol,
                            'ex_date': date.strftime('%Y-%m-%d'),
                            'payment_date': None,
                            'record_date': None,
                            'declaration_date': None,
                            'amount': float(amount),
                            'currency': 'USD',
                            'frequency': 'Unknown'
                        })
                    return divs, 'yahoo'

        except Exception as e:
            logger.debug(f"Error fetching Yahoo dividends for {symbol}: {e}")

    return None, None

def save_prices_batch(prices_data):
    """Save a batch of price data to the database."""
    if not prices_data:
        return 0

    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare data for insertion
                insert_data = []
                for price in prices_data:
                    # Convert numpy types to Python native types
                    insert_data.append((
                        price['symbol'],
                        price['date'],
                        float(price.get('open')) if price.get('open') is not None else None,
                        float(price.get('high')) if price.get('high') is not None else None,
                        float(price.get('low')) if price.get('low') is not None else None,
                        float(price.get('close')) if price.get('close') is not None else None,
                        int(price.get('volume')) if price.get('volume') is not None else None,
                        float(price.get('adjusted_close')) if price.get('adjusted_close') is not None else None
                    ))

                # Use ON CONFLICT to handle duplicates
                query = """
                    INSERT INTO stock_prices (symbol, date, open, high, low, close, volume, adjusted_close)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, date) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        adjusted_close = EXCLUDED.adjusted_close
                """

                execute_batch(cursor, query, insert_data, page_size=100)
                conn.commit()

                return len(insert_data)

    except Exception as e:
        logger.error(f"Error saving prices batch: {e}")
        return 0

def save_dividends_batch(dividends_data):
    """Save a batch of dividend data to the database."""
    if not dividends_data:
        return 0

    try:
        with get_postgres_connection() as conn:
            with conn.cursor() as cursor:
                # Prepare data for insertion into dividend_history
                insert_data = []

                for div in dividends_data:
                    # Convert empty strings to None for date fields
                    payment_date = div.get('payment_date') or None
                    if payment_date == '':
                        payment_date = None

                    # Use payment_date if available, otherwise use ex_date
                    history_date = payment_date if payment_date else div['ex_date']

                    # Convert numpy types to Python native types
                    amount = float(div['amount']) if div['amount'] is not None else None

                    # Only insert valid dividends with amount > 0
                    if amount and amount > 0:
                        insert_data.append((
                            div['symbol'],
                            history_date,
                            amount
                        ))

                # Insert into dividend_history table
                if insert_data:
                    query = """
                        INSERT INTO dividend_history
                        (symbol, payment_date, amount)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (symbol, payment_date) DO UPDATE SET
                            amount = EXCLUDED.amount,
                            last_updated = CURRENT_TIMESTAMP
                    """
                    execute_batch(cursor, query, insert_data, page_size=100)

                conn.commit()
                return len(insert_data)

    except Exception as e:
        logger.error(f"Error saving dividends batch: {e}")
        return 0

def process_symbol(symbol):
    """Process a single symbol - fetch prices and dividends."""
    results = {
        'symbol': symbol,
        'prices_fetched': False,
        'dividends_fetched': False,
        'prices_source': None,
        'dividends_source': None,
        'price_count': 0,
        'dividend_count': 0,
        'incremental': False
    }

    # Get latest dates from database
    latest_price_date, latest_div_date = get_latest_dates(symbol)

    # Determine start dates for fetching
    price_start_date = None
    div_start_date = None

    if latest_price_date:
        # Add one day to the latest date to avoid re-fetching the same data
        next_day = latest_price_date + timedelta(days=1)
        price_start_date = next_day.strftime('%Y-%m-%d')
        results['incremental'] = True
        logger.debug(f"{symbol}: Fetching prices from {price_start_date} (latest: {latest_price_date})")
    else:
        price_start_date = PRICES_START_DATE
        logger.debug(f"{symbol}: No existing prices, fetching from {price_start_date}")

    if latest_div_date:
        # Add one day to the latest date to avoid re-fetching the same data
        next_day = latest_div_date + timedelta(days=1)
        div_start_date = next_day.strftime('%Y-%m-%d')
        logger.debug(f"{symbol}: Fetching dividends from {div_start_date} (latest: {latest_div_date})")
    else:
        div_start_date = DIVIDENDS_START_DATE
        logger.debug(f"{symbol}: No existing dividends, fetching from {div_start_date}")

    # Fetch prices with appropriate start date (FMP → Alpha Vantage → Yahoo)
    prices, source = fetch_fmp_prices(symbol, price_start_date)
    if not prices:
        prices, source = fetch_alpha_vantage_prices(symbol, price_start_date)
    if not prices:
        prices, source = fetch_yahoo_prices(symbol, price_start_date)

    if prices:
        saved = save_prices_batch(prices)
        results['prices_fetched'] = True
        results['prices_source'] = source
        results['price_count'] = len(prices)
    else:
        # Check if this is a completely new symbol with no data
        if not results['incremental']:
            # No data available from any source for a new symbol
            add_to_excluded(symbol, "No price data available from any source")
            logger.warning(f"❌ {symbol}: No price data available, added to excluded list")

    # Fetch dividends with appropriate start date (FMP → Alpha Vantage → Yahoo)
    dividends, source = fetch_fmp_dividends(symbol, div_start_date)
    if not dividends:
        dividends, source = fetch_alpha_vantage_dividends(symbol, div_start_date)
    if not dividends:
        dividends, source = fetch_yahoo_dividends(symbol, div_start_date)

    if dividends:
        saved = save_dividends_batch(dividends)
        results['dividends_fetched'] = True
        results['dividends_source'] = source
        results['dividend_count'] = len(dividends)

    return results

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("Starting Price and Dividend Data Collection")
    logger.info("=" * 80)

    # Test database connection
    if not test_postgres_connection():
        logger.error("Cannot proceed without database connection")
        return

    # Create tables if they don't exist
    if not create_tables_if_not_exist():
        logger.error("Cannot proceed without database tables")
        return

    # Get all symbols
    symbols = get_all_symbols()
    logger.info(f"📊 Found {len(symbols)} symbols to process")

    if not symbols:
        logger.error("No symbols found in database")
        return

    # Process statistics
    total_symbols = len(symbols)
    prices_success = 0
    dividends_success = 0
    total_price_records = 0
    total_dividend_records = 0

    # Process in batches
    total_batches = (total_symbols + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num in range(0, total_symbols, BATCH_SIZE):
        batch = symbols[batch_num:batch_num + BATCH_SIZE]
        current_batch = (batch_num // BATCH_SIZE) + 1

        logger.info(f"\n📦 Processing batch {current_batch}/{total_batches} ({len(batch)} symbols)")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(process_symbol, symbol): symbol for symbol in batch}

            for future in as_completed(futures):
                symbol = futures[future]
                try:
                    result = future.result(timeout=60)

                    if result['prices_fetched']:
                        prices_success += 1
                        total_price_records += result['price_count']
                        if result['price_count'] > 0:
                            update_type = "📈 UPDATE" if result['incremental'] else "✅ NEW"
                            logger.info(f"{update_type} {symbol}: {result['price_count']} prices from {result['prices_source']}")
                    else:
                        if result['incremental']:
                            logger.debug(f"✓ {symbol}: No new price data")
                        else:
                            logger.debug(f"⚠️ {symbol}: No price data available")

                    if result['dividends_fetched']:
                        dividends_success += 1
                        total_dividend_records += result['dividend_count']
                        if result['dividend_count'] > 0:
                            logger.info(f"💰 {symbol}: {result['dividend_count']} dividends from {result['dividends_source']}")

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")

        # Log progress
        logger.info(f"Progress: {min(batch_num + BATCH_SIZE, total_symbols)}/{total_symbols} symbols processed")

    # Final statistics
    logger.info("\n" + "=" * 80)
    logger.info("DATA COLLECTION COMPLETE")
    logger.info("=" * 80)

    with get_postgres_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(DISTINCT symbol) as symbols, COUNT(*) as records FROM raw_stock_prices")
            price_stats = cursor.fetchone()

            cursor.execute("SELECT COUNT(DISTINCT symbol) as symbols, COUNT(*) as records FROM stock_dividends")
            div_stats = cursor.fetchone()

    logger.info(f"📈 Price Data:")
    logger.info(f"   - Symbols with prices: {price_stats[0]}")
    logger.info(f"   - Total price records: {price_stats[1]}")
    logger.info(f"   - Success rate: {(prices_success / total_symbols * 100):.1f}%")

    logger.info(f"💰 Dividend Data:")
    logger.info(f"   - Symbols with dividends: {div_stats[0]}")
    logger.info(f"   - Total dividend records: {div_stats[1]}")
    logger.info(f"   - Dividend-paying stocks: {(dividends_success / total_symbols * 100):.1f}%")

if __name__ == "__main__":
    main()