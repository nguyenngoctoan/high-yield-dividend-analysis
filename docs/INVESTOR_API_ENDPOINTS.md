# Dividend API - Investor-Focused Endpoints

## Overview
Production-ready API endpoints for dividend investors using real data from our database.

## Core Investor Needs

### 1. Stock Discovery & Screening
- Find high-yield dividend stocks
- Filter by dividend characteristics
- Screen by financial metrics
- Discover monthly/quarterly dividend payers

### 2. Dividend Information
- Upcoming dividend payments (ex-date, pay-date)
- Historical dividend history
- Dividend growth rates
- Payment frequency and consistency

### 3. Portfolio Management
- Track dividend income
- Calculate yield on cost
- Project future dividend income
- Analyze diversification

### 4. Market Data
- Real-time prices
- Historical price charts
- Total return calculations
- Price-to-dividend ratios

---

## API Endpoints Specification

### Stocks Endpoints

#### `GET /v1/stocks`
**Purpose**: List and filter dividend stocks
**Parameters**:
- `has_dividends`: boolean - Only show dividend-paying stocks
- `min_yield`: float - Minimum dividend yield %
- `max_yield`: float - Maximum dividend yield %
- `sector`: string - Filter by sector
- `exchange`: string - Filter by exchange (NASDAQ, NYSE, etc.)
- `min_price`: float - Minimum stock price
- `max_price`: float - Maximum stock price
- `limit`: int - Results per page (default 100, max 1000)
- `cursor`: string - Pagination cursor

**Response**:
```json
{
  "object": "list",
  "has_more": false,
  "cursor": null,
  "data": [
    {
      "id": "stock_aapl",
      "symbol": "AAPL",
      "company": "Apple Inc.",
      "exchange": "NASDAQ",
      "sector": "Technology",
      "price": 185.50,
      "dividend_yield": 0.52,
      "annual_dividend": 0.96,
      "type": "stock",
      "market_cap": 2850000000000
    }
  ]
}
```

#### `GET /v1/stocks/{symbol}`
**Purpose**: Get detailed information for a specific stock
**Response**:
```json
{
  "id": "stock_aapl",
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "price": 185.50,
  "dividend_yield": 0.52,
  "annual_dividend": 0.96,
  "dividend_frequency": "quarterly",
  "ex_dividend_date": "2025-11-08",
  "payment_date": "2025-11-14",
  "payout_ratio": 15.2,
  "consecutive_years": 12,
  "market_cap": 2850000000000,
  "pe_ratio": 28.5,
  "52_week_high": 199.62,
  "52_week_low": 164.08
}
```

### Dividends Endpoints

