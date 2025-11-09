# Quick Reference: Table Renaming to raw_ Prefix

## Core Tables to Rename (8 tables)

| # | Old Name | New Name | Type | Priority |
|---|----------|----------|------|----------|
| 1 | `stocks` | `raw_stocks` | Master data | CRITICAL |
| 2 | `stock_prices` | `raw_stock_prices` | Time-series | CRITICAL |
| 3 | `dividend_history` | `raw_dividend_history` | Events | CRITICAL |
| 4 | `stock_splits` | `raw_stock_splits` | Events | HIGH |
| 5 | `stock_prices_hourly` | `raw_stock_prices_hourly` | Time-series | HIGH |
| 6 | `holdings_history` | `raw_holdings_history` | Time-series | HIGH |
| 7 | `stocks_excluded` | `raw_stocks_excluded` | Lists | MEDIUM |
| 8 | `excluded_symbols` | `raw_excluded_symbols` | Legacy | MEDIUM |

## Files to Update by Category

### CRITICAL (Must Update First)
- [x] `/Users/toan/dev/high-yield-dividend-analysis/supabase_helpers.py` - 45+ occurrences
- [x] `/Users/toan/dev/high-yield-dividend-analysis/lib/processors/incremental_processor.py` - Direct table refs
- [x] `/Users/toan/dev/high-yield-dividend-analysis/migrations/*.sql` - 9 migration files

### HIGH PRIORITY (Update Before Testing)
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/lib/processors/price_processor.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/lib/processors/dividend_processor.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/lib/processors/company_processor.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/lib/processors/etf_classifier.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/lib/processors/holdings_processor.py`

### MEDIUM PRIORITY (Scripts)
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_all_international_symbols.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/scripts/calculate_stock_metrics.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/scripts/fetch_stock_splits.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/scripts/fetch_hourly_prices.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_old_hourly_data.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/scripts/cleanup_duplicates.py`
- [ ] `/Users/toan/dev/high-yield-dividend-analysis/scripts/repopulate_all_dividends.py`

### LOW PRIORITY (Archive, Tests, Docs)
- [ ] Archive scripts in `archive/` directory
- [ ] Test files (`test_*.py`, `debug_*.py`)
- [ ] Documentation files (`docs/*.md`, `README.md`)

## Search & Replace Patterns

### For Python Code
```
Pattern 1: .table('stocks') → .table('raw_stocks')
Pattern 2: .table('stock_prices') → .table('raw_stock_prices')
Pattern 3: .table('dividend_history') → .table('raw_dividend_history')
Pattern 4: .table('stock_splits') → .table('raw_stock_splits')
Pattern 5: .table('stock_prices_hourly') → .table('raw_stock_prices_hourly')
Pattern 6: .table('holdings_history') → .table('raw_holdings_history')
Pattern 7: .table('stocks_excluded') → .table('raw_stocks_excluded')
Pattern 8: supabase_select('stocks', → supabase_select('raw_stocks',
```

### For SQL Files
```
Pattern 1: FROM stocks → FROM raw_stocks
Pattern 2: ALTER TABLE stocks → ALTER TABLE raw_stocks
Pattern 3: REFERENCES stocks → REFERENCES raw_stocks
Pattern 4: ON stock_prices → ON raw_stock_prices
```

### For Shell Scripts
```
Pattern 1: FROM stocks → FROM raw_stocks
Pattern 2: FROM stock_prices → FROM raw_stock_prices
```

## Foreign Key Dependencies

**Must update together:**
1. `raw_stock_splits` references `raw_stocks`
2. `raw_stock_prices_hourly` references `raw_stocks`

**Constraint names to verify:**
- `fk_splits_symbol` (stock_splits → stocks)
- `fk_hourly_symbol` (stock_prices_hourly → stocks)

## Critical Code Sections

### supabase_helpers.py - Upsert Logic (Lines 417-432)
```python
# UPDATE THESE TABLE NAME CHECKS:
if table == 'raw_stock_prices':  # was 'stock_prices'
elif table == 'raw_stock_prices_hourly':  # was 'stock_prices_hourly'
elif table == 'raw_dividend_history':  # was 'dividend_history'
elif table == 'raw_stocks':  # was 'stocks'
elif table == 'raw_stocks_excluded':  # was 'stocks_excluded'
```

### incremental_processor.py - Direct Table References (Lines 37, 69)
```python
# Line 37: supabase_select('raw_stock_prices', ...)
# Line 69: supabase_select('raw_dividend_history', ...)
```

## Migration Strategy

### Step 1: Create Migration File
Create: `migrations/007_rename_tables_raw_prefix.sql`

### Step 2: Test Migration in Development
```bash
# Apply migration to dev database
# Run all tests
# Verify data integrity
```

### Step 3: Update Code (Priority Order)
1. supabase_helpers.py
2. All migrations (update references)
3. Processors
4. Scripts
5. Archive code
6. Tests/Debug
7. Documentation

### Step 4: Verify & Deploy
```bash
# Test with dev database
# Deploy code changes
# Apply production migration
# Monitor for errors
```

## Impact Summary

| Category | Count | Estimated Time |
|----------|-------|-----------------|
| SQL/Migration files | 15 | 1-2 hours |
| Python files (critical) | 5 | 2-3 hours |
| Python files (medium) | 20+ | 3-4 hours |
| Shell/Scripts | 3-5 | 1 hour |
| Documentation | 20+ | 1-2 hours |
| Testing | N/A | 2-3 hours |
| **TOTAL** | **60+** | **10-15 hours** |

## Rollback Procedure

If issues occur:
1. Keep reverse migration script ready
2. Have database backup available
3. Revert code changes if needed
4. Run reverse migration

---

For complete details, see: `TABLE_RENAMING_ANALYSIS.md`
