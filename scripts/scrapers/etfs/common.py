#!/usr/bin/env python3
"""
ETF Scraper Common Utilities

Shared functionality for all ETF scrapers including:
- Logging setup
- Selenium browser configuration
- Database operations
- Common imports and utilities
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
import time
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from supabase_helpers import supabase_upsert, get_supabase_client


def setup_logging(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Setup standardized logging configuration for ETF scrapers

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)


def get_chrome_options():
    """
    Get standardized Chrome options for headless browsing

    Returns:
        Configured ChromeOptions instance
    """
    from selenium.webdriver.chrome.options import Options

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Set binary location (for Docker container with Chromium)
    chrome_binary = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
    if os.path.exists(chrome_binary):
        chrome_options.binary_location = chrome_binary

    return chrome_options


def create_chrome_driver(chrome_options=None, logger=None):
    """
    Create a Chrome WebDriver instance with standardized configuration

    Args:
        chrome_options: ChromeOptions instance (will create default if None)
        logger: Logger instance for logging (optional)

    Returns:
        Configured WebDriver instance
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service

    if chrome_options is None:
        chrome_options = get_chrome_options()

    # Use ChromeDriver path from environment if available
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    if os.path.exists(chromedriver_path):
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    if logger:
        logger.info("✅ Browser started successfully")

    return driver


def safe_find_element(driver, by, value, logger=None, timeout=10):
    """
    Safely find an element with timeout and error handling

    Args:
        driver: WebDriver instance
        by: Selenium By locator type
        value: Locator value
        logger: Logger instance (optional)
        timeout: Timeout in seconds (default: 10)

    Returns:
        WebElement if found, None otherwise
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except (TimeoutException, NoSuchElementException) as e:
        if logger:
            logger.warning(f"Element not found: {value}")
        return None


def safe_find_elements(driver, by, value, logger=None, timeout=10):
    """
    Safely find multiple elements with timeout and error handling

    Args:
        driver: WebDriver instance
        by: Selenium By locator type
        value: Locator value
        logger: Logger instance (optional)
        timeout: Timeout in seconds (default: 10)

    Returns:
        List of WebElements (empty list if none found)
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return driver.find_elements(by, value)
    except TimeoutException:
        if logger:
            logger.warning(f"Elements not found: {value}")
        return []


def save_to_database(table_name: str, data: Dict[str, Any], logger=None) -> bool:
    """
    Save scraped data to database with error handling

    Args:
        table_name: Name of the database table
        data: Dictionary containing data to save
        logger: Logger instance (optional)

    Returns:
        True if successful, False otherwise
    """
    try:
        record = {
            'ticker': data['ticker'],
            'fund_name': data['fund_name'],
            'url': data.get('url'),
            'scraped_at': datetime.utcnow().isoformat(),
            **{k: v for k, v in data.items() if k not in ['ticker', 'fund_name', 'url']}
        }

        result = supabase_upsert(table_name, [record])

        if result:
            if logger:
                logger.info(f"✅ Saved {data['ticker']} data to database")
            return True
        else:
            if logger:
                logger.error(f"❌ Failed to save {data['ticker']} to database")
            return False
    except Exception as e:
        if logger:
            logger.error(f"❌ Error saving {data.get('ticker', 'unknown')} to database: {e}")
        return False


def scrape_with_retry(
    scrape_func: Callable,
    max_retries: int = 3,
    retry_delay: int = 5,
    logger=None
) -> Optional[Any]:
    """
    Execute a scraping function with retry logic

    Args:
        scrape_func: Function to execute (should return data or None)
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries
        logger: Logger instance (optional)

    Returns:
        Result from scrape_func or None if all retries failed
    """
    for attempt in range(1, max_retries + 1):
        try:
            result = scrape_func()
            if result is not None:
                return result

            if logger and attempt < max_retries:
                logger.warning(f"Attempt {attempt}/{max_retries} returned no data, retrying...")
        except Exception as e:
            if logger:
                logger.error(f"Attempt {attempt}/{max_retries} failed: {e}")

        if attempt < max_retries:
            if logger:
                logger.info(f"Waiting {retry_delay} seconds before retry...")
            time.sleep(retry_delay)

    if logger:
        logger.error(f"All {max_retries} attempts failed")
    return None


