# ETF Time Series Architecture

## Overview

The ETF data collection system is designed as an **append-only audit log** that captures daily snapshots of all ETF metrics. This enables trend analysis, historical comparisons, and performance tracking over time.

## Design Principle: Append-Only, Never Delete

### Core Rule
**NEVER DELETE or UPDATE rows in `raw_etfs_*` tables**

The raw tables serve as the single source of truth and audit log. All historical data must be preserved.

```sql
-- ❌ NEVER DO THIS
DELETE FROM raw_etfs_yieldmax WHERE scraped_at < '2025-01-01';
UPDATE raw_etfs_yieldmax SET distribution_rate = 0.05 WHERE ticker = 'TSLY';

-- ✅ DO THIS INSTEAD
-- Only INSERT new data
INSERT INTO raw_etfs_yieldmax (...) VALUES (...);
```

### Why Append-Only?

1. **Audit Trail**: Complete history of all data changes
2. **Time Series Analysis**: Track metrics over days/weeks/months
3. **Reconciliation**: Verify data consistency across snapshots
4. **Debugging**: Identify when values changed and by how much
5. **Compliance**: Immutable record for analysis/reporting

## Database Schema

### Raw Tables (`raw_etfs_*`)

**Pattern**: `raw_etfs_{provider}`

#### Core Columns (All Providers)
```sql
id              BIGSERIAL PRIMARY KEY
ticker          VARCHAR(10) NOT NULL
fund_name       TEXT
url             TEXT
scraped_at      TIMESTAMPTZ NOT NULL (auto-set on insert)
created_at      TIMESTAMPTZ NOT NULL (auto-set on insert)
updated_at      TIMESTAMPTZ (only updated by trigger, never manually)

CONSTRAINT unique_ticker_scraped_at UNIQUE (ticker, scraped_at)
```

#### JSONB Columns (Flexible Storage)
- `fund_overview`: Fund-level metrics
- `fund_details`: Pricing, NAV, premiums
- `distributions`: Dividend/distribution data
- `performance_*`: Historical performance metrics
- `holdings`: Top holdings data

### Time Series Views (Materialized)

**Pattern**: `mv_etf_timeseries_*`

These views extract and normalize JSONB data into typed columns:

1. **mv_etf_timeseries_nav**
   - NAV history (numeric)
   - Price history (numeric)
   - Premium/discount percentage (numeric)

2. **mv_etf_timeseries_distributions**
   - Distribution amounts (numeric)
   - Distribution rates (numeric)
   - Annualized yields (numeric)

3. **mv_etf_timeseries_performance**
   - 1M, 3M, 6M, 1Y, 3Y, 5Y, inception returns (numeric)

4. **mv_etf_timeseries_summary**
   - Combined view with all metrics

## Data Flow

```
Daily Schedule (6 PM EST)
        ↓
run_daily_etf_scrapers.sh
        ↓
[8 Provider Scrapers]
  - YieldMax
  - Roundhill
  - Neos
  - Kurv
  - GraniteShares
  - Defiance
  - GlobalX
  - Purpose
        ↓
INSERT raw_etfs_* (append-only)
        ↓
Materialized Views
(mv_etf_timeseries_*)
        ↓
Analytics/Dashboards
```

## Scheduling

### Daily Scraper Job

**File**: `scripts/automation/run_daily_etf_scrapers.sh`

**Cron Schedule**:
```
0 18 * * 1-5  /path/to/run_daily_etf_scrapers.sh
```
- Time: 6 PM EST (18:00 UTC)
- Days: Monday-Friday only (weekdays, not holidays)
- Frequency: Once per day
- Delay between scrapers: 2 seconds (rate limiting)

**Logging**: `logs/etf_scrapers_cron.log`

**Output**:
- 8 new rows per scrape (one per provider)
- Total per day: 8 × (number of unique ETFs) rows
- Example: 530 rows already (from 1 scrape cycle)

## Key Data Points

### Current Data Distribution

| Provider | ETFs | Snapshots | Dates |
|----------|------|-----------|-------|
| YieldMax | 57 | 57 | 1 |
| Roundhill | 44 | 88 | 2 |
| Neos | 13 | 13 | 1 |
| Kurv | 7 | 7 | 1 |
| GraniteShares | 59 | 59 | 1 |
| Defiance | 60 | 120 | 2 |
| GlobalX | 108 | 108 | 1 |
| Purpose | 79 | 79 | 1 |
| **TOTAL** | **427** | **530** | 2 days |

### Growth Projections

With daily scrapes (5 days/week):

| Period | Rows per ETF | Total Rows | Storage (est.) |
|--------|-------------|-----------|----------------|
| 1 week (5 days) | 5 | 2,135 | ~10 MB |
| 1 month (20 days) | 20 | 8,540 | ~40 MB |
| 3 months (60 days) | 60 | 25,620 | ~120 MB |
| 1 year (250 days) | 250 | 106,750 | ~500 MB |
| 5 years | 1,250 | 533,750 | ~2.5 GB |

