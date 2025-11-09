# Database Table Renaming Analysis Report
## High-Yield Dividend Analysis System

---

## EXECUTIVE SUMMARY

This report provides a comprehensive mapping of all database tables in the codebase that reference raw data ingestion. **8 core tables** need to be renamed with the `raw_` prefix to distinguish raw data ingestion layer from processed/application data.

**Total Files Affected: 104+ files**
- SQL files: 15 migration/database files
- Python files: 59 scripts and modules  
- Shell scripts: 10 automation files
- Documentation files: 20+ markdown files

---

## SECTION 1: CORE TABLES TO RENAME

### 1.1 Primary Data Tables

| Current Table | New Table | Data Type | Location Defined | Status |
|---|---|---|---|---|
| `stocks` | `raw_stocks` | Core metadata | database/create_tables.py | Active |
| `stock_prices` | `raw_stock_prices` | Time-series prices | migrations/002_add_adj_close.sql | Active |
| `dividend_history` | `raw_dividend_history` | Dividend events | database/create_tables.py | Active |
| `stock_splits` | `raw_stock_splits` | Corporate actions | migrations/create_stock_splits.sql | Active |
| `stock_prices_hourly` | `raw_stock_prices_hourly` | Intraday prices | migrations/create_stock_prices_hourly.sql | Active |
| `holdings_history` | `raw_holdings_history` | ETF holdings | migrations/006_create_holdings_history.sql | Active |
| `stocks_excluded` | `raw_stocks_excluded` | Exclusion list | database/create_stocks_excluded_table.sql | Active |
| `excluded_symbols` | `raw_excluded_symbols` | Legacy exclusion | database/create_tables.py | Legacy |

### 1.2 Secondary Tables (Consider Renaming)

| Current Table | Purpose | Location | Recommendation |
|---|---|---|---|
| `dividend_calendar` | Future dividend calendar | scripts/scrape_yieldmax.py | Rename to `raw_dividend_calendar` |
| `price_history` | Legacy price storage | database/create_tables.py | DEPRECATED - Remove or archive |

---

## SECTION 2: SCHEMA DEFINITIONS

### 2.1 Core Table Definitions

#### `stocks` → `raw_stocks`
**File:** `/Users/toan/dev/high-yield-dividend-analysis/database/create_tables.py` (lines 24-43)

**Columns:**
- id (SERIAL PRIMARY KEY)
- symbol (VARCHAR 20, UNIQUE NOT NULL)
- company_name, exchange, sector, industry
- market_cap, price, volume, pe_ratio
- dividend_yield, dividend_amount, ex_dividend_date, payment_date
- last_updated, created_at (timestamps)

**Extensions (from migrations):**
- expense_ratio, description (migration 001_add_etf_fields.sql)
- related_stock, investment_strategy (migration 004_add_related_stock_and_investment_strategy.sql)
- holdings, holdings_updated_at (migration 005_add_holdings_column.sql)
- is_etf, type, currency, country, ipo_date, exchange_short_name (from core/models.py)

**Indexes:**
- idx_stocks_symbol on stocks(symbol)
- idx_stocks_dividend_yield on stocks(dividend_yield DESC)
- idx_stocks_related_stock on stocks(related_stock)
- idx_stocks_investment_strategy on stocks(investment_strategy)
- idx_stocks_holdings on stocks USING GIN (holdings)

---

#### `stock_prices` → `raw_stock_prices`
**Files:**
- migrations/002_add_adj_close.sql (line 5-6)
- migrations/001_add_etf_fields.sql (line 15)

**Columns (inferred from migrations and code):**
- symbol (VARCHAR 20, NOT NULL)
- date (DATE, NOT NULL - UNIQUE constraint with symbol)
- open, high, low, close (DECIMAL 12,4)
- adj_close (DECIMAL 12,4 - added by migration 002)
- volume (BIGINT)
- change, change_percent (DECIMAL)
- vwap (DECIMAL 12,4)
- label, change_over_time (from models)
- aum (BIGINT - added by migration 001 for ETF Assets Under Management)
- iv (DECIMAL - Implied Volatility)

**Indexes:**
- idx_stock_prices_symbol_date on stock_prices(symbol, date DESC)
- idx_stock_prices_adj_close on stock_prices(symbol, date, adj_close)

