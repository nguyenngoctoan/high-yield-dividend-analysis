# Mart-Only Remote Architecture

## Overview

This document describes the Pure Mart-Only Remote Architecture for the dividend tracker project. This architecture separates data processing (local) from data serving (remote) to optimize costs and performance.

## Architecture Principles

### Local Database (Development & Processing)
- **Purpose**: Complete data processing pipeline
- **Location**: Local Supabase instance (127.0.0.1:54322)
- **Size**: ~10GB (full dataset)
- **Contains**:
  - ALL raw tables (`raw_stocks`, `raw_stock_prices`, `raw_dividends`, etc.)
  - ALL staging tables (`stg_*`)
  - ALL intermediate tables
  - ALL mart tables (`mart_*`)
  - Historical data (20M+ price records, 686K dividend records)

### Remote Database (Production API)
- **Purpose**: Lightweight API data store for Next.js frontend
- **Location**: Supabase Cloud (uykxgbrzpfswbdxtyzlv.supabase.co)
- **Target Size**: 50-100MB (mart tables only)
- **Contains**:
  - ONLY mart/presentation tables
  - NO raw data
  - NO staging data
  - NO intermediate data

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         LOCAL ENVIRONMENT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Data Ingestion (Python Scripts)                             │
│     ├─ update_stock_v2.py (FMP API, Alpha Vantage)              │
│     ├─ scrape_yieldmax.py                                        │
│     ├─ scrape_cboe_dividends.py                                  │
│     ├─ scrape_nasdaq_dividends.py                                │
│     ├─ scrape_nyse_dividends.py                                  │
│     └─ scrape_snowball_dividends.py                              │
│           ↓                                                       │
│  2. Raw Tables (Local PostgreSQL)                                │
│     ├─ raw_stocks (24,842 rows, 219 MB)                         │
│     ├─ raw_stock_prices (20,254,716 rows, ~7.5 GB)              │
│     ├─ raw_dividends (686,000+ rows, ~250 MB)                   │
│     ├─ raw_dividends_cboe, nasdaq, nyse, snowball, yieldmax     │
│     └─ raw_future_dividends, raw_holdings_history, etc.         │
│           ↓                                                       │
│  3. DBT Transformations (Local - Future)                         │
│     ├─ Staging models (stg_*)                                    │
│     ├─ Intermediate models (int_*)                               │
│     └─ Mart models (mart_*)                                      │
│           ↓                                                       │
│  4. Mart Tables (Local PostgreSQL)                               │
│     ├─ mart_stocks_summary                                       │
│     ├─ mart_dividend_calendar                                    │
│     ├─ mart_etf_holdings                                         │
│     ├─ mart_portfolio_performance                                │
│     └─ mart_screener_results                                     │
│                                                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Sync Script (Daily)
                            │ scripts/sync_marts_to_remote.sh
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                        REMOTE ENVIRONMENT                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Mart Tables ONLY (Supabase Cloud)                              │
│     ├─ mart_stocks_summary (~25K rows, ~30 MB)                  │
│     ├─ mart_dividend_calendar (~50K rows, ~15 MB)               │
│     ├─ mart_etf_holdings (~10K rows, ~5 MB)                     │
│     ├─ mart_portfolio_performance (~100 rows, <1 MB)            │
│     └─ mart_screener_results (~5K rows, ~5 MB)                  │
│           ↓                                                       │
│  Next.js Frontend (Vercel)                                       │
│     └─ Queries ONLY mart tables via Supabase API                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Frontend-Facing Mart Tables

### Current Mart Tables
Based on the current database structure:

1. **mart_portfolio_current_holdings**
   - Purpose: Current portfolio holdings for users
   - Estimated size: <1 MB
   - Status: Empty (needs population logic)

2. **mart_portfolio_list_with_holdings**
   - Purpose: Portfolio list with aggregated holdings data
   - Estimated size: <1 MB
   - Status: Empty (needs population logic)

3. **mart_portfolio_performance_metrics**
   - Purpose: Performance metrics and analytics
   - Estimated size: <1 MB
   - Status: Empty (needs population logic)

### Proposed Additional Marts

4. **mart_stocks_summary** (TO BE CREATED)
   - Purpose: Aggregated stock data for screener and search
   - Source: `raw_stocks` + latest price from `raw_stock_prices`
   - Estimated rows: ~25,000
   - Estimated size: ~30 MB
   - Fields: symbol, name, price, dividend_yield, sector, market_cap, etc.

5. **mart_dividend_calendar** (TO BE CREATED)
   - Purpose: Upcoming dividend payments for calendar view
   - Source: `raw_dividends` + `raw_future_dividends`
   - Estimated rows: ~50,000 (rolling 12 months)
   - Estimated size: ~15 MB
   - Fields: symbol, ex_date, payment_date, amount, frequency

6. **mart_etf_holdings** (TO BE CREATED)
   - Purpose: ETF holdings and composition
   - Source: `raw_holdings_history` (latest snapshot)
   - Estimated rows: ~10,000
   - Estimated size: ~5 MB
   - Fields: etf_symbol, holding_symbol, weight, shares, value

