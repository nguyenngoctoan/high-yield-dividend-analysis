# Dividend API - Production Architecture

## Overview

A production-grade RESTful API designed for dividend investors, providing comprehensive access to stock prices, dividend data, ETF holdings, and portfolio analytics. Inspired by Stripe's developer experience with clear documentation, predictable patterns, and intuitive endpoints.

## Design Philosophy

### Core Principles

1. **Dividend-First**: Every endpoint optimized for dividend investor workflows
2. **Developer Experience**: Clear, predictable, well-documented endpoints
3. **Performance**: Sub-100ms response times with intelligent caching
4. **Reliability**: 99.9% uptime with graceful degradation
5. **Simplicity**: RESTful patterns with minimal cognitive overhead

### API Patterns (Stripe-Inspired)

- **Resource-based URLs**: `/v1/dividends`, `/v1/stocks/{symbol}`
- **Versioned**: `/v1` namespace for stability
- **Predictable errors**: Structured error responses with codes
- **Pagination**: Cursor-based for large datasets
- **Filtering**: Rich query parameters for data slicing
- **Expansion**: `?expand=company,holdings` to reduce requests

## API Endpoints

### 1. Stocks & Symbols

#### `GET /v1/stocks`
List all available stocks with optional filtering.

**Query Parameters**:
- `exchange`: Filter by exchange (NYSE, NASDAQ, etc.)
- `type`: Filter by type (stock, etf, trust)
- `has_dividends`: Boolean filter for dividend-paying only
- `min_yield`: Minimum dividend yield (e.g., 5.0 for 5%)
- `max_yield`: Maximum dividend yield
- `sector`: Filter by sector
- `limit`: Results per page (default 100, max 1000)
- `cursor`: Pagination cursor
- `expand`: Comma-separated fields to expand (company, dividends, prices)

**Response**:
```json
{
  "object": "list",
  "has_more": true,
  "cursor": "eyJzeW1ib2wiOiJBQVBMIn0=",
  "data": [
    {
      "id": "stock_abc123",
      "object": "stock",
      "symbol": "AAPL",
      "exchange": "NASDAQ",
      "type": "stock",
      "company": "Apple Inc.",
      "sector": "Technology",
      "price": 185.50,
      "dividend_yield": 0.52,
      "updated_at": "2025-11-12T10:30:00Z"
    }
  ]
}
```

#### `GET /v1/stocks/{symbol}`
Retrieve detailed information for a specific stock.

**Query Parameters**:
- `expand`: Expand related data (company, dividends, holdings, prices)

**Response**:
```json
{
  "id": "stock_abc123",
  "object": "stock",
  "symbol": "AAPL",
  "exchange": "NASDAQ",
  "type": "stock",
  "company": {
    "name": "Apple Inc.",
    "description": "Technology company...",
    "ceo": "Tim Cook",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "market_cap": 2850000000000,
    "employees": 164000,
    "website": "https://www.apple.com"
  },
  "pricing": {
    "current": 185.50,
    "open": 184.20,
    "high": 186.30,
    "low": 183.90,
    "volume": 52000000,
    "change": 1.30,
    "change_percent": 0.71
  },
  "dividends": {
    "yield": 0.52,
    "annual_amount": 0.96,
    "frequency": "quarterly",
    "ex_dividend_date": "2025-11-08",
    "payment_date": "2025-11-15",
    "payout_ratio": 15.2,
    "5yr_growth_rate": 5.8
  },
  "updated_at": "2025-11-12T10:30:00Z",
  "metadata": {}
}
```

### 2. Dividends

#### `GET /v1/dividends/calendar`
Get upcoming dividend events (ex-dates, payment dates).

**Query Parameters**:
- `start_date`: Start of date range (ISO 8601)
- `end_date`: End of date range
- `symbols`: Comma-separated symbol filter
- `min_yield`: Minimum yield filter
- `event_type`: Filter by event (ex_dividend, payment, declaration)
- `limit`: Results per page
- `cursor`: Pagination cursor

**Response**:
```json
{
  "object": "list",
  "has_more": false,
  "data": [
    {
      "id": "div_event_xyz789",
      "object": "dividend_event",
      "symbol": "AAPL",
      "event_type": "ex_dividend",
      "event_date": "2025-11-08",
      "amount": 0.24,
      "yield": 0.52,
      "frequency": "quarterly",
      "declaration_date": "2025-10-26",
      "record_date": "2025-11-09",
      "payment_date": "2025-11-15",
      "company": "Apple Inc."
    }
  ]
}
```

