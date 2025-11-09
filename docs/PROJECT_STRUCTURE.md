# Project Structure

This document describes the organization of the high-yield dividend analysis project.

## 📁 Directory Structure

```
high-yield-dividend-analysis/
├── 📄 Core Scripts (Production)
│   ├── update_stock.py                      - Main stock data update pipeline
│   ├── fetch_hourly_prices.py               - Hourly price data collection
│   ├── scrape_yieldmax.py                   - Dynamic YieldMax dividend scraper
│   ├── scrape_dividend_calendar_requests.py - YieldMax scraping core functions
│   ├── cleanup_old_hourly_data.py           - Hourly data maintenance
│   ├── portfolio_performance_calculator.py  - Portfolio analytics
│   ├── run_all_scripts.py                   - Orchestration script
│   └── run_all_projections.py               - Projection calculations
│
├── 📚 Helper Modules
│   ├── supabase_helpers.py                  - Database operations
│   └── sector_helpers.py                    - Sector data utilities
│
├── 🔧 Shell Scripts
│   ├── daily_update.sh                      - Daily data update cron job
│   ├── setup_hourly_cron.sh                 - Hourly price tracking setup
│   └── install_dependencies.sh              - Dependency installation
│
├── 🗄️ database/
│   ├── create_tables.py                     - Table creation script
│   ├── create_hourly_table.py               - Hourly prices table setup
│   ├── create_stocks_excluded_table.sql     - Exclusion table schema
│   ├── disable_rls.sql                      - Disable Row Level Security
│   └── grant_permissions.sql                - Permission grants
│
├── 📊 logs/
│   ├── daily_update.log                     - Daily update logs
│   └── hourly_prices.log                    - Hourly price fetch logs
│
├── 📦 archive/
│   ├── dividend_scrapers/
│   │   ├── README.md
│   │   └── scrape_dividend_calendar_supabase.py  - Old Selenium version
│   │
│   ├── migration_scripts/
│   │   ├── analyze_column_usage.py
│   │   ├── backfill_exchange_from_api.py
│   │   ├── backfill_exchange_from_fmp.py
│   │   ├── backfill_exchange_metadata.py
│   │   ├── cleanup_international_symbols.py
│   │   ├── cleanup_null_international_symbols.py
│   │   ├── investigate_null_exchanges.py
│   │   ├── populate_sector_data.py
│   │   └── enhanced_discovery.py
│   │
│   ├── logs/
│   │   ├── discovery_enhanced_run.log
│   │   ├── final_test_discovery.log
│   │   ├── test_discovery_fixed.log
│   │   ├── hourly_test_run.log
│   │   ├── hourly_final_test.log
│   │   ├── yieldmax_scrape_test.log
│   │   ├── null_exchange_investigation.log
│   │   ├── sector_population.log
│   │   ├── exchange_backfill.log
│   │   └── hybrid_update.log (51MB)
│   │
│   └── docs/
│       ├── DISCOVERY_IMPROVEMENT_PLAN.md
│       └── ENHANCED_DISCOVERY_RESULTS.md
│
├── 📦 archive_postgresql/
│   └── (Pre-Supabase migration scripts)
│
├── 📦 migrations/
│   └── create_stock_prices_hourly.sql
│
└── 📄 Documentation
    ├── CLAUDE.md                            - AI assistant instructions
    ├── PROJECT_STRUCTURE.md                 - This file
    └── README.md                            - Project overview
```

## 🚀 Main Workflows

### Daily Stock Updates
```bash
./daily_update.sh
# OR
python update_stock.py --mode discover
```

### Hourly Price Tracking
```bash
# Setup cron job (runs 4 AM - 8 PM ET, Mon-Fri)
./setup_hourly_cron.sh

# Manual run
python fetch_hourly_prices.py
```

### YieldMax Dividend Scraping
```bash
# Recent dividends (last 7 days)
python scrape_yieldmax.py --recent-only

# Full scan (last 90 days)
python scrape_yieldmax.py
```

### Portfolio Performance
```bash
python portfolio_performance_calculator.py
```

## 📊 Database

**Backend**: Supabase (local container on port 3004)

**Key Tables**:
- `stocks` - Stock metadata
- `stock_prices` - Daily prices
- `stock_prices_hourly` - Intraday hourly prices
- `dividend_payments` - Dividend data
- `dividend_history` - Historical dividends
- `excluded_symbols` - Symbols to skip

## 🔧 Configuration

**Environment Variables** (`.env`):
```
SUPABASE_URL=http://localhost:3004
SUPABASE_KEY=[anonymous_key]
FMP_API_KEY=[financial_modeling_prep_key]
```

## 📝 Notes

- **Active Development**: Core scripts in root directory
- **Archived**: One-time migration scripts in `archive/migration_scripts/`
- **Database Setup**: SQL and setup scripts in `database/`
- **Logs**: Active logs in `logs/`, historical logs in `archive/logs/`

## 🗑️ Cleanup Summary

**Archived**:
- 51MB of old log files
- 9 one-time migration/investigation scripts
- 2 planning documentation files
- 1 deprecated Selenium scraper

**Organized**:
- Database scripts → `database/`
- Active logs → `logs/`
- Migration scripts → `archive/migration_scripts/`
- Test logs → `archive/logs/`

**Result**: Clean project root with only production scripts and active configurations.