#### `GET /v1/dividends/calendar`
**Purpose**: Get upcoming dividend events
**Parameters**:
- `start_date`: string (YYYY-MM-DD) - Start date for calendar
- `end_date`: string (YYYY-MM-DD) - End date for calendar
- `symbols`: string - Comma-separated list of symbols
- `min_yield`: float - Minimum yield filter
- `event_type`: string - "ex_date", "pay_date", "declaration_date"

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "symbol": "AAPL",
      "company": "Apple Inc.",
      "amount": 0.24,
      "ex_date": "2025-11-08",
      "payment_date": "2025-11-14",
      "declaration_date": "2025-10-31",
      "yield": 0.52,
      "frequency": "quarterly",
      "currency": "USD"
    }
  ]
}
```

#### `GET /v1/dividends/{symbol}/history`
**Purpose**: Get historical dividend payments for a stock
**Parameters**:
- `start_date`: string - Start date
- `end_date`: string - End date
- `limit`: int - Number of records

**Response**:
```json
{
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "dividends": [
    {
      "amount": 0.24,
      "ex_date": "2025-08-09",
      "payment_date": "2025-08-15",
      "currency": "USD"
    }
  ],
  "stats": {
    "total_payments": 48,
    "average_amount": 0.23,
    "growth_rate_5yr": 4.2,
    "consistency_score": 98
  }
}
```

### Screeners Endpoints

#### `GET /v1/screeners/high-yield`
**Purpose**: Find high-yield dividend stocks
**Parameters**:
- `min_yield`: float - Minimum yield (default 5.0)
- `min_market_cap`: float - Minimum market cap
- `sectors`: string - Comma-separated sectors
- `limit`: int - Results limit

**Response**:
```json
{
  "screener": "high-yield",
  "criteria": {
    "min_yield": 5.0,
    "min_market_cap": 1000000000
  },
  "data": [
    {
      "symbol": "T",
      "company": "AT&T Inc.",
      "yield": 6.8,
      "price": 15.20,
      "annual_dividend": 1.11,
      "payout_ratio": 55.2,
      "sector": "Telecommunications"
    }
  ]
}
```

#### `GET /v1/screeners/monthly-payers`
**Purpose**: Find stocks that pay dividends monthly
**Response**: List of monthly dividend payers with yields

#### `GET /v1/screeners/dividend-aristocrats`
**Purpose**: Find dividend aristocrats (25+ years of increases)
**Response**: List of stocks with long dividend growth streaks

####`GET /v1/screeners/dividend-growth`
**Purpose**: Find stocks with strong dividend growth
**Parameters**:
- `min_growth_rate`: float - Minimum 5-year growth rate
- `min_consecutive_years`: int - Minimum years of increases

### Analytics Endpoints

#### `POST /v1/analytics/portfolio`
**Purpose**: Analyze a dividend portfolio
**Request Body**:
```json
{
  "positions": [
    {"symbol": "AAPL", "shares": 100},
    {"symbol": "MSFT", "shares": 50}
  ],
  "projection_years": 5,
  "reinvest_dividends": true,
  "annual_contribution": 10000
}
```

**Response**:
```json
{
  "current_value": 25000.00,
  "current_yield": 2.1,
  "annual_dividend_income": 525.00,
  "monthly_income": 43.75,
  "projected_value_5yr": 42000.00,
  "projected_income_5yr": 1050.00,
  "diversification": {
    "sectors": {
      "Technology": 65,
      "Healthcare": 35
    },
    "dividend_frequency": {
      "quarterly": 100
    }
  },
  "positions": [
    {
      "symbol": "AAPL",
      "shares": 100,
      "cost_basis": 150.00,
      "current_value": 18550.00,
      "annual_dividends": 96.00,
      "yield_on_cost": 0.64,
      "total_return": 23.7
    }
  ]
}
```

#### `GET /v1/analytics/dividend-income/{symbol}`
**Purpose**: Calculate potential dividend income for a position
**Parameters**:
- `shares`: int - Number of shares
- `purchase_price`: float - Purchase price per share

**Response**:
```json
{
  "symbol": "AAPL",
  "shares": 100,
  "purchase_price": 150.00,
  "investment": 15000.00,
  "annual_dividend": 96.00,
  "monthly_income": 8.00,
  "yield_on_cost": 0.64,
  "current_yield": 0.52,
  "years_to_recover": 156.25
}
```

### Prices Endpoints

#### `GET /v1/prices/{symbol}/history`
**Purpose**: Get historical price data
**Parameters**:
- `start_date`: string - Start date
- `end_date`: string - End date
- `interval`: string - "daily", "weekly", "monthly"

**Response**:
```json
{
  "symbol": "AAPL",
  "interval": "daily",
  "prices": [
    {
      "date": "2025-11-12",
      "open": 184.20,
      "high": 186.50,
      "low": 183.80,
      "close": 185.50,
      "volume": 52000000,
      "adjusted_close": 185.50
    }
  ]
}
```

#### `GET /v1/prices/{symbol}/quote`
**Purpose**: Get current price and basic info
**Response**:
```json
{
  "symbol": "AAPL",
  "price": 185.50,
  "change": 2.30,
  "change_percent": 1.26,
  "volume": 52000000,
  "market_cap": 2850000000000,
  "pe_ratio": 28.5,
  "dividend_yield": 0.52,
  "52_week_high": 199.62,
  "52_week_low": 164.08,
  "timestamp": "2025-11-12T20:00:00Z"
}
```

### Search Endpoint

#### `GET /v1/search`
**Purpose**: Search for stocks by symbol, name, or sector
**Parameters**:
- `q`: string - Search query
- `type`: string - "stock", "etf", "all"
- `limit`: int - Results limit

**Response**:
```json
{
  "query": "apple",
  "results": [
    {
      "symbol": "AAPL",
      "company": "Apple Inc.",
      "type": "stock",
      "exchange": "NASDAQ",
      "sector": "Technology",
      "dividend_yield": 0.52,
      "match_type": "company_name"
    }
  ]
}
```

---

## Response Format Standards

### Success Response
```json
{
  "object": "list|stock|dividend|portfolio",
  "data": [...],
  "has_more": false,
  "cursor": null
}
```

### Error Response
```json
{
  "error": {
    "type": "invalid_request_error|api_error|authentication_error",
    "message": "Human-readable error message",
    "param": "parameter_name",
    "code": "error_code"
  }
}
```

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid API key)
- `404`: Not Found (symbol doesn't exist)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

---

## Rate Limits (per API key)

| Tier | Per Minute | Per Hour | Per Day |
|------|------------|----------|---------|
| Free | 60 | 1,000 | 10,000 |
| Pro | 600 | 20,000 | 500,000 |
| Enterprise | 6,000 | 200,000 | 10,000,000 |

---

## Authentication

All requests (except documentation) require an API key in the header:

```
X-API-Key: sk_live_your_api_key_here
```

---

## Implementation Priority

### Phase 1: Core Dividend Data ✅
1. `/v1/stocks` - List stocks with dividend filters
2. `/v1/stocks/{symbol}` - Stock details
3. `/v1/dividends/calendar` - Upcoming dividends
4. `/v1/dividends/{symbol}/history` - Historical dividends

### Phase 2: Screening & Discovery ⏳
5. `/v1/screeners/high-yield` - High-yield screener
6. `/v1/screeners/monthly-payers` - Monthly dividend payers
7. `/v1/screeners/dividend-aristocrats` - Long-term growers
8. `/v1/search` - Stock search

### Phase 3: Analytics & Portfolio 📋
9. `/v1/analytics/portfolio` - Portfolio analysis
10. `/v1/analytics/dividend-income/{symbol}` - Income calculator
11. `/v1/prices/{symbol}/history` - Price history
12. `/v1/prices/{symbol}/quote` - Current quote

---

## Data Sources

- **Stock Data**: `raw_stocks` table
- **Dividend Data**: `raw_dividends`, `raw_dividends_fixed` tables
- **Price Data**: `raw_historical_stock_prices` table
- **Calculated Views**: `mart_comprehensive_dividend_stocks`, `mart_dividend_calendar`

---

**Status**: Ready for implementation
**Last Updated**: 2025-11-13
**Version**: 1.0.0