**Constraints:**
- UNIQUE(symbol, date)

---

#### `dividend_history` → `raw_dividend_history`
**File:** `/Users/toan/dev/high-yield-dividend-analysis/database/create_tables.py` (lines 74-87)
**Migration:** migrations/003_add_dividend_unique_constraint.sql

**Columns:**
- id (SERIAL PRIMARY KEY)
- symbol (VARCHAR 20, NOT NULL)
- ex_date (DATE, NOT NULL - was ex_dividend_date in v1)
- payment_date (DATE)
- record_date (DATE)
- declaration_date (DATE)
- amount (DECIMAL 10,4)
- currency (VARCHAR 10, DEFAULT 'USD')

**Constraints:**
- UNIQUE(symbol, ex_date) - added by migration 003

**Indexes:**
- idx_dividend_history_symbol_date on dividend_history(symbol, ex_date DESC)

---

#### `stock_splits` → `raw_stock_splits`
**File:** `/Users/toan/dev/high-yield-dividend-analysis/migrations/create_stock_splits.sql` (lines 4-47)

**Columns:**
- id (BIGSERIAL PRIMARY KEY)
- symbol (VARCHAR 20, NOT NULL)
- split_date (DATE NOT NULL)
- split_ratio (NUMERIC 12,8)
- numerator, denominator (INTEGER)
- split_string (VARCHAR 20)
- description (TEXT)
- source (VARCHAR 50)
- created_at, updated_at (TIMESTAMPTZ)

**Constraints:**
- UNIQUE(symbol, split_date)
- Foreign Key: symbol REFERENCES stocks(symbol) ON DELETE CASCADE

**Indexes:**
- idx_splits_symbol on stock_splits(symbol)
- idx_splits_date on stock_splits(split_date)
- idx_splits_symbol_date on stock_splits(symbol, split_date DESC)

---

#### `stock_prices_hourly` → `raw_stock_prices_hourly`
**File:** `/Users/toan/dev/high-yield-dividend-analysis/migrations/create_stock_prices_hourly.sql` (lines 4-53)

**Columns:**
- id (BIGSERIAL PRIMARY KEY)
- symbol (VARCHAR 20, NOT NULL)
- timestamp (TIMESTAMPTZ, NOT NULL)
- date (DATE NOT NULL)
- hour (INTEGER 0-23)
- price, open, high, low, close (NUMERIC 12,4)
- adj_close (NUMERIC 12,4 - added by migration 002)
- volume (BIGINT)
- change, change_percent (NUMERIC 8,4)
- vwap (NUMERIC 12,4)
- trade_count (INTEGER)
- currency (VARCHAR 10, DEFAULT 'USD')
- source (VARCHAR 50)
- created_at (TIMESTAMPTZ DEFAULT NOW())

**Constraints:**
- UNIQUE(symbol, timestamp)
- Foreign Key: symbol REFERENCES stocks(symbol) ON DELETE CASCADE

**Indexes:**
- idx_hourly_symbol on stock_prices_hourly(symbol)
- idx_hourly_date on stock_prices_hourly(date)
- idx_hourly_timestamp on stock_prices_hourly(timestamp)
- idx_hourly_symbol_date on stock_prices_hourly(symbol, date)
- idx_hourly_symbol_timestamp on stock_prices_hourly(symbol, timestamp DESC)
- idx_hourly_adj_close on stock_prices_hourly(symbol, timestamp, adj_close)

---

#### `holdings_history` → `raw_holdings_history`
**File:** `/Users/toan/dev/high-yield-dividend-analysis/migrations/006_create_holdings_history.sql` (lines 7-35)

**Columns:**
- id (BIGSERIAL PRIMARY KEY)
- symbol (VARCHAR 20, NOT NULL)
- date (DATE NOT NULL)
- holdings (JSONB NOT NULL)
- holdings_count (INTEGER)
- data_source (VARCHAR 50, DEFAULT 'FMP')
- created_at (TIMESTAMPTZ DEFAULT NOW())

**Constraints:**
- UNIQUE(symbol, date)

**Indexes:**
- idx_holdings_history_symbol on holdings_history(symbol)
- idx_holdings_history_date on holdings_history(date)
- idx_holdings_history_symbol_date on holdings_history(symbol, date)
- idx_holdings_history_holdings on holdings_history USING GIN (holdings)

