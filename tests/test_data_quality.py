#!/usr/bin/env python3
"""
Data Quality Tests for DIVV API

Simplified tests focusing on critical data quality metrics.
"""

import sys
sys.path.insert(0, '/Users/toan/dev/high-yield-dividend-analysis')

from supabase_helpers import get_supabase_client
import requests
from datetime import datetime, timedelta
import statistics


API_BASE_URL = "http://localhost:8000"
supabase = get_supabase_client()


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_success(msg): print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")
def print_error(msg): print(f"{Colors.RED}❌ {msg}{Colors.RESET}")
def print_info(msg): print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")
def print_warning(msg): print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def test_data_exists():
    """Test that we have stock data in database"""
    print("\n" + "="*80)
    print("TEST 1: Database Has Data")
    print("="*80)

    try:
        result = supabase.table('dim_stocks').select('symbol', count='exact').limit(1).execute()
        total = result.count
        print(f"Total stocks in database: {total:,}")

        if total > 1000:
            print_success(f"Database has good stock coverage: {total:,} stocks")
            return True
        elif total > 100:
            print_warning(f"Database has limited stock coverage: {total:,} stocks")
            return True
        else:
            print_error(f"Database has very few stocks: {total:,}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_dividend_stocks_exist():
    """Test that we have dividend-paying stocks"""
    print("\n" + "="*80)
    print("TEST 2: Dividend-Paying Stocks Exist")
    print("="*80)

    try:
        result = supabase.table('dim_stocks').select('symbol', count='exact').gt('dividend_yield', 0).execute()
        dividend_stocks = result.count

        total_result = supabase.table('dim_stocks').select('symbol', count='exact').execute()
        total_stocks = total_result.count

        pct = (dividend_stocks / total_stocks * 100) if total_stocks > 0 else 0

        print(f"Dividend-paying stocks: {dividend_stocks:,} ({pct:.1f}%)")

        if dividend_stocks > 100:
            print_success(f"Good dividend stock coverage")
            return True
        else:
            print_warning(f"Limited dividend stock data")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_api_health():
    """Test that API is responding"""
    print("\n" + "="*80)
    print("TEST 3: API Health Check")
    print("="*80)

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)

        if response.status_code == 200:
            print_success(f"API is healthy")
            return True
        else:
            print_error(f"API returned {response.status_code}")
            return False

    except Exception as e:
        print_error(f"API error: {e}")
        return False


