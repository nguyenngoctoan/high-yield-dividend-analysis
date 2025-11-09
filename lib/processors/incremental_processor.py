"""
Incremental Data Processor Module

Provides intelligent incremental updates by checking the database for
the latest data date and only fetching newer data.
"""

import logging
from typing import Optional
from datetime import date, datetime, timedelta

from supabase_helpers import supabase_select

logger = logging.getLogger(__name__)


class IncrementalProcessor:
    """
    Base class for incremental data processing.

    Checks database for latest data and fetches only newer records.
    """

    @staticmethod
    def get_latest_price_date(symbol: str) -> Optional[date]:
        """
        Get the latest price date for a symbol from the database.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Latest price date or None if no data exists
        """
        try:
            result = supabase_select(
                'raw_stock_prices',
                columns='date',
                where_clause={'symbol': symbol},
                order_by='date.desc',
                limit=1
            )

            if result and len(result) > 0:
                latest_date = datetime.strptime(result[0]['date'], '%Y-%m-%d').date()
                logger.debug(f"📊 {symbol}: Latest price date in DB: {latest_date}")
                return latest_date
            else:
                logger.debug(f"📊 {symbol}: No price data in DB")
                return None

        except Exception as e:
            logger.warning(f"⚠️  {symbol}: Error checking latest price date - {e}")
            return None

    @staticmethod
    def get_latest_dividend_date(symbol: str) -> Optional[date]:
        """
        Get the latest dividend date for a symbol from the database.

        Args:
            symbol: Stock/ETF symbol

        Returns:
            Latest ex-dividend date or None if no data exists
        """
        try:
            result = supabase_select(
                'raw_dividends',
                columns='ex_date',
                where_clause={'symbol': symbol},
                order_by='ex_date.desc',
                limit=1
            )

            if result and len(result) > 0 and result[0].get('ex_date'):
                latest_date = datetime.strptime(result[0]['ex_date'], '%Y-%m-%d').date()
                logger.debug(f"💰 {symbol}: Latest dividend date in DB: {latest_date}")
                return latest_date
            else:
                logger.debug(f"💰 {symbol}: No dividend data in DB")
                return None

        except Exception as e:
            logger.warning(f"⚠️  {symbol}: Error checking latest dividend date - {e}")
            return None

    @staticmethod
    def calculate_from_date(
        latest_date: Optional[date],
        default_lookback_days: int = 365 * 5,
        add_buffer_days: int = 1
    ) -> date:
        """
        Calculate the from_date for incremental fetching.

        Args:
            latest_date: Latest date from database
            default_lookback_days: Days to look back if no data exists (default: 5 years)
            add_buffer_days: Extra days to add for overlap/safety (default: 1)

        Returns:
            Calculated from_date for API fetching
        """
        if latest_date:
            # Fetch from day after latest date (with optional buffer)
            from_date = latest_date + timedelta(days=add_buffer_days)
            logger.debug(f"📅 Incremental update from {from_date} (latest + {add_buffer_days} days)")
        else:
            # No data exists, fetch historical data
            from_date = datetime.now().date() - timedelta(days=default_lookback_days)
            logger.debug(f"📅 Full historical fetch from {from_date} ({default_lookback_days} days ago)")

        return from_date

    @staticmethod
    def should_update(
        latest_date: Optional[date],
        max_staleness_days: int = 7
    ) -> bool:
        """
        Check if data should be updated based on staleness.

        Args:
            latest_date: Latest date from database
            max_staleness_days: Maximum days before data is considered stale

        Returns:
            True if update is needed
        """
        if not latest_date:
            logger.debug("🔄 Update needed: No data in database")
            return True

        days_stale = (datetime.now().date() - latest_date).days

        if days_stale > max_staleness_days:
            logger.debug(f"🔄 Update needed: Data is {days_stale} days old (max: {max_staleness_days})")
            return True
        else:
            logger.debug(f"✅ Data is fresh ({days_stale} days old, max: {max_staleness_days})")
            return False


# Export main class
__all__ = ['IncrementalProcessor']
