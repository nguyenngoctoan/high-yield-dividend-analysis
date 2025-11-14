# Divv - High-Yield Dividend Analysis & Portfolio Management System

A comprehensive, production-ready financial data platform with multi-source data collection, intelligent source tracking, and REST API for dividend investors. **Divv API** powers dividend investing apps and spreadsheet integrations.

## 🎯 Overview

This system provides:
- **Data Collection**: Multi-source API integration (FMP, Alpha Vantage Premium, Yahoo Finance)
- **Smart Source Tracking**: Automatic discovery and caching of best data sources
- **Dividend Focus**: Specialized tools for dividend stocks and covered call ETFs
- **REST API**: Production-grade API with authentication and rate limiting
- **Portfolio Analysis**: Performance tracking and distribution projections

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase (local or cloud)
- API Keys: FMP, Alpha Vantage Premium

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd high-yield-dividend-analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Quick Commands

```bash
# Data Collection
python update_stock_v2.py --mode discover --limit 100  # Discover symbols
python update_stock_v2.py --mode update                # Update all data

# Covered Call ETF IV Discovery (Alpha Vantage Premium)
python scripts/discover_iv_for_covered_call_etfs.py --test XYLD
python scripts/discover_iv_for_covered_call_etfs.py     # All covered call ETFs

# Start REST API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Portfolio Analysis
python portfolio_performance_calculator.py
```

## 📚 Core Features

### 1. Data Source Tracking System ⭐

Intelligent system that discovers and tracks which data sources have specific data types for each symbol.

**Key Benefits**:
- 60-80% reduction in API calls after initial discovery
- <1ms lookup time with in-memory cache
- Automatic fallback if preferred source fails

```python
from lib.processors.aum_discovery_processor import discover_aum

# Automatically finds AUM from FMP or Yahoo, remembers which source works
result = discover_aum('SPY')
print(f"AUM: ${result['aum']:,.0f} from {result['source']}")
```

**Documentation**: `docs/DATA_SOURCE_TRACKING.md`

### 2. Covered Call ETF IV Analysis 📊

**Alpha Vantage Premium Required**

Implied Volatility (IV) is THE key indicator for covered call ETF distributions. Higher IV = higher option premiums = higher distributions to shareholders.

```bash
# Test with a single ETF
python scripts/discover_iv_for_covered_call_etfs.py --test XYLD

# Discover for all covered call ETFs
python scripts/discover_iv_for_covered_call_etfs.py
```

```sql
-- Query IV data
SELECT symbol, name, iv, close, date
FROM raw_stocks s
JOIN raw_stock_prices p ON s.symbol = p.symbol
WHERE investment_strategy LIKE '%covered call%'
  AND iv IS NOT NULL
ORDER BY iv DESC;
```

**Documentation**: `docs/COVERED_CALL_ETF_IV_GUIDE.md`

### 3. Multi-Source Data Integration

**Data Sources**:
- **FMP (Primary)**: Comprehensive fundamental data, AUM, ETF info
- **Alpha Vantage Premium**: Options data with IV and Greeks, historical options
- **Yahoo Finance (Fallback)**: Price data, AUM, dividends

**Data Types Tracked**:
| Data Type | FMP | Alpha Vantage | Yahoo |
|-----------|-----|---------------|-------|
| AUM | ✅ | ❌ | ✅ |
| Dividends | ✅ | ✅ | ✅ |
| Volume | ✅ | ✅ | ✅ |
| IV (Options) | ❌ | ✅ Premium | ⚠️ Unreliable |

### 4. REST API

Production-ready REST API with authentication, rate limiting, and 23+ endpoints.

```bash
# Start API
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/v1/stocks?limit=5
curl http://localhost:8000/v1/search?q=apple
```

**API Features**:
- API key authentication (3 tiers: Free, Pro, Enterprise)
- Token bucket rate limiting
- Sub-100ms response times
- 24,000+ stocks/ETFs covered

