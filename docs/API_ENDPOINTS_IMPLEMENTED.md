# Dividend API - Implemented Endpoints

## Status: Production Ready ✅

All investor-focused endpoints are implemented and accessible at `http://localhost:8000/v1/`

---

## 📊 Stocks Endpoints

### `GET /v1/stocks`
**List and filter dividend stocks**

**Query Parameters:**
- `has_dividends` (boolean) - Only dividend-paying stocks
- `min_yield` (float) - Minimum dividend yield %
- `max_yield` (float) - Maximum dividend yield %
- `sector` (string) - Filter by sector
- `exchange` (string) - Filter by exchange
- `type` (string) - "stock", "etf", or "trust"
- `limit` (int) - Results per page (max 1000)
- `cursor` (string) - Pagination cursor

**Example Request:**
```bash
curl "http://localhost:8000/v1/stocks?has_dividends=true&min_yield=5.0&limit=20"
```

**Example Response:**
```json
{
  "object": "list",
  "has_more": false,
  "cursor": null,
  "data": [
    {
      "id": "stock_t",
      "symbol": "T",
      "company": "AT&T Inc.",
      "exchange": "NYSE",
      "sector": "Telecommunications",
      "price": 15.20,
      "dividend_yield": 6.8,
      "annual_dividend": 1.11,
      "type": "stock"
    }
  ]
}
```

### `GET /v1/stocks/{symbol}`
**Get detailed stock information**

**Example Request:**
```bash
curl "http://localhost:8000/v1/stocks/AAPL"
```

**Example Response:**
```json
{
  "id": "stock_aapl",
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "exchange": "NASDAQ",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "price": 185.50,
  "dividend_yield": 0.52,
  "annual_dividend": 0.96,
  "dividend_frequency": "quarterly",
  "ex_dividend_date": "2025-11-08",
  "payment_date": "2025-11-14",
  "payout_ratio": 15.2,
  "market_cap": 2850000000000,
  "pe_ratio": 28.5
}
```

---

## 💰 Dividends Endpoints

### `GET /v1/dividends/calendar`
**Upcoming dividend events**

**Query Parameters:**
- `start_date` (string) - Start date (YYYY-MM-DD)
- `end_date` (string) - End date (YYYY-MM-DD)
- `symbols` (string) - Comma-separated symbols
- `min_yield` (float) - Minimum yield filter

**Example Request:**
```bash
curl "http://localhost:8000/v1/dividends/calendar?start_date=2025-11-01&end_date=2025-12-31"
```

**Example Response:**
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
      "yield": 0.52,
      "frequency": "quarterly"
    }
  ]
}
```

### `GET /v1/dividends/{symbol}/history`
**Historical dividend payments**

**Query Parameters:**
- `start_date` (string) - Start date
- `end_date` (string) - End date
- `limit` (int) - Number of records

**Example Request:**
```bash
curl "http://localhost:8000/v1/dividends/AAPL/history?limit=12"
```

**Example Response:**
```json
{
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "dividends": [
    {
      "amount": 0.24,
      "ex_date": "2025-08-09",
      "payment_date": "2025-08-15"
    }
  ],
  "stats": {
    "total_payments": 48,
    "average_amount": 0.23,
    "growth_rate_5yr": 4.2
  }
}
```

---

## 🔍 Screeners Endpoints

### `GET /v1/screeners/high-yield`
**High-yield dividend stocks**

**Query Parameters:**
- `min_yield` (float) - Minimum yield (default 5.0)
- `min_market_cap` (float) - Minimum market cap
- `sectors` (string) - Comma-separated sectors
- `limit` (int) - Results limit

**Example Request:**
```bash
curl "http://localhost:8000/v1/screeners/high-yield?min_yield=6.0&limit=50"
```

**Example Response:**
```json
{
  "screener": "high-yield",
  "criteria": {
    "min_yield": 6.0
  },
  "count": 25,
  "data": [
    {
      "symbol": "T",
      "company": "AT&T Inc.",
      "yield": 6.8,
      "price": 15.20,
      "annual_dividend": 1.11,
      "sector": "Telecommunications",
      "payout_ratio": 55.2
    }
  ]
}
```

### `GET /v1/screeners/monthly-payers`
**Monthly dividend payers**

**Example Request:**
```bash
curl "http://localhost:8000/v1/screeners/monthly-payers"
```

### `GET /v1/screeners/dividend-aristocrats`
**Dividend aristocrats (25+ years of increases)**

**Query Parameters:**
- `min_years` (int) - Minimum consecutive years (default 25)

**Example Request:**
```bash
curl "http://localhost:8000/v1/screeners/dividend-aristocrats"
```

### `GET /v1/screeners/dividend-growth`
**Strong dividend growth stocks**

**Query Parameters:**
- `min_growth_rate` (float) - Minimum 5-year growth rate
- `min_consecutive_years` (int) - Minimum years of increases

**Example Request:**
```bash
curl "http://localhost:8000/v1/screeners/dividend-growth?min_growth_rate=10.0"
```

---

## 📈 Analytics Endpoints

### `POST /v1/analytics/portfolio`
**Analyze dividend portfolio**

**Request Body:**
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

**Example Request:**
```bash
curl -X POST "http://localhost:8000/v1/analytics/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "positions": [
      {"symbol": "AAPL", "shares": 100}
    ],
    "projection_years": 5
  }'
