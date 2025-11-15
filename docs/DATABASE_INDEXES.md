# Database Indexes Documentation

## Overview

This document describes all database indexes in the High Yield Dividend Analysis platform. Proper indexing is critical for query performance, especially as data volume grows.

## Index Strategy

Our indexing strategy follows these principles:

1. **Primary Keys**: All tables have unique indexes on primary keys
2. **Foreign Keys**: All foreign key columns are indexed for efficient joins
3. **Common Filters**: Frequently filtered columns (sector, exchange, type) are indexed
4. **Sorting Columns**: Columns used for ORDER BY have DESC indexes
5. **Partial Indexes**: Indexes with WHERE clauses for selective filtering (e.g., only non-null values)
6. **Composite Indexes**: Multi-column indexes for common query patterns
7. **Covering Indexes**: Indexes with INCLUDE columns to avoid table lookups

## Indexes by Table

### raw_stocks

Core stock information table with ~20,000 symbols.

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_raw_stocks_pkey` | symbol | UNIQUE | Primary key lookup |
| `idx_raw_stocks_exchange` | exchange | PARTIAL | Filter by exchange (NYSE, NASDAQ, etc.) |
| `idx_raw_stocks_type` | type | PARTIAL | Filter by type (stock, etf) |
| `idx_raw_stocks_sector` | sector | PARTIAL | Filter by sector |
| `idx_raw_stocks_industry` | industry | PARTIAL | Filter by industry |
| `idx_raw_stocks_dividend_yield` | dividend_yield DESC | PARTIAL | Sort by dividend yield (high to low) |
| `idx_raw_stocks_has_dividends` | dividend_yield | PARTIAL | Filter dividend-paying stocks |
| `idx_raw_stocks_market_cap` | market_cap DESC | PARTIAL | Sort by market cap |
| `idx_raw_stocks_price` | price DESC | PARTIAL | Sort by price |
| `idx_raw_stocks_exchange_type_yield` | exchange, type, dividend_yield DESC | COMPOSITE, PARTIAL | Common filter combination |
| `idx_raw_stocks_sector_yield` | sector, dividend_yield DESC | COMPOSITE, PARTIAL | Sector + yield queries |
| `idx_raw_stocks_updated_at` | updated_at DESC | INDEX | Cache invalidation |
| `idx_raw_stocks_pe_ratio` | pe_ratio | PARTIAL | P/E ratio filtering |
| `idx_raw_stocks_volume` | volume DESC | PARTIAL | Volume-based queries |

**Common Query Patterns**:
```sql
-- High dividend yield stocks in a sector
SELECT * FROM raw_stocks
WHERE sector = 'Technology'
  AND dividend_yield > 3.0
ORDER BY dividend_yield DESC
LIMIT 20;
-- Uses: idx_raw_stocks_sector_yield

-- Dividend-paying stocks on NYSE
SELECT * FROM raw_stocks
WHERE exchange = 'NYSE'
  AND type = 'stock'
  AND dividend_yield > 0
ORDER BY dividend_yield DESC;
-- Uses: idx_raw_stocks_exchange_type_yield
```

### raw_stock_prices

Historical price data (time-series). This is the largest table with millions of rows.

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_raw_stock_prices_symbol_date` | symbol, date DESC | UNIQUE | Primary composite key |
| `idx_raw_stock_prices_date` | date DESC | INDEX | Date range queries |
| `idx_raw_stock_prices_symbol` | symbol | INDEX | Symbol-specific queries |
| `idx_raw_stock_prices_volume` | volume DESC | PARTIAL | Volume filtering |
| `idx_raw_stock_prices_change_percent` | change_percent DESC | PARTIAL | Price change analytics |
| `idx_raw_stock_prices_recent` | symbol, date DESC | COVERING | Recent prices with included columns |

**Common Query Patterns**:
```sql
-- Get latest prices for a symbol
SELECT * FROM raw_stock_prices
WHERE symbol = 'AAPL'
ORDER BY date DESC
LIMIT 30;
-- Uses: idx_raw_stock_prices_symbol_date

-- Price history in date range
SELECT * FROM raw_stock_prices
WHERE date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY date DESC;
-- Uses: idx_raw_stock_prices_date

-- Biggest movers (change_percent)
SELECT symbol, close, change_percent
FROM raw_stock_prices
WHERE date = '2024-11-15'
  AND change_percent IS NOT NULL
ORDER BY ABS(change_percent) DESC
LIMIT 50;
-- Uses: idx_raw_stock_prices_change_percent
```

