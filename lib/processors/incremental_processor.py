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

    @staticmethod
    def get_bulk_latest_dates(table: str, date_column: str = 'date') -> dict:
        """
        Bulk fetch latest dates for all symbols in a single query.
        This replaces individual queries for each symbol, dramatically improving performance.

        Args:
            table: Table name ('raw_stock_prices' or 'raw_dividends')
            date_column: Date column name ('date' for prices, 'ex_date' for dividends)

        Returns:
            Dictionary mapping symbol -> latest date
        """
        try:
            from supabase_helpers import get_supabase_client
            supabase = get_supabase_client()

            logger.info(f"📊 Bulk fetching latest {date_column}s from {table}...")

            # Use RPC function for efficient bulk fetching
            # This single query replaces tens of thousands of individual queries
            result = supabase.rpc(
                'get_latest_dates_by_symbol',
                {'table_name': table, 'date_col': date_column}
            ).execute()

            if result.data:
                # Convert to dict for fast lookups
                latest_dates = {}
                for row in result.data:
                    try:
                        symbol = row['symbol']
                        date_str = row['latest_date']
                        latest_dates[symbol] = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except Exception as e:
                        logger.debug(f"⚠️  Error parsing date for {row.get('symbol')}: {e}")
                        continue

                logger.info(f"✅ Fetched latest dates for {len(latest_dates):,} symbols in single query")
                return latest_dates
            else:
                logger.info("📊 No existing data found in {table}")
                return {}

        except Exception as e:
            # Fallback to empty dict if RPC function doesn't exist
            logger.warning(f"⚠️  Bulk fetch failed (falling back to individual queries): {e}")
            logger.info("💡 To enable bulk fetching, run: migrations/create_bulk_latest_dates_function.sql")
            return {}

    @staticmethod
    def filter_stale_symbols(symbols: list, max_staleness_hours: int = 24) -> tuple:
        """
        Filter symbols to only those that need updating based on staleness.
        Checks updated_at timestamp in raw_stocks table.

        Args:
            symbols: List of symbols to check
            max_staleness_hours: Maximum hours before symbol needs update (default: 24)

        Returns:
            Tuple of (stale_symbols, fresh_symbols)
        """
        try:
            from supabase_helpers import get_supabase_client
            supabase = get_supabase_client()

            # Calculate staleness cutoff
            cutoff = datetime.now() - timedelta(hours=max_staleness_hours)
            cutoff_iso = cutoff.isoformat()

            logger.info(f"📊 Checking staleness for {len(symbols):,} symbols (cutoff: {max_staleness_hours}h)...")

            # Batch query to check updated_at timestamps
            # Query all symbols at once for efficiency
            result = supabase.table('raw_stocks') \
                .select('symbol, updated_at') \
                .in_('symbol', symbols) \
                .execute()

            if not result.data:
                logger.info("📊 No symbols found in database, all need updating")
                return symbols, []

            # Categorize symbols based on staleness
            stale_symbols = []
            fresh_symbols = []

            # Create lookup dict for fast access
            updated_at_map = {row['symbol']: row.get('updated_at') for row in result.data}

            for symbol in symbols:
                updated_at_str = updated_at_map.get(symbol)

                if not updated_at_str:
                    # Symbol not in database or no updated_at
                    stale_symbols.append(symbol)
                else:
                    try:
                        # Parse ISO timestamp
                        updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                        # Remove timezone for comparison
                        updated_at = updated_at.replace(tzinfo=None)

                        if updated_at < cutoff:
                            stale_symbols.append(symbol)
                        else:
                            fresh_symbols.append(symbol)
                    except Exception as e:
                        logger.debug(f"⚠️  Error parsing updated_at for {symbol}: {e}")
                        stale_symbols.append(symbol)  # Default to stale if parsing fails

            logger.info(
                f"✅ Staleness check complete: {len(stale_symbols):,} stale (need update), "
                f"{len(fresh_symbols):,} fresh (skip)"
            )

            if fresh_symbols:
                logger.info(f"⏭️  Skipping {len(fresh_symbols):,} recently updated symbols (saving ~{len(fresh_symbols) * 2}min)")

            return stale_symbols, fresh_symbols

        except Exception as e:
            logger.warning(f"⚠️  Staleness check failed: {e}")
            logger.info("📊 Proceeding with all symbols (no filtering)")
            return symbols, []


# Export main class
__all__ = ['IncrementalProcessor']