**Storage**: JSONB is efficient. 500 rows ≈ 5 MB with proper indexing.

## Indexes

### Raw Tables
```sql
-- Ticker lookup
CREATE INDEX idx_raw_etfs_ticker ON raw_etfs_{provider}(ticker);

-- Time-based queries
CREATE INDEX idx_raw_etfs_scraped_at ON raw_etfs_{provider}(scraped_at DESC);

-- Time series queries
CREATE INDEX idx_raw_etfs_ticker_scraped_at
ON raw_etfs_{provider}(ticker, scraped_at DESC);

-- JSON search (enables json queries)
CREATE INDEX idx_raw_etfs_distributions
ON raw_etfs_{provider} USING GIN (distributions);
```

### Materialized Views
```sql
CREATE INDEX idx_mv_etf_timeseries_nav_ticker_date
ON mv_etf_timeseries_nav(ticker, snapshot_date DESC);

CREATE INDEX idx_mv_etf_timeseries_nav_provider
ON mv_etf_timeseries_nav(provider);
```

## Query Examples

### Example 1: NAV Trend for Single ETF
```sql
SELECT
    snapshot_date,
    nav,
    current_price,
    ROUND(nav - LAG(nav) OVER (ORDER BY snapshot_date), 2) as nav_change
FROM mv_etf_timeseries_nav
WHERE ticker = 'TSLY'
ORDER BY snapshot_date DESC
LIMIT 30;
```

### Example 2: Distribution Rate Changes Over Time
```sql
SELECT
    ticker,
    snapshot_date,
    distribution_rate,
    LAG(distribution_rate) OVER (PARTITION BY ticker ORDER BY snapshot_date) as prev_rate,
    ROUND(distribution_rate - LAG(distribution_rate) OVER (PARTITION BY ticker ORDER BY snapshot_date), 4) as rate_change
FROM mv_etf_timeseries_distributions
WHERE provider = 'yieldmax'
  AND distribution_rate IS NOT NULL
ORDER BY ticker, snapshot_date DESC
LIMIT 100;
```

### Example 3: Performance Comparison Across Providers
```sql
SELECT
    provider,
    ticker,
    snapshot_date,
    perf_1m,
    perf_3m,
    perf_1y,
    RANK() OVER (PARTITION BY snapshot_date ORDER BY perf_1y DESC) as rank_by_1y_perf
FROM mv_etf_timeseries_performance
WHERE snapshot_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY snapshot_date DESC, rank_by_1y_perf;
```

### Example 4: Top Yielding ETFs (Current)
```sql
SELECT DISTINCT ON (ticker)
    ticker,
    fund_name,
    provider,
    distribution_rate,
    annualized_yield,
    snapshot_date
FROM mv_etf_timeseries_distributions
WHERE distribution_rate IS NOT NULL
ORDER BY ticker, snapshot_date DESC
LIMIT 20;
```

### Example 5: ETF with Largest NAV Drift
```sql
WITH nav_changes AS (
    SELECT
        ticker,
        snapshot_date,
        nav,
        LAG(nav) OVER (PARTITION BY ticker ORDER BY snapshot_date) as prev_nav,
        ABS(nav - LAG(nav) OVER (PARTITION BY ticker ORDER BY snapshot_date)) as nav_change
    FROM mv_etf_timeseries_nav
)
SELECT
    ticker,
    snapshot_date,
    nav,
    prev_nav,
    ROUND(nav_change, 2) as abs_change,
    ROUND(100 * nav_change / prev_nav, 2) as pct_change
FROM nav_changes
WHERE nav_change IS NOT NULL
ORDER BY nav_change DESC NULLS LAST
LIMIT 20;
```

## Refresh Strategy

### Materialized Views Refresh

Since materialized views are static snapshots, they should be refreshed daily after scraping:

```bash
# Add to run_daily_etf_scrapers.sh (after all scrapers complete)
PGPASSWORD="$PGPASSWORD" psql -h $PGHOST -p $PGPORT -U postgres -d postgres << EOF
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_etf_timeseries_nav;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_etf_timeseries_distributions;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_etf_timeseries_performance;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_etf_timeseries_summary;
EOF
```

## Data Integrity Rules

### ✅ Allowed Operations

1. **INSERT** new snapshots
   ```sql
   INSERT INTO raw_etfs_yieldmax (ticker, fund_name, ...)
   VALUES ('TSLY', 'YieldMax TSLA...', ...);
   ```

2. **SELECT** for analysis
   ```sql
   SELECT * FROM raw_etfs_yieldmax WHERE ticker = 'TSLY';
   ```

3. **REFRESH** materialized views
   ```sql
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_etf_timeseries_nav;
   ```

### ❌ Prohibited Operations