#### `GET /v1/dividends/history`
Historical dividend payments across symbols.

**Query Parameters**:
- `symbols`: Comma-separated symbols (required)
- `start_date`: Start of date range
- `end_date`: End of date range
- `limit`: Results per page

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "div_hist_abc456",
      "object": "dividend_payment",
      "symbol": "AAPL",
      "payment_date": "2025-08-15",
      "ex_dividend_date": "2025-08-08",
      "amount": 0.24,
      "type": "cash",
      "declared_date": "2025-07-26"
    }
  ]
}
```

#### `GET /v1/stocks/{symbol}/dividends`
All dividend data for a specific stock.

**Query Parameters**:
- `include_future`: Include future scheduled dividends
- `years`: Number of years of history (default 5)

**Response**:
```json
{
  "object": "dividend_summary",
  "symbol": "AAPL",
  "current": {
    "yield": 0.52,
    "annual_amount": 0.96,
    "frequency": "quarterly",
    "payout_ratio": 15.2
  },
  "next_payment": {
    "ex_date": "2025-11-08",
    "payment_date": "2025-11-15",
    "estimated_amount": 0.24
  },
  "history": [
    {
      "date": "2025-08-15",
      "amount": 0.24,
      "type": "cash"
    }
  ],
  "growth": {
    "1yr": 4.2,
    "3yr": 5.1,
    "5yr": 5.8,
    "10yr": 8.5
  },
  "consistency": {
    "consecutive_years": 12,
    "increases": 12,
    "decreases": 0,
    "suspensions": 0
  }
}
```

### 3. Screeners

#### `GET /v1/screeners/high-yield`
Pre-built screener for high-yield dividend stocks.

**Query Parameters**:
- `min_yield`: Minimum yield (default 4.0)
- `min_market_cap`: Minimum market cap
- `sectors`: Comma-separated sectors
- `exchanges`: Comma-separated exchanges
- `exclude_etfs`: Boolean to exclude ETFs
- `min_payout_ratio`: Minimum payout ratio
- `max_payout_ratio`: Maximum payout ratio
- `min_consecutive_years`: Minimum years of dividend payments
- `limit`: Results per page
- `sort`: Sort field (yield, market_cap, consistency)
- `order`: asc or desc

**Response**:
```json
{
  "object": "screener_results",
  "screener": "high_yield",
  "criteria": {
    "min_yield": 4.0,
    "min_market_cap": 1000000000
  },
  "count": 347,
  "data": [
    {
      "symbol": "T",
      "company": "AT&T Inc.",
      "yield": 7.2,
      "price": 15.80,
      "market_cap": 112000000000,
      "payout_ratio": 92.5,
      "consecutive_years": 39,
      "5yr_growth": -2.1
    }
  ]
}
```

#### `GET /v1/screeners/dividend-aristocrats`
Stocks with 25+ consecutive years of dividend increases.

#### `GET /v1/screeners/dividend-kings`
Stocks with 50+ consecutive years of dividend increases.

#### `GET /v1/screeners/monthly-payers`
Stocks/ETFs that pay monthly dividends.

### 4. ETFs

#### `GET /v1/etfs/{symbol}/holdings`
ETF portfolio holdings breakdown.

**Query Parameters**:
- `limit`: Number of holdings to return (default 50)
- `include_weights`: Include position weights

**Response**:
```json
{
  "object": "etf_holdings",
  "symbol": "VYM",
  "name": "Vanguard High Dividend Yield ETF",
  "total_holdings": 446,
  "aum": 52000000000,
  "expense_ratio": 0.06,
  "updated_at": "2025-11-10",
  "holdings": [
    {
      "symbol": "JPM",
      "company": "JPMorgan Chase & Co.",
      "weight": 3.42,
      "shares": 2500000,
      "market_value": 437500000,
      "sector": "Financials"
    }
  ],
  "sector_allocation": {
    "Financials": 23.5,
    "Healthcare": 14.2,
    "Consumer Staples": 12.8
  }
}
```

#### `GET /v1/etfs/classify/{symbol}`
Identify ETF investment strategy and related stocks.

**Response**:
```json
{
  "object": "etf_classification",
  "symbol": "TSLY",
  "strategy": "Covered Call on Single Stock",
  "underlying_stock": "TSLA",
  "strategy_details": {
    "type": "income",
    "mechanism": "options_premium",
    "risk_level": "high",
    "leveraged": false,
    "inverse": false
  },
  "related_etfs": [
    "YIELDMAX TSLA",
    "NVDY"
  ]
}
```

### 5. Prices

#### `GET /v1/prices/{symbol}`
Price history for a symbol.

**Query Parameters**:
- `start_date`: Start date (ISO 8601)
- `end_date`: End date
- `interval`: daily, weekly, monthly (default daily)
- `limit`: Results per page

**Response**:
```json
{
  "object": "price_history",
  "symbol": "AAPL",
  "interval": "daily",
  "data": [
    {
      "date": "2025-11-12",
      "open": 184.20,
      "high": 186.30,
      "low": 183.90,
      "close": 185.50,
      "volume": 52000000,
      "adj_close": 185.50
    }
  ]
}
```

#### `GET /v1/prices/{symbol}/latest`
Latest price snapshot.

**Response**:
```json
{
  "object": "price_snapshot",
  "symbol": "AAPL",
  "price": 185.50,
  "change": 1.30,
  "change_percent": 0.71,
  "volume": 52000000,
  "timestamp": "2025-11-12T16:00:00Z",
  "market_status": "closed"
}
```

### 6. Analytics

#### `POST /v1/analytics/portfolio`
Calculate portfolio dividend income projections.

**Request Body**:
```json
{
  "positions": [
    {
      "symbol": "AAPL",
      "shares": 100
    },
    {
      "symbol": "MSFT",
      "shares": 50
    }
  ],
  "projection_years": 5,
  "reinvest_dividends": true,
  "annual_contribution": 10000
}
```

**Response**:
```json
{
  "object": "portfolio_analysis",
  "current_value": 25000.00,
  "annual_dividend_income": 520.00,
  "portfolio_yield": 2.08,
  "projections": [
    {
      "year": 1,
      "dividend_income": 520.00,
      "portfolio_value": 26500.00,
      "yield": 1.96
    }
  ],
  "by_symbol": [
    {
      "symbol": "AAPL",
      "shares": 100,
      "value": 18550.00,
      "annual_dividends": 96.00,
      "weight": 74.2
    }
  ]
}
```

#### `GET /v1/analytics/dividend-growth`
Analyze dividend growth trends across sectors/symbols.

### 7. Search

#### `GET /v1/search`
Search stocks by symbol, company name, or sector.

**Query Parameters**:
- `q`: Search query (required)
- `type`: Filter by type (stock, etf, trust)
- `limit`: Results limit

**Response**:
```json
{
  "object": "search_results",
  "query": "apple",
  "count": 3,
  "data": [
    {
      "symbol": "AAPL",
      "company": "Apple Inc.",
      "exchange": "NASDAQ",
      "type": "stock",
      "relevance": 1.0
    }
  ]
}
```

## Authentication & Authorization

### API Keys

Following Stripe's model:
- **Test Mode**: `sk_test_...` for development
- **Live Mode**: `sk_live_...` for production
- **Publishable Keys**: `pk_test_...` / `pk_live_...` for frontend (limited access)

### Authentication Method

HTTP Bearer token in Authorization header:
```
Authorization: Bearer sk_live_51H...
```

### API Key Scopes

```json
{
  "key_id": "key_abc123",
  "type": "secret",
  "scopes": [
    "stocks:read",
    "dividends:read",
    "analytics:read",
    "analytics:write"
  ],
  "rate_limit": {
    "tier": "professional",
    "requests_per_minute": 1000
  }
}
```

### Rate Limiting

**Tiers**:
1. **Free**: 100 requests/minute, 10,000/day
2. **Basic**: 500 requests/minute, 50,000/day
3. **Professional**: 1,000 requests/minute, 500,000/day
4. **Enterprise**: Custom limits

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1699876800
```