```

**Example Response:**
```json
{
  "current_value": 18550.00,
  "current_yield": 0.52,
  "annual_dividend_income": 96.00,
  "monthly_income": 8.00,
  "projected_value_5yr": 25000.00,
  "projected_income_5yr": 150.00,
  "positions": [
    {
      "symbol": "AAPL",
      "shares": 100,
      "current_value": 18550.00,
      "annual_dividends": 96.00,
      "yield_on_cost": 0.52
    }
  ]
}
```

### `GET /v1/analytics/dividend-income/{symbol}`
**Calculate dividend income**

**Query Parameters:**
- `shares` (int) - Number of shares
- `purchase_price` (float) - Purchase price per share

**Example Request:**
```bash
curl "http://localhost:8000/v1/analytics/dividend-income/AAPL?shares=100&purchase_price=150.00"
```

**Example Response:**
```json
{
  "symbol": "AAPL",
  "shares": 100,
  "purchase_price": 150.00,
  "investment": 15000.00,
  "annual_dividend": 96.00,
  "monthly_income": 8.00,
  "yield_on_cost": 0.64,
  "current_yield": 0.52
}
```

---

## 💹 Prices Endpoints

### `GET /v1/prices/{symbol}/history`
**Historical price data**

**Query Parameters:**
- `start_date` (string) - Start date
- `end_date` (string) - End date
- `interval` (string) - "daily", "weekly", "monthly"

**Example Request:**
```bash
curl "http://localhost:8000/v1/prices/AAPL/history?start_date=2025-10-01&end_date=2025-11-01"
```

**Example Response:**
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
      "volume": 52000000
    }
  ]
}
```

### `GET /v1/prices/{symbol}/quote`
**Current price quote**

**Example Request:**
```bash
curl "http://localhost:8000/v1/prices/AAPL/quote"
```

**Example Response:**
```json
{
  "symbol": "AAPL",
  "price": 185.50,
  "change": 2.30,
  "change_percent": 1.26,
  "volume": 52000000,
  "dividend_yield": 0.52,
  "52_week_high": 199.62,
  "52_week_low": 164.08,
  "market_cap": 2850000000000
}
```

---

## 🔎 Search Endpoint

### `GET /v1/search`
**Search for stocks**

**Query Parameters:**
- `q` (string) - Search query (required)
- `type` (string) - "stock", "etf", "all"
- `limit` (int) - Results limit

**Example Request:**
```bash
curl "http://localhost:8000/v1/search?q=apple"
```

**Example Response:**
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

## 🔐 Authentication

All endpoints (except `/health`) require an API key:

```bash
curl -H "X-API-Key: sk_live_your_key_here" \
  "http://localhost:8000/v1/stocks?limit=10"
```

### API Key Management

#### `POST /v1/keys`
Create a new API key

#### `GET /v1/keys`
List your API keys

#### `DELETE /v1/keys/{key_id}`
Revoke an API key

---

## ⚡ Rate Limits

Rate limits are enforced per API key:

| Tier | Per Minute | Per Hour | Per Day |
|------|------------|----------|---------|
| Free | 60 | 1,000 | 10,000 |
| Pro | 600 | 20,000 | 500,000 |
| Enterprise | 6,000 | 200,000 | 10,000,000 |

Rate limit headers are included in all responses:
- `X-RateLimit-Limit` - Your rate limit
- `X-RateLimit-Remaining` - Requests remaining
- `X-RateLimit-Reset` - Reset timestamp

---

## 📋 Response Format

### Success Response
All successful responses follow this format:

```json
{
  "object": "list|stock|dividend",
  "data": [...],
  "has_more": false,
  "cursor": null
}
```

### Error Response
All errors follow this format:

```json
{
  "error": {
    "type": "invalid_request_error",
    "message": "Symbol 'INVALID' not found",
    "param": "symbol",
    "code": "symbol_not_found"
  }
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

---

## 🚀 Quick Start

### 1. List High-Yield Stocks
```bash
curl "http://localhost:8000/v1/screeners/high-yield?min_yield=5.0"
```

### 2. Get Dividend Calendar
```bash
curl "http://localhost:8000/v1/dividends/calendar?start_date=2025-11-01&end_date=2025-11-30"
```

### 3. Analyze a Portfolio
```bash
curl -X POST "http://localhost:8000/v1/analytics/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "positions": [
      {"symbol": "T", "shares": 100},
      {"symbol": "VZ", "shares": 50}
    ]
  }'
```

### 4. Search for Stocks
```bash
curl "http://localhost:8000/v1/search?q=dividend"
```

---

## 📚 Interactive Documentation

Full interactive API documentation with try-it-out functionality:

- **Swagger UI**: http://localhost:8000/v1/docs
- **ReDoc**: http://localhost:8000/v1/redoc
- **Custom Docs**: http://localhost:3000

---

## 💾 Database Tables Used

- `raw_stocks` - Stock information
- `raw_dividends` - Dividend history
- `raw_dividends_fixed` - Validated dividends
- `raw_historical_stock_prices` - Price history
- `mart_high_yield_stocks` - Materialized view for high-yield screener
- `mart_dividend_calendar` - Materialized view for dividend calendar

---

## 🎯 Use Cases

### For Dividend Investors
- Find high-yield stocks in specific sectors
- Track upcoming dividend payments
- Analyze dividend growth history
- Calculate yield on cost for holdings

### For Portfolio Managers
- Analyze entire portfolio dividend income
- Project future dividend growth
- Evaluate diversification
- Calculate total return

### For Developers
- Build dividend tracking apps
- Create screening tools
- Develop portfolio analytics
- Integrate dividend data into platforms

---

**API Version**: 1.0.0
**Last Updated**: 2025-11-13
**Status**: Production Ready ✅
**Base URL**: http://localhost:8000/v1