1. **DELETE** rows (destroys history)
2. **UPDATE** rows (creates ambiguity)
3. **ALTER** table structure (use migrations)
4. **DROP** raw tables (data loss)
5. **TRUNCATE** tables (total data loss)

### Enforcement

**Method 1: Row-Level Security (RLS)**
```sql
-- Allow reads
CREATE POLICY "allow_select_raw_etfs"
ON raw_etfs_yieldmax
FOR SELECT
USING (true);

-- Deny deletes
CREATE POLICY "deny_delete_raw_etfs"
ON raw_etfs_yieldmax
FOR DELETE
USING (false);

-- Deny updates
CREATE POLICY "deny_update_raw_etfs"
ON raw_etfs_yieldmax
FOR UPDATE
USING (false);
```

**Method 2: Application-Level**
- Scrapers use `supabase_upsert()` with unique constraint on (ticker, scraped_at)
- If same data scraped twice, duplicate is ignored (upsert)
- Never triggers a DELETE or UPDATE

## Data Cleanup (Archive, Not Delete)

For data older than retention period, **ARCHIVE instead of DELETE**:

```sql
-- Example: Archive ETF data older than 2 years
CREATE TABLE archive_raw_etfs_yieldmax AS
SELECT * FROM raw_etfs_yieldmax
WHERE scraped_at < CURRENT_DATE - INTERVAL '2 years';

-- THEN delete from main table (after verification)
DELETE FROM raw_etfs_yieldmax
WHERE scraped_at < CURRENT_DATE - INTERVAL '2 years'
  AND id IN (SELECT id FROM archive_raw_etfs_yieldmax);

-- Keep archive for compliance
VACUUM archive_raw_etfs_yieldmax;
```

## Monitoring

### Data Freshness
```sql
SELECT
    'yieldmax' as provider,
    COUNT(DISTINCT ticker) as etf_count,
    MAX(scraped_at)::date as latest_date,
    CURRENT_DATE - MAX(scraped_at)::date as days_since_scrape
FROM raw_etfs_yieldmax
UNION ALL
SELECT 'roundhill', COUNT(DISTINCT ticker), MAX(scraped_at)::date,
    CURRENT_DATE - MAX(scraped_at)::date
FROM raw_etfs_roundhill
-- ... repeat for all providers
ORDER BY provider;
```

### Row Growth
```sql
SELECT
    'yieldmax' as provider,
    COUNT(*) as total_rows,
    COUNT(DISTINCT ticker) as unique_tickers,
    COUNT(DISTINCT DATE(scraped_at)) as unique_dates,
    ROUND(pg_total_relation_size('raw_etfs_yieldmax') / 1024.0 / 1024.0, 2) as size_mb
FROM raw_etfs_yieldmax
UNION ALL
-- ... repeat for all providers
ORDER BY provider;
```

### Scraper Success Rate
```sql
-- Check logs for failed runs
tail -n 100 /Users/toan/dev/high-yield-dividend-analysis/logs/etf_scrapers_cron.log |
grep -E "Success|Failed"
```

## Disaster Recovery

### Backup Strategy
1. **Database backups**: Handled by Supabase (automated daily)
2. **Archive tables**: Keep separate archive tables for compliance
3. **Version control**: Migration files in `supabase/migrations/`

### Restore Procedure (if data is corrupted)
```bash
# Restore from Supabase backup
# Contact Supabase support or use their dashboard

# Or, restore from Git history
git log --all --oneline -- supabase/migrations/ | head -5
# Then re-run the relevant migration
```

## Performance Considerations

### Write Performance
- INSERTS are fast (O(1) on indexed columns)
- ~1000 rows/second typical (with proper indexes)
- 8 providers × 60 seconds delay = acceptable

### Read Performance
- Materialized views are pre-computed (fast)
- Indexes on `(ticker, snapshot_date)` enable range scans
- Typical query: <100ms for 1000s of rows

### Storage Efficiency
- JSONB is binary (compact vs text JSON)
- Indexes add ~30-50% overhead
- 1 year of data: ~500 MB (8 providers, 427 ETFs, 250 snapshots each)

## Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Daily scrapes | 5 days/week (weekdays) | `run_daily_etf_scrapers.sh` |
| View refresh | Daily (after scrapes) | `REFRESH MATERIALIZED VIEW` |
| Backup | Automated | Supabase (built-in) |
| Index maintenance | Weekly | `REINDEX` (optional, auto by Postgres) |
| Archive old data | Annually | Archive 2+ year old data |
| Monitor health | Daily | Check logs and freshness |

## Summary

- **Append-only architecture** ensures data integrity and enables time series analysis
- **Daily snapshots** capture all ETF metrics for trend analysis
- **Materialized views** provide fast access to normalized data
- **Never delete** raw data; archive when needed
- **Indexes** ensure query performance
- **Scheduled runs** keep data fresh automatically