**429 Response**:
```json
{
  "error": {
    "type": "rate_limit_error",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

## Response Format

### Success Response

All successful responses follow this structure:
```json
{
  "object": "stock",
  "id": "stock_abc123",
  "...": "resource fields"
}
```

### List Response

```json
{
  "object": "list",
  "has_more": true,
  "cursor": "base64_encoded_cursor",
  "data": []
}
```

### Error Response

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

### Error Types

- `api_error`: Internal server error
- `authentication_error`: Invalid API key
- `invalid_request_error`: Bad request parameters
- `rate_limit_error`: Too many requests
- `resource_not_found_error`: Resource doesn't exist

## Caching Strategy

### Cache Layers

1. **Redis Cache** (60s TTL):
   - Latest prices
   - Popular symbols
   - Search results

2. **CDN Cache** (5min TTL):
   - Static lists
   - Historical data
   - Documentation

3. **Database Cache** (materialized views):
   - Screener results
   - Aggregated analytics

### Cache Headers

```
Cache-Control: public, max-age=60
ETag: "abc123xyz"
Last-Modified: Tue, 12 Nov 2025 10:30:00 GMT
```

### Conditional Requests

Support `If-None-Match` and `If-Modified-Since` for bandwidth optimization.

## Database Optimizations

### Materialized Views

```sql
-- High-yield stocks (updated hourly)
CREATE MATERIALIZED VIEW mart_high_yield_stocks AS
SELECT
    symbol,
    company,
    price,
    dividend_yield,
    sector,
    market_cap,
    payout_ratio
