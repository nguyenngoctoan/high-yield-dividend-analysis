# File-by-File Update Checklist for Table Renaming

## SQL Files (15 files)

### Migrations (9 files) - CRITICAL
- [ ] `migrations/001_add_etf_fields.sql` (2 refs: stocks, stock_prices)
- [ ] `migrations/002_add_adj_close.sql` (2 refs: stock_prices, stock_prices_hourly)
- [ ] `migrations/003_add_dividend_unique_constraint.sql` (1 ref: dividend_history)
- [ ] `migrations/004_add_related_stock_and_investment_strategy.sql` (1 ref: stocks)
- [ ] `migrations/005_add_holdings_column.sql` (1 ref: stocks)
- [ ] `migrations/006_create_holdings_history.sql` (1 ref: holdings_history)
- [ ] `migrations/create_stock_prices_hourly.sql` (2 refs: stock_prices_hourly, stocks)
- [ ] `migrations/add_iv_column.sql` (1 ref: stock_prices)
- [ ] `migrations/create_stock_splits.sql` (2 refs: stock_splits, stocks)

### Database Setup (4 files) - HIGH
- [ ] `database/create_tables.py` (4 refs: stocks, excluded_symbols, price_history, dividend_history)
- [ ] `database/create_stocks_excluded_table.sql` (1 ref: stocks_excluded)
- [ ] `database/disable_rls.sql` (1 ref: stocks_excluded)
- [ ] `database/grant_permissions.sql` (1 ref: stocks_excluded)

### Metadata Scripts (2 files) - MEDIUM
- [ ] `scripts/populate_etf_metadata.sql` (1 ref: stocks)
- [ ] `scripts/populate_all_etf_metadata.sql` (1 ref: stocks)

## Python Core Helper Files (1 file)

### Critical Helper
- [ ] `supabase_helpers.py` (40+ refs: stocks, stock_prices, stock_prices_hourly, dividend_history, stocks_excluded, excluded_symbols)
  - Lines 52, 71: `.table('stocks')`
  - Lines 417-432: Upsert logic with table-specific conflict handling
  - Function `get_excluded_symbols()`: line 596
  - Function `get_existing_symbols()`: line 605

## Python Processor Files (7 files)

### Critical Processor
- [ ] `lib/processors/incremental_processor.py` (2 direct refs: stock_prices line 37, dividend_history line 69)

### High Priority Processors
- [ ] `lib/processors/price_processor.py` (indirect via supabase_batch_upsert)
- [ ] `lib/processors/dividend_processor.py` (indirect via supabase_batch_upsert)
- [ ] `lib/processors/company_processor.py` (stocks refs)
- [ ] `lib/processors/etf_classifier.py` (stocks refs)
- [ ] `lib/processors/holdings_processor.py` (holdings_history refs)

## Python Data Source Files (3 files)

- [ ] `lib/data_sources/fmp_client.py` (stocks, stock_prices, dividend_history - indirect)
- [ ] `lib/data_sources/yahoo_client.py` (stock_prices - indirect)
- [ ] `lib/data_sources/alpha_vantage_client.py` (indirect refs)

## Python Utility Scripts (20+ files)

### High Priority Scripts
- [ ] `scripts/cleanup_all_international_symbols.py` (6 tables: stocks, stock_prices, stock_prices_hourly, dividend_history, stock_splits, holdings_history)
- [ ] `scripts/calculate_stock_metrics.py` (3 tables: stocks, stock_prices, dividend_history)
- [ ] `scripts/fetch_stock_splits.py` (2 tables: stock_splits, stocks)
- [ ] `scripts/fetch_hourly_prices.py` (1 table: stock_prices_hourly)
- [ ] `scripts/cleanup_old_hourly_data.py` (1 table: stock_prices_hourly)
- [ ] `scripts/cleanup_duplicates.py` (1 table: stock_prices)
- [ ] `scripts/repopulate_all_dividends.py` (1 table: dividend_history)
- [ ] `scripts/fix_yahoo_prices.py` (1 table: stocks)
- [ ] `scripts/fix_tsyy_prices.py` (1 table: stock_prices)
- [ ] `scripts/run_all_projections.py` (stocks ref, potentially)
- [ ] `scripts/scrape_yieldmax.py` (dividend_calendar ref)

### Medium Priority Scripts
- [ ] `update_stock_v2.py` (multiple table refs)
- [ ] `sector_helpers.py` (stocks refs)
- [ ] `database/create_hourly_table.py` (stock_prices_hourly refs)
- [ ] `lib/discovery/symbol_discovery.py` (stocks, excluded_symbols refs)

## Python Test & Debug Files (10+ files)

### Debug Scripts (Lower Priority)
- [ ] `debug_ttm_issue.py` (stocks, stock_prices, dividend_history)
- [ ] `debug_ymag_frequency.py` (stocks, dividend_history)
- [ ] `verify_annualization.py` (stocks, dividend_history)
- [ ] `verify_weekly_ttm.py` (dividend_history)
- [ ] `test_dividend_upsert.py` (dividend_history)

### Test Archive Files
- [ ] `test_archive/test_source_completion_logic.py`
- [ ] `test_archive/test_incremental_logic.py` (stock_prices ref)
- [ ] `test_archive/test_enhanced_historical.py`

## Python Archive Files (20+ files - LOWER PRIORITY)

### Archive PostgreSQL Scripts
- [ ] `archive_postgresql/update_stock.py` (stocks, stock_prices, dividend_history)
- [ ] `archive_postgresql/fetch_prices_dividends.py` (multiple tables)

