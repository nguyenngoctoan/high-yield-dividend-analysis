# Dividend API

Production-grade RESTful API for dividend investors.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Deploy database optimizations
psql $DATABASE_URL < ../migrations/create_api_optimizations.sql

# Start server
./start_api.sh
```

## Access

- **API Base**: http://localhost:8000/v1
- **Interactive Docs**: http://localhost:8000/v1/docs
- **ReDoc**: http://localhost:8000/v1/redoc

## Endpoints

### Stocks
- `GET /v1/stocks` - List stocks with filtering
- `GET /v1/stocks/{symbol}` - Get stock details

### Dividends
- `GET /v1/dividends/calendar` - Upcoming dividend events
- `GET /v1/dividends/history` - Historical dividends
- `GET /v1/stocks/{symbol}/dividends` - Complete dividend summary

### Screeners
- `GET /v1/screeners/high-yield` - High-yield stocks
- `GET /v1/screeners/monthly-payers` - Monthly dividend payers

### ETFs
- `GET /v1/etfs/{symbol}/holdings` - ETF holdings
- `GET /v1/etfs/classify/{symbol}` - ETF strategy classification

### Prices
- `GET /v1/prices/{symbol}` - Price history
- `GET /v1/prices/{symbol}/latest` - Latest price

### Analytics
- `POST /v1/analytics/portfolio` - Portfolio analysis

### Search
- `GET /v1/search` - Search stocks

## Example

```bash
# Get high-yield stocks
curl "http://localhost:8000/v1/screeners/high-yield?min_yield=5.0"

# Get stock with dividends
curl "http://localhost:8000/v1/stocks/AAPL?expand=dividends"

# Search
curl "http://localhost:8000/v1/search?q=technology"
```

## Documentation

See `../docs/` for complete documentation:
- **API_ARCHITECTURE.md** - Complete API design
- **API_DEPLOYMENT_GUIDE.md** - Deployment guide
- **API_IMPLEMENTATION_SUMMARY.md** - Implementation details

## Structure

```
api/
├── main.py              # FastAPI application
├── routers/             # Endpoint routers
│   ├── stocks.py
│   ├── dividends.py
│   ├── screeners.py
│   ├── etfs.py
│   ├── prices.py
│   ├── analytics.py
│   └── search.py
├── models/
│   └── schemas.py       # Pydantic models
├── requirements.txt
└── start_api.sh
```

## Development

```bash
# Run with hot reload
uvicorn api.main:app --reload

# Run on custom port
uvicorn api.main:app --port 8080

# Run in production mode
uvicorn api.main:app --host 0.0.0.0 --workers 4
```

## Performance

- Materialized views for fast queries
- 20+ indexes for optimization
- Expected response times < 100ms

## Next Steps

1. Test endpoints via Swagger UI
2. Add authentication (API keys)
3. Add rate limiting
4. Build documentation frontend
5. Deploy to production
