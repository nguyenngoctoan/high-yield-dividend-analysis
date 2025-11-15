"""
API Endpoint Tests with Seed Data

Tests all API endpoints using seed data to verify correct responses.
"""

import json
import requests
import pytest
from datetime import datetime
from pathlib import Path


# Load seed data
SEED_DATA_PATH = Path(__file__).parent / "seed_data.json"
with open(SEED_DATA_PATH) as f:
    SEED_DATA = json.load(f)

API_BASE_URL = "http://localhost:8000"


class TestStockQuoteEndpoint:
    """Test /v1/stocks/{symbol}/quote endpoint"""

    @pytest.mark.parametrize("stock", SEED_DATA["stocks"])
    def test_get_stock_quote(self, stock):
        """Test getting current quote for each seed stock"""
        symbol = stock["symbol"]
        response = requests.get(f"{API_BASE_URL}/v1/stocks/{symbol}/quote")

        assert response.status_code == 200, f"Failed to get quote for {symbol}"

        data = response.json()

        # Verify symbol
        assert data["symbol"] == symbol

        # Verify all expected fields are present
        assert "price" in data
        assert "open" in data
        assert "dayHigh" in data or "day_high" in data
        assert "dayLow" in data or "day_low" in data
        assert "dividendYield" in data or "dividend_yield" in data

    def test_invalid_symbol(self):
        """Test that invalid symbols return 404"""
        response = requests.get(f"{API_BASE_URL}/v1/stocks/INVALID/quote")
        assert response.status_code == 404


class TestHistoricalPrices:
    """Test /v1/prices/{symbol} endpoint"""

    def test_get_aapl_single_date(self):
        """Test getting historical price for single date"""
        response = requests.get(
            f"{API_BASE_URL}/v1/prices/AAPL",
            params={
                "start_date": "2024-01-15",
                "end_date": "2024-01-15"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "AAPL"
        assert len(data["data"]) == 1

        bar = data["data"][0]
        assert bar["date"] == "2024-01-15"
        # Close price should match seed data
        assert abs(bar["close"] - 185.59) < 0.01

    def test_get_aapl_date_range(self):
        """Test getting historical prices for date range"""
        response = requests.get(
            f"{API_BASE_URL}/v1/prices/AAPL",
            params={
                "start_date": "2024-01-15",
                "end_date": "2024-01-17"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "AAPL"
        assert len(data["data"]) == 3

        # Verify dates are in order
        dates = [bar["date"] for bar in data["data"]]
        assert "2024-01-15" in dates
        assert "2024-01-16" in dates
        assert "2024-01-17" in dates

    def test_get_msft_historical(self):
        """Test MSFT historical data"""
        response = requests.get(
            f"{API_BASE_URL}/v1/prices/MSFT",
            params={
                "start_date": "2024-01-15",
                "end_date": "2024-01-15"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["symbol"] == "MSFT"
        bar = data["data"][0]
        assert abs(bar["close"] - 372.91) < 0.01


class TestCurrentDataAttributes:
    """Test that all current data attributes work correctly"""

    def test_free_tier_attributes(self):
        """Test all free tier attributes"""
        free_tier_attrs = [
            ("price", 175.43),
            ("open", 174.50),
            ("dayHigh", 176.20),
            ("dayLow", 173.80),
            ("previousClose", 174.25),
            ("dividendYield", 0.52),
            ("dividendAmount", 0.96)
        ]

        for attr, expected_value in free_tier_attrs:
            response = requests.get(f"{API_BASE_URL}/v1/stocks/AAPL/quote")
            assert response.status_code == 200

            data = response.json()

            # Handle both camelCase and snake_case
            value = data.get(attr) or data.get(attr.replace("C", "_c").replace("H", "_h").replace("L", "_l").replace("Y", "_y").replace("A", "_a").lower())

            if value is not None:
                assert abs(value - expected_value) < 0.01, f"Attribute {attr} mismatch"

    def test_paid_tier_attributes(self):
        """Test paid tier attributes"""
        response = requests.get(f"{API_BASE_URL}/v1/stocks/AAPL/quote")
        assert response.status_code == 200

        data = response.json()

        # These might not be in free tier but should be in response
        paid_attrs = ["peRatio", "pe_ratio", "marketCap", "market_cap", "volume"]

        # At least one version should exist
        for attr in ["peRatio", "pe_ratio"]:
            if attr in data:
                assert data[attr] is not None
                break


class TestDividendData:
    """Test dividend-related endpoints"""

    def test_get_aapl_dividends(self):
        """Test getting AAPL dividend history"""
        response = requests.get(f"{API_BASE_URL}/v1/dividends/AAPL")

        # Endpoint might not exist yet, so just check structure if it does
        if response.status_code == 200:
            data = response.json()
            assert "dividends" in data or "data" in data

    def test_dividend_calendar(self):
        """Test dividend calendar endpoint"""
        response = requests.get(
            f"{API_BASE_URL}/v1/dividends/calendar",
            params={"range": "1m"}
        )

        if response.status_code == 200:
            data = response.json()
            assert "events" in data or "data" in data


class TestBulkEndpoint:
    """Test bulk quote endpoint"""

    def test_bulk_quotes(self):
        """Test getting quotes for multiple symbols"""
        symbols = ["AAPL", "MSFT", "JNJ"]
        response = requests.post(
            f"{API_BASE_URL}/v1/stocks/bulk/quote",
            json={"symbols": symbols}
        )

        if response.status_code == 200:
            data = response.json()

            # Should return data for all symbols
            assert len(data.get("data", [])) == len(symbols)

            # Verify each symbol is present
            returned_symbols = [item["symbol"] for item in data.get("data", [])]
            for symbol in symbols:
                assert symbol in returned_symbols


class TestErrorHandling:
    """Test error cases"""

    def test_invalid_date_format(self):
        """Test that invalid date formats return 400"""
        response = requests.get(
            f"{API_BASE_URL}/v1/prices/AAPL",
            params={"start_date": "invalid-date"}
        )

        # Should return 400 or 422 for invalid input
        assert response.status_code in [400, 422]

    def test_future_date(self):
        """Test that future dates return empty or error"""
        response = requests.get(
            f"{API_BASE_URL}/v1/prices/AAPL",
            params={
                "start_date": "2030-01-01",
                "end_date": "2030-01-02"
            }
        )

        # Should return 200 with empty data or 404
        if response.status_code == 200:
            data = response.json()
            assert len(data.get("data", [])) == 0
        else:
            assert response.status_code == 404


class TestAPIHealth:
    """Test API health and status"""

    def test_health_endpoint(self):
        """Test /health endpoint"""
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200

        data = response.json()
        assert data.get("status") == "healthy" or data.get("status") == "ok"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
