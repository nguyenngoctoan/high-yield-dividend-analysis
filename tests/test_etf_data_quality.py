"""
Data Quality Tests for ETF Scrapers (YieldMax, Roundhill, NEOS, Defiance, Kurv, and GraniteShares)

Tests validate that scraped data meets quality standards:
- Launch/inception dates are valid and not in the future
- No percentage values in date fields
- Expense ratios are valid percentages
- Distribution rates are valid (where applicable)
- Distribution frequencies are valid (Defiance, Kurv)
- Holdings counts are valid numbers
- JSON fields are properly formatted
- Required fields are present
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client


class TestYieldMaxDataQuality:
    """Data quality tests for YieldMax ETF data"""

    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Initialize Supabase client"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            pytest.skip("Supabase credentials not configured")
        return create_client(url, key)

    @pytest.fixture(scope="class")
    def yieldmax_data(self, supabase_client) -> List[Dict[str, Any]]:
        """Fetch latest YieldMax data"""
        response = supabase_client.table('v_yieldmax_latest').select('*').execute()
        return response.data

    def test_yieldmax_data_exists(self, yieldmax_data):
        """Test that YieldMax data exists in database"""
        assert len(yieldmax_data) > 0, "No YieldMax ETF data found in database"
        assert len(yieldmax_data) >= 19, f"Expected at least 19 YieldMax ETFs, found {len(yieldmax_data)}"

    def test_yieldmax_required_fields(self, yieldmax_data):
        """Test that all required fields are present"""
        required_fields = ['ticker', 'fund_name', 'url', 'scraped_at']

        for etf in yieldmax_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            for field in required_fields:
                assert field in etf, f"{ticker}: Missing required field '{field}'"
                assert etf[field] is not None, f"{ticker}: Field '{field}' is None"

    def test_yieldmax_ticker_format(self, yieldmax_data):
        """Test that tickers are valid format (2-5 uppercase letters)"""
        ticker_pattern = re.compile(r'^[A-Z]{2,5}$')

        for etf in yieldmax_data:
            ticker = etf.get('ticker', '')
            assert ticker_pattern.match(ticker), \
                f"Invalid ticker format: {ticker} (expected 2-5 uppercase letters)"

    def test_yieldmax_url_format(self, yieldmax_data):
        """Test that URLs are valid YieldMax URLs"""
        for etf in yieldmax_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            url = etf.get('url', '')

            assert url.startswith('https://yieldmaxetfs.com/'), \
                f"{ticker}: Invalid URL format: {url}"
            assert ticker.lower() in url.lower(), \
                f"{ticker}: Ticker not found in URL: {url}"

    def test_yieldmax_no_percentage_in_dates(self, yieldmax_data):
        """Test that scraped_at doesn't contain percentage values"""
        for etf in yieldmax_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            scraped_at = str(etf.get('scraped_at', ''))

            assert '%' not in scraped_at, \
                f"{ticker}: Percentage sign found in scraped_at field: {scraped_at}"

    def test_yieldmax_json_fields_valid(self, yieldmax_data):
        """Test that JSON fields are valid JSON objects or parseable JSON strings"""
        import json

        json_fields = [
            'performance_month_end',
            'performance_quarter_end',
            'fund_overview',
            'fund_details',
            'distributions',
            'top_10_holdings'
        ]

        for etf in yieldmax_data:
            ticker = etf.get('ticker', 'UNKNOWN')

            for field in json_fields:
                value = etf.get(field)
                if value is not None:
                    # Check if it's already parsed JSON
                    if isinstance(value, (dict, list)):
                        continue

                    # If it's a string, try to parse it
                    if isinstance(value, str):
                        try:
                            parsed = json.loads(value)
                            # None is valid for JSON fields (means empty/null)
                            if parsed is not None:
                                assert isinstance(parsed, (dict, list)), \
                                    f"{ticker}: Parsed '{field}' is not dict/list (got {type(parsed).__name__})"
                        except json.JSONDecodeError as e:
                            pytest.fail(f"{ticker}: Field '{field}' is not valid JSON string: {e}")
                    else:
                        pytest.fail(f"{ticker}: Field '{field}' is neither JSON nor string (got {type(value).__name__})")

    def test_yieldmax_distributions_structure(self, yieldmax_data):
        """Test that distributions field has expected structure"""
        for etf in yieldmax_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            distributions = etf.get('distributions')

            if distributions and isinstance(distributions, list) and len(distributions) > 0:
                # Check first distribution has expected keys
                first_dist = distributions[0]
                assert isinstance(first_dist, dict), \
                    f"{ticker}: Distribution is not a dict: {type(first_dist).__name__}"

    def test_yieldmax_fund_name_not_empty(self, yieldmax_data):
        """Test that fund names are not empty"""
        for etf in yieldmax_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            fund_name = etf.get('fund_name', '')

            assert len(fund_name) > 0, f"{ticker}: Fund name is empty"
            assert 'yieldmax' in fund_name.lower() or ticker in fund_name.upper(), \
                f"{ticker}: Fund name doesn't contain YieldMax or ticker: {fund_name}"