### raw_dividends

Dividend payment history.

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_raw_dividends_symbol_ex_date` | symbol, ex_date DESC | UNIQUE | Primary composite key |
| `idx_raw_dividends_ex_date` | ex_date DESC | INDEX | Ex-date filtering |
| `idx_raw_dividends_payment_date` | payment_date DESC | PARTIAL | Payment date queries |
| `idx_raw_dividends_symbol` | symbol | INDEX | Symbol dividends |
| `idx_raw_dividends_amount` | amount DESC | PARTIAL | Dividend amount sorting |
| `idx_raw_dividends_declaration_date` | declaration_date DESC | PARTIAL | Declaration date queries |
| `idx_raw_dividends_recent` | symbol, ex_date DESC | COVERING | Recent dividends with included columns |

**Common Query Patterns**:
```sql
-- Get dividend history for a symbol
SELECT * FROM raw_dividends
WHERE symbol = 'AAPL'
ORDER BY ex_date DESC
LIMIT 20;
-- Uses: idx_raw_dividends_symbol_ex_date

-- Upcoming dividend payments
SELECT * FROM raw_dividends
WHERE payment_date > NOW()
ORDER BY payment_date ASC
LIMIT 100;
-- Uses: idx_raw_dividends_payment_date

-- High dividend amounts
SELECT symbol, amount, ex_date
FROM raw_dividends
WHERE ex_date > '2024-01-01'
  AND amount > 1.0
ORDER BY amount DESC;
-- Uses: idx_raw_dividends_amount
```

### raw_stocks_excluded

Excluded/invalid symbols.

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_raw_stocks_excluded_pkey` | symbol | UNIQUE | Primary key |
| `idx_raw_stocks_excluded_excluded_at` | excluded_at DESC | INDEX | Exclusion date |
| `idx_raw_stocks_excluded_reason` | reason | PARTIAL | Exclusion reason |
| `idx_raw_stocks_excluded_source` | source | PARTIAL | Data source tracking |

### users

OAuth authenticated users.

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_users_google_id` | google_id | UNIQUE | Google OAuth ID lookup |
| `idx_users_email` | email | UNIQUE | Email lookup |
| `idx_users_tier` | tier | INDEX | Tier-based filtering |
| `idx_users_created_at` | created_at DESC | INDEX | User registration tracking |
| `idx_users_is_active` | is_active | PARTIAL | Active users filter |
| `idx_users_last_login_at` | last_login_at DESC | INDEX | Login tracking |

### divv_api_keys

API key management.

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_divv_api_keys_key_hash` | key_hash | UNIQUE | Fast API key validation |
| `idx_divv_api_keys_expires_at` | expires_at | PARTIAL | Expiration checking |
| `idx_divv_api_keys_created_at` | created_at DESC | INDEX | Key creation tracking |
| `idx_divv_api_keys_user_id` | user_id | INDEX | User's keys lookup |
| `idx_divv_api_keys_is_active` | is_active | PARTIAL | Active keys filter |
| `idx_divv_api_keys_tier` | tier | PARTIAL | Tier-based filtering |
| `idx_divv_api_keys_last_used_at` | last_used_at DESC | INDEX | Usage tracking |
| `idx_divv_api_keys_request_count` | request_count DESC | INDEX | Analytics |
| `idx_divv_api_keys_active_valid` | is_active, expires_at | COMPOSITE, PARTIAL | Valid key lookup |

**Critical for Performance**:
```sql
-- API key validation (runs on EVERY request)
SELECT * FROM divv_api_keys
WHERE key_hash = 'sha256_hash_here'
  AND is_active = true
  AND (expires_at IS NULL OR expires_at > NOW());
-- Uses: idx_divv_api_keys_active_valid
```

### raw_data_source_tracking

Tracks which data sources have data for each symbol.

| Index Name | Columns | Type | Purpose |
|------------|---------|------|---------|
| `idx_data_source_tracking_symbol` | symbol | INDEX | Symbol lookup |
| `idx_data_source_tracking_data_type` | data_type | INDEX | Data type filtering |
| `idx_data_source_tracking_has_data` | has_data | PARTIAL | Sources with data |
| `idx_data_source_tracking_last_checked` | last_checked_at | INDEX | Staleness detection |
| `idx_data_source_tracking_lookup` | symbol, data_type, has_data, source | COMPOSITE | Preferred source lookup |
| `idx_data_source_tracking_last_successful` | last_successful_fetch_at DESC | INDEX | Success tracking |

