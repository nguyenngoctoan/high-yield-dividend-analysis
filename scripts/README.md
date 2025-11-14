# Scripts Directory

This directory contains all operational scripts for the dividend tracker system, organized by purpose.

## Directory Structure

```
scripts/
├── automation/          # Automated tasks and cron setup
├── data-collection/     # Data fetching and discovery
├── cleanup/            # Database cleanup and maintenance
├── scrapers/           # Web scrapers for dividend data
├── portfolio/          # Portfolio analysis and calculations
├── migrations/         # Database migrations and setup
├── testing/            # Test scripts
├── debug/              # Debug and verification utilities
└── archive/            # Deprecated scripts
```

## Automation Scripts (`automation/`)

Daily and hourly automation tasks:

- **`backup_database.sh`** - Daily database backup (runs at ~10:30 PM)
- **`run_metrics_calculation.sh`** - Hourly metrics calculation
- **`setup_hourly_cron.sh`** - Set up hourly price fetching cron job
- **`setup_hourly_metrics_cron.sh`** - Set up metrics calculation cron job
- **`install_dependencies.sh`** - Install system dependencies
- **`update_parallel_by_exchange.sh`** - Parallel updates by exchange

## Data Collection (`data-collection/`)

Scripts for fetching and discovering financial data:

- **`fetch_hourly_prices.py`** - Fetch hourly price data (runs 4 AM - 8 PM weekdays)
- **`fetch_stock_splits.py`** - Fetch and process stock splits from FMP API
- **`repopulate_all_dividends.py`** - Repopulate dividend data for all symbols
- **`discover_iv_for_covered_call_etfs.py`** - Discover implied volatility data for covered call ETFs

## Cleanup & Maintenance (`cleanup/`)

Database cleanup and maintenance scripts:

- **`cleanup_duplicates.py`** - Remove duplicate records
- **`cleanup_old_hourly_data.py`** - Clean up old hourly price data
- **`cleanup_international_sql.sh`** - Clean up international symbols (SQL)
- **`cleanup_all_international_symbols.py`** - Remove all international symbols
- **`cleanup_international_batch.py`** - Batch cleanup of international symbols

## Web Scrapers (`scrapers/`)

Scraping tools for dividend data from various sources:

- **`scrape_yieldmax.py`** - Scrape YieldMax ETF data
- **`scrape_cboe_dividends.py`** - Scrape CBOE dividend data
- **`scrape_nasdaq_dividends.py`** - Scrape NASDAQ dividend data
- **`scrape_nyse_dividends.py`** - Scrape NYSE dividend data
- **`scrape_snowball_dividends.py`** - Scrape Snowball Analytics dividend data

## Portfolio & Analysis (`portfolio/`)

Portfolio performance and analysis tools:

- **`portfolio_performance_calculator.py`** - Portfolio performance analysis
- **`run_all_projections.py`** - Run dividend projections
- **`calculate_stock_metrics.py`** - Calculate portfolio metrics

## Database Migrations (`migrations/`)

Database setup and migration scripts:

- **`create_api_keys_table.py`** - Create API keys table
- **`run_api_keys_migration.py`** - Run API keys migration
- **`setup_data_source_tracking.py`** - Set up data source tracking system

## Testing (`testing/`)

Test and validation scripts:

- **`test_optimizations.py`** - Test optimization improvements
- **`test_symbol_filtering.py`** - Test symbol filtering logic
- **`test_yahoo_rate_limiting.py`** - Test Yahoo Finance rate limiting

## Debug Utilities (`debug/`)

Testing and debugging utilities:

- **`debug_ttm_issue.py`** - Debug TTM calculation issues
- **`debug_ymag_frequency.py`** - Debug dividend frequency for YMAG
- **`verify_weekly_ttm.py`** - Verify weekly TTM calculations
- **`verify_annualization.py`** - Verify dividend annualization
- **`test_dividend_upsert.py`** - Test dividend upsert logic

## Archived Scripts (`archive/`)

Old/deprecated scripts kept for reference:

- **`daily_update.sh`** - Old daily update script (replaced)
- **`fix_tsyy_prices.py`** - One-off price fix
- **`fix_yahoo_prices.py`** - One-off Yahoo price fix
- **`update_feat_fivy_prices.py`** - One-off FIVY price update
- **`run_all_scripts.py`** - Old script runner

## Main Executables (in `bin/`)

Main automation scripts are located in the `bin/` directory:

- **`daily_update_v3_parallel.sh`** - Main daily update script (parallel execution)
- **`daily_update_v2.sh`** - Daily update script (v2)
- **`monitor_update.sh`** - Monitor daily update progress
- **`setup_daily_cron.sh`** - Set up daily cron job
- **`test_daily_update.sh`** - Test daily update process

## Active Cron Jobs

```bash
# Hourly price fetching (weekdays 4 AM - 8 PM)
0 4-20 * * 1-5  cd /path/to/project && python3 scripts/data-collection/fetch_hourly_prices.py

# Metrics calculation (every hour)
5 * * * *  cd /path/to/project && bash scripts/automation/run_metrics_calculation.sh

# Daily update (10 PM every night)
0 22 * * *  cd /path/to/project && bash bin/daily_update_v3_parallel.sh
```

View current cron jobs: `crontab -l`

## Usage Examples

```bash
# Data Collection
python3 scripts/data-collection/fetch_hourly_prices.py
python3 scripts/data-collection/fetch_stock_splits.py

# Portfolio Analysis
python3 scripts/portfolio/portfolio_performance_calculator.py
python3 scripts/portfolio/run_all_projections.py

# Cleanup
python3 scripts/cleanup/cleanup_old_hourly_data.py
python3 scripts/cleanup/cleanup_duplicates.py

# Testing
python3 scripts/testing/test_optimizations.py
python3 scripts/testing/test_symbol_filtering.py

# Run Daily Update
bash bin/daily_update_v3_parallel.sh

# Monitor Progress
bash bin/monitor_update.sh
```

## Notes

- All scripts should be run from the project root directory
- Activate virtual environment before running Python scripts: `source venv/bin/activate`
- Check script documentation for specific requirements and options
- Most scripts support `--help` flag for usage information