class TestRoundhillDataQuality:
    """Data quality tests for Roundhill ETF data"""

    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Initialize Supabase client"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            pytest.skip("Supabase credentials not configured")
        return create_client(url, key)

    @pytest.fixture(scope="class")
    def roundhill_data(self, supabase_client) -> List[Dict[str, Any]]:
        """Fetch latest Roundhill data"""
        response = supabase_client.table('v_roundhill_latest').select('*').execute()
        return response.data

    def test_roundhill_data_exists(self, roundhill_data):
        """Test that Roundhill data exists in database"""
        assert len(roundhill_data) > 0, "No Roundhill ETF data found in database"
        assert len(roundhill_data) >= 40, f"Expected at least 40 Roundhill ETFs, found {len(roundhill_data)}"

    def test_roundhill_required_fields(self, roundhill_data):
        """Test that all required fields are present"""
        required_fields = ['ticker', 'fund_name', 'url', 'scraped_at']

        for etf in roundhill_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            for field in required_fields:
                assert field in etf, f"{ticker}: Missing required field '{field}'"
                assert etf[field] is not None, f"{ticker}: Field '{field}' is None"

    def test_roundhill_launch_date_format(self, roundhill_data):
        """Test that launch dates are in valid format and not in far future"""
        today = datetime.now().date()
        max_future_date = today + timedelta(days=365)  # Allow up to 1 year in future

        date_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')

        for etf in roundhill_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            launch_date = etf.get('launch_date')

            if launch_date:
                # Check format
                assert date_pattern.match(launch_date), \
                    f"{ticker}: Invalid launch date format: {launch_date} (expected MM/DD/YYYY)"

                # Check no percentage signs
                assert '%' not in launch_date, \
                    f"{ticker}: Percentage sign found in launch date: {launch_date}"

                # Parse and validate date is reasonable
                try:
                    parts = launch_date.split('/')
                    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])

                    # Validate ranges
                    assert 1 <= month <= 12, f"{ticker}: Invalid month in launch date: {month}"
                    assert 1 <= day <= 31, f"{ticker}: Invalid day in launch date: {day}"
                    assert 2000 <= year <= max_future_date.year + 1, \
                        f"{ticker}: Invalid year in launch date: {year} (must be 2000-{max_future_date.year + 1})"

                    # Check date is not too far in future
                    launch_datetime = datetime(year, month, day).date()
                    assert launch_datetime <= max_future_date, \
                        f"{ticker}: Launch date is too far in future: {launch_date}"

                except (ValueError, IndexError) as e:
                    pytest.fail(f"{ticker}: Invalid launch date value: {launch_date} - {e}")

    def test_roundhill_expense_ratio_format(self, roundhill_data):
        """Test that expense ratios are valid percentages (if present)"""
        # Pattern: 0.XX% or X.XX%
        expense_pattern = re.compile(r'^\d+\.?\d*%$')

        for etf in roundhill_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            expense_ratio = etf.get('expense_ratio')

            # Expense ratio is optional (some ETFs may fail to scrape)
            if expense_ratio is None:
                continue

            assert expense_pattern.match(expense_ratio), \
                f"{ticker}: Invalid expense ratio format: {expense_ratio} (expected X.XX%)"

            # Extract numeric value and validate range
            numeric_value = float(expense_ratio.rstrip('%'))
            assert 0.0 <= numeric_value <= 5.0, \
                f"{ticker}: Expense ratio out of expected range: {numeric_value}% (expected 0-5%)"

    def test_roundhill_holdings_count_format(self, roundhill_data):
        """Test that holdings counts are valid numbers (if present)"""
        for etf in roundhill_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            holdings_count = etf.get('holdings_count')

            if holdings_count is not None:
                # Should not contain percentage signs
                assert '%' not in str(holdings_count), \
                    f"{ticker}: Percentage sign in holdings count: {holdings_count}"

                # Should not contain non-numeric characters (except commas)
                clean_value = str(holdings_count).replace(',', '')
                assert clean_value.isdigit(), \
                    f"{ticker}: Holdings count is not numeric: {holdings_count}"

                # Should be reasonable (1-1000 for ETFs)
                count = int(clean_value)
                assert 1 <= count <= 1000, \
                    f"{ticker}: Holdings count out of expected range: {count} (expected 1-1000)"

    def test_roundhill_json_fields_valid(self, roundhill_data):
        """Test that JSON fields are valid JSON objects or parseable JSON strings"""
        import json

        json_fields = [
            'fund_overview',
            'performance_data',
            'fund_details',
            'distributions',
            'holdings'
        ]

        for etf in roundhill_data:
            ticker = etf.get('ticker', 'UNKNOWN')

            for field in json_fields:
                value = etf.get(field)
                if value is not None:
                    # Check if it's already parsed JSON
                    if isinstance(value, (dict, list)):
                        continue

                    # If it's a string, try to parse it
                    if isinstance(value, str):
                        try:
                            parsed = json.loads(value)
                            # None is valid for JSON fields (means empty/null)
                            if parsed is not None:
                                assert isinstance(parsed, (dict, list)), \
                                    f"{ticker}: Parsed '{field}' is not dict/list (got {type(parsed).__name__})"
                        except json.JSONDecodeError as e:
                            pytest.fail(f"{ticker}: Field '{field}' is not valid JSON string: {e}")
                    else:
                        pytest.fail(f"{ticker}: Field '{field}' is neither JSON nor string (got {type(value).__name__})")

    def test_roundhill_no_corrupted_data(self, roundhill_data):
        """Test that there's no corrupted data like 'TRS' or strange identifiers"""
        for etf in roundhill_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            holdings_count = str(etf.get('holdings_count', ''))
            launch_date = etf.get('launch_date')

            # Check for known corruption patterns in holdings count
            if holdings_count and holdings_count != 'None':
                assert 'TRS' not in holdings_count, \
                    f"{ticker}: Corrupted holdings count: {holdings_count}"
                assert not re.search(r'\d{8,}', holdings_count), \
                    f"{ticker}: Holdings count looks like identifier: {holdings_count}"

            # Launch date should have date separator if present
            if launch_date and launch_date != 'None':
                assert '/' in str(launch_date), \
                    f"{ticker}: Launch date missing date separator: {launch_date}"

    def test_roundhill_url_format(self, roundhill_data):
        """Test that URLs are valid Roundhill URLs"""
        for etf in roundhill_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            url = etf.get('url', '')

            assert url.startswith('https://www.roundhillinvestments.com/'), \
                f"{ticker}: Invalid URL format: {url}"
            assert ticker.lower() in url.lower(), \
                f"{ticker}: Ticker not found in URL: {url}"


