"""
Financial Modeling Prep (FMP) API Client

Client for fetching stock data, dividends, company info, and symbol discovery
from the Financial Modeling Prep API.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta

from lib.core.config import Config
from lib.core.rate_limiters import GlobalRateLimiters
from lib.data_sources.base_client import DataSourceClient

logger = logging.getLogger(__name__)


class FMPClient(DataSourceClient):
    """
    Financial Modeling Prep API client.

    Provides access to:
    - Historical and real-time price data
    - Dividend history and calendar
    - Company and ETF information
    - Symbol discovery and screening
    """

    BASE_URL = "https://financialmodelingprep.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FMP client.

        Args:
            api_key: FMP API key (defaults to Config.API.FMP_API_KEY)
        """
        self.api_key = api_key or Config.API.FMP_API_KEY

        # Initialize with global FMP rate limiter
        rate_limiter = GlobalRateLimiters.get_fmp_limiter(
            max_concurrent=Config.API.FMP_CONCURRENT_REQUESTS
        )

        super().__init__(
            name="FMP",
            rate_limiter=rate_limiter,
            timeout=Config.API.REQUEST_TIMEOUT,
            max_retries=Config.API.MAX_RETRIES
        )

    def is_available(self) -> bool:
        """Check if FMP is available and properly configured."""
        if not self.api_key or self.api_key == 'demo':
            logger.warning("[FMP] API key not configured or using demo key")
            return False
        return True

    def fetch_prices(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch historical price data from FMP.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date for historical data

        Returns:
            Dictionary with price data:
            {
                'source': 'FMP',
                'data': [list of price records],
                'count': number of records,
                'aum': optional AUM for ETFs
            }
        """
        try:
            # Build URL
            if from_date:
                from_str = from_date.strftime('%Y-%m-%d')
            else:
                from_str = Config.DATA_FETCH.PRICES_START_DATE

            url = (
                f"{self.BASE_URL}/api/v3/historical-price-full/{symbol}"
                f"?from={from_str}&apikey={self.api_key}"
            )

            logger.debug(f"[FMP] Fetching prices for {symbol}")
            data = self._fetch_with_retry(url, symbol=symbol)

            if data and 'historical' in data and data['historical']:
                # Try to get AUM for ETFs
                aum = None
                try:
                    etf_metadata = self.fetch_etf_metadata(symbol)
                    if etf_metadata and etf_metadata.get('aum'):
                        aum = etf_metadata['aum']
                        logger.debug(f"[FMP] Found AUM for {symbol}: ${aum:,.0f}")
                except:
                    pass  # Not an ETF or AUM not available

                # Add AUM to the most recent (first) record if available
                # FMP returns newest first, so index 0 is the most recent
                price_data = data['historical']
                if aum and len(price_data) > 0:
                    price_data[0]['aum'] = aum

                return {
                    'source': 'FMP',
                    'data': price_data,
                    'count': len(price_data),
                    'aum': aum
                }

        except Exception as e:
            logger.error(f"[FMP] Prices error for {symbol}: {e}")

        return None

    def fetch_dividends(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch historical dividend data from FMP.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date for historical data

        Returns:
            Dictionary with dividend data:
            {
                'source': 'FMP',
                'data': [list of dividend records],
                'count': number of records
            }
        """
        try:
            # Build URL
            if from_date:
                from_str = from_date.strftime('%Y-%m-%d')
            else:
                from_str = Config.DATA_FETCH.DIVIDENDS_START_DATE

            url = (
                f"{self.BASE_URL}/api/v3/historical-price-full/stock_dividend/{symbol}"
                f"?from={from_str}&apikey={self.api_key}"
            )

            logger.debug(f"[FMP] Fetching dividends for {symbol}")
            data = self._fetch_with_retry(url, symbol=symbol)

            if data and 'historical' in data and data['historical']:
                return {
                    'source': 'FMP',
                    'data': data['historical'],
                    'count': len(data['historical'])
                }

        except Exception as e:
            logger.error(f"[FMP] Dividends error for {symbol}: {e}")

        return None

    def fetch_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company profile from FMP.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with company info
        """
        try:
            url = f"{self.BASE_URL}/api/v3/profile/{symbol}?apikey={self.api_key}"

            logger.debug(f"[FMP] Fetching company profile for {symbol}")
            data = self._fetch_with_retry(url, symbol=symbol)

            if data and isinstance(data, list) and len(data) > 0:
                profile = data[0]
                return {
                    'source': 'FMP',
                    'symbol': profile.get('symbol'),
                    'company_name': profile.get('companyName'),
                    'description': profile.get('description'),
                    'sector': profile.get('sector'),
                    'industry': profile.get('industry'),
                    'website': profile.get('website'),
                    'ceo': profile.get('ceo'),
                    'employees': profile.get('fullTimeEmployees'),
                    'market_cap': profile.get('mktCap'),
                    'exchange': profile.get('exchangeShortName'),
                    'currency': profile.get('currency'),
                    'country': profile.get('country'),
                    'ipo_date': profile.get('ipoDate'),
                    'is_etf': profile.get('isEtf', False)
                }

        except Exception as e:
            logger.error(f"[FMP] Company info error for {symbol}: {e}")

        return None

    def fetch_etf_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ETF-specific information from FMP.

        Args:
            symbol: ETF symbol

        Returns:
            Dictionary with ETF info including fund family, expense ratio, etc.
        """
        try:
            url = f"{self.BASE_URL}/stable/etf/info?symbol={symbol}&apikey={self.api_key}"

            logger.debug(f"[FMP] Fetching ETF info for {symbol}")
            data = self._fetch_with_retry(url, symbol=symbol)

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
            logger.error(f"[FMP] ETF info error for {symbol}: {e}")

        return None

    def fetch_etf_metadata(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ETF metadata including AUM.

        Args:
            symbol: ETF symbol

        Returns:
            Dictionary with AUM and other metadata
        """
        # Try stable endpoint first
        etf_info = self.fetch_etf_info(symbol)
        if etf_info and etf_info.get('aum'):
            return {'aum': etf_info['aum'], 'source': 'FMP-ETF'}

        # Try profile endpoint as fallback
        profile = self.fetch_company_info(symbol)
        if profile:
            # Check if market cap can be used as AUM proxy for ETFs
            if profile.get('is_etf') and profile.get('market_cap'):
                return {'aum': profile['market_cap'], 'source': 'FMP-Profile'}

        return None

    def discover_symbols(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discover all available symbols from FMP.

        Args:
            limit: Optional limit on number of symbols to return

        Returns:
            List of symbol dictionaries
        """
        logger.info(
            f"[FMP] Discovering symbols "
            f"(limit: {'None - fetching ALL' if limit is None else limit})"
        )

        symbols = []

        try:
            url = f"{self.BASE_URL}/api/v3/available-traded/list?apikey={self.api_key}"
            data = self._fetch_with_retry(url)

            if data:
                items_to_process = data if limit is None else data[:limit]
                allowed_exchanges = Config.EXCHANGE.ALLOWED_EXCHANGES

                for item in items_to_process:
                    symbol = item.get('symbol', '').strip()
                    exchange = item.get('exchangeShortName', '')

                    if symbol and exchange in allowed_exchanges:
                        symbols.append({
                            'symbol': symbol,
                            'name': item.get('name', ''),
                            'source': f'FMP-{exchange}',
                            'exchange': exchange,
                            'price': item.get('price'),
                            'type': 'STOCK'
                        })

                logger.info(f"[FMP] Discovered {len(symbols)} symbols from allowed exchanges")
            else:
                logger.error("[FMP] Failed to fetch symbol list")

        except Exception as e:
            logger.error(f"[FMP] Discovery error: {e}")

        return symbols

    def discover_etfs(self) -> List[Dict[str, Any]]:
        """
        Discover all ETFs from FMP's comprehensive ETF list.

        Returns:
            List of ETF dictionaries
        """
        logger.info("[FMP] Discovering ALL ETFs from comprehensive list")

        symbols = []

        try:
            url = f"{self.BASE_URL}/api/v3/etf/list?apikey={self.api_key}"
            data = self._fetch_with_retry(url)

            if data and isinstance(data, list):
                logger.info(f"[FMP] Found {len(data)} ETFs in comprehensive list")

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

                logger.info(f"[FMP] Discovered {len(symbols)} ETFs from comprehensive list")
            else:
                logger.warning("[FMP] No ETF data returned from comprehensive list")

        except Exception as e:
            logger.error(f"[FMP] ETF list discovery failed: {e}")

        return symbols

    def discover_dividend_stocks(self, min_yield: float = 0.01,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discover dividend-paying stocks using FMP screener.

        Args:
            min_yield: Minimum dividend yield (default: 0.01 = 1%)
            limit: Optional limit on results

        Returns:
            List of dividend stock dictionaries
        """
        logger.info(
            f"[FMP] Discovering dividend stocks "
            f"(yield > {min_yield:.1%}, "
            f"limit: {'None - fetching ALL' if limit is None else limit})"
        )

        symbols = []

        try:
            # FMP API requires a limit parameter, use 10000 as high number if no limit
            api_limit = 10000 if limit is None else limit
            url = (
                f"{self.BASE_URL}/api/v3/stock-screener"
                f"?dividendYieldMoreThan={min_yield}&limit={api_limit}&apikey={self.api_key}"
            )

            data = self._fetch_with_retry(url)

            if data and isinstance(data, list):
                logger.info(f"[FMP] Found {len(data)} dividend stocks")
                allowed_exchanges = Config.EXCHANGE.ALLOWED_EXCHANGES

                for stock in data:
                    symbol = stock.get('symbol', '').strip()
                    name = stock.get('companyName', '')
                    exchange = stock.get('exchangeShortName', '')
                    dividend_yield = stock.get('dividendYield', 0)

                    if symbol and exchange in allowed_exchanges and dividend_yield > 0:
                        symbols.append({
                            'symbol': symbol,
                            'name': name,
                            'source': f'FMP-DIV-{exchange}',
                            'exchange': exchange,
                            'dividend_yield': dividend_yield
                        })

                logger.info(f"[FMP] Discovered {len(symbols)} dividend stocks")
            else:
                logger.warning("[FMP] No dividend stock data returned")

        except Exception as e:
            logger.error(f"[FMP] Dividend screener failed: {e}")

        return symbols

    def fetch_dividend_calendar(self, from_date: Optional[date] = None,
                               to_date: Optional[date] = None,
                               symbols: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch future dividend calendar from FMP.

        Args:
            from_date: Start date (default: today)
            to_date: End date (default: 3 months from now)
            symbols: Optional list of symbols to filter for

        Returns:
            Dictionary with future dividend data
        """
        try:
            # Set default date range if not provided
            if not from_date:
                from_date = datetime.now().date()
            if not to_date:
                to_date = (datetime.now() + timedelta(days=90)).date()

            from_str = from_date.strftime('%Y-%m-%d')
            to_str = to_date.strftime('%Y-%m-%d')

            url = (
                f"{self.BASE_URL}/api/v3/stock_dividend_calendar"
                f"?from={from_str}&to={to_str}&apikey={self.api_key}"
            )

            logger.info(f"[FMP] Fetching future dividends from {from_str} to {to_str}")
            data = self._fetch_with_retry(url)

            if data:
                future_dividends = []

                for dividend in data:
                    symbol = dividend.get('symbol', '').strip()

                    # Filter by symbols if provided
                    if symbols and symbol not in symbols:
                        continue

                    future_dividends.append({
                        'symbol': symbol,
                        'date': dividend.get('date'),
                        'amount': dividend.get('dividend'),
                        'record_date': dividend.get('recordDate'),
                        'payment_date': dividend.get('paymentDate'),
                        'declaration_date': dividend.get('declarationDate'),
                        'adj_dividend': dividend.get('adjDividend'),
                        'label': dividend.get('label')
                    })

                return {
                    'source': 'FMP',
                    'data': future_dividends,
                    'count': len(future_dividends),
                    'from_date': from_str,
                    'to_date': to_str
                }

        except Exception as e:
            logger.error(f"[FMP] Dividend calendar error: {e}")

        return None

    def fetch_etf_holdings(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ETF holdings from FMP.

        Args:
            symbol: ETF symbol

        Returns:
            Dictionary with holdings data:
            {
                'source': 'FMP',
                'symbol': symbol,
                'holdings': [list of holdings],
                'count': number of holdings,
                'updated_at': timestamp
            }
        """
        try:
            url = f"{self.BASE_URL}/stable/etf/holdings?symbol={symbol}&apikey={self.api_key}"

            logger.debug(f"[FMP] Fetching ETF holdings for {symbol}")
            data = self._fetch_with_retry(url, symbol=symbol)

            if data and isinstance(data, list) and len(data) > 0:
                # Get the most recent update timestamp from holdings
                updated_at = None
                if data[0].get('updatedAt'):
                    updated_at = data[0]['updatedAt']

                return {
                    'source': 'FMP',
                    'symbol': symbol,
                    'holdings': data,
                    'count': len(data),
                    'updated_at': updated_at
                }

        except Exception as e:
            logger.error(f"[FMP] ETF holdings error for {symbol}: {e}")

        return None


# Export FMP client
__all__ = ['FMPClient']
