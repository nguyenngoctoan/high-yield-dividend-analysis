"""
Symbol Validator Module

Validates discovered symbols to determine if they meet criteria for inclusion.
Checks for recent price activity and dividend history.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from lib.core.config import Config
from lib.core.models import ValidationResult
from lib.data_sources.fmp_client import FMPClient
from lib.data_sources.alpha_vantage_client import AlphaVantageClient
from lib.data_sources.yahoo_client import YahooClient

logger = logging.getLogger(__name__)


class SymbolValidator:
    """
    Validates symbols to determine if they should be included in the database.

    Validation criteria:
    1. Must have recent price data (within 7 days) OR
    2. Must have dividend history (within 365 days) OR
    3. Symbol is in a user's portfolio (bypass validation)
    """

    def __init__(self, fmp_client: Optional[FMPClient] = None,
                 portfolio_symbols: Optional[set] = None):
        """
        Initialize validator.

        Args:
            fmp_client: Optional FMP client (creates new one if not provided)
            portfolio_symbols: Optional set of symbols in user portfolios that bypass validation
        """
        self.fmp_client = fmp_client or FMPClient()
        self.av_client = AlphaVantageClient() if Config.FEATURES.ENABLE_ALPHA_VANTAGE else None
        self.yahoo_client = YahooClient() if Config.FEATURES.ENABLE_YAHOO else None
        self.portfolio_symbols = portfolio_symbols or set()

        if self.portfolio_symbols:
            logger.info(f"📋 Loaded {len(self.portfolio_symbols)} portfolio symbols for validation bypass")

    def validate_symbol(self, symbol: str,
                       symbol_data: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate a symbol against criteria.

        Args:
            symbol: Stock/ETF symbol to validate
            symbol_data: Optional additional data about the symbol

        Returns:
            ValidationResult with validation outcome
        """
        logger.debug(f"🔍 Validating symbol: {symbol}")

        # Check if symbol is in portfolio - bypass validation if so
        if symbol in self.portfolio_symbols:
            logger.info(f"✅ {symbol}: Portfolio symbol - bypassing strict validation")
            return ValidationResult(
                symbol=symbol,
                is_valid=True,
                has_recent_price=False,  # Unknown, but not required
                has_dividend_history=False,  # Unknown, but not required
                last_price_date=None,
                last_dividend_date=None,
                exclusion_reason=None,
                validation_messages=["Portfolio symbol - validation bypassed"]
            )

        # Check if this is an Alpha Vantage-discovered symbol
        source = symbol_data.get('source', '') if symbol_data else ''
        is_av_symbol = 'AV' in source or 'Alpha Vantage' in source

        # Prepare date ranges
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=Config.DATA_FETCH.MAX_DAYS_SINCE_PRICE)
        one_year_ago = today - timedelta(days=Config.DATA_FETCH.MIN_DIVIDEND_LOOKBACK_DAYS)

        has_recent_price = False
        has_dividend_history = False
        last_price_date = None
        last_dividend_date = None
        messages = []

        # For AV-discovered symbols, use AV first then Yahoo fallback
        if is_av_symbol:
            logger.debug(f"🔍 {symbol}: Alpha Vantage-discovered symbol, using AV/Yahoo validation")

            # Try Alpha Vantage for prices
            if self.av_client and self.av_client.is_available():
                try:
                    prices = self.av_client.fetch_prices(symbol, from_date=seven_days_ago)
                    if prices and prices.get('data'):
                        has_recent_price = True
                        # AV returns oldest first, so last item is most recent
                        last_price_date = datetime.strptime(
                            prices['data'][-1]['date'],
                            '%Y-%m-%d'
                        ).date()
                        messages.append(
                            f"Has recent price data from AV ({len(prices['data'])} records, "
                            f"latest: {last_price_date})"
                        )
                        logger.debug(f"✅ {symbol}: {messages[-1]}")
                except Exception as e:
                    messages.append(f"AV prices failed: {str(e)[:50]}")
                    logger.debug(f"⚠️  {symbol}: {messages[-1]}")

            # If AV didn't have prices, try Yahoo
            if not has_recent_price and self.yahoo_client:
                try:
                    prices = self.yahoo_client.fetch_prices(symbol, from_date=seven_days_ago)
                    if prices and prices.get('data'):
                        has_recent_price = True
                        # Yahoo returns newest first
                        last_price_date = datetime.strptime(
                            prices['data'][0]['date'],
                            '%Y-%m-%d'
                        ).date()
                        messages.append(
                            f"Has recent price data from Yahoo ({len(prices['data'])} records, "
                            f"latest: {last_price_date})"
                        )
                        logger.debug(f"✅ {symbol}: {messages[-1]}")
                except Exception as e:
                    messages.append(f"Yahoo prices failed: {str(e)[:50]}")
                    logger.debug(f"⚠️  {symbol}: {messages[-1]}")

            # Try Alpha Vantage for dividends
            if self.av_client and self.av_client.is_available():
                try:
                    dividends = self.av_client.fetch_dividends(symbol, from_date=one_year_ago)
                    if dividends and dividends.get('data'):
                        has_dividend_history = True
                        # AV returns oldest first, so last item is most recent
                        last_dividend_date = datetime.strptime(
                            dividends['data'][-1]['date'],
                            '%Y-%m-%d'
                        ).date()
                        messages.append(
                            f"Has dividend history from AV ({len(dividends['data'])} records, "
                            f"latest: {last_dividend_date})"
                        )
                        logger.debug(f"✅ {symbol}: {messages[-1]}")
                except Exception as e:
                    messages.append(f"AV dividends failed: {str(e)[:50]}")
                    logger.debug(f"⚠️  {symbol}: {messages[-1]}")

            # If AV didn't have dividends, try Yahoo
            if not has_dividend_history and self.yahoo_client:
                try:
                    dividends = self.yahoo_client.fetch_dividends(symbol, from_date=one_year_ago)
                    if dividends and dividends.get('data'):
                        has_dividend_history = True
                        # Yahoo returns newest first
                        last_dividend_date = datetime.strptime(
                            dividends['data'][0]['date'],
                            '%Y-%m-%d'
                        ).date()
                        messages.append(
                            f"Has dividend history from Yahoo ({len(dividends['data'])} records, "
                            f"latest: {last_dividend_date})"
                        )
                        logger.debug(f"✅ {symbol}: {messages[-1]}")
                except Exception as e:
                    messages.append(f"Yahoo dividends failed: {str(e)[:50]}")
                    logger.debug(f"⚠️  {symbol}: {messages[-1]}")

        # For non-AV symbols, use FMP (original behavior)
        else:
            # Check for recent price activity
            try:
                prices = self.fmp_client.fetch_prices(symbol, from_date=seven_days_ago)
                if prices and prices.get('data'):
                    has_recent_price = True
                    # Get most recent date (FMP returns newest first)
                    last_price_date = datetime.strptime(
                        prices['data'][0]['date'],
                        '%Y-%m-%d'
                    ).date()
                    messages.append(
                        f"Has recent price data ({len(prices['data'])} records, "
                        f"latest: {last_price_date})"
                    )
                    logger.debug(f"✅ {symbol}: {messages[-1]}")
            except Exception as e:
                messages.append(f"Could not check recent prices: {e}")
                logger.debug(f"⚠️  {symbol}: {messages[-1]}")

            # Check for dividend history
            try:
                dividends = self.fmp_client.fetch_dividends(symbol, from_date=one_year_ago)
                if dividends and dividends.get('data'):
                    has_dividend_history = True
                    # Get most recent dividend date
                    last_dividend_date = datetime.strptime(
                        dividends['data'][0]['date'],
                        '%Y-%m-%d'
                    ).date()
                    messages.append(
                        f"Has dividend history ({len(dividends['data'])} records, "
                        f"latest: {last_dividend_date})"
                    )
                    logger.debug(f"✅ {symbol}: {messages[-1]}")
            except Exception as e:
                messages.append(f"Could not check dividends: {e}")
                logger.debug(f"⚠️  {symbol}: {messages[-1]}")

        # Determine if symbol meets criteria
        is_valid = has_recent_price or has_dividend_history

        # Determine exclusion reason if invalid
        exclusion_reason = None
        if not is_valid:
            if not has_recent_price and not has_dividend_history:
                exclusion_reason = (
                    f"No recent price data (within {Config.DATA_FETCH.MAX_DAYS_SINCE_PRICE} days) "
                    f"and no dividend history (within {Config.DATA_FETCH.MIN_DIVIDEND_LOOKBACK_DAYS} days)"
                )
            elif not has_recent_price:
                exclusion_reason = f"No recent price data (within {Config.DATA_FETCH.MAX_DAYS_SINCE_PRICE} days)"
            else:
                exclusion_reason = f"No dividend history (within {Config.DATA_FETCH.MIN_DIVIDEND_LOOKBACK_DAYS} days)"

            logger.debug(f"❌ {symbol}: Excluded - {exclusion_reason}")

        # Create validation result
        result = ValidationResult(
            symbol=symbol,
            is_valid=is_valid,
            has_recent_price=has_recent_price,
            has_dividend_history=has_dividend_history,
            last_price_date=last_price_date,
            last_dividend_date=last_dividend_date,
            exclusion_reason=exclusion_reason,
            validation_messages=messages
        )

        if is_valid:
            logger.debug(
                f"✅ {symbol}: Validated "
                f"(price: {has_recent_price}, dividend: {has_dividend_history})"
            )

        return result

    def validate_batch(self, symbols: list, max_workers: int = None) -> Dict[str, ValidationResult]:
        """
        Validate multiple symbols in parallel.

        Args:
            symbols: List of symbols or symbol dictionaries
            max_workers: Maximum number of parallel workers (default: FMP concurrent requests / 2)

        Returns:
            Dictionary mapping symbol -> ValidationResult
        """
        if max_workers is None:
            # Use half of FMP concurrent requests for validation (2 API calls per validation)
            max_workers = max(1, Config.API.FMP_CONCURRENT_REQUESTS // 2)

        logger.info(f"🔍 Validating {len(symbols)} symbols with {max_workers} parallel workers...")

        results = {}

        # Helper function to validate a single item
        def validate_item(item):
            # Handle both string symbols and dictionaries
            if isinstance(item, str):
                symbol = item
                symbol_data = None
            else:
                symbol = item.get('symbol')
                symbol_data = item

            if symbol:
                result = self.validate_symbol(symbol, symbol_data)
                return symbol, result
            return None, None

        # Use ThreadPoolExecutor for parallel validation
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {executor.submit(validate_item, item): item for item in symbols}

            # Process results as they complete with progress bar
            for future in tqdm(as_completed(futures), total=len(symbols), desc="Validating symbols", unit="symbol"):
                try:
                    symbol, result = future.result()
                    if symbol and result:
                        results[symbol] = result
                except Exception as e:
                    item = futures[future]
                    symbol_str = item if isinstance(item, str) else item.get('symbol', 'unknown')
                    logger.error(f"❌ Validation error for {symbol_str}: {e}")

        # Log summary
        valid_count = sum(1 for r in results.values() if r.is_valid)
        invalid_count = len(results) - valid_count

        logger.info(
            f"✅ Batch validation complete: "
            f"{valid_count} valid, {invalid_count} invalid, "
            f"{len(results)} total"
        )

        return results

    def get_valid_symbols(self, symbols: list) -> list:
        """
        Filter symbols to only those that are valid.

        Args:
            symbols: List of symbols or symbol dictionaries

        Returns:
            List of valid symbols (strings)
        """
        results = self.validate_batch(symbols)
        valid_symbols = [
            symbol for symbol, result in results.items()
            if result.is_valid
        ]

        logger.info(f"✅ Found {len(valid_symbols)}/{len(symbols)} valid symbols")
        return valid_symbols

    def get_invalid_symbols(self, symbols: list) -> Dict[str, str]:
        """
        Get invalid symbols with their exclusion reasons.

        Args:
            symbols: List of symbols or symbol dictionaries

        Returns:
            Dictionary mapping symbol -> exclusion_reason
        """
        results = self.validate_batch(symbols)
        invalid = {
            symbol: result.exclusion_reason
            for symbol, result in results.items()
            if not result.is_valid
        }

        logger.info(f"❌ Found {len(invalid)}/{len(symbols)} invalid symbols")
        return invalid


# Convenience functions for quick validation
def validate_symbol(symbol: str) -> ValidationResult:
    """
    Quick symbol validation function.

    Args:
        symbol: Symbol to validate

    Returns:
        ValidationResult

    Example:
        result = validate_symbol('AAPL')
        if result.is_valid:
            print(f"Valid! Has price: {result.has_recent_price}")
    """
    validator = SymbolValidator()
    return validator.validate_symbol(symbol)


def validate_symbols(symbols: list) -> Dict[str, ValidationResult]:
    """
    Quick batch validation function.

    Args:
        symbols: List of symbols

    Returns:
        Dictionary of ValidationResults

    Example:
        results = validate_symbols(['AAPL', 'MSFT', 'GOOGL'])
        valid = [s for s, r in results.items() if r.is_valid]
    """
    validator = SymbolValidator()
    return validator.validate_batch(symbols)


def get_valid_symbols(symbols: list) -> list:
    """
    Quick function to filter valid symbols.

    Args:
        symbols: List of symbols

    Returns:
        List of valid symbols

    Example:
        valid = get_valid_symbols(['AAPL', 'INVALID', 'MSFT'])
    """
    validator = SymbolValidator()
    return validator.get_valid_symbols(symbols)


# Export main classes and functions
__all__ = [
    'SymbolValidator',
    'validate_symbol',
    'validate_symbols',
    'get_valid_symbols'
]