class TestNEOSDataQuality:
    """Data quality tests for NEOS ETF data"""

    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Initialize Supabase client"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            pytest.skip("Supabase credentials not configured")
        return create_client(url, key)

    @pytest.fixture(scope="class")
    def neos_data(self, supabase_client) -> List[Dict[str, Any]]:
        """Fetch latest NEOS data"""
        response = supabase_client.table('v_neos_latest').select('*').execute()
        return response.data

    def test_neos_data_exists(self, neos_data):
        """Test that NEOS data exists in database"""
        assert len(neos_data) > 0, "No NEOS ETF data found in database"
        assert len(neos_data) >= 13, f"Expected at least 13 NEOS ETFs, found {len(neos_data)}"

    def test_neos_required_fields(self, neos_data):
        """Test that all required fields are present"""
        required_fields = ['ticker', 'fund_name', 'url', 'scraped_at']

        for etf in neos_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            for field in required_fields:
                assert field in etf, f"{ticker}: Missing required field '{field}'"
                assert etf[field] is not None, f"{ticker}: Field '{field}' is None"

    def test_neos_inception_date_format(self, neos_data):
        """Test that inception dates are in valid format and not in far future"""
        today = datetime.now().date()
        max_future_date = today + timedelta(days=365)

        date_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')

        for etf in neos_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            inception_date = etf.get('inception_date')

            if inception_date:
                # Check format
                assert date_pattern.match(inception_date), \
                    f"{ticker}: Invalid inception date format: {inception_date} (expected MM/DD/YYYY)"

                # Check no percentage signs
                assert '%' not in inception_date, \
                    f"{ticker}: Percentage sign found in inception date: {inception_date}"

                # Parse and validate date is reasonable
                try:
                    parts = inception_date.split('/')
                    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])

                    # Validate ranges
                    assert 1 <= month <= 12, f"{ticker}: Invalid month in inception date: {month}"
                    assert 1 <= day <= 31, f"{ticker}: Invalid day in inception date: {day}"
                    assert 2000 <= year <= max_future_date.year + 1, \
                        f"{ticker}: Invalid year in inception date: {year} (must be 2000-{max_future_date.year + 1})"

                    # Check date is not too far in future
                    inception_datetime = datetime(year, month, day).date()
                    assert inception_datetime <= max_future_date, \
                        f"{ticker}: Inception date is too far in future: {inception_date}"

                except (ValueError, IndexError) as e:
                    pytest.fail(f"{ticker}: Invalid inception date value: {inception_date} - {e}")

    def test_neos_expense_ratio_format(self, neos_data):
        """Test that expense ratios are valid percentages (if present)"""
        expense_pattern = re.compile(r'^\d+\.?\d*%$')

        for etf in neos_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            expense_ratio = etf.get('expense_ratio')

            if expense_ratio is None:
                continue

            assert expense_pattern.match(expense_ratio), \
                f"{ticker}: Invalid expense ratio format: {expense_ratio} (expected X.XX%)"

            # Extract numeric value and validate range
            numeric_value = float(expense_ratio.rstrip('%'))
            assert 0.0 <= numeric_value <= 5.0, \
                f"{ticker}: Expense ratio out of expected range: {numeric_value}% (expected 0-5%)"

    def test_neos_distribution_rate_format(self, neos_data):
        """Test that distribution rates are valid percentages (if present)"""
        dist_pattern = re.compile(r'^\d+\.?\d*%$')

        for etf in neos_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            distribution_rate = etf.get('distribution_rate')

            if distribution_rate is None:
                continue

            assert dist_pattern.match(distribution_rate), \
                f"{ticker}: Invalid distribution rate format: {distribution_rate} (expected X.XX%)"

            # Extract numeric value and validate range
            numeric_value = float(distribution_rate.rstrip('%'))
            assert 0.0 <= numeric_value <= 50.0, \
                f"{ticker}: Distribution rate out of expected range: {numeric_value}% (expected 0-50%)"

    def test_neos_json_fields_valid(self, neos_data):
        """Test that JSON fields are valid JSON objects or parseable JSON strings"""
        import json

        json_fields = [
            'fund_details',
            'performance_data',
            'distributions',
            'holdings'
        ]

        for etf in neos_data:
            ticker = etf.get('ticker', 'UNKNOWN')

            for field in json_fields:
                value = etf.get(field)
                if value is not None:
                    # Check if it's already parsed JSON
                    if isinstance(value, (dict, list)):
                        continue

                    # If it's a string, try to parse it
                    if isinstance(value, str):
                        try:
                            parsed = json.loads(value)
                            # None is valid for JSON fields (means empty/null)
                            if parsed is not None:
                                assert isinstance(parsed, (dict, list)), \
                                    f"{ticker}: Parsed '{field}' is not dict/list (got {type(parsed).__name__})"
                        except json.JSONDecodeError as e:
                            pytest.fail(f"{ticker}: Field '{field}' is not valid JSON string: {e}")
                    else:
                        pytest.fail(f"{ticker}: Field '{field}' is neither JSON nor string (got {type(value).__name__})")

    def test_neos_url_format(self, neos_data):
        """Test that URLs are valid NEOS URLs"""
        for etf in neos_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            url = etf.get('url', '')

            assert url.startswith('https://neosfunds.com/'), \
                f"{ticker}: Invalid URL format: {url}"
            assert ticker.lower() in url.lower(), \
                f"{ticker}: Ticker not found in URL: {url}"


