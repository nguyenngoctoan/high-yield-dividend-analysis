# Scripts Directory

This directory contains all operational scripts for the dividend tracker system.

## Daily Automation

### Core Scripts (Run Automatically)
- **`backup_database.sh`** - Daily database backup (runs at ~10:30 PM)
  - See [README_BACKUP.md](README_BACKUP.md) for details
- **`run_metrics_calculation.sh`** - Hourly metrics calculation (runs every hour via cron)
- **`fetch_hourly_prices.py`** - Fetch hourly price data (runs 4 AM - 8 PM weekdays)

### Setup Scripts
- **`setup_hourly_cron.sh`** - Set up hourly price fetching cron job
- **`setup_hourly_metrics_cron.sh`** - Set up metrics calculation cron job
- **`install_dependencies.sh`** - Install system dependencies

## Data Processing Scripts

### Stock Splits
- **`fetch_stock_splits.py`** - Fetch and process stock splits from FMP API

### Dividends
- **`repopulate_all_dividends.py`** - Repopulate dividend data for all symbols

### ETF & Stock Metadata
- **`populate_etf_metadata.sql`** - Populate ETF metadata from API
- **`populate_all_etf_metadata.sql`** - Bulk ETF metadata population
- **`classify_all_etfs.sql`** - Classify ETFs by type and strategy

### Cleanup & Maintenance
- **`cleanup_duplicates.py`** - Remove duplicate records
- **`cleanup_old_hourly_data.py`** - Clean up old hourly price data
- **`cleanup_international_sql.sh`** - Clean up international symbols
- **`cleanup_all_international_symbols.py`** - Remove all international symbols

## Portfolio & Analysis

- **`calculate_stock_metrics.py`** - Calculate portfolio metrics
- **`portfolio_performance_calculator.py`** - Portfolio performance analysis
- **`run_all_projections.py`** - Run dividend projections

## Specialized Scripts

- **`scrape_yieldmax.py`** - Scrape YieldMax ETF data

## Development & Debug

### Debug Scripts (`debug/`)
Testing and debugging utilities:
- `debug_ttm_issue.py` - Debug TTM calculation issues
- `debug_ymag_frequency.py` - Debug dividend frequency for YMAG
- `verify_weekly_ttm.py` - Verify weekly TTM calculations
- `verify_annualization.py` - Verify dividend annualization
- `test_dividend_upsert.py` - Test dividend upsert logic

### Archived Scripts (`archive/`)
Old/deprecated scripts kept for reference:
- `daily_update.sh` - Old daily update script (replaced by daily_update_v2.sh)
- `fix_tsyy_prices.py` - One-off price fix
- `fix_yahoo_prices.py` - One-off Yahoo price fix
- `update_feat_fivy_prices.py` - One-off FIVY price update
- `run_all_scripts.py` - Old script runner

## Active Cron Jobs

```bash
# Hourly price fetching (weekdays 4 AM - 8 PM)
0 4-20 * * 1-5  fetch_hourly_prices.py

# Metrics calculation (every hour)
5 * * * *  run_metrics_calculation.sh

# Daily update (10 PM every night)
0 22 * * *  daily_update_v2.sh
```

View current cron jobs: `crontab -l`
