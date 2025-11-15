# Divv Test Suite

Comprehensive test suite for the Divv API and Google Sheets integration (DIVV function).

## Overview

This test suite validates:
- ✅ API endpoints with real-world data
- ✅ Google Sheets DIVV() function behavior
- ✅ Tier restrictions (free vs. paid)
- ✅ Historical data queries
- ✅ Error handling
- ✅ GOOGLEFINANCE() parity

## Test Files

### `seed_data.json`
Comprehensive test fixture data including:
- **5 stocks**: AAPL, MSFT, JNJ, PG, T
- **Current data**: Price, dividends, PE ratio, market cap, volume, etc.
- **Historical prices**: AAPL (5 dates), MSFT (2 dates)
- **Dividend history**: AAPL (5 dividends), JNJ (4 dividends)
- **Test cases**: 40+ predefined test scenarios

### `test_api_endpoints.py`
Python/pytest test suite for API endpoints:
- Stock quote endpoint (`/v1/stocks/{symbol}/quote`)
- Historical prices endpoint (`/v1/prices/{symbol}`)
- Current data attributes (free & paid tier)
- Dividend data endpoints
- Bulk quote endpoint
- Error handling (invalid symbols, dates)
- API health checks

### `test_divv_integration.js`
JavaScript test suite for Google Sheets integration:
- Current data tests (free tier)
- Current data tests (paid tier)
- Historical data queries
- Tier restrictions enforcement
- Error handling
- Real-world use cases (portfolio calculations)

### `run_tests.sh`
Automated test runner script:
- Checks if API is running, starts if needed
- Runs Python API tests with pytest
- Provides instructions for manual Google Sheets tests
- Generates test report with summary

## Quick Start

### Run All Tests

```bash
cd tests
./run_tests.sh
```

This will:
1. Check if API is running at `http://localhost:8000`
2. Start API if not running
3. Run Python API tests
4. Display instructions for Google Sheets tests
5. Generate test report

### Run Only API Tests

```bash
cd tests
pytest test_api_endpoints.py -v
```

### Run Specific Test Class

```bash
# Test stock quotes only
pytest test_api_endpoints.py::TestStockQuoteEndpoint -v

# Test historical prices only
pytest test_api_endpoints.py::TestHistoricalPrices -v

# Test tier restrictions
pytest test_api_endpoints.py::TestCurrentDataAttributes -v
```

## Google Sheets Integration Tests

The Google Sheets integration tests (`test_divv_integration.js`) require a Google Apps Script environment.

### Option 1: Manual Testing in Google Sheets

1. Open a new Google Sheet
2. Go to **Extensions > Apps Script**
3. Copy the contents of `test_divv_integration.js`
4. Also copy `DIVV.gs` from `docs-site/public/DIVV.gs`
5. Run the function: `runAllTests()`

### Option 2: Using clasp (Google Apps Script CLI)

```bash
# Install clasp
npm install -g @google/clasp

# Login to Google
clasp login

# Create new Apps Script project
clasp create --title "DIVV Tests" --type sheets

# Push code
clasp push

# Run tests
clasp run runAllTests
```

## Test Data Structure

### Stocks in Seed Data

| Symbol | Name | Sector | Dividend Yield | Special |
|--------|------|--------|----------------|---------|
| AAPL | Apple Inc. | Technology | 0.52% | Has historical data |
| MSFT | Microsoft | Technology | 0.89% | Has historical data |
| JNJ | Johnson & Johnson | Healthcare | 3.00% | Dividend Aristocrat (61 years) |
| PG | Procter & Gamble | Consumer Staples | 2.45% | Dividend Aristocrat (67 years) |
| T | AT&T | Telecommunications | 6.15% | High yield |

### Test Coverage

#### Current Data Tests (Free Tier)
- ✅ `price` - Current/last traded price
- ✅ `open` - Opening price
- ✅ `dayHigh` - Day high price
- ✅ `dayLow` - Day low price
- ✅ `previousClose` - Previous closing price
- ✅ `dividendYield` - Dividend yield percentage
- ✅ `dividendAmount` - Annual dividend per share

