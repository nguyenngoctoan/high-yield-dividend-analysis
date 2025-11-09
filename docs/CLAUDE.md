# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a high-yield dividend stock analysis and portfolio management system that fetches financial data, manages stock databases, and calculates portfolio performance. The system uses Supabase as the database backend and integrates with multiple financial data APIs (FMP, Yahoo Finance, Alpha Vantage).

**Status**: ✅ **Fully refactored and production-ready** (October 2025)

## Core Architecture

### Modular Library Structure

The codebase has been completely refactored from a monolithic 3,821-line script into a clean modular architecture:

**Library Modules** (`lib/`):
- **Core** (`lib/core/`): Configuration, rate limiting, data models
- **Data Sources** (`lib/data_sources/`): API clients (FMP, Yahoo, Alpha Vantage)
- **Discovery** (`lib/discovery/`): Symbol discovery and validation
- **Processors** (`lib/processors/`): Price, dividend, company data, ETF holdings, and ETF classification

**Total**: 16 focused modules, 4,200+ lines of clean, reusable code

### Database Layer
- **Supabase**: Local container from ai-dividend-tracker project (port 3004)
- **Key Tables**: `stocks`, `excluded_symbols`, `stock_prices`, `stock_prices_hourly`, `dividend_history`, `dividend_calendar`, `stock_splits`
- **Authentication**: Uses both anonymous key and service role key for different operations
- **Admin Operations**: Deletions and high-privilege operations use service role key
- **Helper Module**: `supabase_helpers.py` - Provides all database operations

### Data Pipeline Architecture

The system uses a modular pipeline with hybrid API fallback:

1. **Symbol Discovery** (`lib/discovery/symbol_discovery.py`)
   - Multi-source discovery (FMP, Alpha Vantage)
   - Automatic deduplication
   - ETF and dividend stock screening

2. **Symbol Validation** (`lib/discovery/symbol_validator.py`)
   - Recent price activity check (7 days)
   - Dividend history validation (1 year)
   - Exclusion reason tracking

3. **Data Processing** (`lib/processors/`)
   - **Prices**: Hybrid fetching (FMP → Yahoo → Alpha Vantage)
   - **Dividends**: Historical + future calendar
   - **Company Info**: Stock profiles + ETF metadata
   - **ETF Holdings**: Portfolio composition from FMP
   - **ETF Classification**: Automatic strategy identification

4. **Rate Limiting** (`lib/core/rate_limiters.py`)
   - Adaptive rate limiters with automatic backoff
   - FMP: 144 concurrent requests
   - Alpha Vantage: 2 concurrent requests
   - Yahoo Finance: 3 concurrent requests

## Essential Commands

### Main Pipeline (New Modular Architecture)

```bash
# Activate virtual environment (required for all operations)
source venv/bin/activate

# Discovery mode - find new symbols
python update_stock_v2.py --mode discover --limit 100

# Discovery with validation
python update_stock_v2.py --mode discover --validate

# Update all data (prices, dividends, companies)
python update_stock_v2.py --mode update

# Update specific data types
python update_stock_v2.py --mode update --prices-only
python update_stock_v2.py --mode update --dividends-only
python update_stock_v2.py --mode update --companies-only

# Update with date range
python update_stock_v2.py --mode update --from-date 2025-01-01

# Refresh NULL company names
python update_stock_v2.py --mode refresh-companies --limit 1000

# Fetch future dividends
python update_stock_v2.py --mode future-dividends --days-ahead 90

# Update ETF holdings
python update_stock_v2.py --mode update-holdings

# Classify ETFs (investment strategy & related stock)
python update_stock_v2.py --mode classify-etfs

# Get help on all modes
python update_stock_v2.py --help
```

### Supporting Scripts

```bash
# Portfolio performance calculations
python portfolio_performance_calculator.py

# Fetch hourly prices
python fetch_hourly_prices.py

# Fetch stock splits data
python fetch_stock_splits.py

# Cleanup old hourly data
python cleanup_old_hourly_data.py

# Scrape YieldMax ETFs
python scrape_yieldmax.py

# Run all scripts in sequence
python run_all_scripts.py

# Run comprehensive projections
python run_all_projections.py
```

## Project Structure