class TestDefianceDataQuality:
    """Data quality tests for Defiance ETF data"""

    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Initialize Supabase client"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            pytest.skip("Supabase credentials not configured")
        return create_client(url, key)

    @pytest.fixture(scope="class")
    def defiance_data(self, supabase_client) -> List[Dict[str, Any]]:
        """Fetch latest Defiance data"""
        response = supabase_client.table('v_defiance_latest').select('*').execute()
        return response.data

    def test_defiance_data_exists(self, defiance_data):
        """Test that Defiance data exists in database"""
        assert len(defiance_data) > 0, "No Defiance ETF data found in database"
        assert len(defiance_data) >= 57, f"Expected at least 57 Defiance ETFs, found {len(defiance_data)}"

    def test_defiance_required_fields(self, defiance_data):
        """Test that all required fields are present"""
        required_fields = ['ticker', 'fund_name', 'url', 'scraped_at']

        for etf in defiance_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            for field in required_fields:
                assert field in etf, f"{ticker}: Missing required field '{field}'"
                assert etf[field] is not None, f"{ticker}: Field '{field}' is None"

    def test_defiance_inception_date_format(self, defiance_data):
        """Test that inception dates are in valid format and not in far future"""
        today = datetime.now().date()
        max_future_date = today + timedelta(days=365)

        date_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')

        for etf in defiance_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            inception_date = etf.get('inception_date')

            if inception_date:
                # Check format
                assert date_pattern.match(inception_date), \
                    f"{ticker}: Invalid inception date format: {inception_date} (expected MM/DD/YYYY)"

                # Check no percentage signs
                assert '%' not in inception_date, \
                    f"{ticker}: Percentage sign found in inception date: {inception_date}"

                # Parse and validate date is reasonable
                try:
                    parts = inception_date.split('/')
                    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])

                    # Validate ranges
                    assert 1 <= month <= 12, f"{ticker}: Invalid month in inception date: {month}"
                    assert 1 <= day <= 31, f"{ticker}: Invalid day in inception date: {day}"
                    assert 2000 <= year <= max_future_date.year + 1, \
                        f"{ticker}: Invalid year in inception date: {year} (must be 2000-{max_future_date.year + 1})"

                    # Check date is not too far in future
                    inception_datetime = datetime(year, month, day).date()
                    assert inception_datetime <= max_future_date, \
                        f"{ticker}: Inception date is too far in future: {inception_date}"

                except (ValueError, IndexError) as e:
                    pytest.fail(f"{ticker}: Invalid inception date value: {inception_date} - {e}")

    def test_defiance_expense_ratio_format(self, defiance_data):
        """Test that expense ratios are valid percentages (if present)"""
        expense_pattern = re.compile(r'^\d+\.?\d*%$')

        for etf in defiance_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            expense_ratio = etf.get('expense_ratio')

            if expense_ratio is None:
                continue

            assert expense_pattern.match(expense_ratio), \
                f"{ticker}: Invalid expense ratio format: {expense_ratio} (expected X.XX%)"

            # Extract numeric value and validate range
            numeric_value = float(expense_ratio.rstrip('%'))
            assert 0.0 <= numeric_value <= 5.0, \
                f"{ticker}: Expense ratio out of expected range: {numeric_value}% (expected 0-5%)"

    def test_defiance_distribution_rate_format(self, defiance_data):
        """Test that distribution rates are valid percentages (if present)"""
        dist_pattern = re.compile(r'^\d+\.?\d*%$')

        for etf in defiance_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            distribution_rate = etf.get('distribution_rate')

            if distribution_rate is None:
                continue

            assert dist_pattern.match(distribution_rate), \
                f"{ticker}: Invalid distribution rate format: {distribution_rate} (expected X.XX%)"

            # Extract numeric value and validate range (Defiance can have higher rates)
            numeric_value = float(distribution_rate.rstrip('%'))
            assert 0.0 <= numeric_value <= 150.0, \
                f"{ticker}: Distribution rate out of expected range: {numeric_value}% (expected 0-150%)"

    def test_defiance_distribution_frequency_format(self, defiance_data):
        """Test that distribution frequencies are valid values (if present)"""
        valid_frequencies = ['Weekly', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual']

        for etf in defiance_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            distribution_frequency = etf.get('distribution_frequency')

            if distribution_frequency is None:
                continue

            assert distribution_frequency in valid_frequencies, \
                f"{ticker}: Invalid distribution frequency: {distribution_frequency} (expected one of {valid_frequencies})"

    def test_defiance_json_fields_valid(self, defiance_data):
        """Test that JSON fields are valid JSON objects or parseable JSON strings"""
        import json

        json_fields = [
            'fund_details',
            'performance_data',
            'distributions',
            'holdings'
        ]

        for etf in defiance_data:
            ticker = etf.get('ticker', 'UNKNOWN')

            for field in json_fields:
                value = etf.get(field)
                if value is not None:
                    # Check if it's already parsed JSON
                    if isinstance(value, (dict, list)):
                        continue

                    # If it's a string, try to parse it
                    if isinstance(value, str):
                        try:
                            parsed = json.loads(value)
                            # None is valid for JSON fields (means empty/null)
                            if parsed is not None:
                                assert isinstance(parsed, (dict, list)), \
                                    f"{ticker}: Parsed '{field}' is not dict/list (got {type(parsed).__name__})"
                        except json.JSONDecodeError as e:
                            pytest.fail(f"{ticker}: Field '{field}' is not valid JSON string: {e}")
                    else:
                        pytest.fail(f"{ticker}: Field '{field}' is neither JSON nor string (got {type(value).__name__})")

    def test_defiance_url_format(self, defiance_data):
        """Test that URLs are valid Defiance URLs"""
        for etf in defiance_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            url = etf.get('url', '')

            assert url.startswith('https://www.defianceetfs.com/'), \
                f"{ticker}: Invalid URL format: {url}"
            assert ticker.lower() in url.lower(), \
                f"{ticker}: Ticker not found in URL: {url}"


class TestKurvDataQuality:
    """Data quality tests for Kurv ETF data"""

    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Initialize Supabase client"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            pytest.skip("Supabase credentials not configured")
        return create_client(url, key)

    @pytest.fixture(scope="class")
    def kurv_data(self, supabase_client) -> List[Dict[str, Any]]:
        """Fetch latest Kurv data"""
        response = supabase_client.table('v_kurv_latest').select('*').execute()
        return response.data

    def test_kurv_data_exists(self, kurv_data):
        """Test that Kurv data exists in database"""
        assert len(kurv_data) > 0, "No Kurv ETF data found in database"
        assert len(kurv_data) >= 7, f"Expected at least 7 Kurv ETFs, found {len(kurv_data)}"

    def test_kurv_required_fields(self, kurv_data):
        """Test that all required fields are present"""
        required_fields = ['ticker', 'fund_name', 'url', 'scraped_at']

        for etf in kurv_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            for field in required_fields:
                assert field in etf, f"{ticker}: Missing required field '{field}'"
                assert etf[field] is not None, f"{ticker}: Field '{field}' is None"

    def test_kurv_inception_date_format(self, kurv_data):
        """Test that inception dates are in valid format and not in far future"""
        today = datetime.now().date()
        max_future_date = today + timedelta(days=365)

        date_pattern = re.compile(r'^\d{1,2}/\d{1,2}/\d{4}$')

        for etf in kurv_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            inception_date = etf.get('inception_date')

            if inception_date:
                # Check format
                assert date_pattern.match(inception_date), \
                    f"{ticker}: Invalid inception date format: {inception_date} (expected MM/DD/YYYY)"

                # Check no percentage signs
                assert '%' not in inception_date, \
                    f"{ticker}: Percentage sign found in inception date: {inception_date}"

                # Parse and validate date is reasonable
                try:
                    parts = inception_date.split('/')
                    month, day, year = int(parts[0]), int(parts[1]), int(parts[2])

                    # Validate ranges
                    assert 1 <= month <= 12, f"{ticker}: Invalid month in inception date: {month}"
                    assert 1 <= day <= 31, f"{ticker}: Invalid day in inception date: {day}"
                    assert 2000 <= year <= max_future_date.year + 1, \
                        f"{ticker}: Invalid year in inception date: {year} (must be 2000-{max_future_date.year + 1})"

                    # Check date is not too far in future
                    inception_datetime = datetime(year, month, day).date()
                    assert inception_datetime <= max_future_date, \
                        f"{ticker}: Inception date is too far in future: {inception_date}"

                except (ValueError, IndexError) as e:
                    pytest.fail(f"{ticker}: Invalid inception date value: {inception_date} - {e}")

    def test_kurv_expense_ratio_format(self, kurv_data):
        """Test that expense ratios are valid percentages (if present)"""
        expense_pattern = re.compile(r'^\d+\.?\d*%$')

        for etf in kurv_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            expense_ratio = etf.get('expense_ratio')

            if expense_ratio is None:
                continue

            assert expense_pattern.match(expense_ratio), \
                f"{ticker}: Invalid expense ratio format: {expense_ratio} (expected X.XX%)"

            # Extract numeric value and validate range
            numeric_value = float(expense_ratio.rstrip('%'))
            assert 0.0 <= numeric_value <= 5.0, \
                f"{ticker}: Expense ratio out of expected range: {numeric_value}% (expected 0-5%)"

    def test_kurv_distribution_rate_format(self, kurv_data):
        """Test that distribution rates are valid percentages (if present)"""
        dist_pattern = re.compile(r'^\d+\.?\d*%$')

        for etf in kurv_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            distribution_rate = etf.get('distribution_rate')

            if distribution_rate is None:
                continue

            assert dist_pattern.match(distribution_rate), \
                f"{ticker}: Invalid distribution rate format: {distribution_rate} (expected X.XX%)"

            # Extract numeric value and validate range
            numeric_value = float(distribution_rate.rstrip('%'))
            assert 0.0 <= numeric_value <= 50.0, \
                f"{ticker}: Distribution rate out of expected range: {numeric_value}% (expected 0-50%)"

    def test_kurv_distribution_frequency_format(self, kurv_data):
        """Test that distribution frequencies are valid values (if present)"""
        valid_frequencies = ['Weekly', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual']

        for etf in kurv_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            distribution_frequency = etf.get('distribution_frequency')

            if distribution_frequency is None:
                continue

            assert distribution_frequency in valid_frequencies, \
                f"{ticker}: Invalid distribution frequency: {distribution_frequency} (expected one of {valid_frequencies})"

    def test_kurv_json_fields_valid(self, kurv_data):
        """Test that JSON fields are valid JSON objects or parseable JSON strings"""
        import json

        json_fields = [
            'fund_details',
            'performance_data',
            'distributions',
            'holdings'
        ]

        for etf in kurv_data:
            ticker = etf.get('ticker', 'UNKNOWN')

            for field in json_fields:
                value = etf.get(field)
                if value is not None:
                    # Check if it's already parsed JSON
                    if isinstance(value, (dict, list)):
                        continue

                    # If it's a string, try to parse it
                    if isinstance(value, str):
                        try:
                            parsed = json.loads(value)
                            # None is valid for JSON fields (means empty/null)
                            if parsed is not None:
                                assert isinstance(parsed, (dict, list)), \
                                    f"{ticker}: Parsed '{field}' is not dict/list (got {type(parsed).__name__})"
                        except json.JSONDecodeError as e:
                            pytest.fail(f"{ticker}: Field '{field}' is not valid JSON string: {e}")
                    else:
                        pytest.fail(f"{ticker}: Field '{field}' is neither JSON nor string (got {type(value).__name__})")

    def test_kurv_url_format(self, kurv_data):
        """Test that URLs are valid Kurv URLs"""
        for etf in kurv_data:
            ticker = etf.get('ticker', 'UNKNOWN')
            url = etf.get('url', '')

            assert url.startswith('https://www.kurvinvest.com/'), \
                f"{ticker}: Invalid URL format: {url}"
            assert ticker.lower() in url.lower(), \
                f"{ticker}: Ticker not found in URL: {url}"


class TestGraniteSharesDataQuality:
    """Data quality tests for GraniteShares ETF data"""

    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Initialize Supabase client"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            pytest.skip("Supabase credentials not configured")
        return create_client(url, key)

    @pytest.fixture(scope="class")
    def graniteshares_data(self, supabase_client) -> List[Dict[str, Any]]:
        """Fetch latest GraniteShares data"""
        response = supabase_client.table('v_graniteshares_latest').select('*').execute()
        return response.data

    def test_graniteshares_data_exists(self, graniteshares_data):
        """Test that GraniteShares data exists in database"""
        assert len(graniteshares_data) > 0, "No GraniteShares ETF data found in database"
        # Expect at least 1 ETF (TQQY that we tested)
        assert len(graniteshares_data) >= 1, f"Expected at least 1 GraniteShares ETF, found {len(graniteshares_data)}"

    def test_graniteshares_required_fields(self, graniteshares_data):
        """Test that all required fields are present"""
        for row in graniteshares_data:
            ticker = row['ticker']
            assert row.get('ticker'), f"{ticker}: Ticker is missing"
            assert row.get('fund_name'), f"{ticker}: Fund name is missing"
            assert row.get('url'), f"{ticker}: URL is missing"
            assert row.get('scraped_at'), f"{ticker}: scraped_at is missing"
            assert row.get('category'), f"{ticker}: Category is missing"

    def test_graniteshares_category_format(self, graniteshares_data):
        """Test that category is one of the valid categories"""
        valid_categories = ['YieldBOOST', 'Leveraged', 'Commodities', 'Gold', 'Equity', 'Income']
        for row in graniteshares_data:
            ticker = row['ticker']
            category = row.get('category')
            if category:
                assert category in valid_categories, \
                    f"{ticker}: Invalid category '{category}'. Must be one of {valid_categories}"

    def test_graniteshares_leverage_format(self, graniteshares_data):
        """Test that leverage is a valid number"""
        for row in graniteshares_data:
            ticker = row['ticker']
            leverage = row.get('leverage')
            if leverage:
                # Leverage should be a number (0, 1.25, 2, 3, -2, etc.)
                try:
                    lev_val = float(leverage)
                    assert -3 <= lev_val <= 3, \
                        f"{ticker}: Leverage {lev_val} out of expected range (-3 to 3)"
                except ValueError:
                    pytest.fail(f"{ticker}: Leverage '{leverage}' is not a valid number")

    def test_graniteshares_expense_ratio_format(self, graniteshares_data):
        """Test expense ratio format if present"""
        for row in graniteshares_data:
            ticker = row['ticker']
            expense_ratio = row.get('expense_ratio')
            if expense_ratio:
                # Should contain '%' or 'per annum'
                assert '%' in expense_ratio or 'per annum' in expense_ratio.lower(), \
                    f"{ticker}: Expense ratio '{expense_ratio}' should contain '%' or 'per annum'"

    def test_graniteshares_nav_format(self, graniteshares_data):
        """Test NAV format if present"""
        for row in graniteshares_data:
            ticker = row['ticker']
            nav = row.get('nav')
            if nav:
                # Should contain '$'
                assert '$' in nav, \
                    f"{ticker}: NAV '{nav}' should contain '$'"

    def test_graniteshares_json_fields_valid(self, graniteshares_data):
        """Test that JSON fields are valid JSON"""
        import json
        for row in graniteshares_data:
            ticker = row['ticker']

            # Test fund_details
            if row.get('fund_details') and row['fund_details'] not in ['null', None]:
                if isinstance(row['fund_details'], str):
                    # If it's a string, try to parse it
                    try:
                        json.loads(row['fund_details'])
                    except json.JSONDecodeError:
                        pytest.fail(f"{ticker}: fund_details is not valid JSON")
                else:
                    assert isinstance(row['fund_details'], dict), \
                        f"{ticker}: fund_details should be a JSON object or valid JSON string"

            # Test performance_data
            if row.get('performance_data') and row['performance_data'] not in ['null', None]:
                if isinstance(row['performance_data'], str):
                    try:
                        json.loads(row['performance_data'])
                    except json.JSONDecodeError:
                        pytest.fail(f"{ticker}: performance_data is not valid JSON")
                else:
                    assert isinstance(row['performance_data'], dict), \
                        f"{ticker}: performance_data should be a JSON object or valid JSON string"

            # Test distributions
            if row.get('distributions') and row['distributions'] not in ['null', None]:
                if isinstance(row['distributions'], str):
                    try:
                        json.loads(row['distributions'])
                    except json.JSONDecodeError:
                        pytest.fail(f"{ticker}: distributions is not valid JSON")
                else:
                    assert isinstance(row['distributions'], dict), \
                        f"{ticker}: distributions should be a JSON object or valid JSON string"

            # Test holdings
            if row.get('holdings') and row['holdings'] not in ['null', None]:
                if isinstance(row['holdings'], str):
                    try:
                        json.loads(row['holdings'])
                    except json.JSONDecodeError:
                        pytest.fail(f"{ticker}: holdings is not valid JSON")
                else:
                    assert isinstance(row['holdings'], dict), \
                        f"{ticker}: holdings should be a JSON object or valid JSON string"

    def test_graniteshares_url_format(self, graniteshares_data):
        """Test URL format"""
        for row in graniteshares_data:
            ticker = row['ticker']
            url = row.get('url')
            if url:
                assert url.startswith('https://graniteshares.com/'), \
                    f"{ticker}: Invalid URL format: {url}"
                assert ticker.lower() in url.lower(), \
                    f"{ticker}: Ticker not found in URL: {url}"


class TestCrossETFDataQuality:
    """Cross-ETF validation tests"""

    @pytest.fixture(scope="class")
    def supabase_client(self):
        """Initialize Supabase client"""
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_KEY')
        if not url or not key:
            pytest.skip("Supabase credentials not configured")
        return create_client(url, key)

    def test_no_duplicate_tickers(self, supabase_client):
        """Test that there are no duplicate tickers in YieldMax data"""
        response = supabase_client.table('v_yieldmax_latest').select('ticker').execute()
        tickers = [row['ticker'] for row in response.data]

        duplicates = [t for t in set(tickers) if tickers.count(t) > 1]
        assert len(duplicates) == 0, f"Duplicate YieldMax tickers found: {duplicates}"

    def test_no_duplicate_roundhill_tickers(self, supabase_client):
        """Test that there are no duplicate tickers in Roundhill data"""
        response = supabase_client.table('v_roundhill_latest').select('ticker').execute()
        tickers = [row['ticker'] for row in response.data]

        duplicates = [t for t in set(tickers) if tickers.count(t) > 1]
        assert len(duplicates) == 0, f"Duplicate Roundhill tickers found: {duplicates}"

    def test_no_duplicate_neos_tickers(self, supabase_client):
        """Test that there are no duplicate tickers in NEOS data"""
        response = supabase_client.table('v_neos_latest').select('ticker').execute()
        tickers = [row['ticker'] for row in response.data]

        duplicates = [t for t in set(tickers) if tickers.count(t) > 1]
        assert len(duplicates) == 0, f"Duplicate NEOS tickers found: {duplicates}"

    def test_no_duplicate_defiance_tickers(self, supabase_client):
        """Test that there are no duplicate tickers in Defiance data"""
        response = supabase_client.table('v_defiance_latest').select('ticker').execute()
        tickers = [row['ticker'] for row in response.data]

        duplicates = [t for t in set(tickers) if tickers.count(t) > 1]
        assert len(duplicates) == 0, f"Duplicate Defiance tickers found: {duplicates}"

    def test_no_duplicate_kurv_tickers(self, supabase_client):
        """Test that there are no duplicate tickers in Kurv data"""
        response = supabase_client.table('v_kurv_latest').select('ticker').execute()
        tickers = [row['ticker'] for row in response.data]

        duplicates = [t for t in set(tickers) if tickers.count(t) > 1]
        assert len(duplicates) == 0, f"Duplicate Kurv tickers found: {duplicates}"

    def test_no_duplicate_graniteshares_tickers(self, supabase_client):
        """Test that there are no duplicate tickers in GraniteShares data"""
        response = supabase_client.table('v_graniteshares_latest').select('ticker').execute()
        tickers = [row['ticker'] for row in response.data]

        duplicates = [t for t in set(tickers) if tickers.count(t) > 1]
        assert len(duplicates) == 0, f"Duplicate GraniteShares tickers found: {duplicates}"

    def test_scraped_at_recent(self, supabase_client):
        """Test that data was scraped recently (within last 7 days)"""
        from datetime import timezone
        from dateutil import parser
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

        # Check YieldMax
        response = supabase_client.table('v_yieldmax_latest').select('ticker, scraped_at').execute()
        for row in response.data:
            # Use dateutil.parser for robust datetime parsing
            scraped_at = parser.isoparse(row['scraped_at'])
            assert scraped_at >= seven_days_ago, \
                f"YieldMax {row['ticker']}: Data is stale (scraped {scraped_at.date()})"

        # Check Roundhill
        response = supabase_client.table('v_roundhill_latest').select('ticker, scraped_at').execute()
        for row in response.data:
            # Use dateutil.parser for robust datetime parsing
            scraped_at = parser.isoparse(row['scraped_at'])
            assert scraped_at >= seven_days_ago, \
                f"Roundhill {row['ticker']}: Data is stale (scraped {scraped_at.date()})"

        # Check NEOS
        response = supabase_client.table('v_neos_latest').select('ticker, scraped_at').execute()
        for row in response.data:
            # Use dateutil.parser for robust datetime parsing
            scraped_at = parser.isoparse(row['scraped_at'])
            assert scraped_at >= seven_days_ago, \
                f"NEOS {row['ticker']}: Data is stale (scraped {scraped_at.date()})"

        # Check Defiance
        response = supabase_client.table('v_defiance_latest').select('ticker, scraped_at').execute()
        for row in response.data:
            # Use dateutil.parser for robust datetime parsing
            scraped_at = parser.isoparse(row['scraped_at'])
            assert scraped_at >= seven_days_ago, \
                f"Defiance {row['ticker']}: Data is stale (scraped {scraped_at.date()})"

        # Check Kurv
        response = supabase_client.table('v_kurv_latest').select('ticker, scraped_at').execute()
        for row in response.data:
            # Use dateutil.parser for robust datetime parsing
            scraped_at = parser.isoparse(row['scraped_at'])
            assert scraped_at >= seven_days_ago, \
                f"Kurv {row['ticker']}: Data is stale (scraped {scraped_at.date()})"

        # Check GraniteShares
        response = supabase_client.table('v_graniteshares_latest').select('ticker, scraped_at').execute()
        for row in response.data:
            # Use dateutil.parser for robust datetime parsing
            scraped_at = parser.isoparse(row['scraped_at'])
            assert scraped_at >= seven_days_ago, \
                f"GraniteShares {row['ticker']}: Data is stale (scraped {scraped_at.date()})"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