**Documentation**: `docs/API_ARCHITECTURE.md`

## 📁 Project Structure

```
high-yield-dividend-analysis/
├── lib/                          # Core library modules
│   ├── core/                     # Configuration, rate limiters, models
│   ├── data_sources/             # API clients (FMP, AV, Yahoo)
│   ├── processors/               # Data processors (prices, dividends, IV, AUM)
│   └── utils/                    # Data source tracker
│
├── api/                          # REST API
│   ├── main.py                   # FastAPI application
│   ├── routers/                  # API endpoints
│   └── models/                   # Pydantic schemas
│
├── scripts/                      # Utility scripts
│   ├── discover_iv_for_covered_call_etfs.py
│   └── setup_data_source_tracking.py
│
├── migrations/                   # Database migrations
│   ├── create_data_source_tracking.sql
│   └── create_api_keys.sql
│
├── docs/                         # Documentation
│   ├── DATA_SOURCE_TRACKING.md
│   ├── COVERED_CALL_ETF_IV_GUIDE.md
│   ├── IMPLIED_VOLATILITY_DATA_SOURCES.md
│   └── API_ARCHITECTURE.md
│
├── update_stock_v2.py           # Main data collection script
├── portfolio_performance_calculator.py
└── README.md                    # This file
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Supabase
SUPABASE_URL=http://localhost:3004
SUPABASE_KEY=<your_anon_key>
SUPABASE_SERVICE_KEY=<your_service_role_key>

# API Keys
FMP_API_KEY=<your_fmp_key>
ALPHA_VANTAGE_API_KEY=<your_alpha_vantage_premium_key>

# Optional
DEBUG_MODE=false
```

### Allowed Exchanges

```python
# Configured in lib/core/config.py
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "BATS", "BTS", "BYX", "BZX", "CBOE",
    "EDGA", "EDGX", "PCX", "NGM",
    "OTCM", "OTCX",  # OTC markets
    "TSX", "TSXV", "CSE", "TSE"  # Canadian exchanges
]
```

## 📊 Database Schema

### Core Tables

- **raw_stocks**: Stock/ETF master list with company info
- **raw_stock_prices**: Daily OHLCV with AUM and IV
- **raw_dividends**: Historical dividend payments
- **raw_future_dividends**: Upcoming dividend calendar
- **raw_data_source_tracking**: Source availability tracking
- **api_keys**: API authentication and rate limiting

### Key Features

- **AUM Tracking**: Daily AUM for ETFs
- **IV Support**: Implied volatility for options analysis
- **Source Tracking**: Records which sources have which data types

## 🎯 Common Use Cases

### 1. Discover and Track Covered Call ETF Distributions

```bash
# Setup data source tracking
python scripts/setup_data_source_tracking.py

# Discover IV for covered call ETFs (requires Alpha Vantage Premium)
python scripts/discover_iv_for_covered_call_etfs.py

# Query results
psql -h your-host -d your-db -c "
  SELECT symbol, name, iv, close,
         (close * iv * SQRT(1.0/12)) as estimated_monthly_dist
  FROM raw_stocks s
  JOIN raw_stock_prices p ON s.symbol = p.symbol
  WHERE investment_strategy LIKE '%covered call%'
    AND iv IS NOT NULL
  ORDER BY estimated_monthly_dist DESC;
"
```

### 2. Build a High-Yield Dividend Portfolio

```bash
# Discover dividend stocks
python update_stock_v2.py --mode discover --validate

# Update dividend data
python update_stock_v2.py --mode update --dividends-only

# Calculate portfolio performance
python portfolio_performance_calculator.py
```

### 3. Track ETF Holdings and Composition

```bash
# Update ETF holdings
python update_stock_v2.py --mode update-holdings

# Classify ETFs by strategy
python update_stock_v2.py --mode classify-etfs
```

### 4. Build a Dividend API

```bash
# Start API server
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# Create API key (see docs/API_ARCHITECTURE.md)
# Use API endpoints for integration
```