```
high-yield-dividend-analysis/
├── lib/                          # Modular library (14 modules)
│   ├── core/                     # Core infrastructure
│   │   ├── config.py            # Configuration management
│   │   ├── rate_limiters.py    # API rate limiting
│   │   └── models.py            # Data models
│   ├── data_sources/            # API clients
│   │   ├── base_client.py       # Abstract base
│   │   ├── fmp_client.py        # FMP API
│   │   ├── yahoo_client.py      # Yahoo Finance
│   │   └── alpha_vantage_client.py
│   ├── discovery/               # Symbol discovery & validation
│   │   ├── symbol_discovery.py
│   │   └── symbol_validator.py
│   └── processors/              # Data processing
│       ├── price_processor.py
│       ├── dividend_processor.py
│       └── company_processor.py
│
├── update_stock_v2.py           # Main pipeline (376 lines, 90% reduction!)
├── portfolio_performance_calculator.py
├── fetch_hourly_prices.py
├── fetch_stock_splits.py
├── cleanup_old_hourly_data.py
├── scrape_yieldmax.py
├── run_all_scripts.py
├── run_all_projections.py
├── supabase_helpers.py          # Database operations
├── sector_helpers.py            # Sector management
│
├── docs/                        # All documentation
│   ├── CLAUDE.md               # This file
│   ├── PROJECT_STRUCTURE.md
│   ├── REFACTORING_COMPLETE.md
│   ├── FINAL_SUMMARY.md
│   ├── VERIFICATION_REPORT.md
│   └── [10 more docs]
│
├── archive/                     # Archived old files
│   ├── scripts_v1/             # Original update_stock.py (3,821 lines)
│   ├── old_scripts/            # 7 deprecated scripts
│   ├── old_logs/               # 14 old log files
│   └── old_docs/               # 4 research documents
│
├── database/                    # Database migrations
├── migrations/                  # SQL migrations
└── venv/                        # Virtual environment
```

## Configuration

### Environment Variables (.env)

```bash
# Supabase Configuration
SUPABASE_URL=http://localhost:3004
SUPABASE_KEY=[anonymous_key]
SUPABASE_SERVICE_ROLE_KEY=[service_role_key]

# API Keys
FMP_API_KEY=[your_fmp_api_key]
ALPHA_VANTAGE_API_KEY=[your_alpha_vantage_key]

# Optional
DEBUG_MODE=false
```

### Exchange Filtering

The system filters stocks by allowed exchanges:
```python
["NYSE", "NASDAQ", "AMEX", "TSX", "BATS", "CBOE", "TSE"]
```

### Database Protection Rules

**High-Risk Operations (require confirmation):**
- Database resets or drops
- Clearing ALL data from tables
- Truncating tables
- Operations affecting significant amounts of data

**Safe Operations (no confirmation needed):**
- Reading files and viewing data
- SELECT queries
- INSERT/UPDATE with proper WHERE clauses
- Individual record modifications
- Normal data updates and inserts

## Key Implementation Details

### Modular Architecture Benefits

1. **Reusability**: All modules can be imported and used independently
2. **Testability**: Clear interfaces make unit testing straightforward
3. **Maintainability**: 90% code reduction (3,821 → 376 lines in main script)
4. **Scalability**: Easy to add new data sources or processors

### API Integration

**FMP (Financial Modeling Prep)**:
- Primary data source
- Comprehensive symbol lists
- ETF metadata with AUM
- Dividend calendar
- Rate limit: 144 concurrent requests

**Yahoo Finance** (via yfinance):
- Fallback for price data
- Daily AUM tracking for ETFs
- Rich company metadata
- No API key required
- Rate limit: 3 concurrent requests

**Alpha Vantage**:
- Secondary fallback
- LISTING_STATUS for symbol discovery
- Adjusted close prices
- Rate limit: 2 concurrent requests

### Hybrid Fetching Strategy

All processors use a fallback chain:
```
FMP (primary) → Yahoo Finance (fallback) → Alpha Vantage (final fallback)
```

This ensures maximum data availability even with API key limitations.

### Concurrent Processing

- Uses ThreadPoolExecutor for parallel API calls
- Adaptive rate limiting with automatic backoff on 429 errors
- Batch processing for database operations (1,000 records/batch)
- Statistics tracking for all operations

### Error Handling

- Comprehensive logging with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Graceful degradation on API failures
- Connection testing for Supabase before operations
- Retry logic with exponential backoff

### Data Validation

**Symbol Validation Criteria**:
- Must have recent price data (within 7 days) OR
- Must have dividend history (within last 365 days)

**Price Data**:
- AUM (Assets Under Management) tracked daily for ETFs
- IV (Implied Volatility) support for options analysis
- Hourly prices for intraday analysis

