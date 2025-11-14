"""
Yahoo Finance Client

Client for fetching stock data using yfinance library.
Provides excellent coverage including newest ETFs and alternative data.
"""

import logging
import pandas as pd
import yfinance as yf
from typing import Optional, Dict, Any, List
from datetime import date, datetime, timedelta

from lib.core.config import Config
from lib.core.rate_limiters import GlobalRateLimiters
from lib.data_sources.base_client import DataSourceClient

logger = logging.getLogger(__name__)


class YahooClient(DataSourceClient):
    """
    Yahoo Finance client using yfinance library.

    Provides access to:
    - Historical price data with adjusted prices
    - Dividend history
    - Company/ETF metadata (including AUM for ETFs)
    - Free access with excellent coverage
    """

    def __init__(self):
        """Initialize Yahoo Finance client."""
        # Initialize with global Yahoo rate limiter
        rate_limiter = GlobalRateLimiters.get_yahoo_limiter(
            max_concurrent=Config.API.YAHOO_CONCURRENT_REQUESTS
        )

        super().__init__(
            name="Yahoo Finance",
            rate_limiter=rate_limiter,
            timeout=Config.API.REQUEST_TIMEOUT,
            max_retries=Config.API.MAX_RETRIES
        )

    def is_available(self) -> bool:
        """Check if Yahoo Finance is available."""
        # Yahoo Finance is always available (no API key required)
        return Config.DATA_FETCH.FALLBACK_TO_YAHOO

    def fetch_prices(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch historical price data from Yahoo Finance.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date (not used - Yahoo returns max history)

        Returns:
            Dictionary with price data including AUM for ETFs
        """
        if not self.is_available():
            return None

        try:
            with self.rate_limiter.limit():
                logger.debug(f"[Yahoo] Fetching prices for {symbol}")
                ticker = yf.Ticker(symbol)

                # Get AUM (total assets) for ETFs - this is current value
                aum = None
                try:
                    info = ticker.info
                    aum = info.get('totalAssets')
                    if aum:
                        logger.debug(f"[Yahoo] Found AUM for {symbol}: ${aum:,.0f}")
                except:
                    pass  # AUM not available for this symbol

                # Get historical prices with auto_adjust=False to get both raw and adjusted close
                # Using download() instead of history() to access unadjusted prices
                hist = yf.download(symbol, period="max", auto_adjust=False, progress=False)

                if not hist.empty:
                    # Convert to format similar to FMP
                    price_data = []
                    for date_idx, row in hist.iterrows():
                        # Handle multi-column index from download()
                        try:
                            record = {
                                'date': date_idx.strftime('%Y-%m-%d'),
                                'open': float(row['Open'].iloc[0] if hasattr(row['Open'], 'iloc') else row['Open']),
                                'high': float(row['High'].iloc[0] if hasattr(row['High'], 'iloc') else row['High']),
                                'low': float(row['Low'].iloc[0] if hasattr(row['Low'], 'iloc') else row['Low']),
                                'close': float(row['Close'].iloc[0] if hasattr(row['Close'], 'iloc') else row['Close']),
                                'adjClose': float(row['Adj Close'].iloc[0] if hasattr(row['Adj Close'], 'iloc') else row['Adj Close']),
                                'volume': int(row['Volume'].iloc[0] if hasattr(row['Volume'], 'iloc') else row['Volume']) if not pd.isna(row['Volume'].iloc[0] if hasattr(row['Volume'], 'iloc') else row['Volume']) else 0
                            }
                            # Add AUM to ALL records for daily AUM tracking (if available)
                            # Note: AUM represents current assets, recorded daily to track growth over time
                            if aum:
                                record['aum'] = int(aum)
                            price_data.append(record)
                        except Exception as e:
                            logger.debug(f"[Yahoo] Skipping invalid price record for {symbol} on {date_idx}: {e}")
                            continue

                    if price_data:
                        # Report success to rate limiter
                        if hasattr(self.rate_limiter, 'report_success'):
                            self.rate_limiter.report_success()

                        return {
                            'source': 'Yahoo Finance',
                            'data': price_data,
                            'count': len(price_data),
                            'aum': aum  # Also include AUM at top level
                        }

        except Exception as e:
            error_msg = str(e)

            # Check if it's a rate limit error
            if 'Too Many Requests' in error_msg or '429' in error_msg or 'Rate limited' in error_msg:
                logger.error(f"[Yahoo] Prices error for {symbol}: {e}")
                # Report rate limit to adaptive limiter
                if hasattr(self.rate_limiter, 'report_rate_limit'):
                    self.rate_limiter.report_rate_limit()
            else:
                logger.error(f"[Yahoo] Prices error for {symbol}: {e}")
                # Report general error
                if hasattr(self.rate_limiter, 'report_error'):
                    self.rate_limiter.report_error()

        return None

    def fetch_dividends(self, symbol: str, from_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch historical dividend data from Yahoo Finance.

        Args:
            symbol: Stock/ETF symbol
            from_date: Optional start date (not used - Yahoo returns max history)

        Returns:
            Dictionary with dividend data
        """
        if not self.is_available():
            return None

        try:
            with self.rate_limiter.limit():
                logger.debug(f"[Yahoo] Fetching dividends for {symbol}")
                ticker = yf.Ticker(symbol)

                # Get dividend history
                dividends = ticker.dividends

                if not dividends.empty:
                    # Convert to format similar to FMP
                    dividend_data = []
                    for date_idx, amount in dividends.items():
                        dividend_data.append({
                            'date': date_idx.strftime('%Y-%m-%d'),
                            'amount': float(amount),
                            'adjDividend': float(amount),
                            'label': f"{date_idx.strftime('%B %d, %y')}"
                        })

                    # Report success to rate limiter
                    if hasattr(self.rate_limiter, 'report_success'):
                        self.rate_limiter.report_success()

                    return {
                        'source': 'Yahoo Finance',
                        'data': dividend_data,
                        'count': len(dividend_data)
                    }

        except Exception as e:
            error_msg = str(e)

            # Check if it's a rate limit error
            if 'Too Many Requests' in error_msg or '429' in error_msg or 'Rate limited' in error_msg:
                logger.error(f"[Yahoo] Dividends error for {symbol}: {e}")
                # Report rate limit to adaptive limiter
                if hasattr(self.rate_limiter, 'report_rate_limit'):
                    self.rate_limiter.report_rate_limit()
            else:
                logger.error(f"[Yahoo] Dividends error for {symbol}: {e}")
                # Report general error
                if hasattr(self.rate_limiter, 'report_error'):
                    self.rate_limiter.report_error()

        return None

    def fetch_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company/ETF information from Yahoo Finance.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Dictionary with company/ETF info
        """
        if not self.is_available():
            return None

        try:
            with self.rate_limiter.limit():
                logger.debug(f"[Yahoo] Fetching company info for {symbol}")
                ticker = yf.Ticker(symbol)
                info = ticker.info

                if info:
                    # Determine if it's an ETF
                    quote_type = info.get('quoteType', '')
                    is_etf = quote_type == 'ETF'

                    # Extract company name or fund family
                    company_name = None
                    if is_etf:
                        # For ETFs, try fundFamily first, then longName
                        company_name = info.get('fundFamily') or info.get('longName')
                    else:
                        # For stocks, use longName or shortName
                        company_name = info.get('longName') or info.get('shortName')

                    # Get expense ratio - try both fields (reported as percentage like 1.28 for 1.28%)
                    expense_ratio = None
                    if is_etf:
                        expense_ratio = info.get('annualReportExpenseRatio') or info.get('netExpenseRatio')
                        # Convert from percentage (1.28) to decimal (0.0128) if needed
                        if expense_ratio and expense_ratio > 1:
                            expense_ratio = expense_ratio / 100

                    # Get AUM - try totalAssets or netAssets
                    aum = None
                    if is_etf:
                        aum = info.get('totalAssets') or info.get('netAssets')

                    # Get inception date and convert timestamp to date
                    inception_date = None
                    if is_etf:
                        inception_ts = info.get('fundInceptionDate')
                        if inception_ts:
                            try:
                                inception_date = datetime.fromtimestamp(inception_ts).date()
                            except:
                                pass  # Invalid timestamp

                    # Report success to rate limiter
                    if hasattr(self.rate_limiter, 'report_success'):
                        self.rate_limiter.report_success()

                    return {
                        'source': 'Yahoo Finance',
                        'symbol': symbol,
                        'company_name': company_name,
                        'fund_family': info.get('fundFamily') if is_etf else None,
                        'description': info.get('longBusinessSummary'),
                        'sector': info.get('sector'),
                        'industry': info.get('industry'),
                        'website': info.get('website'),
                        'employees': info.get('fullTimeEmployees'),
                        'market_cap': info.get('marketCap'),
                        'exchange': info.get('exchange'),
                        'currency': info.get('currency'),
                        'country': info.get('country'),
                        'is_etf': is_etf,
                        # ETF-specific fields
                        'aum': aum,
                        'expense_ratio': expense_ratio,
                        'inception_date': inception_date,
                        # Additional metadata
                        'quote_type': quote_type,
                        'dividend_yield': info.get('dividendYield'),
                        'trailing_pe': info.get('trailingPE'),
                        'forward_pe': info.get('forwardPE')
                    }

        except Exception as e:
            error_msg = str(e)

            # Check if it's a rate limit error
            if 'Too Many Requests' in error_msg or '429' in error_msg or 'Rate limited' in error_msg:
                logger.error(f"[Yahoo] Company info error for {symbol}: {e}")
                # Report rate limit to adaptive limiter
                if hasattr(self.rate_limiter, 'report_rate_limit'):
                    self.rate_limiter.report_rate_limit()
            else:
                logger.error(f"[Yahoo] Company info error for {symbol}: {e}")
                # Report general error
                if hasattr(self.rate_limiter, 'report_error'):
                    self.rate_limiter.report_error()

        return None

    def fetch_future_dividends(self, symbol: str,
                              include_predictions: bool = True) -> Optional[Dict[str, Any]]:
        """
        Fetch future dividend information from Yahoo Finance.

        Args:
            symbol: Stock/ETF symbol
            include_predictions: Include predicted dividends based on history

        Returns:
            Dictionary with future dividend data
        """
        if not self.is_available():
            return None

        try:
            with self.rate_limiter.limit():
                logger.debug(f"[Yahoo] Fetching future dividends for {symbol}")
                ticker = yf.Ticker(symbol)
                info = ticker.info

                future_dividends = []

                # Get next dividend date and amount from info
                ex_dividend_date = info.get('exDividendDate')
                dividend_rate = info.get('dividendRate')

                if ex_dividend_date and dividend_rate:
                    # Convert timestamp to date
                    if isinstance(ex_dividend_date, int):
                        ex_date = datetime.fromtimestamp(ex_dividend_date).date()
                    else:
                        ex_date = ex_dividend_date

                    # Only include if it's in the future
                    if ex_date > datetime.now().date():
                        future_dividends.append({
                            'symbol': symbol,
                            'date': ex_date.strftime('%Y-%m-%d'),
                            'amount': dividend_rate,
                            'source': 'Yahoo-Scheduled',
                            'is_prediction': False
                        })

                # Optionally predict future dividends based on history
                if include_predictions:
                    dividends = ticker.dividends
                    if not dividends.empty and len(dividends) >= 4:
                        # Calculate average frequency and amount
                        dates = dividends.index
                        intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
                        avg_interval = sum(intervals) / len(intervals)
                        avg_amount = dividends.tail(4).mean()

                        # Predict next 3 dividends
                        last_date = dates[-1].date()
                        for i in range(1, 4):
                            predicted_date = last_date + timedelta(days=int(avg_interval * i))
                            if predicted_date > datetime.now().date():
                                future_dividends.append({
                                    'symbol': symbol,
                                    'date': predicted_date.strftime('%Y-%m-%d'),
                                    'amount': float(avg_amount),
                                    'source': 'Yahoo-Predicted',
                                    'is_prediction': True
                                })

                if future_dividends:
                    # Report success to rate limiter
                    if hasattr(self.rate_limiter, 'report_success'):
                        self.rate_limiter.report_success()

                    return {
                        'source': 'Yahoo Finance',
                        'data': future_dividends,
                        'count': len(future_dividends)
                    }

        except Exception as e:
            error_msg = str(e)

            # Check if it's a rate limit error
            if 'Too Many Requests' in error_msg or '429' in error_msg or 'Rate limited' in error_msg:
                logger.error(f"[Yahoo] Future dividends error for {symbol}: {e}")
                # Report rate limit to adaptive limiter
                if hasattr(self.rate_limiter, 'report_rate_limit'):
                    self.rate_limiter.report_rate_limit()
            else:
                logger.error(f"[Yahoo] Future dividends error for {symbol}: {e}")
                # Report general error
                if hasattr(self.rate_limiter, 'report_error'):
                    self.rate_limiter.report_error()

        return None

    def discover_symbols(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Symbol discovery not supported by Yahoo Finance.

        Yahoo Finance doesn't provide a comprehensive symbol list API.
        Use FMP or Alpha Vantage for symbol discovery instead.

        Returns:
            Empty list
        """
        logger.info("[Yahoo] Symbol discovery not supported - use FMP or Alpha Vantage instead")
        return []


# Export Yahoo client
__all__ = ['YahooClient']