## Index Maintenance

### Monitoring Index Usage

Check which indexes are being used:

```sql
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Identifying Unused Indexes

Find indexes that are never used:

```sql
SELECT
    schemaname,
    tablename,
    indexname
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey';
```

### Table and Index Sizes

Check storage usage:

```sql
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) -
                   pg_relation_size(schemaname||'.'||tablename)) AS indexes_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Performance Impact

### Before Indexes
- Symbol lookup: O(n) table scan - ~500ms for 20,000 rows
- Dividend filtering: Full table scan - 1-2 seconds
- API key validation: Sequential scan - 100-500ms per request

### After Indexes
- Symbol lookup: O(log n) B-tree lookup - <1ms
- Dividend filtering: Index scan - <10ms
- API key validation: Hash index lookup - <1ms

### Expected Improvements

| Query Type | Before | After | Improvement |
|------------|--------|-------|-------------|
| Single stock lookup | 500ms | <1ms | 500x faster |
| Dividend yield filter | 2000ms | 10ms | 200x faster |
| API key validation | 200ms | <1ms | 200x faster |
| Date range queries | 3000ms | 50ms | 60x faster |
| Sector filtering | 1500ms | 20ms | 75x faster |

## Best Practices

1. **Use Partial Indexes**: Include WHERE clauses to reduce index size
   ```sql
   -- Good: Only indexes non-null dividends
   CREATE INDEX idx_stocks_dividend_yield
   ON raw_stocks(dividend_yield DESC)
   WHERE dividend_yield > 0;

   -- Bad: Indexes all rows including NULLs
   CREATE INDEX idx_stocks_dividend_yield
   ON raw_stocks(dividend_yield DESC);
   ```

2. **Composite Index Column Order**: Put equality filters first, ranges last
   ```sql
   -- Good: exchange (equality) before yield (range)
   CREATE INDEX idx_stocks_exchange_yield
   ON raw_stocks(exchange, dividend_yield DESC);

   -- Bad: range before equality
   CREATE INDEX idx_stocks_yield_exchange
   ON raw_stocks(dividend_yield DESC, exchange);
   ```

3. **Covering Indexes**: Include frequently accessed columns
   ```sql
   -- Avoids table lookup for price queries
   CREATE INDEX idx_prices_recent
   ON raw_stock_prices(symbol, date DESC)
   INCLUDE (close, open, high, low, volume);
   ```

4. **DESC for Time Series**: Use DESC for descending date queries
   ```sql
   -- Optimized for "ORDER BY date DESC"
   CREATE INDEX idx_prices_date
   ON raw_stock_prices(date DESC);
   ```

## Migration

To apply all indexes:

```bash
# 1. Copy migration to clipboard
cat supabase/migrations/20251115_add_comprehensive_indexes.sql | pbcopy

# 2. Open Supabase SQL Editor
./scripts/open_supabase_sql.sh

# 3. Paste and run the migration

# 4. Verify indexes
python3 scripts/verify_indexes.py
```

## Troubleshooting

### Slow Queries After Indexing

If queries are still slow after adding indexes:

1. Check if index is being used:
   ```sql
   EXPLAIN ANALYZE
   SELECT * FROM raw_stocks
   WHERE dividend_yield > 5.0
   ORDER BY dividend_yield DESC;
   ```

2. Update table statistics:
   ```sql
   ANALYZE raw_stocks;
   ```

3. Rebuild indexes if fragmented:
   ```sql
   REINDEX INDEX idx_raw_stocks_dividend_yield;
   ```

### Index Bloat

Monitor and rebuild bloated indexes:

```sql
-- Check index bloat
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Additional Resources

- [PostgreSQL Index Documentation](https://www.postgresql.org/docs/current/indexes.html)
- [Supabase Database Optimization](https://supabase.com/docs/guides/database/performance)
- [Query Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)

## Files

- Migration: `supabase/migrations/20251115_add_comprehensive_indexes.sql`
- Verification: `scripts/verify_indexes.py`
- Analysis: `scripts/check_indexes.py`
