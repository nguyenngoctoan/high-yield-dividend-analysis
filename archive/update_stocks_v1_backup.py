#!/usr/bin/env python
# update_stocks_v1.py - Optimized version of stock update script

import logging
import time
import sys
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta, time as dt_time
import requests
from requests.exceptions import HTTPError
from supabase import create_client, Client
from postgrest.exceptions import APIError as PostgrestAPIError
import os
from dotenv import load_dotenv
from collections import defaultdict
from threading import Semaphore, Lock
import argparse

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv('FMP_API_KEY', 'demo')  # Financial Modeling Prep API key
fmp_limiter = Semaphore(5)  # Rate limiter for FMP API calls

# Environment variables
# Default to local Supabase instance if not specified
SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0")
API_KEY = os.getenv("FMP_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Debug settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
DEBUG_SYMBOLS = ["AAPL", "MSFT", "T", "VZ", "ABNB", "AMZN", "TSLA", "F", "GM", "META", "GOOG", "NVDA", "JNJ"]

# FMP endpoints
STOCK_SCREEN_URL = "https://financialmodelingprep.com/api/v3/stock-screener"
STOCK_LIST_URL = f"https://financialmodelingprep.com/api/v3/stock/list?apikey={API_KEY}"
ETF_INFO_URL_TEMPLATE = f"https://financialmodelingprep.com/api/v4/etf-info?symbol={{symbol}}&apikey={API_KEY}"
STOCK_PROFILE_URL_TEMPLATE = f"https://financialmodelingprep.com/api/v3/profile/{{symbol}}?apikey={API_KEY}"
DIVIDEND_URL_TEMPLATE = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{{symbol}}?apikey={API_KEY}"
# New FMP future dividend endpoints
DIVIDEND_CALENDAR_URL = f"https://financialmodelingprep.com/api/v3/stock_dividend_calendar?apikey={API_KEY}"
DIVIDEND_CALENDAR_RANGE_URL = f"https://financialmodelingprep.com/api/v3/stock_dividend_calendar?from={{from_date}}&to={{to_date}}&apikey={API_KEY}"
DIVIDEND_COMPANY_URL_TEMPLATE = f"https://financialmodelingprep.com/stable/dividends?symbol={{symbol}}&apikey={API_KEY}"
AV_DIVIDEND_URL_TEMPLATE = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={{symbol}}&apikey={ALPHA_VANTAGE_API_KEY}"
PRICES_BASE_URL = f"https://financialmodelingprep.com/api/v3/historical-price-full/"
FMP_SPLIT_BASE_URL = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_split/"

# Configuration
ALLOWED_EXCHANGES = ["NYSE", "NASDAQ", "AMEX", "TSX", "BATS", "CBOE", "TSE"]
BATCH_SIZE = 100
DAYS_THRESHOLD = 365  # Only consider stocks with prices in the last X days (TEMPORARILY INCREASED)
DELAY_BETWEEN_CALLS = 0.2
PRICES_API_DELAY = 0.2  # Base delay for price API calls
AV_API_DELAY = 0.1  # Reduced from 0.7 for premium account
MAX_RETRIES = 3
RETRY_DELAY = 1
# Remove this as we won't force update recent days anymore
# FORCE_UPDATE_DAYS = 10  # Force update most recent X days of data
TIMESERIES_DAYS = 365  # Default number of days for time series data
RECALC_CHUNK_SIZE = 200  # Number of symbols to process in one batch for recalc
USE_AV_FALLBACK = True  # Use Alpha Vantage as a fallback for prices/dividends
AV_PREMIUM_ACCOUNT = True  # Set to True if using a premium Alpha Vantage account
FETCH_ALL_SPLITS = False  # Whether to re-fetch all splits

# Future dividend configuration
ENABLE_FUTURE_DIVIDENDS = True  # Enable fetching of upcoming dividend payments
FUTURE_DIVIDEND_DAYS = 365  # How many days ahead to fetch future dividends
UPDATE_FUTURE_DIVIDENDS_DAYS = 7  # How often to update future dividends (in days)

# Stock filtering configuration
FILTER_DIVIDEND_OR_PORTFOLIO_ONLY = True  # Only include stocks with dividends or in portfolios (TEMPORARILY DISABLED)

# Temporary data collection mode - disable all filters to get maximum data
TEMPORARY_DATA_COLLECTION_MODE = True  # Disable all filters and checks to collect all available data

# Concurrency limits
MAX_WORKERS_STOCKS = 3
MAX_WORKERS_PRICES = 5
MAX_WORKERS_SPLITS = 5
MAX_WORKERS_METRICS = 8
MAX_WORKERS_DIVIDENDS = 10  # Increased from 4 to 10 for premium account
MAX_CONCURRENT_REQUESTS = 10  # Increased from 5 for premium account
MAX_CONCURRENT_DB = 3  # Max concurrent DB operations

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("update_stocks_v1.log")
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("postgrest").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Initialize Supabase client
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"Supabase client initialized successfully with URL: {SUPABASE_URL}")
        
        # Test connection to local Supabase
        try:
            # Try a simple query to test connection
            test_response = supabase.table("stocks").select("symbol").limit(1).execute()
            logger.info("Successfully connected to local Supabase instance")
        except Exception as test_e:
            logger.warning(f"Could not connect to Supabase tables - they may not exist yet: {test_e}")
            logger.info("This is normal for a fresh local Supabase instance")
            
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase credentials missing - will use test data only")

