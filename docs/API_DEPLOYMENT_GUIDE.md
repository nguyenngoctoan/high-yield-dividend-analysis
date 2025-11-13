# Dividend API - Deployment & Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install API dependencies
pip install -r api/requirements.txt
```

### 2. Deploy Database Optimizations

```bash
# Connect to your Supabase database
psql $DATABASE_URL < migrations/create_api_optimizations.sql
```

This creates:
- 4 materialized views for fast queries
- 20+ performance indexes
- 4 helper functions for complex operations

### 3. Start the API Server

```bash
# Development mode (with hot reload)
./api/start_api.sh

# Or manually
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **API Base**: http://localhost:8000/v1
- **Interactive Docs**: http://localhost:8000/v1/docs
- **ReDoc**: http://localhost:8000/v1/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Stocks

```bash
# List all stocks with filtering
GET /v1/stocks?has_dividends=true&min_yield=5.0&limit=50

# Get specific stock details
GET /v1/stocks/AAPL?expand=company,dividends,prices

# Example Response:
{
  "id": "stock_aapl",
  "symbol": "AAPL",
  "company": {
    "name": "Apple Inc.",
    "sector": "Technology",
    "market_cap": 2850000000000
  },
  "pricing": {
    "current": 185.50,
    "change": 1.30,
    "change_percent": 0.71
  },
  "dividends": {
    "yield": 0.52,
    "annual_amount": 0.96,
    "frequency": "quarterly"
  }
}
```

### Dividends

```bash
# Get dividend calendar (upcoming ex-dates)
GET /v1/dividends/calendar?start_date=2025-11-01&end_date=2025-12-31

# Get historical dividends
GET /v1/dividends/history?symbols=AAPL,MSFT&start_date=2024-01-01

# Get complete dividend summary for a stock
GET /v1/stocks/AAPL/dividends?include_future=true&years=5
```

### Screeners

```bash
# High-yield dividend stocks
GET /v1/screeners/high-yield?min_yield=4.0&min_market_cap=1000000000

# Monthly dividend payers
GET /v1/screeners/monthly-payers?min_yield=5.0

# Example Response:
{
  "screener": "high_yield",
  "criteria": {"min_yield": 4.0},
  "count": 347,
  "data": [
    {
      "symbol": "T",
      "company": "AT&T Inc.",
      "yield": 7.2,
      "price": 15.80,
      "market_cap": 112000000000
    }
  ]
}
```

### ETFs

```bash
# Get ETF holdings
GET /v1/etfs/VYM/holdings?limit=50

# Classify ETF strategy
GET /v1/etfs/classify/TSLY

# Example Response:
{
  "symbol": "TSLY",
  "strategy": "Covered Call on Single Stock",
  "underlying_stock": "TSLA",
  "strategy_details": {
    "type": "income",
    "mechanism": "options_premium",
    "risk_level": "high"
  }
}
```

### Prices

```bash
# Get price history
GET /v1/prices/AAPL?start_date=2025-01-01&end_date=2025-11-12

# Get latest price snapshot
GET /v1/prices/AAPL/latest
```

### Analytics

```bash
# Analyze portfolio
POST /v1/analytics/portfolio
Content-Type: application/json

{
  "positions": [
    {"symbol": "AAPL", "shares": 100},
    {"symbol": "MSFT", "shares": 50}
  ],
  "projection_years": 5,
  "reinvest_dividends": true,
  "annual_contribution": 10000
}

# Example Response:
{
  "current_value": 25000.00,
  "annual_dividend_income": 520.00,
  "portfolio_yield": 2.08,
  "projections": [
    {
      "year": 1,
      "dividend_income": 536.00,
      "portfolio_value": 37500.00,
      "yield": 1.43
    }
  ]
}
```

### Search

```bash
# Search stocks by symbol, company, or sector
GET /v1/search?q=apple&limit=10

# Example Response:
{
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

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/v1"

# Get high-yield stocks
response = requests.get(
    f"{BASE_URL}/stocks",
    params={
        "has_dividends": True,
        "min_yield": 5.0,
        "limit": 20
    }
)
stocks = response.json()

# Get dividend calendar
response = requests.get(
    f"{BASE_URL}/dividends/calendar",
    params={
        "start_date": "2025-11-01",
        "end_date": "2025-12-31"
    }
)
calendar = response.json()

# Analyze portfolio
response = requests.post(
    f"{BASE_URL}/analytics/portfolio",
    json={
        "positions": [
            {"symbol": "AAPL", "shares": 100},
            {"symbol": "MSFT", "shares": 50}
        ],
        "projection_years": 5,
        "reinvest_dividends": True
    }
)
analysis = response.json()
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/v1';

// Get high-yield stocks
const stocks = await fetch(`${BASE_URL}/stocks?has_dividends=true&min_yield=5.0`)
  .then(res => res.json());

// Search for stocks
const results = await fetch(`${BASE_URL}/search?q=dividend`)
  .then(res => res.json());

// Analyze portfolio
const analysis = await fetch(`${BASE_URL}/analytics/portfolio`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    positions: [
      {symbol: 'AAPL', shares: 100},
      {symbol': 'MSFT', shares: 50}
    ],
    projection_years: 5,
    reinvest_dividends: true
  })
}).then(res => res.json());
```