FROM raw_stocks
WHERE dividend_yield >= 4.0
AND type = 'stock'
ORDER BY dividend_yield DESC;

-- Dividend calendar (updated daily)
CREATE MATERIALIZED VIEW mart_dividend_calendar AS
SELECT
    symbol,
    ex_dividend_date,
    payment_date,
    amount,
    frequency,
    company
FROM raw_future_dividends
WHERE ex_dividend_date >= CURRENT_DATE
ORDER BY ex_dividend_date;

-- ETF holdings summary
CREATE MATERIALIZED VIEW mart_etf_holdings_summary AS
SELECT
    etf_symbol,
    COUNT(*) as total_holdings,
    SUM(weight) as total_weight,
    jsonb_agg(
        jsonb_build_object(
            'symbol', holding_symbol,
            'weight', weight
        ) ORDER BY weight DESC
    ) as top_holdings
FROM raw_etf_holdings
GROUP BY etf_symbol;
```

### Indexes

```sql
-- Dividend yield index
CREATE INDEX idx_stocks_dividend_yield
ON raw_stocks(dividend_yield DESC NULLS LAST)
WHERE dividend_yield IS NOT NULL;

-- Symbol lookup
CREATE INDEX idx_stocks_symbol_gin
ON raw_stocks USING gin(symbol gin_trgm_ops);

-- Company search
CREATE INDEX idx_stocks_company_gin
ON raw_stocks USING gin(company gin_trgm_ops);

-- Dividend calendar
CREATE INDEX idx_future_dividends_ex_date
ON raw_future_dividends(ex_dividend_date)
WHERE ex_dividend_date >= CURRENT_DATE;

-- Price history
CREATE INDEX idx_stock_prices_symbol_date
ON raw_stock_prices(symbol, date DESC);
```

### Database Functions

```sql
-- Fast screener function
CREATE OR REPLACE FUNCTION get_high_yield_stocks(
    min_yield float DEFAULT 4.0,
    min_market_cap bigint DEFAULT 1000000000,
    limit_count int DEFAULT 100
)
RETURNS TABLE(...) AS $$
BEGIN
    RETURN QUERY
    SELECT ... FROM raw_stocks
    WHERE dividend_yield >= min_yield
    AND market_cap >= min_market_cap
    ORDER BY dividend_yield DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;