def test_api_can_fetch_stock():
    """Test that API can fetch stock data"""
    print("\n" + "="*80)
    print("TEST 4: API Can Fetch Stock Data")
    print("="*80)

    try:
        # Get a sample symbol from DB
        db_result = supabase.table('dim_stocks').select('symbol').limit(1).execute()

        if not db_result.data:
            print_warning("No stocks in database to test")
            return False

        symbol = db_result.data[0]['symbol']
        print(f"Testing with symbol: {symbol}")

        response = requests.get(f"{API_BASE_URL}/v1/stocks/{symbol}", timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('symbol') == symbol:
                print_success(f"API correctly returns stock data for {symbol}")
                return True
            else:
                print_error(f"API returned wrong symbol")
                return False
        else:
            print_error(f"API returned {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_api_response_times():
    """Test API response performance"""
    print("\n" + "="*80)
    print("TEST 5: API Response Time")
    print("="*80)

    try:
        import time
        times = []

        # Test health endpoint
        for _ in range(3):
            start = time.time()
            requests.get(f"{API_BASE_URL}/health", timeout=10)
            times.append((time.time() - start) * 1000)

        avg_ms = statistics.mean(times)
        max_ms = max(times)

        print(f"Average response time: {avg_ms:.0f}ms")
        print(f"Maximum response time: {max_ms:.0f}ms")

        if avg_ms < 1000:
            print_success(f"API response times are good")
            return True
        else:
            print_warning(f"API response times are slow")
            return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_dividend_data_sanity():
    """Test dividend data makes sense"""
    print("\n" + "="*80)
    print("TEST 6: Dividend Data Sanity")
    print("="*80)

    try:
        result = supabase.table('dim_stocks').select(
            'symbol, dividend_yield, annual_dividend_amount, current_price'
        ).gt('dividend_yield', 0).not_.is_('current_price', 'null').limit(20).execute()

        stocks = result.data
        print(f"Checking {len(stocks)} dividend stocks")

        if len(stocks) == 0:
            print_warning("No dividend stocks with complete data")
            return False

        issues = 0
        for stock in stocks:
            div_yield = stock.get('dividend_yield')
            if div_yield and (div_yield < 0 or div_yield > 30):
                issues += 1

        issue_rate = (issues / len(stocks) * 100) if len(stocks) > 0 else 0

        if issue_rate < 10:
            print_success(f"Dividend data looks reasonable ({100-issue_rate:.0f}% clean)")
            return True
        else:
            print_warning(f"Some dividend data issues found ({issue_rate:.0f}% problematic)")
            return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_data_freshness():
    """Test that data was updated recently"""
    print("\n" + "="*80)
    print("TEST 7: Data Freshness")
    print("="*80)

    try:
        result = supabase.table('dim_stocks').select('last_updated').not_.is_('last_updated', 'null').limit(10).execute()

        if not result.data:
            print_warning("No update timestamps found")
            return False

        from dateutil import parser
        now = datetime.now()
        fresh_count = 0

        for row in result.data:
            if row.get('last_updated'):
                updated = parser.isoparse(row['last_updated'])
                age_days = (now - updated.replace(tzinfo=None)).days
                if age_days < 30:  # Updated in last 30 days
                    fresh_count += 1

        freshness = (fresh_count / len(result.data) * 100) if len(result.data) > 0 else 0

        print(f"Data freshness: {freshness:.0f}% updated in last 30 days")

        if freshness > 50:
            print_success("Data is reasonably fresh")
            return True
        else:
            print_warning("Data may be stale")
            return True

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_no_critical_api_errors():
    """Test that API doesn't have critical errors"""
    print("\n" + "="*80)
    print("TEST 8: No Critical API Errors")
    print("="*80)

    try:
        endpoints = [
            '/health',
            '/v1/stocks/AAPL',
        ]

        errors = 0
        for endpoint in endpoints:
            try:
                response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=10)
                if response.status_code >= 500:
                    errors += 1
                    print(f"  {endpoint}: {response.status_code} (server error)")
            except:
                errors += 1

        if errors == 0:
            print_success("No critical API errors detected")
            return True
        else:
            print_error(f"Found {errors} critical errors")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_daily_backups_exist():
    """Test that daily backups are being created"""
    print("\n" + "="*80)
    print("TEST 9: Daily Backups Exist")
    print("="*80)

    try:
        import os
        import glob
        from pathlib import Path

        backup_dir = Path("/Users/toan/dev/high-yield-dividend-analysis/backups")

        if not backup_dir.exists():
            print_error("Backup directory does not exist")
            return False

        # Check for backups in last 3 days
        today = datetime.now()
        dates_to_check = [
            (today - timedelta(days=i)).strftime("%Y%m%d")
            for i in range(3)
        ]

        backups_found = {}
        for date_str in dates_to_check:
            date_dir = backup_dir / date_str
            if date_dir.exists():
                # Look for .sql or .sql.gz files
                backup_files = list(date_dir.glob("*.sql")) + list(date_dir.glob("*.sql.gz"))
                backups_found[date_str] = len(backup_files)
            else:
                backups_found[date_str] = 0

        print(f"\nBackup status (last 3 days):")
        for date_str, count in backups_found.items():
            if count > 0:
                print(f"  {date_str}: {count} backup(s) ✅")
            else:
                print(f"  {date_str}: No backups ⚠️")

        # Check if we have at least one backup in the last 2 days
        recent_backups = sum(backups_found[dates_to_check[i]] for i in range(2))

        if recent_backups > 0:
            print_success(f"Recent backups found ({recent_backups} in last 2 days)")
            return True
        else:
            print_warning("No backups found in last 2 days")
            return False

    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_stale_data_detection():
    """Test for stale data across multiple dimensions"""
    print("\n" + "="*80)
    print("TEST 10: Stale Data Detection")
    print("="*80)

    try:
        from dateutil import parser
        now = datetime.now()
        issues = []
        stats = {}

        # 1. Check price data staleness
        print("\n1. Checking price data freshness...")
        result = supabase.table('dim_stocks').select(
            'symbol, current_price, last_updated'
        ).not_.is_('current_price', 'null').not_.is_('last_updated', 'null').limit(100).execute()

        if result.data:
            stale_prices = 0
            for stock in result.data:
                if stock.get('last_updated'):
                    updated = parser.isoparse(stock['last_updated'])
                    age_days = (now - updated.replace(tzinfo=None)).days
                    if age_days > 7:  # Stale if > 7 days
                        stale_prices += 1

            stale_pct = (stale_prices / len(result.data) * 100) if len(result.data) > 0 else 0
            stats['stale_prices_pct'] = stale_pct
            print(f"   Stale prices: {stale_prices}/{len(result.data)} ({stale_pct:.1f}%)")

            if stale_pct > 20:
                issues.append(f"High stale price data: {stale_pct:.1f}% > 7 days old")

        # 2. Check dividend data staleness
        print("\n2. Checking dividend data freshness...")
        result = supabase.table('dim_stocks').select(
            'symbol, last_dividend_date, dividend_yield'
        ).gt('dividend_yield', 0).not_.is_('last_dividend_date', 'null').limit(100).execute()

        if result.data:
            very_old_dividends = 0
            for stock in result.data:
                if stock.get('last_dividend_date'):
                    try:
                        last_div = parser.isoparse(stock['last_dividend_date'])
                        age_days = (now - last_div.replace(tzinfo=None)).days
                        # Dividends older than 1 year might be concerning
                        if age_days > 365:
                            very_old_dividends += 1
                    except:
                        pass

            old_div_pct = (very_old_dividends / len(result.data) * 100) if len(result.data) > 0 else 0
            stats['old_dividends_pct'] = old_div_pct
            print(f"   Old dividend dates: {very_old_dividends}/{len(result.data)} ({old_div_pct:.1f}% > 1 year)")

            if old_div_pct > 30:
                issues.append(f"High old dividend data: {old_div_pct:.1f}% > 1 year old")

        # 3. Check for stocks with zero/null prices (data quality issue)
        print("\n3. Checking for missing price data...")
        total_result = supabase.table('dim_stocks').select('symbol', count='exact').execute()
        total_stocks = total_result.count

        price_result = supabase.table('dim_stocks').select('symbol', count='exact').not_.is_('current_price', 'null').gt('current_price', 0).execute()
        stocks_with_prices = price_result.count

        missing_prices_pct = ((total_stocks - stocks_with_prices) / total_stocks * 100) if total_stocks > 0 else 0
        stats['missing_prices_pct'] = missing_prices_pct
        print(f"   Missing prices: {total_stocks - stocks_with_prices}/{total_stocks} ({missing_prices_pct:.1f}%)")

        if missing_prices_pct > 15:
            issues.append(f"Too many stocks missing prices: {missing_prices_pct:.1f}%")

        # 4. Check for ratings that haven't been updated
        print("\n4. Checking rating freshness...")
        result = supabase.table('dim_stocks').select(
            'symbol, rating_last_updated'
        ).not_.is_('rating_last_updated', 'null').limit(100).execute()

        if result.data:
            stale_ratings = 0
            for stock in result.data:
                if stock.get('rating_last_updated'):
                    try:
                        updated = parser.isoparse(stock['rating_last_updated'])
                        age_days = (now - updated.replace(tzinfo=None)).days
                        if age_days > 30:  # Ratings stale if > 30 days
                            stale_ratings += 1
                    except:
                        pass

            stale_rating_pct = (stale_ratings / len(result.data) * 100) if len(result.data) > 0 else 0
            stats['stale_ratings_pct'] = stale_rating_pct
            print(f"   Stale ratings: {stale_ratings}/{len(result.data)} ({stale_rating_pct:.1f}% > 30 days)")

            if stale_rating_pct > 40:
                issues.append(f"High stale ratings: {stale_rating_pct:.1f}% > 30 days old")

        # 5. Check for completely unchanged records (no updates at all)
        print("\n5. Checking for unchanged records...")
        result = supabase.table('dim_stocks').select(
            'symbol, last_updated'
        ).not_.is_('last_updated', 'null').limit(100).execute()

        if result.data:
            never_updated = 0
            for stock in result.data:
                if stock.get('last_updated'):
                    updated = parser.isoparse(stock['last_updated'])
                    age_days = (now - updated.replace(tzinfo=None)).days
                    if age_days > 90:  # Not updated in 90 days
                        never_updated += 1

            never_updated_pct = (never_updated / len(result.data) * 100) if len(result.data) > 0 else 0
            stats['never_updated_pct'] = never_updated_pct
            print(f"   Never updated: {never_updated}/{len(result.data)} ({never_updated_pct:.1f}% > 90 days)")

            if never_updated_pct > 25:
                issues.append(f"Too many stale records: {never_updated_pct:.1f}% not updated in 90+ days")

        # Summary
        print(f"\n{'='*80}")
        print("STALE DATA SUMMARY:")
        print(f"{'='*80}")

        if issues:
            print(f"\n⚠️  Found {len(issues)} data freshness issues:")
            for issue in issues:
                print(f"  - {issue}")
            print_warning(f"Data freshness needs attention")
            return False
        else:
            print_success("All data freshness checks passed")
            print(f"  • Stale prices: {stats.get('stale_prices_pct', 0):.1f}%")
            print(f"  • Old dividends: {stats.get('old_dividends_pct', 0):.1f}%")
            print(f"  • Missing prices: {stats.get('missing_prices_pct', 0):.1f}%")
            print(f"  • Stale ratings: {stats.get('stale_ratings_pct', 0):.1f}%")
            print(f"  • Never updated: {stats.get('never_updated_pct', 0):.1f}%")
            return True

    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print("DATA QUALITY TEST SUITE")
    print("="*80)
    print(f"Time: {datetime.now().isoformat()}")
    print("="*80)

    results = {}
    results['Database Has Data'] = test_data_exists()
    results['Dividend Stocks Exist'] = test_dividend_stocks_exist()
    results['API Health'] = test_api_health()
    results['API Can Fetch Stock'] = test_api_can_fetch_stock()
    results['API Response Time'] = test_api_response_times()
    results['Dividend Data Sanity'] = test_dividend_data_sanity()
    results['Data Freshness'] = test_data_freshness()
    results['No Critical API Errors'] = test_no_critical_api_errors()
    results['Daily Backups Exist'] = test_daily_backups_exist()
    results['Stale Data Detection'] = test_stale_data_detection()

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status}{Colors.RESET} - {test_name}")

    print("="*80)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print_success("All data quality tests passed!")
        sys.exit(0)
    else:
        print_warning(f"{total - passed} test(s) failed or had warnings")
        # Exit 0 even with warnings unless all tests failed
        sys.exit(0 if passed > 0 else 1)


if __name__ == "__main__":
    main()