#### Current Data Tests (Paid Tier)
- ✅ `peRatio` - Price-to-earnings ratio
- ✅ `marketCap` - Market capitalization
- ✅ `volume` - Trading volume
- ✅ `yearHigh` - 52-week high
- ✅ `yearLow` - 52-week low

#### Historical Data Tests (Paid Tier)
- ✅ Single date query: `=DIVV("AAPL", "close", "2024-01-15")`
- ✅ Date range query: `=DIVV("AAPL", "close", "2024-01-15", "2024-01-17")`
- ✅ Multiple date formats (ISO, DATE(), cell reference)
- ✅ 2D array output for charting

#### Tier Restriction Tests
- ✅ Free tier blocked on PE ratio
- ✅ Free tier blocked on volume
- ✅ Free tier blocked on market cap
- ✅ Free tier blocked on historical data
- ✅ Free tier blocked on DIVVDIVIDENDS()
- ✅ Free tier blocked on DIVVARISTOCRAT()

#### Error Handling Tests
- ✅ Invalid symbol returns `#ERROR`
- ✅ Invalid attribute returns `#N/A`
- ✅ Empty symbol returns error
- ✅ Null symbol returns error
- ✅ Invalid date format returns error
- ✅ Future date returns empty data

## Prerequisites

### Python Tests
```bash
pip3 install pytest requests
```

### API Server
The API must be running at `http://localhost:8000`. The test runner will start it automatically if not running.

```bash
# Manual start
cd /path/to/project
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Google Sheets Tests (Optional)
- Google Account
- Google Sheets access
- Apps Script editor access
- OR clasp CLI installed (`npm install -g @google/clasp`)

## Test Results

Test results are saved to `test_results_YYYYMMDD_HHMMSS.log` with:
- Detailed pytest output
- Pass/fail counts
- Error messages and stack traces
- Summary report

Example output:
```
=================================================================================================
                                  Test Summary
=================================================================================================

Python API Tests:
  ✓ Passed: 25
  ✗ Failed: 0

Google Sheets Integration Tests:
  ℹ Manual test available at: tests/test_divv_integration.js

Test Seed Data:
  📁 Location: tests/seed_data.json
  📊 Stocks: 5 (AAPL, MSFT, JNJ, PG, T)
  📈 Historical Prices: AAPL (5 dates), MSFT (2 dates)
  💰 Dividend History: AAPL (5 dividends), JNJ (4 dividends)
  🧪 Test Cases: 40+ scenarios
```

## Continuous Integration

To run tests in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run API Tests
  run: |
    pip install pytest requests
    cd tests
    pytest test_api_endpoints.py -v --tb=short
```

## Troubleshooting

### API Not Starting
- Check if port 8000 is already in use: `lsof -i :8000`
- Check if uvicorn is installed: `pip3 install uvicorn`
- Check API logs for errors

### Tests Failing
- Ensure API is running and healthy: `curl http://localhost:8000/health`
- Check if seed data exists: `cat tests/seed_data.json`
- Verify database has test data loaded
- Check API logs for errors

### Google Sheets Tests Not Working
- Ensure you're using the latest DIVV.gs from `docs-site/public/DIVV.gs`
- Check API key is set in script properties
- Verify `ACCOUNT_TIER` is set correctly
- Check Apps Script execution logs

## Adding New Tests

### Add API Test
```python
# In test_api_endpoints.py
class TestNewFeature:
    def test_new_endpoint(self):
        response = requests.get(f"{API_BASE_URL}/v1/new-endpoint")
        assert response.status_code == 200
```

### Add Integration Test
```javascript
// In test_divv_integration.js
runTest("Test new feature", () => {
    const result = DIVV("AAPL", "newAttribute");
    assertEquals(result, expectedValue, "Should return correct value");
}, results);
```

### Add Seed Data
```json
// In seed_data.json
{
  "stocks": [
    {
      "symbol": "NEW",
      "price": 123.45,
      ...
    }
  ]
}
```

## Documentation

For more information:
- [API Documentation](../docs-site/app/api)
- [Google Sheets Integration](../docs-site/app/integrations/google-sheets)
- [Historical Data Feature](../docs-site/HISTORICAL_DATA_FEATURE.md)
- [Pricing Strategy](../docs-site/INTEGRATIONS_PRICING_STRATEGY.md)
- [Rate Limiting Tests](./README.md)
