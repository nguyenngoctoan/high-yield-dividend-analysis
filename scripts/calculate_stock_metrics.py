#!/usr/bin/env python3
"""
Calculate Stock Metrics Script

Calculates and updates derived metrics in the stocks table:
- Dividend frequency (monthly, quarterly, semi-annual, annual)
- Total return TTM (trailing twelve months)
- Price change TTM (trailing twelve months)
- Price change YTD (year-to-date)
- Last dividend date and amount
- Current price from latest stock_prices
"""

import logging
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase_helpers import supabase_select, supabase_batch_upsert, supabase_update

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class StockMetricsCalculator:
    """Calculates derived metrics for stocks based on historical data."""

    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'frequency_calculated': 0,
            'ttm_calculated': 0,
            'ytd_calculated': 0,
            'errors': []
        }

    def calculate_dividend_frequency(self, dividends: List[Dict[str, Any]]) -> Optional[str]:
        """
        Calculate dividend payment frequency from historical dividends.

        Args:
            dividends: List of dividend records with ex_date

        Returns:
            Frequency string: 'Weekly', 'Bi-Weekly', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual', or None
        """
        if not dividends or len(dividends) < 2:
            return None

        # Sort by ex_date (no deduplication needed - DB has unique constraint)
        sorted_divs = sorted(dividends, key=lambda d: d['ex_date'])

        # Calculate days between consecutive dividends
        intervals = []
        for i in range(1, len(sorted_divs)):
            prev_date = datetime.strptime(sorted_divs[i-1]['ex_date'], '%Y-%m-%d').date()
            curr_date = datetime.strptime(sorted_divs[i]['ex_date'], '%Y-%m-%d').date()
            days_between = (curr_date - prev_date).days
            intervals.append(days_between)

        if not intervals:
            return None

        # Calculate average interval
        avg_interval = sum(intervals) / len(intervals)

        # Determine frequency based on average interval
        # Weekly: ~7 days (4-13 days tolerance)
        # Bi-Weekly: ~14 days (11-20 days tolerance)
        # Monthly: ~30 days (21-45 days tolerance)
        # Quarterly: ~90 days (70-115 days tolerance)
        # Semi-Annual: ~180 days (140-220 days tolerance)
        # Annual: ~365 days (320-410 days tolerance)

        if 4 <= avg_interval <= 13:
            return 'Weekly'
        elif 11 <= avg_interval <= 20:
            return 'Bi-Weekly'
        elif 21 <= avg_interval <= 45:
            return 'Monthly'
        elif 70 <= avg_interval <= 115:
            return 'Quarterly'
        elif 140 <= avg_interval <= 220:
            return 'Semi-Annual'
        elif 320 <= avg_interval <= 410:
            return 'Annual'
        else:
            # If it doesn't fit, use the most common interval
            interval_counts = Counter(intervals)
            most_common_interval = interval_counts.most_common(1)[0][0]

            if 4 <= most_common_interval <= 13:
                return 'Weekly'
            elif 11 <= most_common_interval <= 20:
                return 'Bi-Weekly'
            elif 21 <= most_common_interval <= 45:
                return 'Monthly'
            elif 70 <= most_common_interval <= 115:
                return 'Quarterly'
            elif 140 <= most_common_interval <= 220:
                return 'Semi-Annual'
            elif 320 <= most_common_interval <= 410:
                return 'Annual'

        return None

    def calculate_total_return_ttm(self,
                                   symbol: str,
                                   current_price: float,
                                   price_12mo_ago: Optional[float],
                                   dividends_ttm: float,
                                   days_of_data: Optional[int] = None) -> Optional[float]:
        """
        Calculate trailing twelve months total return.

        Total Return = (Current Price - Price 12mo ago + Dividends TTM) / Price 12mo ago

        For stocks with < 12 months of data, annualizes the return based on available days.

        Args:
            symbol: Stock symbol
            current_price: Current stock price
            price_12mo_ago: Price 12 months ago (or earliest price for projection)
            dividends_ttm: Total dividends paid in available period
            days_of_data: Number of days of data available (for annualization)

        Returns:
            Total return as decimal (e.g., 0.15 for 15% return) or None
        """
        if not price_12mo_ago or price_12mo_ago <= 0:
            return None

        price_change = current_price - price_12mo_ago

        # If we have less than 365 days, annualize the return
        if days_of_data and days_of_data < 365:
            # Calculate return for the period we have
            period_return = (price_change + dividends_ttm) / price_12mo_ago

            # Annualize: ((1 + period_return) ^ (365/days)) - 1
            annualized_return = ((1 + period_return) ** (365.0 / days_of_data)) - 1

            logger.debug(f"📊 {symbol}: Projected TTM from {days_of_data} days: {period_return*100:.2f}% → {annualized_return*100:.2f}% annualized")
            return annualized_return
        else:
            # Full 12 months of data
            total_return = (price_change + dividends_ttm) / price_12mo_ago
            return total_return

    def calculate_price_change_ttm(self,
                                   current_price: float,
                                   price_12mo_ago: Optional[float],
                                   days_of_data: Optional[int] = None) -> Optional[float]:
        """
        Calculate trailing twelve months price change.

        Price Change = (Current Price - Price 12mo ago) / Price 12mo ago

        For stocks with < 12 months of data, annualizes the return based on available days.

        Args:
            current_price: Current stock price
            price_12mo_ago: Price 12 months ago (or earliest price for projection)
            days_of_data: Number of days of data available (for annualization)

        Returns:
            Price change as decimal (e.g., 0.10 for 10% increase) or None
        """
        if not price_12mo_ago or price_12mo_ago <= 0:
            return None

        # Calculate period return
        period_return = (current_price - price_12mo_ago) / price_12mo_ago

        # If we have less than 365 days, annualize the return
        if days_of_data and days_of_data < 365:
            # Annualize: ((1 + period_return) ^ (365/days)) - 1
            annualized_return = ((1 + period_return) ** (365.0 / days_of_data)) - 1
            return annualized_return
        else:
            return period_return

    def calculate_price_change_ytd(self,
                                   current_price: float,
                                   price_year_start: Optional[float]) -> Optional[float]:
        """
        Calculate year-to-date price change.

        YTD Change = (Current Price - Price at Year Start) / Price at Year Start

        Args:
            current_price: Current stock price
            price_year_start: Price at start of current year

        Returns:
            YTD change as decimal (e.g., 0.08 for 8% increase) or None
        """
        if not price_year_start or price_year_start <= 0:
            return None

        ytd_change = (current_price - price_year_start) / price_year_start

        return ytd_change

    def get_stock_price_history(self, symbol: str) -> Dict[str, Any]:
        """
        Get price history for a symbol.

        Returns:
            Dictionary with current_price, price_12mo_ago, price_year_start
        """
        today = date.today()
        twelve_months_ago = today - timedelta(days=365)
        year_start = date(today.year, 1, 1)

        result = {
            'current_price': None,
            'price_12mo_ago': None,
            'price_year_start': None
        }

        try:
            # Get current price (most recent)
            # Use adj_close for split-adjusted prices
            current_prices = supabase_select(
                'raw_stock_prices',
                columns='adj_close,date',
                where_clause={'symbol': symbol},
                order_by='date.desc',
                limit=1
            )

            if current_prices and len(current_prices) > 0:
                result['current_price'] = float(current_prices[0]['adj_close'])

            # Get historical prices using direct PostgreSQL for accurate date range queries
            try:
                import os
                from dotenv import load_dotenv
                load_dotenv()

                # Direct PostgreSQL query for better date range filtering
                import psycopg2
                conn = psycopg2.connect(
                    host='localhost',
                    port=5434,
                    database='postgres',
                    user='postgres',
                    password=os.getenv('PGPASSWORD', 'postgres')
                )
                cursor = conn.cursor()

                # Find price closest to 12 months ago (within 30-day window)
                twelve_mo_start = twelve_months_ago - timedelta(days=15)
                twelve_mo_end = twelve_months_ago + timedelta(days=15)

                cursor.execute("""
                    SELECT adj_close, date
                    FROM raw_stock_prices
                    WHERE symbol = %s
                      AND date >= %s
                      AND date <= %s
                    ORDER BY ABS(EXTRACT(EPOCH FROM (date::timestamp - %s::timestamp)))
                    LIMIT 1
                """, (symbol, twelve_mo_start, twelve_mo_end, twelve_months_ago))

                row = cursor.fetchone()
                if row:
                    result['price_12mo_ago'] = float(row[0])
                    result['price_12mo_ago_date'] = row[1]
                else:
                    # No data in 30-day window, try to find earliest available price
                    # We'll use this to calculate a projected TTM
                    cursor.execute("""
                        SELECT adj_close, date
                        FROM raw_stock_prices
                        WHERE symbol = %s
                        ORDER BY date ASC
                        LIMIT 1
                    """, (symbol,))

                    row = cursor.fetchone()
                    if row:
                        earliest_date = row[1]
                        days_of_data = (today - earliest_date).days

                        # For projected TTM, require:
                        # 1. At least 90 days of data (3 months minimum)
                        # 2. Less than 18 months (to avoid using very old data)
                        # 3. Check for large gaps (would invalidate projection)
                        if 90 <= days_of_data < 547:  # 547 days = 18 months
                            # Check for gaps > 90 days in the price history
                            cursor.execute("""
                                WITH gaps AS (
                                    SELECT date - LAG(date) OVER (ORDER BY date) as gap_days
                                    FROM raw_stock_prices
                                    WHERE symbol = %s
                                    ORDER BY date
                                )
                                SELECT MAX(gap_days) as max_gap
                                FROM gaps
                            """, (symbol,))

                            max_gap_row = cursor.fetchone()
                            max_gap = max_gap_row[0] if max_gap_row and max_gap_row[0] else 0

                            if max_gap and max_gap > 90:
                                logger.debug(f"📊 {symbol}: Data has gap of {max_gap} days - skipping projected TTM")
                            else:
                                result['price_12mo_ago'] = float(row[0])
                                result['price_12mo_ago_date'] = earliest_date
                                result['projected_ttm'] = True
                                result['days_of_data'] = days_of_data
                                logger.debug(f"📊 {symbol}: Using earliest price from {earliest_date} for projected TTM ({days_of_data} days of data)")
                        elif days_of_data < 90:
                            logger.debug(f"📊 {symbol}: Insufficient data for projected TTM ({days_of_data} days, need 90+)")
                        else:
                            logger.debug(f"📊 {symbol}: Data too old for projected TTM ({days_of_data} days, max 18 months)")

                # Get price at year start (with 15-day window)
                year_start_window_end = year_start + timedelta(days=15)

                cursor.execute("""
                    SELECT adj_close, date
                    FROM raw_stock_prices
                    WHERE symbol = %s
                      AND date >= %s
                      AND date <= %s
                    ORDER BY date ASC
                    LIMIT 1
                """, (symbol, year_start, year_start_window_end))

                row = cursor.fetchone()
                if row:
                    result['price_year_start'] = float(row[0])

                cursor.close()
                conn.close()

            except Exception as e:
                logger.debug(f"⚠️  {symbol}: Direct SQL query failed - {e}")

        except Exception as e:
            logger.debug(f"⚠️  {symbol}: Error fetching price history - {e}")

        return result

    def get_dividend_history(self, symbol: str, earliest_price_date: Optional[date] = None,
                              use_raw_dividends: bool = False) -> Dict[str, Any]:
        """
        Get dividend history for a symbol.

        Args:
            symbol: Stock symbol
            earliest_price_date: Earliest price date for annualization calculation
            use_raw_dividends: If True, return raw dividends (no annualization) for projected TTM

        Returns:
            Dictionary with last_dividend_date, last_dividend_amount, dividends_ttm, all_dividends, days_of_data
        """
        result = {
            'last_dividend_date': None,
            'last_dividend_amount': None,
            'dividends_ttm': 0.0,
            'all_dividends': [],
            'days_of_dividend_data': None
        }

        try:
            # Get all dividends for frequency calculation
            all_dividends = supabase_select(
                'raw_dividends',
                columns='ex_date,amount',
                where_clause={'symbol': symbol},
                order_by='ex_date.desc',
                limit=100  # Get enough for frequency calculation
            )

            if all_dividends:
                result['all_dividends'] = all_dividends

                # Last dividend (from first entry)
                result['last_dividend_date'] = all_dividends[0]['ex_date']
                result['last_dividend_amount'] = float(all_dividends[0]['amount'])

                # Calculate TTM dividends (DB unique constraint ensures no duplicates)
                # If we have earliest_price_date, use that as the start date (for projection)
                # Otherwise use 12 months ago
                if earliest_price_date:
                    start_date = earliest_price_date
                    days_of_data = (date.today() - earliest_price_date).days
                    result['days_of_dividend_data'] = days_of_data
                else:
                    start_date = date.today() - timedelta(days=365)

                ttm_sum = 0.0

                # Sum dividends in period
                for div in all_dividends:
                    div_date = datetime.strptime(div['ex_date'], '%Y-%m-%d').date()
                    if div_date >= start_date:
                        ttm_sum += float(div['amount'])

                # For projected TTM, return RAW dividends (will be annualized with price return)
                # For regular TTM or dividend yield, annualize dividends separately
                if use_raw_dividends:
                    # Return raw dividends for compound annualization
                    result['dividends_ttm'] = ttm_sum
                    logger.debug(f"📊 {symbol}: Using raw dividends ${ttm_sum:.4f} over {days_of_data if earliest_price_date else 365} days (for compound annualization)")
                elif earliest_price_date and days_of_data < 365 and days_of_data > 0:
                    # Linear annualization for dividend yield calculation
                    annualized_dividends = ttm_sum * (365.0 / days_of_data)
                    logger.debug(f"📊 {symbol}: Annualizing dividends: ${ttm_sum:.4f} over {days_of_data} days → ${annualized_dividends:.4f} annually")
                    result['dividends_ttm'] = annualized_dividends
                else:
                    result['dividends_ttm'] = ttm_sum

        except Exception as e:
            logger.debug(f"⚠️  {symbol}: Error fetching dividend history - {e}")

        return result

    def calculate_metrics_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Calculate all metrics for a single symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with calculated metrics or None if failed
        """
        try:
            metrics = {'symbol': symbol}

            # Get price history
            price_data = self.get_stock_price_history(symbol)

            # Determine if we're using projected TTM
            earliest_price_date = None
            days_of_data = None
            is_projected = price_data.get('projected_ttm', False)

            if is_projected:
                earliest_price_date = price_data.get('price_12mo_ago_date')
                days_of_data = price_data.get('days_of_data')

            # Get dividend history for TTM calculation
            # For projected TTM, use RAW dividends (will be annualized with price return)
            dividend_data_ttm = self.get_dividend_history(
                symbol,
                earliest_price_date,
                use_raw_dividends=is_projected
            )

            # Get dividend history for dividend yield (always annualized separately)
            dividend_data_yield = self.get_dividend_history(
                symbol,
                earliest_price_date,
                use_raw_dividends=False
            )

            # Calculate frequency
            if dividend_data_ttm['all_dividends']:
                frequency = self.calculate_dividend_frequency(dividend_data_ttm['all_dividends'])
                if frequency:
                    metrics['frequency'] = frequency
                    self.stats['frequency_calculated'] += 1

            # Set price from latest data
            if price_data['current_price']:
                metrics['price'] = price_data['current_price']

            # Set last dividend info
            if dividend_data_ttm['last_dividend_date']:
                metrics['last_dividend_date'] = dividend_data_ttm['last_dividend_date']
                metrics['last_dividend_amount'] = dividend_data_ttm['last_dividend_amount']

            # Calculate TTM metrics
            if price_data['current_price'] and price_data['price_12mo_ago']:
                # Total return TTM (with projection if needed)
                # Use raw dividends if projected, annualized dividends if not
                total_return = self.calculate_total_return_ttm(
                    symbol,
                    price_data['current_price'],
                    price_data['price_12mo_ago'],
                    dividend_data_ttm['dividends_ttm'],  # Raw for projected, full for regular
                    days_of_data
                )

                if total_return is not None:
                    metrics['total_return_ttm'] = total_return
                    self.stats['ttm_calculated'] += 1

                # Price change TTM (with projection if needed)
                price_change = self.calculate_price_change_ttm(
                    price_data['current_price'],
                    price_data['price_12mo_ago'],
                    days_of_data
                )

                if price_change is not None:
                    metrics['price_change_ttm'] = price_change
            else:
                # Explicitly NULL out TTM fields if we can't calculate them
                # This removes stale/incorrect values from previous calculations
                metrics['total_return_ttm'] = None
                metrics['price_change_ttm'] = None
                logger.debug(f"📊 {symbol}: TTM calculation skipped (insufficient data or gaps)")

            # Calculate YTD metrics
            if price_data['current_price'] and price_data['price_year_start']:
                ytd_change = self.calculate_price_change_ytd(
                    price_data['current_price'],
                    price_data['price_year_start']
                )

                if ytd_change is not None:
                    metrics['price_change_ytd'] = ytd_change
                    self.stats['ytd_calculated'] += 1

            # Calculate dividend yield using annualized dividends
            if price_data['current_price'] and dividend_data_yield['dividends_ttm'] > 0:
                dividend_yield = dividend_data_yield['dividends_ttm'] / price_data['current_price']
                metrics['dividend_yield'] = dividend_yield

            return metrics if len(metrics) > 1 else None  # Return None if only symbol

        except Exception as e:
            logger.error(f"❌ {symbol}: Error calculating metrics - {e}")
            self.stats['errors'].append(f"{symbol}: {str(e)}")
            return None

    def process_all_stocks(self, batch_size: int = 100, limit: Optional[int] = None):
        """
        Process all stocks and update their metrics.

        Args:
            batch_size: Number of stocks to update in each batch
            limit: Optional limit on number of stocks to process
        """
        logger.info("🚀 Starting stock metrics calculation")

        # Get all stock symbols
        stocks = supabase_select('raw_stocks', columns='symbol', limit=limit if limit else 100000)

        if not stocks:
            logger.error("❌ No stocks found in database")
            return

        total_stocks = len(stocks)
        logger.info(f"📊 Processing {total_stocks} stocks")

        # Process in batches
        updates = []

        for idx, stock in enumerate(stocks, 1):
            symbol = stock['symbol']
            self.stats['total_processed'] += 1

            # Calculate metrics
            metrics = self.calculate_metrics_for_symbol(symbol)

            if metrics:
                updates.append(metrics)
                self.stats['successful'] += 1

                # Log progress every 100 stocks
                if idx % 100 == 0:
                    logger.info(f"📈 Progress: {idx}/{total_stocks} ({idx/total_stocks*100:.1f}%)")

                # Update database in batches
                if len(updates) >= batch_size:
                    self._batch_update_stocks(updates)
                    updates = []
            else:
                self.stats['failed'] += 1

        # Update remaining
        if updates:
            self._batch_update_stocks(updates)

        # Print summary
        self._print_summary()

    def _batch_update_stocks(self, updates: List[Dict[str, Any]]):
        """Update stocks table with calculated metrics."""
        try:
            # Use batch upsert to update raw_stocks
            result = supabase_batch_upsert(
                'raw_stocks',
                updates,
                batch_size=100
            )

            if result:
                logger.info(f"✅ Updated {len(updates)} stocks with calculated metrics")
            else:
                logger.error(f"❌ Failed to update {len(updates)} stocks")

        except Exception as e:
            logger.error(f"❌ Batch update error: {e}")

    def _print_summary(self):
        """Print calculation summary."""
        logger.info("\n" + "="*80)
        logger.info("📊 METRICS CALCULATION SUMMARY")
        logger.info("="*80)
        logger.info(f"Total stocks processed: {self.stats['total_processed']}")
        logger.info(f"✅ Successful: {self.stats['successful']}")
        logger.info(f"❌ Failed: {self.stats['failed']}")
        logger.info("")
        logger.info(f"📈 Metrics Calculated:")
        logger.info(f"   - Dividend frequency: {self.stats['frequency_calculated']}")
        logger.info(f"   - Total return TTM: {self.stats['ttm_calculated']}")
        logger.info(f"   - Price change YTD: {self.stats['ytd_calculated']}")

        if self.stats['errors']:
            logger.info(f"\n⚠️  {len(self.stats['errors'])} errors occurred")
            logger.info("First 10 errors:")
            for error in self.stats['errors'][:10]:
                logger.info(f"   - {error}")

        logger.info("="*80)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description='Calculate stock metrics (frequency, TTM, YTD, etc.)')
    parser.add_argument('--limit', type=int, help='Limit number of stocks to process (for testing)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for database updates')
    parser.add_argument('--symbol', type=str, help='Process a specific symbol only')
    args = parser.parse_args()

    calculator = StockMetricsCalculator()

    if args.symbol:
        logger.info(f"📊 Processing single symbol: {args.symbol}")
        metrics = calculator.calculate_metrics_for_symbol(args.symbol)

        if metrics:
            logger.info(f"✅ Calculated metrics for {args.symbol}:")
            for key, value in metrics.items():
                if key != 'symbol':
                    logger.info(f"   - {key}: {value}")

            # Update database
            calculator._batch_update_stocks([metrics])
        else:
            logger.error(f"❌ Failed to calculate metrics for {args.symbol}")
    else:
        calculator.process_all_stocks(
            batch_size=args.batch_size,
            limit=args.limit
        )

    return 0


if __name__ == '__main__':
    sys.exit(main())
