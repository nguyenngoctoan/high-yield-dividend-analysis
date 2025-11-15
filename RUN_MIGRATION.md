# Running the Pricing Tiers Migration

## Option 1: Supabase SQL Editor (Recommended)

1. **Open Supabase SQL Editor:**
   - Go to: https://app.supabase.com/project/YOUR_PROJECT_ID/sql
   - Or navigate to your project > SQL Editor

2. **Copy the migration SQL:**
   ```bash
   cat migrations/update_pricing_tiers_v2.sql | pbcopy
   ```

3. **Paste and run in SQL Editor:**
   - Click "New Query"
   - Paste the SQL (Cmd+V)
   - Click "Run" or press Cmd+Enter

## Option 2: Using psql (If you have direct database access)

```bash
# Get your database connection string from Supabase dashboard
# Settings > Database > Connection string

psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres" \
  -f migrations/update_pricing_tiers_v2.sql
```

## Option 3: Using Supabase CLI (After login)

```bash
# Login to Supabase first
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Push the migration
supabase db push
```

## What This Migration Does

1. **Updates `divv_api_keys` table:**
   - Adds `tier` column (free, starter, premium, professional, enterprise)
   - Adds `user_id` column
   - Adds usage tracking columns (monthly_usage, minute_usage, etc.)

2. **Creates `tier_limits` table:**
   - Stores rate limits for each tier
   - Monthly call limits
   - Per-minute limits with burst support
   - Stock coverage definitions
   - Feature flags

3. **Creates `free_tier_stocks` table:**
   - Sample dataset for free tier users (~150 stocks)

4. **Creates helper functions:**
   - `increment_key_usage()` - Atomic usage counter

5. **Populates initial data:**
   - Tier limits for all 5 tiers
   - Free tier stock list

## Verify Migration Success

After running the migration, verify with:

```sql
-- Check tier_limits table
SELECT tier, monthly_call_limit, calls_per_minute FROM tier_limits ORDER BY monthly_call_limit;

-- Check if columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'divv_api_keys'
AND column_name IN ('tier', 'monthly_usage', 'minute_usage');

-- Count free tier stocks
SELECT COUNT(*) FROM free_tier_stocks;
```

Expected results:
- 5 tiers in tier_limits (free, starter, premium, professional, enterprise)
- New columns in divv_api_keys table
- ~150 stocks in free_tier_stocks

## Troubleshooting

### Error: "table already exists"
The migration is idempotent - it uses `IF NOT EXISTS` and `DO $$` blocks to avoid errors on re-run.

### Error: "permission denied"
Ensure you're running as postgres user or have proper permissions.

### Migration file location
```bash
migrations/update_pricing_tiers_v2.sql
supabase/migrations/20251114_update_pricing_tiers_v2.sql
```

## Next Steps After Migration

1. Restart the API server to load rate limiting middleware
2. Test rate limiting with the test suite:
   ```bash
   python3 tests/test_rate_limits_simple.py
   ```
3. Create a test API key through OAuth login
4. Verify rate limit headers appear in API responses