---

#### `stocks_excluded` → `raw_stocks_excluded`
**File:** `/Users/toan/dev/high-yield-dividend-analysis/database/create_stocks_excluded_table.sql`

**Columns:**
- id (SERIAL PRIMARY KEY)
- symbol (VARCHAR 20, UNIQUE NOT NULL)
- reason (VARCHAR 255)
- excluded_at (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

---

---

## SECTION 3: FILES REQUIRING CHANGES

### 3.1 SQL Files (15 files)

#### Migrations (Must Update)
1. `/Users/toan/dev/high-yield-dividend-analysis/migrations/001_add_etf_fields.sql`
   - References: `stocks`, `stock_prices`
   - Changes: ALTER TABLE statements

2. `/Users/toan/dev/high-yield-dividend-analysis/migrations/002_add_adj_close.sql`
   - References: `stock_prices`, `stock_prices_hourly`
   - Changes: ALTER TABLE statements, index definitions

3. `/Users/toan/dev/high-yield-dividend-analysis/migrations/003_add_dividend_unique_constraint.sql`
   - References: `dividend_history`
   - Changes: ALTER TABLE, constraint definitions

4. `/Users/toan/dev/high-yield-dividend-analysis/migrations/004_add_related_stock_and_investment_strategy.sql`
   - References: `stocks`
   - Changes: ALTER TABLE, index definitions

5. `/Users/toan/dev/high-yield-dividend-analysis/migrations/005_add_holdings_column.sql`
   - References: `stocks`
   - Changes: ALTER TABLE, index definitions

6. `/Users/toan/dev/high-yield-dividend-analysis/migrations/006_create_holdings_history.sql`
   - References: `holdings_history`
   - Changes: CREATE TABLE (rename table name)

7. `/Users/toan/dev/high-yield-dividend-analysis/migrations/create_stock_prices_hourly.sql`
   - References: `stock_prices_hourly`, `stocks`
   - Changes: CREATE TABLE, foreign key references

8. `/Users/toan/dev/high-yield-dividend-analysis/migrations/add_iv_column.sql`
   - References: `stock_prices` (inferred)
   - Changes: ALTER TABLE

9. `/Users/toan/dev/high-yield-dividend-analysis/migrations/create_stock_splits.sql`
   - References: `stock_splits`, `stocks`
   - Changes: CREATE TABLE, foreign key references

#### Database Setup
10. `/Users/toan/dev/high-yield-dividend-analysis/database/create_tables.py`
    - References: `stocks`, `excluded_symbols`, `price_history`, `dividend_history`
    - Changes: CREATE TABLE IF NOT EXISTS statements, index definitions

11. `/Users/toan/dev/high-yield-dividend-analysis/database/create_stocks_excluded_table.sql`
    - References: `stocks_excluded`
    - Changes: CREATE TABLE, GRANT statements

12. `/Users/toan/dev/high-yield-dividend-analysis/database/disable_rls.sql`
    - References: `stocks_excluded`
    - Changes: Table references

13. `/Users/toan/dev/high-yield-dividend-analysis/database/grant_permissions.sql`
    - References: `stocks_excluded`
    - Changes: GRANT statements

14. `/Users/toan/dev/high-yield-dividend-analysis/scripts/populate_etf_metadata.sql`
    - References: `stocks`
    - Changes: UPDATE statements

15. `/Users/toan/dev/high-yield-dividend-analysis/scripts/populate_all_etf_metadata.sql`
    - References: `stocks`
    - Changes: UPDATE statements

16. `/Users/toan/dev/high-yield-dividend-analysis/scripts/classify_all_etfs.sql`
    - References: `stocks`
    - Changes: UPDATE statements

---

### 3.2 Python Files (59 files)

#### Core Helpers (Critical)
1. **`/Users/toan/dev/high-yield-dividend-analysis/supabase_helpers.py`** (CRITICAL)
   - Lines 52, 71: `.table('stocks')`
   - Lines 417-432: Upsert logic with table-specific conflict handling
   - References: `stocks`, `stock_prices`, `stock_prices_hourly`, `dividend_history`, `stocks_excluded`
   - Changes: Multiple `.table()` call parameters

#### Processors (Critical)
2. **`/Users/toan/dev/high-yield-dividend-analysis/lib/processors/price_processor.py`**
   - References: `stock_prices` (via supabase_batch_upsert)
   - Changes: None directly (uses helper functions)

3. **`/Users/toan/dev/high-yield-dividend-analysis/lib/processors/dividend_processor.py`**
   - References: `dividend_history` (via supabase_batch_upsert)
   - Changes: None directly (uses helper functions)

4. **`/Users/toan/dev/high-yield-dividend-analysis/lib/processors/incremental_processor.py`** (CRITICAL)
   - Lines 37, 69: `.select()` calls on `stock_prices`, `dividend_history`
   - Changes: Direct table references in supabase_select calls

5. **`/Users/toan/dev/high-yield-dividend-analysis/lib/processors/holdings_processor.py`**
   - References: `holdings_history`
   - Changes: `.table('holdings_history')` call

6. **`/Users/toan/dev/high-yield-dividend-analysis/lib/processors/company_processor.py`**
   - References: `stocks`
   - Changes: `.table()` calls

7. **`/Users/toan/dev/high-yield-dividend-analysis/lib/processors/etf_classifier.py`**
   - References: `stocks`
   - Changes: `.table()` calls

#### Data Sources
8. **`/Users/toan/dev/high-yield-dividend-analysis/lib/data_sources/fmp_client.py`**
   - References: `stocks`, `stock_prices`, `dividend_history`
   - Changes: Store operations via processors

9. **`/Users/toan/dev/high-yield-dividend-analysis/lib/data_sources/yahoo_client.py`**
   - References: `stock_prices`
   - Changes: Store operations via processors

#### Utility Scripts (15+ files)
10. `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_all_international_symbols.py`
    - References: `stocks`, `stock_prices`, `stock_prices_hourly`, `dividend_history`, `stock_splits`, `holdings_history`
    - Changes: Multiple `.table()` calls with dynamic table names

11. `/Users/toan/dev/high-yield-dividend-analysis/scripts/calculate_stock_metrics.py`
    - References: `stocks`, `stock_prices`, `dividend_history`
    - Changes: `.table()` calls

12. `/Users/toan/dev/high-yield-dividend-analysis/scripts/fetch_stock_splits.py`
    - References: `stock_splits`, `stocks`
    - Changes: `.table()` calls

13. `/Users/toan/dev/high-yield-dividend-analysis/scripts/fetch_hourly_prices.py`
    - References: `stock_prices_hourly`
    - Changes: `.table()` calls

14. `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_old_hourly_data.py`
    - References: `stock_prices_hourly`
    - Changes: Multiple `.table()` calls

15. `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_duplicates.py`
    - References: `stock_prices`
    - Changes: `.table()` calls

16. `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_international_sql.sh`
    - References: `stocks`, `stock_prices`, `stock_prices_hourly`, `dividend_history`, `stock_splits`, `holdings_history`
    - Changes: SQL query table names

17. `/Users/toan/dev/high-yield-dividend-analysis/scripts/repopulate_all_dividends.py`
    - References: `dividend_history`
    - Changes: `.table()` calls

18. `/Users/toan/dev/high-yield-dividend-analysis/scripts/fix_yahoo_prices.py`
    - References: `stocks`
    - Changes: `.table()` calls

19. `/Users/toan/dev/high-yield-dividend-analysis/scripts/fix_tsyy_prices.py`
    - References: `stock_prices`
    - Changes: `.table()` calls

20. `/Users/toan/dev/high-yield-dividend-analysis/update_stock_v2.py`
    - References: Multiple tables
    - Changes: `.table()` calls

#### Test & Debug Scripts (10+ files)
21. `/Users/toan/dev/high-yield-dividend-analysis/debug_ttm_issue.py`
    - References: `stocks`, `stock_prices`, `dividend_history`
    - Changes: supabase_select calls

22. `/Users/toan/dev/high-yield-dividend-analysis/debug_ymag_frequency.py`
    - References: `stocks`, `dividend_history`
    - Changes: supabase_select calls

23. `/Users/toan/dev/high-yield-dividend-analysis/verify_annualization.py`
    - References: `stocks`, `dividend_history`
    - Changes: supabase_select calls

24. `/Users/toan/dev/high-yield-dividend-analysis/verify_weekly_ttm.py`
    - References: `dividend_history`
    - Changes: supabase_select calls

25. `/Users/toan/dev/high-yield-dividend-analysis/test_dividend_upsert.py`
    - References: `dividend_history`
    - Changes: `.table()` calls

#### Archive Scripts (20+ files)
These are in `/Users/toan/dev/high-yield-dividend-analysis/archive/` and may be deprecated but contain references:

26. `/Users/toan/dev/high-yield-dividend-analysis/archive/update_stocks_comprehensive.py`
27. `/Users/toan/dev/high-yield-dividend-analysis/archive/update_stocks_v1_backup.py`
28. `/Users/toan/dev/high-yield-dividend-analysis/archive/old_scripts/refresh_company_data.py`
29. `/Users/toan/dev/high-yield-dividend-analysis/archive/old_scripts/backfill_adj_close*.py` (multiple versions)
30. `/Users/toan/dev/high-yield-dividend-analysis/archive/migration_scripts/populate_sector_data.py`
31. `/Users/toan/dev/high-yield-dividend-analysis/archive/migration_scripts/cleanup_international_symbols.py`
32. `/Users/toan/dev/high-yield-dividend-analysis/archive/migration_scripts/cleanup_null_international_symbols.py`
33. `/Users/toan/dev/high-yield-dividend-analysis/archive/migration_scripts/backfill_exchange_*.py` (multiple)
34. `/Users/toan/dev/high-yield-dividend-analysis/archive/migration_scripts/investigate_null_exchanges.py`
35. `/Users/toan/dev/high-yield-dividend-analysis/archive/migration_scripts/enhanced_discovery.py`
36. `/Users/toan/dev/high-yield-dividend-analysis/archive_postgresql/fetch_prices_dividends.py`
37. `/Users/toan/dev/high-yield-dividend-analysis/archive_postgresql/update_stock.py`
38. `/Users/toan/dev/high-yield-dividend-analysis/archive/dividend_scrapers/scrape_dividend_calendar_supabase.py`

#### Database & Other
39. `/Users/toan/dev/high-yield-dividend-analysis/database/create_hourly_table.py`
    - References: `stock_prices_hourly`
    - Changes: `.table()` calls

40. `/Users/toan/dev/high-yield-dividend-analysis/sector_helpers.py`
    - References: `stocks`
    - Changes: `.table()` calls

41. `/Users/toan/dev/high-yield-dividend-analysis/scripts/run_all_projections.py`
    - References: `stocks` (potentially)
    - Changes: May have `.table()` calls

42. `/Users/toan/dev/high-yield-dividend-analysis/lib/discovery/symbol_discovery.py`
    - References: `stocks`, `excluded_symbols`
    - Changes: `.table()` calls

43. `/Users/toan/dev/high-yield-dividend-analysis/scripts/scrape_yieldmax.py`
    - References: `dividend_calendar`
    - Changes: `.table()` calls

44. `/Users/toan/dev/high-yield-dividend-analysis/daily_update_v2.sh` (shell with embedded Python)
    - References: `stocks`, `excluded_symbols`
    - Changes: `.table()` calls in embedded code

45. `/Users/toan/dev/high-yield-dividend-analysis/test_archive/test_*.py` (test files)
    - References: Various tables
    - Changes: `.table()` calls

---

### 3.3 Shell Scripts (10 files)

1. `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_international_sql.sh`
   - Raw SQL with FROM/DELETE statements
   - References: All core tables
   - Changes: SQL WHERE clauses with table names

2. `/Users/toan/dev/high-yield-dividend-analysis/scripts/daily_update.sh`
   - Embedded SQL/Python
   - References: `stocks`, `stocks_excluded`
   - Changes: SQL statements

3. `/Users/toan/dev/high-yield-dividend-analysis/daily_update_v2.sh`
   - Embedded Python with supabase calls
   - References: `stocks`, `excluded_symbols`
   - Changes: `.table()` calls

4. `/Users/toan/dev/high-yield-dividend-analysis/setup_daily_cron.sh`
   - May reference other scripts
   - Changes: None directly unless it runs other scripts

---

### 3.4 Documentation Files (20+ files)

These need updates for example queries:
- `docs/*.md` files containing SQL examples
- `README.md` with setup instructions
- Implementation docs showing table structure

Key files:
1. `/Users/toan/dev/high-yield-dividend-analysis/README.md`
2. `/Users/toan/dev/high-yield-dividend-analysis/FULL_RUN_REPORT.md`
3. `/Users/toan/dev/high-yield-dividend-analysis/docs/AUM_TRACKING.md`
4. `/Users/toan/dev/high-yield-dividend-analysis/docs/ETF_HOLDINGS_IMPLEMENTATION.md`
5. `/Users/toan/dev/high-yield-dividend-analysis/docs/DAILY_AUTOMATION.md`
6. `/Users/toan/dev/high-yield-dividend-analysis/docs/etf_metadata_queries.md`
7. Other documentation with example queries

---

## SECTION 4: CHANGE PATTERNS BY FILE TYPE

### 4.1 Python Supabase Calls

**Pattern 1: Simple Table Selection**
```python
# BEFORE
result = supabase.table('stocks').select('symbol').execute()

# AFTER
result = supabase.table('raw_stocks').select('symbol').execute()
```

**Pattern 2: Helper Function Calls**
```python
# BEFORE
supabase_select('stock_prices', columns='date', where_clause={...})

# AFTER
supabase_select('raw_stock_prices', columns='date', where_clause={...})
```

**Pattern 3: Batch Operations**
```python
# BEFORE (in supabase_helpers.py)
if table == 'stock_prices':
    result = supabase.table(table).upsert(batch, on_conflict='symbol,date').execute()

# AFTER
if table == 'raw_stock_prices':
    result = supabase.table(table).upsert(batch, on_conflict='symbol,date').execute()
```

### 4.2 SQL Statements

**Pattern 1: ALTER TABLE**
```sql
-- BEFORE
ALTER TABLE stocks ADD COLUMN expense_ratio DECIMAL(10, 6);

-- AFTER
ALTER TABLE raw_stocks ADD COLUMN expense_ratio DECIMAL(10, 6);
```

**Pattern 2: Foreign Key References**
```sql
-- BEFORE
ALTER TABLE stock_splits
ADD CONSTRAINT fk_splits_symbol
FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE;

-- AFTER
ALTER TABLE raw_stock_splits
ADD CONSTRAINT fk_splits_symbol
FOREIGN KEY (symbol) REFERENCES raw_stocks(symbol) ON DELETE CASCADE;
```

**Pattern 3: Index Creation**
```sql
-- BEFORE
CREATE INDEX idx_stock_prices_symbol_date ON stock_prices(symbol, date DESC);

-- AFTER
CREATE INDEX idx_stock_prices_symbol_date ON raw_stock_prices(symbol, date DESC);
```

---

## SECTION 5: CRITICAL DEPENDENCIES

### Foreign Key Relationships
These MUST be updated together:

1. **stock_splits** → **stocks**
   - Constraint: `fk_splits_symbol`
   - Both tables must be renamed atomically

2. **stock_prices_hourly** → **stocks**
   - Constraint: `fk_hourly_symbol`
   - Both tables must be renamed atomically

3. **holdings_history** (references stocks indirectly)
   - Uses symbol field (no FK constraint)
   - Can be renamed independently but maintain consistency

### Conflict Resolution Logic
In `supabase_helpers.py` lines 417-432, update the table name checks:

**CRITICAL:** The upsert conflict handling has table-specific logic:
```python
if table == 'raw_stock_prices':  # was 'stock_prices'
    result = supabase.table(table).upsert(batch, on_conflict='symbol,date').execute()
elif table == 'raw_stock_prices_hourly':  # was 'stock_prices_hourly'
    result = supabase.table(table).insert(batch, upsert=True).execute()
elif table == 'raw_dividend_history':  # was 'dividend_history'
    result = supabase.table(table).upsert(batch, on_conflict='symbol,ex_date').execute()
elif table == 'raw_stocks':  # was 'stocks'
    result = supabase.table(table).upsert(batch, on_conflict='symbol').execute()
elif table == 'raw_stocks_excluded':  # was 'stocks_excluded'
    result = supabase.table(table).upsert(batch, on_conflict='symbol').execute()
```

---

## SECTION 6: IMPLEMENTATION STRATEGY

### Phase 1: Preparation
- [ ] Create backup of current database
- [ ] Document all custom indexes and constraints
- [ ] List all active applications/scripts using these tables
- [ ] Set up development/staging environment for testing

### Phase 2: Database Migration
- [ ] Create new migration file: `007_rename_tables_raw_prefix.sql`
- [ ] Rename tables using ALTER TABLE ... RENAME TO
- [ ] Rename indexes using ALTER INDEX ... RENAME TO
- [ ] Update foreign key constraints
- [ ] Verify all indexes and constraints

### Phase 3: Code Updates - High Priority
1. **supabase_helpers.py** - Core helper functions
2. **lib/processors/incremental_processor.py** - Direct table references
3. **lib/processors/holdings_processor.py** - Holdings table
4. **lib/processors/company_processor.py** - Stocks table
5. **lib/processors/etf_classifier.py** - Stocks table

### Phase 4: Code Updates - Medium Priority
- Core scripts in `scripts/` directory
- Data source clients (FMP, Yahoo, AlphaVantage)
- Configuration files

### Phase 5: Code Updates - Lower Priority
- Archive scripts (if still used)
- Utility/helper scripts
- Test files
- Debug scripts

### Phase 6: Documentation
- Update all markdown files with new table names
- Update README.md with schema documentation
- Update example queries
- Update migration guides

### Phase 7: Testing
- Run all active scripts against development database
- Test data ingestion pipeline
- Verify incremental updates work correctly
- Test batch operations

### Phase 8: Deployment
- Apply migration to production
- Deploy code changes
- Monitor for errors
- Verify data integrity

---

## SECTION 7: SUMMARY TABLE

| Component | Count | Files Affected | Effort |
|---|---|---|---|
| SQL Migrations | 9 | 15 files | HIGH |
| Core Helpers | 1 | supabase_helpers.py | HIGH |
| Processors | 7 | lib/processors/*.py | MEDIUM |
| Data Sources | 3 | lib/data_sources/*.py | MEDIUM |
| Utility Scripts | 20+ | scripts/*.py | MEDIUM |
| Archive Scripts | 20+ | archive/*.py | LOW |
| Shell Scripts | 3-5 | *.sh files | MEDIUM |
| Documentation | 20+ | docs/*.md | LOW |
| Tests/Debug | 10+ | test_*.py, debug_*.py | LOW |
| **TOTAL** | **90+** | **104+ files** | **4-6 weeks** |

---

## SECTION 8: RECOMMENDATIONS

1. **Automated Search & Replace**
   - Use IDE/editor find-and-replace for bulk changes
   - Be careful with patterns like 'stocks_excluded' vs 'stocks' vs 'excluded_symbols'
   - Consider custom scripts for complex replacements

2. **Version Control**
   - Create feature branch: `refactor/rename-tables-raw-prefix`
   - Commit migrations separately from code changes
   - Use meaningful commit messages per file/component

3. **Testing Strategy**
   - Run migrations in development database first
   - Test with recent backup to catch issues early
   - Run complete data pipeline tests before production

4. **Rollback Plan**
   - Keep migration that renames tables back (reverse migration)
   - Document rollback procedures
   - Have database backup available for quick restore

5. **Communication**
   - Document all table renames in clear mapping
   - Notify all stakeholders of the changes
   - Update team documentation

---

## APPENDIX: COMPLETE TABLE REFERENCE MAPPING

| Old Table | New Table | Current Status | Files To Update |
|---|---|---|---|
| stocks | raw_stocks | Active, many references | 45+ |
| stock_prices | raw_stock_prices | Active, core data | 20+ |
| dividend_history | raw_dividend_history | Active, core data | 15+ |
| stock_splits | raw_stock_splits | Active | 8+ |
| stock_prices_hourly | raw_stock_prices_hourly | Active | 12+ |
| holdings_history | raw_holdings_history | Active | 8+ |
| stocks_excluded | raw_stocks_excluded | Active | 10+ |
| excluded_symbols | raw_excluded_symbols | Legacy | 3+ |
| dividend_calendar | raw_dividend_calendar | Optional | 2+ |
| price_history | raw_price_history or DEPRECATE | Deprecated | 1 |