**Total Estimated Remote Database Size: 50-60 MB**

## Implementation Plan

### Phase 1: Create Mart Tables (Local)
```sql
-- Example: mart_stocks_summary
CREATE TABLE mart_stocks_summary AS
SELECT
  s.symbol,
  s.name,
  s.price,
  s.dividend_yield,
  s.sector,
  s.market_cap,
  s.currency,
  s.exchange,
  s.last_updated,
  -- Add latest price data
  (SELECT price FROM raw_stock_prices
   WHERE symbol = s.symbol
   ORDER BY date DESC LIMIT 1) as latest_price,
  (SELECT date FROM raw_stock_prices
   WHERE symbol = s.symbol
   ORDER BY date DESC LIMIT 1) as latest_price_date
FROM raw_stocks s
WHERE s.price IS NOT NULL;

CREATE INDEX idx_mart_stocks_symbol ON mart_stocks_summary(symbol);
CREATE INDEX idx_mart_stocks_yield ON mart_stocks_summary(dividend_yield DESC);
```

### Phase 2: Build Sync Infrastructure
Create `scripts/sync_marts_to_remote.sh` to:
1. Export each mart table from local database
2. Truncate corresponding table in remote database
3. Load new data to remote database
4. Verify row counts match

### Phase 3: Clean Remote Database
Remove all non-mart tables from remote:
- raw_stock_prices (20.2M rows, ~7.5 GB) ← **REMOVE**
- raw_dividends (686K rows, ~250 MB) ← **REMOVE**
- raw_stocks (24,842 rows, 219 MB) ← **REMOVE**
- All other raw_* tables ← **REMOVE**

### Phase 4: Update Frontend
Point Next.js queries to remote mart tables only

### Phase 5: Automate Sync
Add to daily_update_v2.sh:
```bash
# At end of daily update
echo "Syncing mart tables to remote..."
bash scripts/sync_marts_to_remote.sh
```

## Environment Configuration

### .env File Structure
```bash
# Local Supabase (all operations)
SUPABASE_URL_LOCAL=http://127.0.0.1:54321
SUPABASE_KEY_LOCAL=local_service_role_key

# Remote Supabase (marts only)
SUPABASE_URL_REMOTE=https://uykxgbrzpfswbdxtyzlv.supabase.co
SUPABASE_KEY_REMOTE=remote_service_role_key

# Default to local for scripts
SUPABASE_URL=${SUPABASE_URL_LOCAL}
SUPABASE_KEY=${SUPABASE_KEY_LOCAL}
```

### Script Updates
All data ingestion scripts continue using LOCAL database:
- update_stock_v2.py → LOCAL
- scrape_*.py → LOCAL
- daily_update_v2.sh → LOCAL

Only the sync script writes to REMOTE.

## Benefits

1. **Cost Savings**: Remote database shrinks from 10GB to 50-100MB
   - Supabase free tier: 500MB database (plenty of headroom)
   - Reduced bandwidth costs
   - Faster backups

2. **Performance**:
   - Frontend queries hit small, optimized mart tables
   - No complex joins or aggregations in production
   - Faster API response times

3. **Security**:
   - Raw data never exposed to internet
   - Only presentation layer accessible via API
   - Reduced attack surface

4. **Flexibility**:
   - Iterate on raw data processing without affecting production
   - Test DBT models locally before syncing
   - Easy rollback (just re-sync previous version)

5. **Simplicity**:
   - Clear separation of concerns
   - Local = development, Remote = production
   - One-way sync (no conflicts)

## Maintenance

### Daily Operations
1. Run `daily_update_v2.sh` (LOCAL)
2. Data ingestion scripts populate raw tables (LOCAL)
3. DBT models rebuild marts (LOCAL)
4. Sync script pushes marts to remote (REMOTE)

### Weekly Operations
- Backup local database (10GB)
- Verify remote database size (<100MB)
- Check sync logs for errors

### Monthly Operations
- Review mart table definitions
- Optimize mart queries based on frontend usage
- Add/remove marts as needed

## Monitoring

### Key Metrics
- Local database size: ~10GB
- Remote database size: <100MB
- Sync duration: <5 minutes
- Remote API response time: <200ms
- Data freshness: Updated daily

### Alerts
- Sync failures (email notification)
- Remote database size >90MB (warning)
- Local database size >15GB (investigate growth)
- Mart table row count mismatches (error)

## Future Enhancements

1. **Incremental Sync**: Only sync changed rows instead of full truncate/load
2. **Multiple Environments**: Add staging remote database
3. **Real-time Sync**: WebSocket updates for price changes
4. **Mart Versioning**: Track mart schema changes over time
5. **Query Optimization**: Add materialized views for complex aggregations

## Migration Checklist

- [x] Verify local database has all data (20.2M price records)
- [x] Identify mart tables needed for frontend
- [ ] Create mart table SQL definitions
- [ ] Build sync infrastructure script
- [ ] Test sync with sample mart table
- [ ] Clean remote database (remove raw tables)
- [ ] Update Next.js to query marts only
- [ ] Add sync to daily_update_v2.sh
- [ ] Document maintenance procedures
- [ ] Set up monitoring and alerts