### Archive Migration Scripts
- [ ] `archive/migration_scripts/populate_sector_data.py` (stocks)
- [ ] `archive/migration_scripts/analyze_column_usage.py`
- [ ] `archive/migration_scripts/cleanup_null_international_symbols.py` (stocks, stock_prices, dividend_history, stock_splits)
- [ ] `archive/migration_scripts/investigate_null_exchanges.py` (stocks, stock_prices, dividend_history)
- [ ] `archive/migration_scripts/backfill_exchange_from_api.py` (stocks)
- [ ] `archive/migration_scripts/backfill_exchange_from_fmp.py` (stocks)
- [ ] `archive/migration_scripts/backfill_exchange_metadata.py` (stocks)
- [ ] `archive/migration_scripts/cleanup_international_symbols.py` (stocks, stock_prices, dividend_history, stock_splits)
- [ ] `archive/migration_scripts/enhanced_discovery.py` (stocks)

### Archive Update Scripts
- [ ] `archive/update_stocks_comprehensive.py` (stocks, stocks_excluded)
- [ ] `archive/update_stocks_v1_backup.py` (stocks, stock_prices, dividend_history)
- [ ] `archive/old_scripts/refresh_company_data.py` (stocks)
- [ ] `archive/old_scripts/backfill_adj_close.py` (stock_prices)
- [ ] `archive/old_scripts/backfill_adj_close_simple.py` (stock_prices)
- [ ] `archive/old_scripts/backfill_adj_close_prioritized.py` (stock_prices)
- [ ] `archive/old_scripts/run_migration_adj_close.py` (stock_prices)

### Archive Other
- [ ] `archive/dividend_scrapers/scrape_dividend_calendar_supabase.py`
- [ ] `archive/scripts_v1/update_stock.py`
- [ ] `archive/fix_company_names.py` (stocks)

## Shell Scripts (3-5 files)

### Critical Shell Scripts
- [ ] `scripts/cleanup_international_sql.sh` (stocks, stock_prices, stock_prices_hourly, dividend_history, stock_splits, holdings_history)
- [ ] `daily_update_v2.sh` (stocks, excluded_symbols - embedded Python)
- [ ] `scripts/daily_update.sh` (stocks, stocks_excluded - embedded SQL/Python)

### Potential References
- [ ] `setup_daily_cron.sh` (check for indirect references)

## Documentation Files (20+ files)

### Critical Docs
- [ ] `README.md` (table references in examples)

### Implementation Docs
- [ ] `docs/DAILY_AUTOMATION.md` (table examples)
- [ ] `docs/ETF_HOLDINGS_IMPLEMENTATION.md` (holdings_history examples)
- [ ] `docs/etf_metadata_queries.md` (stocks, table examples)
- [ ] `docs/AUM_TRACKING.md` (stock_prices examples)
- [ ] `docs/IV_IMPLEMENTATION.md` (stock_prices examples)
- [ ] `docs/ADJ_CLOSE_README.md` (stock_prices examples)
- [ ] `docs/STOCK_SPLITS_README.md` (stock_splits examples)
- [ ] `docs/HOLDINGS_HISTORY.md` (holdings_history examples)

### Other Docs
- [ ] `FULL_RUN_REPORT.md`
- [ ] `docs/PROJECT_STRUCTURE.md`
- [ ] `docs/METRICS_CALCULATION.md`
- [ ] `docs/TTM_CALCULATION_FIX.md`
- [ ] `docs/INCREMENTAL_UPDATE_LOGIC.md`
- [ ] `docs/CLEANUP_SUMMARY.md`
- [ ] `docs/VERIFICATION_REPORT.md`
- [ ] `docs/REFACTORING_COMPLETE.md`
- [ ] `docs/PHASE2_COMPLETE.md`
- [ ] `docs/PHASE3_COMPLETE.md`
- [ ] `docs/ETF_CLASSIFICATION.md`
- [ ] `docs/ETF_CLASSIFICATION_COMPLETE.md`
- [ ] `docs/ETF_CLASSIFICATION_IMPLEMENTATION.md`

### Legacy Docs
- [ ] `archive/old_docs/*.md` (if needed)

## Configuration & Other Files

- [ ] `.cursorrules` (example queries with table names)
- [ ] `lib/core/models.py` (table references in comments)
- [ ] `lib/core/config.py` (potential table references)

## Summary by Priority

### CRITICAL (Must complete first - 15-20 files)
- All 9 migrations
- supabase_helpers.py
- incremental_processor.py
- 5-6 processor files
- Critical shell scripts

### HIGH (Must complete before testing - 15-20 files)
- Database setup files (4)
- Core utility scripts (8-10)
- Data source files (3)

### MEDIUM (Update before production - 20+ files)
- Additional utility scripts
- Archive scripts that might still be used
- Some documentation

### LOW (Can be deferred - 30+ files)
- Archive scripts
- Test files
- Documentation (unless examples are critical)

## Total Files: 104+
- Critical: 15-20 files
- High: 15-20 files
- Medium: 20-30 files
- Low: 50+ files

---

**Recommended Approach:**
1. Create the new migration file (007_rename_tables_raw_prefix.sql)
2. Use find/replace with IDE for bulk changes (careful with patterns)
3. Update in order: SQL → Critical Python → High Priority → Medium → Low
4. Test after each major category
5. Commit incrementally with clear messages