# Locks and semaphores
api_semaphore = Semaphore(MAX_CONCURRENT_REQUESTS)
db_semaphore = Semaphore(MAX_CONCURRENT_DB)
progress_lock = Lock()
aum_progress_lock = Lock()

# Global counters for progress tracking
dividend_new_records_count = 0
dividend_errors_count = 0
future_dividend_new_records_count = 0
future_dividend_errors_count = 0
aum_symbols_with_aum_found = 0
aum_successful_updates = 0
aum_processed_count = 0
aum_error_count = 0
aum_total_symbols = 0

class AdaptiveRateLimiter:
    """Implements adaptive rate limiting based on API response patterns."""
    
    def __init__(self, base_delay=1.0, max_delay=30.0, backoff_factor=1.5):
        self.base_delay = base_delay
        self.current_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.lock = Lock()
    
    def wait(self):
        """Wait according to current delay."""
        time.sleep(self.current_delay)
    
    def report_success(self):
        """Report a successful API call - gradually reduce delay."""
        with self.lock:
            self.consecutive_failures = 0
            self.consecutive_successes += 1
            
            # After 5 consecutive successes, gradually reduce delay
            if self.consecutive_successes >= 5:
                self.current_delay = max(self.base_delay, self.current_delay / 1.1)
                self.consecutive_successes = 0
    
    def report_failure(self, rate_limit=False):
        """Report a failed API call - increase delay."""
        with self.lock:
            self.consecutive_successes = 0
            self.consecutive_failures += 1
            
            # Increase delay, more aggressively for rate limit errors
            factor = self.backoff_factor * 2 if rate_limit else self.backoff_factor
            self.current_delay = min(self.max_delay, self.current_delay * factor)

# Initialize rate limiters for different APIs
fmp_limiter = AdaptiveRateLimiter(base_delay=PRICES_API_DELAY, max_delay=10.0)
# Set more aggressive parameters for premium account
av_limiter = AdaptiveRateLimiter(
    base_delay=AV_API_DELAY, 
    max_delay=15.0 if AV_PREMIUM_ACCOUNT else 60.0,  # Lower max delay for premium
    backoff_factor=1.5 if AV_PREMIUM_ACCOUNT else 2.0  # Lower backoff for premium
)