## 📖 Documentation

### Core Guides

- **[Data Source Tracking System](docs/DATA_SOURCE_TRACKING.md)** - Complete guide to intelligent source discovery
- **[Covered Call ETF IV Guide](docs/COVERED_CALL_ETF_IV_GUIDE.md)** - Using IV for distribution analysis
- **[IV Data Sources](docs/IMPLIED_VOLATILITY_DATA_SOURCES.md)** - Where to get IV data
- **[API Architecture](docs/API_ARCHITECTURE.md)** - REST API documentation

### Quick References

- **[Data Source Tracking Quick Start](docs/QUICK_START_SOURCE_TRACKING.md)** - 1-minute setup
- **[IV Quick Reference](docs/IV_QUICK_REFERENCE.md)** - IV analysis cheat sheet

### Implementation Details

- **[Implementation Summary](IMPLEMENTATION_SUMMARY.md)** - Data source tracking implementation
- **[IV Implementation Summary](docs/IV_IMPLEMENTATION_SUMMARY.md)** - IV system implementation
- **[CLAUDE.md](docs/CLAUDE.md)** - Development guidelines for AI assistants

## 🔬 Advanced Features

### Source Tracking Statistics

```python
from lib.utils.data_source_tracker import get_tracker, DataType

tracker = get_tracker()

# View statistics for AUM data
stats = tracker.get_statistics(DataType.AUM)
print(f"AUM sources tracked for {stats['count']} symbols")

# Get preferred source for a symbol
preferred = tracker.get_preferred_source('SPY', DataType.AUM)
print(f"Best source for SPY AUM: {preferred.value}")
```

### Batch IV Discovery

```python
from lib.processors.iv_discovery_processor import IVDiscoveryProcessor
from lib.utils.data_source_tracker import DataType

processor = IVDiscoveryProcessor()

# Discover IV for multiple symbols
results = processor.process_batch(
    symbols=['XYLD', 'QYLD', 'RYLD', 'JEPI', 'JEPQ'],
    force_rediscover=False,
    update_prices=True
)

# Get statistics
stats = processor.get_statistics()
print(f"Found IV for {stats['successful']} ETFs")
```

### Custom Data Source Integration

```python
from lib.data_sources.base_client import DataSourceClient

class MyCustomClient(DataSourceClient):
    def __init__(self):
        super().__init__(name="MyAPI", rate_limiter=my_limiter)

    def fetch_prices(self, symbol, from_date=None):
        # Your implementation
        pass
```

## 🚨 Important Notes

### Alpha Vantage Premium

- **IV data requires Premium subscription** (600-1200 req/min)
- Free tier does NOT include options/IV data
- See `docs/IMPLIED_VOLATILITY_DATA_SOURCES.md` for alternatives

### Rate Limits

- **FMP Professional**: 750 requests/min (18 concurrent)
- **Alpha Vantage Premium**: 600-1200 requests/min (6 concurrent)
- **Yahoo Finance**: Unlimited (9 concurrent, rate-limited internally)

### Database

- Uses Supabase (PostgreSQL-compatible)
- Local or cloud deployment supported
- Migrations in `migrations/` folder

## 🤝 Contributing

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black lib/ api/ scripts/
```

### Adding New Features

1. Create module in appropriate `lib/` subdirectory
2. Add tests in `tests/`
3. Update documentation in `docs/`
4. Follow existing patterns for consistency

## 📝 License

[Your License Here]

## 🙋 Support

### Quick Help

```bash
# Main script help
python update_stock_v2.py --help

# IV discovery help
python scripts/discover_iv_for_covered_call_etfs.py --help
```

### Documentation

- Check `docs/` folder for comprehensive guides
- See `CLAUDE.md` for development guidelines
- Review quick reference cards for common tasks

### Issues

For bugs or feature requests, please open an issue with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs

---

**Status**: ✅ Production Ready
**Last Updated**: 2025-11-13
**Version**: 2.0 (Modular Architecture with Source Tracking)