```

## Tech Stack

### Backend

- **Framework**: FastAPI 0.104+
- **Python**: 3.11+
- **Database**: PostgreSQL 15+ (Supabase)
- **Cache**: Redis 7+
- **Task Queue**: Celery + Redis
- **API Gateway**: Kong or AWS API Gateway

### Monitoring & Observability

- **Logging**: Structured JSON logs (Python logging)
- **Metrics**: Prometheus + Grafana
- **Tracing**: OpenTelemetry + Jaeger
- **Errors**: Sentry
- **Uptime**: UptimeRobot or Pingdom

### Infrastructure

- **Hosting**: AWS ECS Fargate or GCP Cloud Run
- **Database**: Supabase (managed PostgreSQL)
- **CDN**: CloudFront or Cloudflare
- **Load Balancer**: AWS ALB or GCP Load Balancer
- **CI/CD**: GitHub Actions

### Security

- **API Keys**: Hashed with bcrypt, stored in database
- **Rate Limiting**: Redis-backed sliding window
- **DDoS Protection**: Cloudflare
- **Secrets**: AWS Secrets Manager or GCP Secret Manager
- **TLS**: Automatic via Let's Encrypt

## Deployment Architecture

```
                              ┌─────────────┐
                              │   Client    │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  CloudFlare │ (CDN, DDoS, TLS)
                              └──────┬──────┘
                                     │
                         ┌───────────▼────────────┐
                         │   Load Balancer (ALB)  │
                         └───────────┬────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐    ┌────▼────┐    ┌─────▼─────┐
              │  API       │    │  API    │    │  API      │
              │  Instance 1│    │  Inst 2 │    │  Inst 3   │
              │  (FastAPI) │    │ (FastAPI│    │ (FastAPI) │
              └─────┬──────┘    └────┬────┘    └─────┬─────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
              ┌─────▼──────┐                  ┌───────▼────────┐
              │   Redis    │                  │   PostgreSQL   │
              │   Cache    │                  │   (Supabase)   │
              └────────────┘                  └────────────────┘
```

## Performance Targets

### Response Times

- **List endpoints**: < 100ms (p95)
- **Detail endpoints**: < 50ms (p95)
- **Analytics**: < 500ms (p95)
- **Search**: < 200ms (p95)

### Throughput

- **Requests/second**: 1,000+ per instance
- **Concurrent connections**: 10,000+
- **Data freshness**: 1-minute staleness max for prices

### Availability

- **Uptime**: 99.9% (43 minutes downtime/month)
- **Error rate**: < 0.1%
- **Cache hit rate**: > 80%

## API Versioning

### Strategy

- **URL-based**: `/v1/stocks`, `/v2/stocks`
- **Backward compatibility**: v1 maintained for 2 years
- **Deprecation warnings**: Headers notify of upcoming changes
- **Sunset headers**: `Sunset: Sat, 01 Jan 2027 00:00:00 GMT`

### Version Headers

```
API-Version: v1
Supported-Versions: v1, v2
Deprecated-Versions:
```

## Documentation Site Architecture

### Frontend Stack

- **Framework**: Next.js 14+ (App Router)
- **Styling**: Tailwind CSS
- **Components**: Radix UI
- **Code Highlighting**: Shiki
- **API Explorer**: React + OpenAPI spec
- **Hosting**: Vercel

### Site Structure

```
docs.dividendapi.com/
├── /                           # Homepage
├── /quickstart                 # Getting started guide
├── /api                        # API reference
│   ├── /stocks                # Stocks endpoints
│   ├── /dividends             # Dividends endpoints
│   ├── /screeners             # Screeners endpoints
│   ├── /etfs                  # ETFs endpoints
│   ├── /prices                # Prices endpoints
│   └── /analytics             # Analytics endpoints
├── /guides                     # Integration guides
│   ├── /authentication        # Auth guide
│   ├── /rate-limits           # Rate limit guide
│   ├── /pagination            # Pagination guide
│   └── /errors                # Error handling
├── /examples                   # Code examples
│   ├── /python                # Python examples
│   ├── /javascript            # JS examples
│   └── /curl                  # cURL examples
├── /playground                 # Interactive API tester
└── /changelog                  # API changelog
```

### Design System (Stripe-Inspired)

**Layout**:
- 3-column design: Navigation | Content | Code Examples
- Sticky navigation sidebar
- Synchronized code snippets
- Dark mode support

**Colors**:
- Primary: Dividend green (#22c55e)
- Accent: Financial blue (#3b82f6)
- Dark mode: True black backgrounds (#000000)

**Typography**:
- Headings: Inter
- Body: Inter
- Code: JetBrains Mono

## Next Steps

1. ✅ Architecture document complete
2. ⏭️ Implement FastAPI application
3. ⏭️ Create database views and functions
4. ⏭️ Build authentication system
5. ⏭️ Implement rate limiting
6. ⏭️ Create Next.js documentation site
7. ⏭️ Build interactive API explorer
8. ⏭️ Deploy to production

---

*Document Version: 1.0*
*Last Updated: 2025-11-12*
