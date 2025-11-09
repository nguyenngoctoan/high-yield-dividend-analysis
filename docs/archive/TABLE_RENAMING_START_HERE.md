# Database Table Renaming - START HERE

## Overview

This directory contains a comprehensive analysis for renaming core database tables to use a `raw_` prefix, distinguishing the raw data ingestion layer from processed application data.

**Key Numbers:**
- 8 core tables to rename
- 104+ files affected
- 200+ code references found
- Estimated effort: 10-15 hours

---

## Read These Documents in Order

### 1. ANALYSIS_SUMMARY.txt (START HERE)
**~150 lines | Read time: 10-15 minutes**

High-level overview with key findings. Read this first to understand:
- What tables are being renamed
- Which files are affected
- How long it will take
- Critical dependencies
- Basic roadmap

### 2. TABLE_RENAMING_QUICK_REFERENCE.md
**~200 lines | Read time: 15-20 minutes**

Quick lookup guide with:
- Core tables mapping table
- File categories by priority
- Search & replace patterns
- Critical code sections
- Implementation timeline

### 3. FILES_TO_UPDATE_CHECKLIST.md
**~300 lines | Read time: 20-30 minutes**

Detailed checklist with:
- Every file that needs updating
- Organized by priority
- Number of references per file
- File-by-file summary
- Recommended update approach

### 4. TABLE_RENAMING_ANALYSIS.md
**~700 lines | Comprehensive Reference**

Complete technical documentation with:
- Full schema definitions for all tables
- All file references with line numbers
- Change patterns for every file type
- Foreign key relationships
- Implementation strategy (8 phases)
- Critical code sections

---

## Quick Start Checklist