### cURL

```bash
# Get high-yield stocks
curl "http://localhost:8000/v1/stocks?has_dividends=true&min_yield=5.0"

# Get stock details with expansion
curl "http://localhost:8000/v1/stocks/AAPL?expand=company,dividends"

# Search
curl "http://localhost:8000/v1/search?q=technology"

# Analyze portfolio
curl -X POST "http://localhost:8000/v1/analytics/portfolio" \
  -H "Content-Type: application/json" \
  -d '{
    "positions": [
      {"symbol": "AAPL", "shares": 100}
    ],
    "projection_years": 5
  }'
```

## Performance Optimization

### Materialized View Refresh

The API uses materialized views for fast queries. Refresh them regularly:

```sql
-- Refresh all views (run hourly via cron)
SELECT refresh_api_materialized_views();

-- Or refresh individually
REFRESH MATERIALIZED VIEW CONCURRENTLY mart_high_yield_stocks;
REFRESH MATERIALIZED VIEW CONCURRENTLY mart_dividend_calendar;
REFRESH MATERIALIZED VIEW CONCURRENTLY mart_monthly_dividend_payers;
REFRESH MATERIALIZED VIEW CONCURRENTLY mart_etf_holdings_summary;
```

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add hourly refresh (adjust DATABASE_URL as needed)
0 * * * * psql $DATABASE_URL -c "SELECT refresh_api_materialized_views();" >> /var/log/api_refresh.log 2>&1
```

### Query Performance

The optimization migration adds:
- **20+ indexes** for fast filtering and sorting
- **Trigram indexes** for fuzzy search (symbol, company name)
- **Materialized views** for complex aggregations
- **Helper functions** for common operations

Expected response times:
- List endpoints: < 100ms
- Detail endpoints: < 50ms
- Analytics: < 500ms
- Search: < 200ms

## Production Deployment

### Environment Variables

Create a `.env.production` file:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Optional
REDIS_URL=redis://localhost:6379
ENVIRONMENT=production
LOG_LEVEL=info
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t dividend-api .
docker run -p 8000:8000 --env-file .env.production dividend-api
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

```bash
# Start services
docker-compose up -d
```

### AWS ECS / GCP Cloud Run

```bash
# Build and push image
docker build -t dividend-api:latest .
docker tag dividend-api:latest your-registry/dividend-api:latest
docker push your-registry/dividend-api:latest

# Deploy to ECS or Cloud Run
# (Follow platform-specific instructions)
```

## Monitoring

### Health Check

```bash
# Check API health
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": 1699876800
}
```

### Logs

```bash
# View API logs
tail -f /var/log/dividend-api.log

# Or with Docker
docker logs -f dividend-api
```

### Metrics

Track these metrics:
- Request rate (requests/second)
- Response time (p50, p95, p99)
- Error rate
- Database connection pool usage
- Cache hit rate

## Troubleshooting

### API Won't Start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check database connectivity
python -c "from supabase_helpers import get_supabase_client; get_supabase_client()"

# Verify .env file exists
cat .env
```

### Slow Queries

```bash
# Check if materialized views are refreshed
psql $DATABASE_URL -c "SELECT * FROM pg_stat_user_tables WHERE relname LIKE 'mart_%';"

# Manually refresh views
psql $DATABASE_URL -c "SELECT refresh_api_materialized_views();"

# Check index usage
psql $DATABASE_URL -c "SELECT * FROM pg_stat_user_indexes WHERE schemaname = 'public';"
```

### Import Errors

```bash
# Ensure you're in the project root
cd /Users/toan/dev/high-yield-dividend-analysis

# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r api/requirements.txt
```

## API Documentation Site

The API includes built-in interactive documentation:

- **Swagger UI**: http://localhost:8000/v1/docs
  - Interactive API explorer
  - Try endpoints directly in browser
  - See request/response schemas

- **ReDoc**: http://localhost:8000/v1/redoc
  - Clean, readable documentation
  - Better for reference
  - Print-friendly

## Next Steps

1. **Authentication**: Add API key authentication (see API_ARCHITECTURE.md)
2. **Rate Limiting**: Implement Redis-based rate limiting
3. **Caching**: Add Redis caching layer
4. **Documentation Site**: Build custom Stripe-style docs frontend
5. **Monitoring**: Set up Prometheus + Grafana
6. **CI/CD**: Automate deployments with GitHub Actions

## Support

For issues or questions:
1. Check the architecture doc: `docs/API_ARCHITECTURE.md`
2. Review interactive API docs: http://localhost:8000/v1/docs
3. Check logs for errors
4. Verify database migrations are applied

---

*Last Updated: 2025-11-12*