class LastRunTracker:
    """Track the last time a specific operation was run."""
    
    def __init__(self, file_prefix="last_run_"):
        self.file_prefix = file_prefix
        
    def get_last_run(self, operation_name):
        """Get the last time an operation was run."""
        filename = f"{self.file_prefix}{operation_name}.txt"
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    timestamp_str = f.read().strip()
                    return datetime.fromisoformat(timestamp_str)
            return None
        except Exception as e:
            logger.error(f"Error reading last run time for {operation_name}: {e}")
            return None
    
    def set_last_run(self, operation_name, timestamp=None):
        """Set the last time an operation was run."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        filename = f"{self.file_prefix}{operation_name}.txt"
        try:
            with open(filename, 'w') as f:
                f.write(timestamp.isoformat())
            return True
        except Exception as e:
            logger.error(f"Error writing last run time for {operation_name}: {e}")
            return False
    
    def should_run(self, operation_name, min_interval_days):
        """Check if an operation should run based on the minimum interval."""
        last_run = self.get_last_run(operation_name)
        if last_run is None:
            return True
        
        now = datetime.now(timezone.utc)
        interval = now - last_run
        return interval.days >= min_interval_days

# Initialize the last run tracker
last_run_tracker = LastRunTracker()

def initialize_data_repository():
    """Create a central repository of all required data to minimize repeated queries."""
    logger.info("Initializing central data repository...")
    
    repo = {
        'symbols': {},           # All symbols with metadata
        'etfs': set(),           # Set of ETF symbols
        'prices': {},            # Latest price data by symbol
        'dividends': {},         # Dividend history by symbol
        'future_dividends': {},  # Future dividend data by symbol
        'existing_splits': {},   # Known splits by symbol
        'max_price_dates': {},   # Most recent price date by symbol
        'max_dividend_dates': {}, # Most recent dividend date by symbol
        'max_future_dividend_dates': {}, # Most recent future dividend date by symbol
        'excluded_symbols': set(), # Symbols to exclude from processing
    }
    
    # Skip complex database queries for now - just return empty repository
    logger.info("Skipping database queries - using empty repository")
    return repo
    
def create_all_tables_if_needed():
    """Create all necessary tables for the local Supabase instance."""
    if not supabase:
        logger.warning("Supabase client not available - cannot create tables")
        return
        
    logger.info("Checking and creating necessary tables for local Supabase...")
    # For now, just log that we're skipping table creation
    logger.info("Skipping table creation - using existing tables")

def test_supabase_connection():
    """Test the Supabase connection by inserting and deleting a test record."""
    if not supabase:
        logger.error("Supabase client not initialized")
        return False
        
    try:
        logger.info("Testing connection to local Supabase...")
        
        # Insert a test record
        test_record = {
            "symbol": "TEST_CONNECTION",
            "name": "Test Connection",
            "company_name": "Test Connection"
        }
        
        result = supabase.table("stocks").insert(test_record).execute()
        logger.info("Successfully inserted test record into stocks table")
        
        # Verify the record was inserted
        verify_result = supabase.table("stocks").select("*").eq("symbol", "TEST_CONNECTION").execute()
        if verify_result.data:
            logger.info("Successfully verified test record in stocks table")
        else:
            logger.error("Failed to verify test record")
            return False
        
        # Clean up the test record
        supabase.table("stocks").delete().eq("symbol", "TEST_CONNECTION").execute()
        logger.info("Cleaned up test record")
        
        return True
        
    except Exception as e:
        logger.error(f"Supabase connection test failed: {e}")
        return False
            
def is_warrant(symbol, name):
    """Check if a symbol is a warrant or other non-stock security."""
    if not symbol:
        return True
    
    # Check symbol patterns common for warrants
    if (symbol.endswith(".WS") or symbol.endswith("-WS") or
        symbol.endswith(".WT") or "+" in symbol or
        "WRT" in symbol):
            return True
            
    # Check name for warrant indicators
    if name and ("WARRANT" in name or "WRT" in name or "WARRANTS" in name):
                    return True
                    
                    return False
        
def should_include_stock(symbol, name=""):
    """Determine if a stock should be included based on dividend history or portfolio presence."""
    # Always include ETFs as they might have dividend-like distributions
    if name and "ETF" in name.upper():
        return True
        
    # For now, let's just include all stocks to test the basic functionality
    # We can add dividend checking later
    return True

def fetch_with_adaptive_retry(url, limiter=None, max_retries=3):
    """Fetch data from URL with adaptive retry logic."""
    import requests
    import time
    
    for attempt in range(max_retries):
        try:
            if limiter:
                limiter.acquire()
                try:
                    response = requests.get(url, timeout=30)
                finally:
                    limiter.release()
            else:
                response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                wait_time = 2 ** attempt
                logger.warning(f"Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
        except Exception as e:
            logger.error(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
                return None
            
def update_stocks_optimized(repo):
    """Simplified function for updating stocks from the market data."""
    try:
        logger.info("Starting simplified stock update...")
        
        # If we're in debug mode, just use a small set of symbols
        if DEBUG_MODE:
            logger.info(f"DEBUG MODE: Using {len(DEBUG_SYMBOLS)} test symbols")
            
            # Get data from the API for these symbols
            symbols_to_process = [{'symbol': s} for s in DEBUG_SYMBOLS]
            success = process_securities_batch(symbols_to_process, repo)
            return success
        
        # In production mode, proceed with full stock list update
        logger.info("Fetching securities from Financial Modeling Prep API...")
        
        url = "https://financialmodelingprep.com/api/v3/stock/list?apikey=" + API_KEY
        data = fetch_with_adaptive_retry(url, None)
        
        if data:
            logger.info(f"Fetched {len(data)} securities from API")
            
            # Filter securities based on our criteria
            filtered_securities = filter_securities_optimized(data)
            logger.info(f"After filtering: {len(filtered_securities)} securities to process")
            
            # Process in batches
            batch_size = 100
            total_processed = 0
            
            for i in range(0, len(filtered_securities), batch_size):
                batch = filtered_securities[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(filtered_securities) + batch_size - 1)//batch_size}")
                
                success = process_securities_batch(batch, repo)
                if not success:
                    logger.error(f"Failed to process batch {i//batch_size + 1}")
                    return False
                
                total_processed += len(batch)
                logger.info(f"Processed {total_processed}/{len(filtered_securities)} securities")
            
            logger.info(f"Successfully processed {total_processed} securities")
            return True
                    else:
            logger.error("Failed to fetch securities from API")
            return False
                    
        except Exception as e:
        logger.error(f"Error in stock update process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def filter_securities_optimized(securities):
    """Filter securities based on our criteria."""
    filtered = []
    skipped_no_dividend_or_portfolio = 0
    
    for security in securities:
        symbol = security.get('symbol', '')
        name = security.get('name', '')
        
        if not symbol:
            continue
            
        # Skip warrants and other non-stock securities
        if is_warrant(symbol, name):
            continue
        
        # Apply dividend/portfolio filtering if enabled
        if FILTER_DIVIDEND_OR_PORTFOLIO_ONLY and not should_include_stock(symbol, name):
            skipped_no_dividend_or_portfolio += 1
            continue
            
        filtered.append(security)
    
    if skipped_no_dividend_or_portfolio > 0:
        logger.info(f"Skipped {skipped_no_dividend_or_portfolio} securities (no dividend history or portfolio presence)")
    
    return filtered

def process_securities_batch(securities_batch, repo):
    """Process a batch of securities."""
    success = True
    processed_count = 0
    
    for security in securities_batch:
        try:
            symbol = security.get('symbol')
            if not symbol:
                continue
                
            # Process the security
            if process_security_optimized(security, repo):
                processed_count += 1
    else:
                logger.warning(f"Failed to process security: {symbol}")
                
        except Exception as e:
            logger.error(f"Error processing security {security.get('symbol', 'unknown')}: {e}")
            success = False
    
    logger.info(f"Processed {processed_count}/{len(securities_batch)} securities in batch")
    return success

def process_security_optimized(security, repo):
    """Process a single security."""
    try:
        symbol = security.get('symbol')
        name = security.get('name', '')
        exchange = security.get('exchange', '')

        if not symbol:
            return False

        # Check if we should include this stock
        if FILTER_DIVIDEND_OR_PORTFOLIO_ONLY and not should_include_stock(symbol, name):
            return False

        # Create stock record (matching actual database schema)
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "symbol": symbol,
            "name": name or "",
            "company_name": name or "",
            "last_updated": now,
        }
        
        # Add to repository
        repo['symbols'][symbol] = record
        
        # Insert into database
            if supabase:
            try:
                    supabase.table("stocks").upsert(record).execute()
                logger.debug(f"Added/updated stock: {symbol}")
            except Exception as e:
                logger.error(f"Error inserting stock {symbol}: {e}")
                return False
                
                return True
            
        except Exception as e:
        logger.error(f"Error processing security {security.get('symbol', 'unknown')}: {e}")
            return False
            
def get_max_dates_for_symbols():
    """Get the maximum date for each symbol in stock_prices and dividend_history tables."""
    try:
        logger.info("Fetching max dates for all symbols...")
        
        # Get max dates from stock_prices
        prices_result = supabase.table("stock_prices").select("symbol, date").order("date", desc=True).execute()
        max_price_dates = {}
        for record in prices_result.data:
            symbol = record['symbol']
            date = record['date']
            if symbol not in max_price_dates or date > max_price_dates[symbol]:
                max_price_dates[symbol] = date
        
        # Get max dates from dividend_history
        dividends_result = supabase.table("dividend_history").select("symbol, payment_date").order("payment_date", desc=True).execute()
        max_dividend_dates = {}
        for record in dividends_result.data:
            symbol = record['symbol']
            date = record['payment_date']
            if symbol not in max_dividend_dates or date > max_dividend_dates[symbol]:
                max_dividend_dates[symbol] = date
        
        logger.info(f"Found max dates for {len(max_price_dates)} symbols in prices, {len(max_dividend_dates)} symbols in dividends")
        return max_price_dates, max_dividend_dates
        
    except Exception as e:
        logger.error(f"Error fetching max dates: {e}")
        return {}, {}

def update_stock_prices_optimized(repo):
    """Update stock prices for all symbols in the database, only fetching new data."""
    try:
        logger.info("Starting incremental stock price updates...")
        
        # Get all symbols from the database
        if not supabase:
            logger.error("Supabase client not available")
            return False
        
        # Fetch all symbols from stocks table with pagination
        symbols = []
        page_size = 1000
        offset = 0
        
        while True:
            result = supabase.table("stocks").select("symbol").range(offset, offset + page_size - 1).execute()
            if not result.data:
                break
            symbols.extend([row['symbol'] for row in result.data])
            offset += page_size
            logger.info(f"Fetched {len(symbols)} symbols so far...")
            
        if not symbols:
            logger.warning("No symbols found in stocks table")
            return True
            
        logger.info(f"Found {len(symbols)} symbols to update prices for")
        
        # Get max dates for existing price data
        max_price_dates, _ = get_max_dates_for_symbols()
        
        # Process in batches
        batch_size = 50  # Smaller batches for price updates
        total_processed = 0
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            logger.info(f"Processing price batch {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size}")
            
            success = process_price_batch(batch, repo, max_price_dates)
            if not success:
                logger.error(f"Failed to process price batch {i//batch_size + 1}")
                return False
            
            total_processed += len(batch)
            logger.info(f"Processed prices for {total_processed}/{len(symbols)} symbols")
        
        logger.info(f"Successfully processed prices for {total_processed} symbols")
        return True
        
    except Exception as e:
        logger.error(f"Error in price update process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_price_batch(symbols_batch, repo, max_price_dates):
    """Process a batch of symbols for price updates, only fetching new data."""
    success = True
    processed_count = 0
    skipped_count = 0
    
    for symbol in symbols_batch:
        try:
            # Check if we need to fetch new data for this symbol
            max_date = max_price_dates.get(symbol)
            if max_date:
                # Skip if we already have recent data (within last 7 days)
                from datetime import datetime, timedelta
                max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
                if max_date_obj > datetime.now() - timedelta(days=7):
                    skipped_count += 1
                    continue
            
            if process_symbol_prices(symbol, repo, max_date):
                processed_count += 1
            else:
                logger.warning(f"Failed to process prices for: {symbol}")
                
            except Exception as e:
            logger.error(f"Error processing prices for {symbol}: {e}")
                success = False
                
    logger.info(f"Processed prices for {processed_count}/{len(symbols_batch)} symbols in batch (skipped {skipped_count} with recent data)")
    return success

def process_symbol_prices(symbol, repo, max_date=None):
    """Process prices for a single symbol, only fetching new data."""
    try:
        # Get historical prices from FMP API
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?apikey={API_KEY}"
        data = fetch_with_adaptive_retry(url, None)
        
        if not data or 'historical' not in data:
            logger.debug(f"No price data found for {symbol}")
        return False

        prices = data['historical']
        if not prices:
            logger.debug(f"No historical prices found for {symbol}")
            return False
        
        # Filter to only include new data if max_date is provided
        if max_date:
            from datetime import datetime
            max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
        filtered_prices = []
            for price in prices:
                price_date = datetime.strptime(price['date'], '%Y-%m-%d')
                if price_date > max_date_obj:
            filtered_prices.append(price)
            prices = filtered_prices
            
            if not prices:
                logger.info(f"No new price data for {symbol} since {max_date}")
                return True
        
        # Insert prices into database
        price_records = []
        for price_data in prices:
            record = {
                    "symbol": symbol,
                "date": price_data.get('date'),
                "open_price": price_data.get('open'),
                "highest_price": price_data.get('high'),
                "lowest_price": price_data.get('low'),
                "close_price": price_data.get('close'),
                "volume": price_data.get('volume')
            }
            price_records.append(record)
        
        # Batch insert prices
        if supabase and price_records:
            try:
                supabase.table("stock_prices").upsert(price_records).execute()
                logger.debug(f"Inserted {len(price_records)} price records for {symbol}")
                return True
            except Exception as e:
                logger.error(f"Error inserting prices for {symbol}: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing prices for {symbol}: {e}")
        return False

def update_dividends_optimized(repo):
    """Update dividend history for all symbols in the database."""
    try:
        logger.info("Starting dividend history updates...")
        
        # Get all symbols from the database
        if not supabase:
            logger.error("Supabase client not available")
            return False
            
        # Fetch all symbols from stocks table with pagination
        symbols = []
        page_size = 1000
        offset = 0
        
        while True:
            result = supabase.table("stocks").select("symbol").range(offset, offset + page_size - 1).execute()
            if not result.data:
                break
            symbols.extend([row['symbol'] for row in result.data])
            offset += page_size
            logger.info(f"Fetched {len(symbols)} symbols so far...")
            
        if not symbols:
            logger.warning("No symbols found in stocks table")
                                return True
            
        logger.info(f"Found {len(symbols)} symbols to update dividend history for")
        
        # Get max dates for existing dividend data
        _, max_dividend_dates = get_max_dates_for_symbols()
        
        # Process in batches
        batch_size = 50  # Smaller batches for dividend updates
        total_processed = 0
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            logger.info(f"Processing dividend batch {i//batch_size + 1}/{(len(symbols) + batch_size - 1)//batch_size}")
            
            success = process_dividend_batch(batch, repo, max_dividend_dates)
            if not success:
                logger.error(f"Failed to process dividend batch {i//batch_size + 1}")
            return False
        
            total_processed += len(batch)
            logger.info(f"Processed dividends for {total_processed}/{len(symbols)} symbols")
        
        logger.info(f"Successfully processed dividend history for {total_processed} symbols")
            return True
        
                except Exception as e:
        logger.error(f"Error in dividend update process: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def process_dividend_batch(symbols_batch, repo, max_dividend_dates):
    """Process a batch of symbols for dividend updates, only fetching new data."""
    success = True
    processed_count = 0
    skipped_count = 0
    
    for symbol in symbols_batch:
        try:
            # Check if we need to fetch new data for this symbol
            max_date = max_dividend_dates.get(symbol)
            if max_date:
                # Skip if we already have recent data (within last 30 days for dividends)
                from datetime import datetime, timedelta
                max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
                if max_date_obj > datetime.now() - timedelta(days=30):
                    skipped_count += 1
                continue
            
            if process_symbol_dividends(symbol, repo, max_date):
                processed_count += 1
        else:
                logger.debug(f"No dividend data found for: {symbol}")
                
                    except Exception as e:
            logger.error(f"Error processing dividends for {symbol}: {e}")
            success = False
    
    logger.info(f"Processed dividends for {processed_count}/{len(symbols_batch)} symbols in batch (skipped {skipped_count} with recent data)")
    return success

def process_symbol_dividends(symbol, repo, max_date=None):
    """Process dividend history for a single symbol, only fetching new data."""
    try:
        # Get dividend history from FMP API
        url = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/{symbol}?apikey={API_KEY}"
        data = fetch_with_adaptive_retry(url, None)
        
        if not data or 'historical' not in data:
            logger.debug(f"No dividend data found for {symbol}")
            return False
        
        dividends = data['historical']
        if not dividends:
            logger.debug(f"No dividend history found for {symbol}")
        return False

        # Filter to only include new data if max_date is provided
        if max_date:
            from datetime import datetime
            max_date_obj = datetime.strptime(max_date, '%Y-%m-%d')
            filtered_dividends = []
            for dividend in dividends:
                div_date = datetime.strptime(dividend['date'], '%Y-%m-%d')
                if div_date > max_date_obj:
                    filtered_dividends.append(dividend)
            dividends = filtered_dividends
            
    if not dividends:
                logger.info(f"No new dividend data for {symbol} since {max_date}")
                return True
        
        # Insert dividends into database
        dividend_records = []
        for div_data in dividends:
        record = {
            "symbol": symbol,
                "payment_date": div_data.get('date'),
                "amount": div_data.get('dividend')
        }
            dividend_records.append(record)
        
        # Batch insert dividends
        if supabase and dividend_records:
        try:
                supabase.table("dividend_history").upsert(dividend_records).execute()
                logger.debug(f"Inserted {len(dividend_records)} dividend records for {symbol}")
                return True
        except Exception as e:
                logger.error(f"Error inserting dividends for {symbol}: {e}")
                return False
            
            return True
        
    except Exception as e:
        logger.error(f"Error processing dividends for {symbol}: {e}")
        return False

def main_optimized(args=None):
    """Main function with optimized processes."""
    global supabase
    success = True
    
    try:
        # Set up command line arguments
        parser = argparse.ArgumentParser(description="Stock Data Update Script (Optimized)")
        parser.add_argument("--skip-stocks", action="store_true", help="Skip updating basic stock data")
        parser.add_argument("--skip-prices", action="store_true", help="Skip updating stock prices")
        parser.add_argument("--skip-splits", action="store_true", help="Skip updating stock splits")
        parser.add_argument("--skip-dividends", action="store_true", help="Skip updating dividends")
        parser.add_argument("--skip-future-dividends", action="store_true", help="Skip updating future dividends")
        parser.add_argument("--skip-metrics", action="store_true", help="Skip recalculating metrics")
        parser.add_argument("--premium-api", action="store_true", help="Use premium API settings (faster rate limits)")
        parser.add_argument("--debug", action="store_true", help="Run in debug mode with limited symbols")
        parser.add_argument("--test-connection", action="store_true", help="Test Supabase connection and exit")
        parser.add_argument("--include-all-stocks", action="store_true", help="Include all stocks (disable dividend/portfolio filtering)")
        parser.add_argument("--temporary-data-mode", action="store_true", help="Temporary data collection mode (disable filters)")
        parser.add_argument("--stocks-only", action="store_true", help="Only run the stock update process")
        parser.add_argument("--prices-only", action="store_true", help="Only run the stock prices update process")
        parser.add_argument("--dividends-only", action="store_true", help="Only run the dividend history update process")
        
        if args:
            parsed_args = parser.parse_args(args)
        else:
            parsed_args = parser.parse_args()
        
        # Set global debug mode
        global DEBUG_MODE
        DEBUG_MODE = parsed_args.debug
        
        # Set global premium API mode
        global AV_PREMIUM_ACCOUNT
        AV_PREMIUM_ACCOUNT = parsed_args.premium_api
        
        # Handle temporary data collection mode
        global TEMPORARY_DATA_COLLECTION_MODE
        TEMPORARY_DATA_COLLECTION_MODE = parsed_args.temporary_data_mode
        
        # Handle include all stocks mode
        global FILTER_DIVIDEND_OR_PORTFOLIO_ONLY
        if parsed_args.include_all_stocks:
            FILTER_DIVIDEND_OR_PORTFOLIO_ONLY = False
        
        # If in temporary mode, keep the current value of FILTER_DIVIDEND_OR_PORTFOLIO_ONLY
        
        # Check if Supabase client is initialized
        if not supabase:
            logger.error("Supabase client not initialized. Check credentials.")
                    return False
        
        # Handle test connection mode
        if parsed_args.test_connection:
            logger.info("Testing Supabase connection...")
            create_all_tables_if_needed()
            if test_supabase_connection():
                logger.info("✅ Supabase connection test PASSED")
        return True
            else:
                logger.error("❌ Supabase connection test FAILED")
        return False

        # Display configuration
        logger.info(f"Debug Mode: {DEBUG_MODE}")
        logger.info(f"Alpha Vantage Premium Mode: {AV_PREMIUM_ACCOUNT}")
        logger.info(f"Max Workers for Dividends: {MAX_WORKERS_DIVIDENDS}")
        logger.info(f"Max Workers for Prices: {MAX_WORKERS_PRICES}")
        logger.info(f"Max Workers for Stocks: {MAX_WORKERS_STOCKS}")
        logger.info(f"Stock Filtering: {'Enabled (dividend payers and portfolio stocks only)' if FILTER_DIVIDEND_OR_PORTFOLIO_ONLY else 'Disabled (all stocks)'}")
        logger.info(f"Temporary Data Collection Mode: {'Enabled (maximum data collection)' if TEMPORARY_DATA_COLLECTION_MODE else 'Disabled'}")
        
        # Initialize Supabase client and test connection
        try:
            test_supabase_connection()
                except Exception as e:
            logger.warning("Supabase connection test failed, but continuing...")
        
        # Handle specific modes
        if parsed_args.stocks_only:
            logger.info("Running stocks-only mode")
            create_all_tables_if_needed()
            repo = initialize_data_repository()
            success = update_stocks_optimized(repo)
            return success
        elif parsed_args.prices_only:
            logger.info("Running prices-only mode")
            create_all_tables_if_needed()
            repo = initialize_data_repository()
            success = update_stock_prices_optimized(repo)
            return success
        elif parsed_args.dividends_only:
            logger.info("Running dividends-only mode")
            create_all_tables_if_needed()
            repo = initialize_data_repository()
            success = update_dividends_optimized(repo)
            return success
        
        # Initialize central data repository
        repo = initialize_data_repository()
        
        # Process each component in sequence, passing the repository
        if not parsed_args or not parsed_args.skip_stocks:
            logger.info("=" * 80)
            logger.info("STARTING OPTIMIZED STOCK UPDATES")
            logger.info("=" * 80)
            if not update_stocks_optimized(repo):
                logger.error("Stock update process failed")
                success = False
        
        if not parsed_args or not parsed_args.skip_prices:
            logger.info("\n" + "=" * 80)
            logger.info("STARTING OPTIMIZED PRICE UPDATES")
            logger.info("=" * 80)
            if not update_stock_prices_optimized(repo):
                logger.error("Price update process failed")
                success = False
        
        if not parsed_args or not parsed_args.skip_splits:
            logger.info("\n" + "=" * 80)
            logger.info("STARTING OPTIMIZED SPLIT UPDATES")
            logger.info("=" * 80)
            if not update_stock_splits_optimized(repo):
                logger.error("Split update process failed")
                success = False
        
        if not parsed_args or not parsed_args.skip_dividends:
            logger.info("\n" + "=" * 80)
            logger.info("STARTING OPTIMIZED DIVIDEND UPDATES")
            logger.info("=" * 80)
            if not update_dividends_optimized(repo):
                logger.error("Dividend update process failed")
                success = False
        
        if not parsed_args or not parsed_args.skip_future_dividends:
            logger.info("\n" + "=" * 80)
            logger.info("STARTING OPTIMIZED FUTURE DIVIDEND UPDATES")
            logger.info("=" * 80)
            if not update_future_dividends_optimized(repo):
                logger.error("Future dividend update process failed")
                success = False
        
        if not parsed_args or not parsed_args.skip_metrics:
            logger.info("\n" + "=" * 80)
            logger.info("STARTING OPTIMIZED METRICS UPDATES")
            logger.info("=" * 80)
            if not update_stock_metrics_optimized(repo):
                logger.error("Metrics update process failed")
                success = False
        
        logger.info("\n" + "=" * 80)
        logger.info("UPDATE PROCESS COMPLETED")
        logger.info("=" * 80)
        
        if success:
            logger.info("✅ All update processes completed successfully")
    else:
            logger.warning("⚠️  Some update processes failed - check logs above")
        
        return success
        
    except Exception as e:
        logger.error(f"Critical error in main_optimized: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("Starting update_stocks_v1.py script")
    success = main_optimized()
    if not success:
            print("Update process failed")
            sys.exit(1)
    print("Update process completed successfully")
