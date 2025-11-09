"""
Alpha Vantage API Client

Client for fetching stock data from Alpha Vantage API.
NASDAQ official vendor with fast updates for new symbols.
"""

import logging
import csv
import io
import requests
from typing import Optional, Dict, Any, List
from datetime import date, datetime

from lib.core.config import Config
from lib.core.rate_limiters import GlobalRateLimiters
from lib.data_sources.base_client import DataSourceClient

logger = logging.getLogger(__name__)


class AlphaVantageClient(DataSourceClient):
    """
    Alpha Vantage API client.

    Provides access to:
    - Historical price data with adjusted close
    - Dividend data from daily adjusted series
    - Symbol listing (LISTING_STATUS endpoint)
    - NASDAQ official vendor - fast updates
    """

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Alpha Vantage client.

        Args:
            api_key: Alpha Vantage API key (defaults to Config.API.ALPHA_VANTAGE_API_KEY)
        """
        self.api_key = api_key or Config.API.ALPHA_VANTAGE_API_KEY

        # Initialize with global Alpha Vantage rate limiter
        rate_limiter = GlobalRateLimiters.get_alpha_vantage_limiter(
            max_concurrent=Config.API.ALPHA_VANTAGE_CONCURRENT_REQUESTS
        )

        super().__init__(
            name="Alpha Vantage",
            rate_limiter=rate_limiter,
            timeout=Config.API.REQUEST_TIMEOUT,
            max_retries=Config.API.MAX_RETRIES
        )

    def is_available(self) -> bool:
        """Check if Alpha Vantage is available and properly configured."""
        if not self.api_key:
            logger.warning("[Alpha Vantage] API key not configured")
            return False
        return True

    def fetch_prices(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch historical price data from Alpha Vantage.

        Uses TIME_SERIES_DAILY_ADJUSTED to get adjusted close prices.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date (not used - AV returns full history)

        Returns:
            Dictionary with price data
        """
        if not self.is_available():
            return None

        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'apikey': self.api_key,
                'outputsize': 'full'
            }

            logger.debug(f"[Alpha Vantage] Fetching prices for {symbol}")

            with self.rate_limiter.limit():
                response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)

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
                                    'adjClose': float(daily_data['5. adjusted close']),
                                    'volume': int(daily_data['6. volume'])
                                })
                            except (ValueError, KeyError) as e:
                                logger.debug(
                                    f"[Alpha Vantage] Skipping invalid price data "
                                    f"for {symbol} on {date_str}: {e}"
                                )
                                continue

                        if price_data:
                            logger.debug(
                                f"[Alpha Vantage] Found {len(price_data)} price records for {symbol}"
                            )
                            return {
                                'source': 'Alpha Vantage',
                                'data': price_data,
                                'count': len(price_data)
                            }

                    elif 'Error Message' in data:
                        logger.debug(f"[Alpha Vantage] Error: {data['Error Message']}")
                    elif 'Note' in data:
                        logger.debug(f"[Alpha Vantage] Rate limited: {data['Note']}")

        except Exception as e:
            logger.error(f"[Alpha Vantage] Prices error for {symbol}: {e}")

        return None

    def fetch_dividends(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch dividend data from Alpha Vantage.

        Extracts dividends from TIME_SERIES_DAILY_ADJUSTED data.
        Field "7. dividend amount" contains the dividend on payment dates.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date (not used - AV returns full history)

        Returns:
            Dictionary with dividend data
        """
        if not self.is_available():
            return None

        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'apikey': self.api_key,
                'outputsize': 'full'
            }

            logger.debug(f"[Alpha Vantage] Fetching dividend data for {symbol}")

            with self.rate_limiter.limit():
                response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()

                    if 'Time Series (Daily)' in data:
                        time_series = data['Time Series (Daily)']

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
                                logger.debug(
                                    f"[Alpha Vantage] Skipping invalid dividend data "
                                    f"for {symbol} on {date_str}: {e}"
                                )
                                continue

                        if dividend_data:
                            logger.debug(
                                f"[Alpha Vantage] Found {len(dividend_data)} dividend records for {symbol}"
                            )
                            return {
                                'source': 'Alpha Vantage',
                                'data': dividend_data,
                                'count': len(dividend_data)
                            }
                        else:
                            logger.debug(f"[Alpha Vantage] No dividends found for {symbol}")
                            return None

        except Exception as e:
            logger.error(f"[Alpha Vantage] Dividends error for {symbol}: {e}")

        return None

    def fetch_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company information from Alpha Vantage.

        Uses OVERVIEW endpoint for company fundamentals.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Dictionary with company info
        """
        if not self.is_available():
            return None

        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }

            logger.debug(f"[Alpha Vantage] Fetching company overview for {symbol}")

            with self.rate_limiter.limit():
                response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()

                    if data and 'Symbol' in data:
                        return {
                            'source': 'Alpha Vantage',
                            'symbol': data.get('Symbol'),
                            'company_name': data.get('Name'),
                            'description': data.get('Description'),
                            'sector': data.get('Sector'),
                            'industry': data.get('Industry'),
                            'exchange': data.get('Exchange'),
                            'currency': data.get('Currency'),
                            'country': data.get('Country'),
                            'market_cap': data.get('MarketCapitalization'),
                            'employees': data.get('FullTimeEmployees'),
                            'dividend_yield': data.get('DividendYield'),
                            'pe_ratio': data.get('PERatio'),
                            'forward_pe': data.get('ForwardPE')
                        }

        except Exception as e:
            logger.error(f"[Alpha Vantage] Company info error for {symbol}: {e}")

        return None

    def discover_symbols(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discover symbols from Alpha Vantage LISTING_STATUS endpoint.

        Returns comprehensive listing of all US-traded securities.

        Args:
            limit: Optional limit on number of symbols to return

        Returns:
            List of symbol dictionaries
        """
        if not self.is_available():
            return []

        logger.info(
            f"[Alpha Vantage] Discovering symbols from LISTING_STATUS "
            f"(limit: {'None - fetching ALL' if limit is None else limit})"
        )

        symbols = []

        try:
            # Clean up API key (remove any formatting issues)
            api_key = self.api_key.strip().rstrip('%')
            url = f"{self.BASE_URL}?function=LISTING_STATUS&apikey={api_key}"

            with self.rate_limiter.limit():
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()

                # Check if response is JSON (error) or CSV (success)
                if response.text.strip().startswith('{'):
                    logger.warning(
                        f"[Alpha Vantage] API returned JSON error: {response.text[:100]}"
                    )
                    raise Exception("API key issue or rate limit exceeded")

                # Parse CSV response
                csv_data = io.StringIO(response.text)
                csv_reader = csv.DictReader(csv_data)

                count = 0
                exchange_map = {
                    'NYSE ARCA': 'AMEX',
                    'NASDAQ': 'NASDAQ',
                    'NYSE': 'NYSE',
                    'BATS': 'BATS'
                }
                allowed_exchanges = Config.EXCHANGE.ALLOWED_EXCHANGES

                for row in csv_reader:
                    if limit is not None and count >= limit:
                        break

                    symbol = row.get('symbol', '').strip()
                    name = row.get('name', '').strip()
                    exchange = row.get('exchange', '').strip()
                    asset_type = row.get('assetType', '').strip()
                    status = row.get('status', '').strip()

                    # Map Alpha Vantage exchange names to standard names
                    mapped_exchange = exchange_map.get(exchange, exchange)

                    # Filter for active stocks and ETFs on major exchanges
                    if (symbol and status == 'Active' and
                        asset_type in ['Stock', 'ETF'] and
                        mapped_exchange in allowed_exchanges):

                        symbols.append({
                            'symbol': symbol,
                            'name': name,
                            'source': f'AV-LISTING-{mapped_exchange}',
                            'exchange': mapped_exchange,
                            'asset_type': asset_type
                        })
                        count += 1

                logger.info(f"[Alpha Vantage] Discovered {len(symbols)} symbols from LISTING_STATUS")

        except Exception as e:
            logger.error(f"[Alpha Vantage] LISTING_STATUS discovery failed: {e}")
            logger.warning("[Alpha Vantage] API failed - returning empty list")

        return symbols


# Export Alpha Vantage client
__all__ = ['AlphaVantageClient']
