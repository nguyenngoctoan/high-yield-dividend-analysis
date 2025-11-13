# SQL Migration Deployment Instructions

## Quick Start

The bulk fetch optimization requires deploying a SQL function to your Supabase database. This is a **one-time setup** that will dramatically improve performance.

## Option 1: Supabase Dashboard (Recommended)

1. Log into your Supabase Dashboard
2. Navigate to **SQL Editor** (left sidebar)
3. Click **New Query**
4. Copy and paste the contents of `create_bulk_latest_dates_function.sql`
5. Click **Run** or press `Ctrl+Enter`
6. Verify success (should see "Success. No rows returned")

## Option 2: Using psql Command Line

If you have the database connection string:

```bash
# Set your database URL
export DATABASE_URL="postgresql://user:password@host:port/database"

# Deploy the migration
psql $DATABASE_URL < create_bulk_latest_dates_function.sql

# Verify deployment
psql $DATABASE_URL -c "SELECT * FROM get_latest_dates_by_symbol('raw_stock_prices', 'date') LIMIT 5;"
```

## Option 3: Using Supabase CLI

If you have Supabase CLI installed:

```bash
# Link your project
supabase link --project-ref your-project-ref

# Run migration
supabase db push create_bulk_latest_dates_function.sql

# Or use db execute
cat create_bulk_latest_dates_function.sql | supabase db execute
```

## Verification

After deployment, test that the function works:

```python
python3 << 'EOF'
from supabase_helpers import get_supabase_client

try:
    supabase = get_supabase_client()
    result = supabase.rpc('get_latest_dates_by_symbol', {
        'table_name': 'raw_stock_prices',
        'date_col': 'date'
    }).limit(5).execute()

    print("✅ Function is working!")
    print(f"Sample results: {len(result.data)} symbols")
    for row in result.data[:3]:
        print(f"  {row['symbol']}: {row['latest_date']}")

except Exception as e:
    print(f"❌ Function not deployed or error: {e}")
    print("Please deploy the SQL migration first.")
EOF
```

Expected output:
```
✅ Function is working!
Sample results: 5 symbols
  AAPL: 2025-11-11
  MSFT: 2025-11-11
  GOOGL: 2025-11-11
```

## What This Migration Does

1. **Creates SQL Function**: `get_latest_dates_by_symbol(table_name, date_col)`
   - Bulk fetches latest dates for all symbols in one query
   - Replaces ~24,000 individual queries with 1 efficient query
   - Saves 5-10 minutes per daily update run

2. **Creates Indexes**:
   - `idx_raw_stock_prices_symbol_date` on `raw_stock_prices(symbol, date DESC)`
   - `idx_raw_dividends_symbol_exdate` on `raw_dividends(symbol, ex_date DESC)`
   - Improves query performance

3. **Grants Permissions**:
   - `authenticated` and `anon` roles can execute the function

## Performance Impact

**Before Migration:**
- 24,842 individual queries to get latest dates
- ~8 minutes per daily update run
- Significant database load

**After Migration:**
- 1 bulk query using PostgreSQL aggregation
- <1 second per daily update run
- Minimal database load
- **Time Saved: ~8 minutes per run**

## Troubleshooting

### Error: "Function does not exist"

**Cause:** Migration not deployed yet

**Solution:** Follow deployment instructions above

### Error: "Permission denied"

**Cause:** Insufficient database permissions

**Solution:**
- Use Supabase Dashboard (automatically uses service role)
- Or connect with superuser/owner role

### Error: "Table does not exist"

**Cause:** Using wrong table names

**Solution:** Verify table names match your schema:
```sql
-- Check table names
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE '%stock%';
```

### Function works but returns no data

**Cause:** Tables might be empty or using different column names

**Solution:**
```sql
-- Check if tables have data
SELECT COUNT(*) FROM raw_stock_prices;
SELECT COUNT(*) FROM raw_dividends;

-- Check column names
SELECT column_name FROM information_schema.columns
WHERE table_name = 'raw_stock_prices';
```

## Rollback (if needed)

If you need to remove the function:

```sql
DROP FUNCTION IF EXISTS get_latest_dates_by_symbol(text, text);
```

The optimization will gracefully fall back to individual queries if the function is not available.

---

*Note: This is a one-time deployment. The function will persist across daily update runs.*