class BaseETFScraper:
    """
    Base class for ETF scrapers with common functionality
    """

    def __init__(self, ticker: str, fund_name: str, url: str, table_name: str, logger=None):
        """
        Initialize the base scraper

        Args:
            ticker: ETF ticker symbol
            fund_name: Full fund name
            url: ETF page URL
            table_name: Database table name
            logger: Logger instance (optional)
        """
        self.ticker = ticker
        self.fund_name = fund_name
        self.url = url
        self.table_name = table_name
        self.logger = logger or setup_logging()

    def scrape_data(self) -> Optional[Dict[str, Any]]:
        """
        Scrape data from the ETF page (to be implemented by subclasses)

        Returns:
            Dictionary containing scraped data or None if error
        """
        raise NotImplementedError("Subclasses must implement scrape_data()")

    def save_data(self, data: Dict[str, Any]) -> bool:
        """
        Save scraped data to database

        Args:
            data: Dictionary containing data to save

        Returns:
            True if successful, False otherwise
        """
        return save_to_database(self.table_name, data, self.logger)

    def run(self) -> bool:
        """
        Run the complete scraping process

        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"📊 Starting scrape for {self.ticker} - {self.fund_name}")

        # Scrape data with retry
        data = scrape_with_retry(
            self.scrape_data,
            max_retries=3,
            retry_delay=5,
            logger=self.logger
        )

        if data is None:
            self.logger.error(f"❌ Failed to scrape {self.ticker}")
            return False

        # Save to database
        success = self.save_data(data)

        if success:
            self.logger.info(f"✅ Completed scrape for {self.ticker}")
        else:
            self.logger.error(f"❌ Failed to save {self.ticker} to database")

        return success


def batch_scrape_etfs(
    etf_configs: Dict[str, Dict[str, str]],
    scraper_class,
    table_name: str,
    tickers: Optional[List[str]] = None,
    delay_between_requests: int = 2,
    logger=None
) -> Dict[str, Any]:
    """
    Batch scrape multiple ETFs with rate limiting

    Args:
        etf_configs: Dictionary mapping tickers to config dicts (name, url)
        scraper_class: Scraper class to use (must accept ticker, name, url, table_name, logger)
        table_name: Database table name
        tickers: Optional list of specific tickers to scrape (None = all)
        delay_between_requests: Delay in seconds between requests
        logger: Logger instance (optional)

    Returns:
        Dictionary with statistics (total, success, failed, duration)
    """
    if logger is None:
        logger = setup_logging()

    # Filter tickers if specified
    if tickers:
        etf_configs = {t: etf_configs[t] for t in tickers if t in etf_configs}

    total = len(etf_configs)
    success_count = 0
    failed_count = 0

    logger.info(f"🚀 Starting batch scrape of {total} ETFs")
    start_time = time.time()

    for idx, (ticker, config) in enumerate(etf_configs.items(), 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {idx}/{total}: {ticker}")
        logger.info(f"{'='*80}")

        try:
            scraper = scraper_class(
                ticker=ticker,
                fund_name=config['name'],
                url=config['url'],
                table_name=table_name,
                logger=logger
            )

            if scraper.run():
                success_count += 1
            else:
                failed_count += 1

        except Exception as e:
            logger.error(f"❌ Error processing {ticker}: {e}")
            failed_count += 1

        # Rate limiting
        if idx < total:
            logger.info(f"⏳ Waiting {delay_between_requests} seconds before next request...")
            time.sleep(delay_between_requests)

    duration = time.time() - start_time

    logger.info(f"\n{'='*80}")
    logger.info(f"📊 Batch Scrape Complete")
    logger.info(f"{'='*80}")
    logger.info(f"Total: {total}")
    logger.info(f"Success: {success_count}")
    logger.info(f"Failed: {failed_count}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Average: {duration/total:.2f} seconds per ETF")

    return {
        'total': total,
        'success': success_count,
        'failed': failed_count,
        'duration': duration
    }