### Before You Start
- [ ] Read ANALYSIS_SUMMARY.txt (this gives context)
- [ ] Review TABLE_RENAMING_QUICK_REFERENCE.md (know what you're doing)
- [ ] Understand the critical dependencies (see summary)

### Preparation Phase
- [ ] Create database backup
- [ ] Create feature branch: `refactor/rename-tables-raw-prefix`
- [ ] Document all current indexes and constraints
- [ ] Set up development database

### Execution Phase
1. [ ] Create migration: `migrations/007_rename_tables_raw_prefix.sql`
2. [ ] Update CRITICAL files (15-20 files) - 2-3 hours
3. [ ] Update HIGH PRIORITY files (15-20 files) - 3-4 hours
4. [ ] Update MEDIUM PRIORITY files (20-30 files) - 3-4 hours
5. [ ] Update LOW PRIORITY files (optional) - 2-3 hours
6. [ ] Update documentation - 1-2 hours

### Testing & Deployment Phase
- [ ] Test migration in development
- [ ] Test complete data pipeline
- [ ] Verify data integrity
- [ ] Deploy to production
- [ ] Monitor for errors

---

## Table Mapping (Quick Reference)

| Old Name | New Name |
|----------|----------|
| stocks | raw_stocks |
| stock_prices | raw_stock_prices |
| dividend_history | raw_dividend_history |
| stock_splits | raw_stock_splits |
| stock_prices_hourly | raw_stock_prices_hourly |
| holdings_history | raw_holdings_history |
| stocks_excluded | raw_stocks_excluded |
| excluded_symbols | raw_excluded_symbols |

---

## Critical Files (Update First)

These files MUST be updated and contain many references:

1. **supabase_helpers.py** (40+ references)
   - Table references: stocks, stock_prices, stock_prices_hourly, dividend_history, stocks_excluded
   - Critical section: Lines 417-432 (upsert logic)

2. **lib/processors/incremental_processor.py** (2 direct references)
   - Line 37: stock_prices
   - Line 69: dividend_history

3. **All 9 Migration Files** (SQL)
   - Migrations 001-006, create_stock_splits.sql, create_stock_prices_hourly.sql, add_iv_column.sql

4. **Core Processors** (5 files)
   - price_processor.py
   - dividend_processor.py
   - company_processor.py
   - etf_classifier.py
   - holdings_processor.py

---

## Search & Replace Patterns

### For Python Code
```python
.table('stocks')              -> .table('raw_stocks')
.table('stock_prices')        -> .table('raw_stock_prices')
.table('dividend_history')    -> .table('raw_dividend_history')
.table('stock_splits')        -> .table('raw_stock_splits')
.table('stock_prices_hourly') -> .table('raw_stock_prices_hourly')
.table('holdings_history')    -> .table('raw_holdings_history')
.table('stocks_excluded')     -> .table('raw_stocks_excluded')
supabase_select('stocks',     -> supabase_select('raw_stocks',
```

### For SQL Files
```sql
FROM stocks                   -> FROM raw_stocks
ALTER TABLE stocks            -> ALTER TABLE raw_stocks
REFERENCES stocks             -> REFERENCES raw_stocks
CREATE TABLE stocks           -> CREATE TABLE raw_stocks
```

---

## Critical Code Sections

### supabase_helpers.py (Lines 417-432)
The upsert function has table-specific conflict handling. ALL of these conditions must be updated:

```python
if table == 'raw_stock_prices':        # was 'stock_prices'
elif table == 'raw_stock_prices_hourly':  # was 'stock_prices_hourly'
elif table == 'raw_dividend_history':  # was 'dividend_history'
elif table == 'raw_stocks':            # was 'stocks'
elif table == 'raw_stocks_excluded':   # was 'stocks_excluded'
```

### incremental_processor.py (Lines 37, 69)
Direct table references in supabase_select calls:

```python
# Line 37
result = supabase_select('raw_stock_prices', columns='date', ...)

# Line 69
result = supabase_select('raw_dividend_history', columns='ex_date', ...)
```

---

## File Organization by Priority

### CRITICAL (Update First - 15-20 files)
- supabase_helpers.py
- incremental_processor.py
- All 9 migration SQL files
- 4 core processor files
- 2-3 shell scripts

**Estimated Time: 2-3 hours**

### HIGH PRIORITY (Update Before Testing - 15-20 files)
- Database setup files (4)
- Processor files (5)
- Data source clients (3)
- Core utility scripts (8-10)

**Estimated Time: 3-4 hours**

### MEDIUM PRIORITY (Update Before Production - 20-30 files)
- Additional utility scripts
- Some archive scripts still in use
- Important documentation

**Estimated Time: 3-4 hours**

### LOW PRIORITY (Can be deferred - 50+ files)
- Archive scripts
- Test files
- Debug utilities
- Legacy documentation

**Estimated Time: 2-3 hours (optional)**

---

## Foreign Key Dependencies

These tables have relationships that MUST be maintained:

1. **raw_stock_splits** -> **raw_stocks**
   - Constraint: `fk_splits_symbol`
   - Both must be renamed together

2. **raw_stock_prices_hourly** -> **raw_stocks**
   - Constraint: `fk_hourly_symbol`
   - Both must be renamed together

3. **raw_holdings_history** (no FK, but references raw_stocks indirectly)
   - Uses symbol field for joins
   - Maintain naming consistency

---

## Migration File Template

Create: `migrations/007_rename_tables_raw_prefix.sql`

```sql
-- Migration: Rename tables with raw_ prefix
-- Date: 2025-11-02
-- Purpose: Distinguish raw data ingestion layer from processed application data

BEGIN;

-- Rename core data tables
ALTER TABLE stocks RENAME TO raw_stocks;
ALTER TABLE stock_prices RENAME TO raw_stock_prices;
ALTER TABLE dividend_history RENAME TO raw_dividend_history;
ALTER TABLE stock_splits RENAME TO raw_stock_splits;
ALTER TABLE stock_prices_hourly RENAME TO raw_stock_prices_hourly;
ALTER TABLE holdings_history RENAME TO raw_holdings_history;
ALTER TABLE stocks_excluded RENAME TO raw_stocks_excluded;
ALTER TABLE excluded_symbols RENAME TO raw_excluded_symbols;

-- Rename indexes (PostgreSQL automatically renames FK constraints)
-- Verify indexes were renamed with: \d raw_stocks

COMMIT;
```

---

## Next Steps

1. **Read ANALYSIS_SUMMARY.txt** (10-15 min)
2. **Review TABLE_RENAMING_QUICK_REFERENCE.md** (15-20 min)
3. **Create feature branch** for the refactoring
4. **Create migration file** 007_rename_tables_raw_prefix.sql
5. **Update code** in priority order using FILES_TO_UPDATE_CHECKLIST.md
6. **Test** thoroughly in development
7. **Deploy** with monitoring

---

## Document Structure

```
TABLE_RENAMING_START_HERE.md (this file)
├── Quick overview and navigation
├── Quick start checklist
├── Table mapping
└── Next steps

ANALYSIS_SUMMARY.txt (70-80 lines)
├── High-level findings
├── Files by category
├── Critical dependencies
└── Recommendations

TABLE_RENAMING_QUICK_REFERENCE.md (200 lines)
├── Table mapping table
├── Files by priority
├── Search & replace patterns
├── Critical code sections
└── Impact summary

FILES_TO_UPDATE_CHECKLIST.md (350+ lines)
├── Complete file list
├── Organized by priority
├── Reference counts
└── Update sequence

TABLE_RENAMING_ANALYSIS.md (700+ lines)
├── Complete technical documentation
├── Full schema definitions
├── All file references with line numbers
├── Change patterns by file type
├── 8-phase implementation strategy
└── Complete dependencies map
```

---

## Questions?

Refer to the appropriate document:
- **"What's this about?"** → ANALYSIS_SUMMARY.txt
- **"How do I do this?"** → TABLE_RENAMING_QUICK_REFERENCE.md
- **"Which files do I update?"** → FILES_TO_UPDATE_CHECKLIST.md
- **"Tell me everything"** → TABLE_RENAMING_ANALYSIS.md

---

**Analysis Generated:** 2025-11-02
**Total Files Analyzed:** 104+
**Total References Found:** 200+
**Estimated Effort:** 10-15 hours
