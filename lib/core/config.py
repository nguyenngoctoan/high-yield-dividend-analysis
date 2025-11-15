"""
Configuration Module

Centralizes all configuration, environment variables, constants, and settings
for the high-yield dividend analysis system.
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIConfig:
    """API keys and endpoint configuration."""

    # API Keys
    FMP_API_KEY = os.getenv('FMP_API_KEY', 'demo')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')

    # API Endpoints
    FMP_BASE_URL = "https://financialmodelingprep.com"
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

    # Rate Limiting Configuration
    # FMP Professional Plan: 750 requests/min (12.5 req/sec)
    # https://site.financialmodelingprep.com/pricing-plans
    FMP_CONCURRENT_REQUESTS = 400  # 400 concurrent to maximize 750 req/min limit (80% utilization = 600 req/min)
    ALPHA_VANTAGE_CONCURRENT_REQUESTS = 6  # Increased from 2 to 6 (3x boost)
    YAHOO_CONCURRENT_REQUESTS = 3  # Conservative to avoid rate limiting (Yahoo is free tier)

    # Request Timeouts
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3

    @classmethod
    def validate(cls):
        """Validate that required API keys are present."""
        if cls.FMP_API_KEY == 'demo':
            logging.warning("⚠️  Using demo FMP API key - limited functionality")
        if not cls.ALPHA_VANTAGE_API_KEY:
            logging.warning("⚠️  Alpha Vantage API key not configured")
        return True


class DatabaseConfig:
    """Database connection and operation configuration."""

    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'http://localhost:3004')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

    # Table Names
    TABLE_STOCKS = "raw_stocks"
    TABLE_STOCK_PRICES = "raw_stock_prices"
    TABLE_DIVIDEND_HISTORY = "raw_dividends"
    TABLE_DIVIDEND_CALENDAR = "raw_future_dividends"
    TABLE_EXCLUDED_SYMBOLS = "raw_stocks_excluded"
    TABLE_STOCK_SPLITS = "raw_stock_splits"

    # Batch Processing
    BATCH_SIZE = 20
    UPSERT_BATCH_SIZE = 1000  # AGGRESSIVE: Increased from 500 to 1000 for max throughput

    # Aggressive Mode Settings (for maximum throughput)
    AGGRESSIVE_MODE = True  # Enable aggressive batching and reduced I/O
    AGGRESSIVE_BATCH_SIZE = 2000  # Batch writes even more aggressively
    REDUCE_LOGGING = True  # Reduce per-symbol logging for less I/O

    @classmethod
    def validate(cls):
        """Validate database configuration."""
        if not cls.SUPABASE_KEY:
            raise ValueError("SUPABASE_KEY environment variable is required")
        return True


class ExchangeConfig:
    """Exchange and market configuration."""

    # US and Canadian exchanges only (international markets removed)
    ALLOWED_EXCHANGES = [
        "NYSE", "NASDAQ", "AMEX", "BATS", "BTS", "BYX", "BZX", "CBOE",
        "EDGA", "EDGX", "PCX", "NGM",
        "OTCM", "OTCX",  # OTC markets for dividend stocks
        "TSX", "TSXV", "CSE", "TSE"  # Canadian exchanges
    ]

    # International exchange suffixes to block
    BLOCKED_SUFFIXES = [
        '.L', '.AX', '.DE', '.AS', '.MI', '.PA', '.SW', '.HK', '.BR',
        '.LS', '.MC', '.CO', '.ST', '.OL', '.HE', '.IC', '.VI', '.AT',
        '.WA', '.PR', '.BD', '.SA', '.MX', '.JK', '.KL', '.SI', '.BK',
        '.TW', '.KS', '.KQ', '.T', '.F', '.NZ', '.JO', '.SG', '.BO',
        '.NS', '.NE', '.ME'
    ]

    # Exchange Filtering
    NASDAQ_ONLY = False  # Controlled by command-line argument

    @classmethod
    def is_allowed_exchange(cls, exchange):
        """Check if an exchange is allowed."""
        if not exchange:
            return False
        return exchange.upper() in cls.ALLOWED_EXCHANGES

    @classmethod
    def is_international_symbol(cls, symbol):
        """Check if symbol has international exchange suffix."""
        if not symbol:
            return False
        symbol_upper = symbol.upper()
        return any(symbol_upper.endswith(suffix.upper()) for suffix in cls.BLOCKED_SUFFIXES)

    @classmethod
    def is_allowed_symbol(cls, symbol, exchange=None):
        """
        Check if symbol is allowed (not international and from allowed exchange).

        Args:
            symbol: Stock symbol to check
            exchange: Optional exchange name

        Returns:
            True if symbol is allowed, False otherwise
        """
        if not symbol:
            return False

        # Block international symbols by suffix
        if cls.is_international_symbol(symbol):
            return False

        # If exchange provided, check it too
        if exchange and not cls.is_allowed_exchange(exchange):
            return False

        return True

    @classmethod
    def filter_by_exchange(cls, symbols_data):
        """Filter symbols by allowed exchanges."""
        return [
            item for item in symbols_data
            if cls.is_allowed_exchange(item.get('exchangeShortName'))
        ]


class DataFetchConfig:
    """Data fetching behavior and feature flags."""

    # Historical Data Configuration
    ENHANCED_HISTORICAL_DATA = True
    PRICES_START_DATE = "1960-01-01"
    DIVIDENDS_START_DATE = "1960-01-01"

    # Hybrid Fetching Strategy
    USE_HYBRID_DIVIDENDS = True  # Enable hybrid dividend fetching
    USE_HYBRID_PRICES = False    # Keep FMP primary for prices (excellent coverage)
    FALLBACK_TO_YAHOO = True     # Enable Yahoo Finance fallback

    # Batch EOD Optimization (Professional/Enterprise plans only)
    USE_BATCH_EOD = True         # Use batch EOD API for recent data (30 days)
    BATCH_EOD_DAYS = 30          # Number of recent days to fetch via batch EOD
    FILTER_DIVIDEND_SYMBOLS = True  # Only fetch dividends for known dividend-paying symbols
    USE_BATCH_QUOTE_FILTER = True  # Use batch quote to skip symbols with no price change
    CACHE_COMPANY_DATA = True     # Cache company data with 90-day refresh cycle
    COMPANY_CACHE_DAYS = 90       # Days before refreshing company data
    PRIORITIZE_SYMBOLS = True     # Process high-priority symbols first (volume, market cap)

    # Validation Thresholds
    MIN_PRICE_THRESHOLD = 0.01  # Minimum valid price
    MAX_DAYS_SINCE_PRICE = 7    # Max days since last price for valid symbol
    MIN_DIVIDEND_LOOKBACK_DAYS = 365  # Look back 1 year for dividend validation

    # Data Quality
    REQUIRE_RECENT_PRICE = True
    REQUIRE_DIVIDEND_HISTORY = True  # For dividend stock filtering

    @classmethod
    def get_date_range(cls, start_date_str=None):
        """Get date range for historical data fetching."""
        if start_date_str:
            start = datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start = datetime.strptime(cls.PRICES_START_DATE, "%Y-%m-%d")

        end = datetime.now()
        return start, end


class LoggingConfig:
    """Logging configuration."""

    # Log Files
    DAILY_UPDATE_LOG = 'daily_update.log'
    ERROR_LOG = 'error.log'

    # Log Levels
    DEFAULT_LEVEL = logging.INFO
    HTTP_LIBRARY_LEVEL = logging.WARNING  # Reduce noise from HTTP libraries

    # Log Format
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

    @classmethod
    def configure_logging(cls, log_file=None, level=None):
        """Configure application logging."""
        log_file = log_file or cls.DAILY_UPDATE_LOG
        level = level or cls.DEFAULT_LEVEL

        logging.basicConfig(
            level=level,
            format=cls.LOG_FORMAT,
            handlers=[
                logging.FileHandler(log_file, mode='w'),  # Overwrite on each run
                logging.StreamHandler()
            ]
        )

        # Reduce HTTP request logging noise
        logging.getLogger("httpx").setLevel(cls.HTTP_LIBRARY_LEVEL)
        logging.getLogger("httpcore").setLevel(cls.HTTP_LIBRARY_LEVEL)
        logging.getLogger("urllib3").setLevel(cls.HTTP_LIBRARY_LEVEL)
        logging.getLogger("requests").setLevel(cls.HTTP_LIBRARY_LEVEL)
        logging.getLogger("yfinance").setLevel(cls.HTTP_LIBRARY_LEVEL)

        return logging.getLogger(__name__)


class FeatureFlags:
    """Feature flags for enabling/disabling functionality."""

    # Debug and Development
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

    # Data Collection Features
    COLLECT_HOURLY_PRICES = True
    COLLECT_STOCK_SPLITS = True
    COLLECT_IV_DATA = True  # Implied Volatility
    COLLECT_AUM_DATA = True  # Assets Under Management (ETFs)

    # Discovery Features
    AUTO_DISCOVER_SYMBOLS = True
    VALIDATE_DISCOVERED_SYMBOLS = True

    # Processing Features
    CONCURRENT_PROCESSING = True
    BATCH_OPERATIONS = True

    # Data Sources
    ENABLE_FMP = True
    ENABLE_ALPHA_VANTAGE = True
    ENABLE_YAHOO = True

    @classmethod
    def is_enabled(cls, feature_name):
        """Check if a feature is enabled."""
        return getattr(cls, feature_name.upper(), False)


class ProcessingConfig:
    """Configuration for concurrent processing and performance."""

    # Thread Pool Configuration
    MAX_WORKERS = 3  # Reduced to prevent socket exhaustion (was 5)
    DISCOVERY_MAX_WORKERS = 3  # Reduced to prevent socket exhaustion (was 5)
    VALIDATION_MAX_WORKERS = 3  # Reduced to prevent socket exhaustion (was 5)

    # Batch Sizes
    SYMBOL_DISCOVERY_BATCH = 100
    PRICE_FETCH_BATCH = 50
    DIVIDEND_FETCH_BATCH = 30

    # Performance Tuning
    ENABLE_PROGRESS_BARS = True
    LOG_BATCH_PROGRESS = True

    # Error Handling
    MAX_CONSECUTIVE_FAILURES = 10
    CONTINUE_ON_ERROR = True


class Config:
    """
    Main configuration class that aggregates all config sections.

    Usage:
        from lib.core.config import Config

        # Access API configuration
        fmp_key = Config.API.FMP_API_KEY

        # Access database configuration
        batch_size = Config.DATABASE.BATCH_SIZE

        # Access feature flags
        if Config.FEATURES.DEBUG_MODE:
            print("Debug mode enabled")
    """

    API = APIConfig
    DATABASE = DatabaseConfig
    EXCHANGE = ExchangeConfig
    DATA_FETCH = DataFetchConfig
    LOGGING = LoggingConfig
    FEATURES = FeatureFlags
    PROCESSING = ProcessingConfig

    @classmethod
    def validate_all(cls):
        """Validate all configuration sections."""
        cls.API.validate()
        cls.DATABASE.validate()
        return True

    @classmethod
    def setup(cls):
        """
        Setup configuration and logging.
        Call this at application startup.
        """
        # Configure logging first
        logger = cls.LOGGING.configure_logging()

        # Validate configuration
        try:
            cls.validate_all()
            logger.info("✅ Configuration validated successfully")
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            raise

        return logger


# Convenience exports for backward compatibility
FMP_API_KEY = APIConfig.FMP_API_KEY
ALPHA_VANTAGE_API_KEY = APIConfig.ALPHA_VANTAGE_API_KEY
ALLOWED_EXCHANGES = ExchangeConfig.ALLOWED_EXCHANGES
DEBUG_MODE = FeatureFlags.DEBUG_MODE

# Export main config
__all__ = ['Config', 'APIConfig', 'DatabaseConfig', 'ExchangeConfig',
           'DataFetchConfig', 'LoggingConfig', 'FeatureFlags', 'ProcessingConfig']