**Dividend Data**:
- Historical dividends
- Future dividend calendar (90 days ahead by default)
- Graceful handling of non-dividend stocks

## Usage Examples

### Quick Start

```bash
# 1. Discover and validate symbols
python update_stock_v2.py --mode discover --validate

# 2. Update all data
python update_stock_v2.py --mode update

# 3. Fetch future dividends
python update_stock_v2.py --mode future-dividends
```

### Using Individual Modules

```python
# Import specific modules
from lib.data_sources.fmp_client import FMPClient
from lib.discovery.symbol_discovery import discover_symbols
from lib.processors.price_processor import PriceProcessor

# Quick price fetch
client = FMPClient()
prices = client.fetch_prices('AAPL', from_date=date(2025, 1, 1))

# Quick symbol discovery
symbols = discover_symbols(limit=100, sources=['fmp'])

# Process prices with hybrid fallback
processor = PriceProcessor()
processor.process_and_store('AAPL', from_date=date(2025, 1, 1))
```

## Development Guidelines

### Adding New Features

1. **New Data Source**: Create client in `lib/data_sources/` inheriting from `BaseClient`
2. **New Processor**: Add processor in `lib/processors/` with hybrid fetching
3. **New Validation**: Extend `SymbolValidator` in `lib/discovery/`
4. **Configuration**: Update `lib/core/config.py` with new settings

### Testing

- Use Python virtual environment: `source venv/bin/activate`
- Test individual modules before integration
- Verify API rate limits are respected
- Check database operations with small datasets first

### Documentation

- Keep `docs/CLAUDE.md` (this file) updated
- Document new modules with docstrings
- Update `docs/PROJECT_STRUCTURE.md` when adding files
- Create feature-specific docs in `docs/` folder

## Migration Notes

### From Original Script

The original `update_stock.py` (3,821 lines) has been replaced by `update_stock_v2.py` (376 lines):

**Old way**:
```bash
python update_stock.py --discover-symbols --validate-discovered
```

**New way**:
```bash
python update_stock_v2.py --mode discover --validate
```

All functionality preserved and enhanced with:
- ✅ 90% code reduction
- ✅ Modular architecture
- ✅ Hybrid API fallback
- ✅ Better error handling
- ✅ Cleaner CLI interface

### Archived Files

Old files are preserved in `archive/` for reference:
- `archive/scripts_v1/update_stock.py` - Original monolithic script
- `archive/old_scripts/` - 7 deprecated scripts
- `archive/old_logs/` - Historical execution logs
- `archive/old_docs/` - Research documents

## Important Notes

- **Always use virtual environment**: `source venv/bin/activate`
- **Rate limiting is automatic**: Managed by rate limiter modules
- **API keys required**: FMP and Alpha Vantage (Yahoo works without key)
- **Database**: Supabase local container must be running (port 3004)
- **Hybrid fallback**: Automatically tries multiple sources on failure
- **Batch operations**: Use configurable batch sizes for efficiency
- **Statistics tracking**: All operations tracked via `ProcessingStats`
- **Logging**: Comprehensive logs with DEBUG/INFO/WARNING/ERROR levels

## Getting Help

### Documentation Files (in `docs/`)

- `REFACTORING_COMPLETE.md` - Complete refactoring overview
- `FINAL_SUMMARY.md` - Final achievement summary
- `VERIFICATION_REPORT.md` - Script verification results
- `PHASE1_COMPLETE.md` - Core modules documentation
- `PHASE2_COMPLETE.md` - Data source clients documentation
- `PHASE3_COMPLETE.md` - Discovery & processors documentation
- `PROJECT_STRUCTURE.md` - Project organization
- `ETF_HOLDINGS_IMPLEMENTATION.md` - ETF holdings feature
- `ETF_CLASSIFICATION.md` - ETF classification system
- `DAILY_AUTOMATION.md` - Daily automation setup
- Feature-specific READMEs (AUM, IV, Stock Splits, etc.)

### Quick Reference

```bash
# Help for main script
python update_stock_v2.py --help

# View module documentation
python -c "from lib.data_sources.fmp_client import FMPClient; help(FMPClient)"

# Check configuration
python -c "from lib.core.config import Config; print(Config.API.FMP_BASE_URL)"
```

## Project Status

**Refactoring**: ✅ Complete (October 2025)
**Testing**: ✅ All tests passing
**Production**: ✅ Ready for use
**Documentation**: ✅ Comprehensive (3,000+ lines)

The codebase is clean, modular, well-tested, and production-ready.
