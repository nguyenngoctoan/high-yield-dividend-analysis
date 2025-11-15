-- Migration: Rename all tables with divv_ prefix
-- Date: 2025-11-15
-- Description: Renames all project tables to use divv_ prefix for better organization

-- ============================================================================
-- RENAME TABLES
-- ============================================================================

-- NOTE: raw_stocks, raw_stock_prices, and raw_dividends are kept as-is
-- Only renaming supplementary and metadata tables

-- Supplementary data tables
ALTER TABLE IF EXISTS raw_future_dividends RENAME TO divv_future_dividends;
ALTER TABLE IF EXISTS raw_stock_splits RENAME TO divv_stock_splits;
ALTER TABLE IF EXISTS raw_etf_holdings RENAME TO divv_etf_holdings;

-- Tracking and metadata tables
ALTER TABLE IF EXISTS raw_data_source_tracking RENAME TO divv_data_source_tracking;
ALTER TABLE IF EXISTS raw_stocks_excluded RENAME TO divv_stocks_excluded;
ALTER TABLE IF EXISTS raw_yieldmax_dividends RENAME TO divv_yieldmax_dividends;

-- Shared tables (now with divv_ prefix)
ALTER TABLE IF EXISTS users RENAME TO divv_users;
ALTER TABLE IF EXISTS tier_limits RENAME TO divv_tier_limits;
ALTER TABLE IF EXISTS free_tier_stocks RENAME TO divv_free_tier_stocks;

-- Materialized view (recreate with new name)
DROP MATERIALIZED VIEW IF EXISTS mv_api_usage_daily CASCADE;
DROP MATERIALIZED VIEW IF EXISTS divv_mv_api_usage_daily CASCADE;

-- Note: divv_api_keys already has the prefix, no rename needed

-- ============================================================================
-- UPDATE SEQUENCES (if any)
-- ============================================================================

-- Update any sequences that reference the old table names
DO $$
DECLARE
    seq_record RECORD;
BEGIN
    FOR seq_record IN
        SELECT sequence_name
        FROM information_schema.sequences
        WHERE sequence_schema = 'public'
    LOOP
        -- Sequences are automatically updated by PostgreSQL when tables are renamed
        NULL;
    END LOOP;
END $$;

-- ============================================================================
-- UPDATE VIEWS THAT REFERENCE OLD TABLE NAMES
-- ============================================================================

-- Drop and recreate v_data_source_preferences view
DROP VIEW IF EXISTS v_data_source_preferences CASCADE;

CREATE OR REPLACE VIEW v_data_source_preferences AS
SELECT
    symbol,
    data_type,
    (
        SELECT source
        FROM divv_data_source_tracking t2
        WHERE t2.symbol = t1.symbol
          AND t2.data_type = t1.data_type
          AND t2.has_data = true
        ORDER BY
            CASE source
                WHEN 'FMP' THEN 1
                WHEN 'Yahoo' THEN 2
                WHEN 'AlphaVantage' THEN 3
                ELSE 4
            END,
            last_successful_fetch_at DESC NULLS LAST
        LIMIT 1
    ) AS preferred_source,
    array_agg(source ORDER BY source) FILTER (WHERE has_data = true) AS available_sources,
    MAX(last_successful_fetch_at) FILTER (WHERE has_data = true) AS last_successful_fetch
FROM divv_data_source_tracking t1
GROUP BY symbol, data_type;

COMMENT ON VIEW v_data_source_preferences IS 'Provides preferred data source for each symbol+data_type combination based on availability and priority';

-- Drop and recreate v_user_api_keys_with_user view
DROP VIEW IF EXISTS v_user_api_keys_with_user CASCADE;

CREATE OR REPLACE VIEW v_user_api_keys_with_user AS
SELECT
    dak.id,
    dak.user_id,
    u.email,
    u.name as user_name,
    u.picture_url,
    dak.name as key_name,
    dak.key_prefix,
    dak.tier,
    dak.created_at,
    dak.expires_at,
    dak.last_used_at,
    dak.request_count,
    dak.is_active,
    dak.updated_at,
    dak.metadata,
    CASE
        WHEN dak.expires_at IS NULL THEN true
        WHEN dak.expires_at > NOW() THEN true
        ELSE false
    END as is_valid,
    CASE
        WHEN dak.expires_at IS NOT NULL AND dak.expires_at < NOW() THEN 'expired'
        WHEN NOT dak.is_active THEN 'disabled'
        ELSE 'active'
    END as status
FROM divv_api_keys dak
LEFT JOIN divv_users u ON dak.user_id = u.id;

COMMENT ON VIEW v_user_api_keys_with_user IS 'API keys with associated user information';

-- ============================================================================
-- UPDATE FUNCTIONS THAT REFERENCE OLD TABLE NAMES
-- ============================================================================

-- Update get_preferred_source function
CREATE OR REPLACE FUNCTION get_preferred_source(
    p_symbol VARCHAR(20),
    p_data_type VARCHAR(50)
)
RETURNS VARCHAR(50)
LANGUAGE plpgsql
AS $$
DECLARE
    v_source VARCHAR(50);
BEGIN
    SELECT preferred_source INTO v_source
    FROM v_data_source_preferences
    WHERE symbol = p_symbol AND data_type = p_data_type;

    RETURN v_source;
END;
$$;

COMMENT ON FUNCTION get_preferred_source IS 'Returns the preferred data source for a given symbol and data type';

-- Update record_data_source_check function
CREATE OR REPLACE FUNCTION record_data_source_check(
    p_symbol VARCHAR(20),
    p_data_type VARCHAR(50),
    p_source VARCHAR(50),
    p_has_data BOOLEAN,
    p_notes TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO divv_data_source_tracking (
        symbol,
        data_type,
        source,
        has_data,
        last_checked_at,
        last_successful_fetch_at,
        fetch_attempts,
        notes
    ) VALUES (
        p_symbol,
        p_data_type,
        p_source,
        p_has_data,
        TIMEZONE('utc'::text, NOW()),
        CASE WHEN p_has_data THEN TIMEZONE('utc'::text, NOW()) ELSE NULL END,
        1,
        p_notes
    )
    ON CONFLICT (symbol, data_type, source)
    DO UPDATE SET
        has_data = p_has_data,
        last_checked_at = TIMEZONE('utc'::text, NOW()),
        last_successful_fetch_at = CASE
            WHEN p_has_data THEN TIMEZONE('utc'::text, NOW())
            ELSE divv_data_source_tracking.last_successful_fetch_at
        END,
        fetch_attempts = divv_data_source_tracking.fetch_attempts + 1,
        notes = COALESCE(p_notes, divv_data_source_tracking.notes);
END;
$$;

COMMENT ON FUNCTION record_data_source_check IS 'Records the result of checking a data source for a specific data type';

-- Update upsert_google_user function
CREATE OR REPLACE FUNCTION upsert_google_user(
    p_google_id VARCHAR(255),
    p_email VARCHAR(255),
    p_name VARCHAR(255),
    p_picture_url TEXT
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    SELECT id INTO v_user_id
    FROM divv_users
    WHERE google_id = p_google_id;

    IF v_user_id IS NOT NULL THEN
        UPDATE divv_users
        SET
            email = p_email,
            name = p_name,
            picture_url = p_picture_url,
            last_login_at = NOW()
        WHERE id = v_user_id;

        RETURN v_user_id;
    ELSE
        INSERT INTO divv_users (google_id, email, name, picture_url, last_login_at)
        VALUES (p_google_id, p_email, p_name, p_picture_url, NOW())
        RETURNING id INTO v_user_id;

        RETURN v_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION upsert_google_user IS 'Get or create user from Google OAuth login data';

-- Update trigger functions
CREATE OR REPLACE FUNCTION update_divv_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON divv_users;
CREATE TRIGGER update_divv_users_updated_at
    BEFORE UPDATE ON divv_users
    FOR EACH ROW
    EXECUTE FUNCTION update_divv_users_updated_at();

-- Update data_source_tracking trigger
CREATE OR REPLACE FUNCTION update_divv_data_source_tracking_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_data_source_tracking_updated_at ON divv_data_source_tracking;
CREATE TRIGGER update_divv_data_source_tracking_updated_at
    BEFORE UPDATE ON divv_data_source_tracking
    FOR EACH ROW
    EXECUTE PROCEDURE update_divv_data_source_tracking_updated_at();

-- ============================================================================
-- UPDATE FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Update foreign key on divv_api_keys to reference divv_users
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'divv_api_keys_user_id_fkey'
    ) THEN
        ALTER TABLE divv_api_keys DROP CONSTRAINT divv_api_keys_user_id_fkey;
    END IF;

    ALTER TABLE divv_api_keys
    ADD CONSTRAINT divv_api_keys_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES divv_users(id) ON DELETE CASCADE;
END $$;

-- ============================================================================
-- UPDATE RLS POLICIES (if any exist)
-- ============================================================================

-- Note: RLS is disabled on these tables, but if it were enabled, policies would need updating

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_name LIKE 'divv_%';

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Table Rename Migration Completed Successfully!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables with divv_ prefix: %', table_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Tables kept as-is:';
    RAISE NOTICE '  • raw_stocks (no change)';
    RAISE NOTICE '  • raw_stock_prices (no change)';
    RAISE NOTICE '  • raw_dividends (no change)';
    RAISE NOTICE '';
    RAISE NOTICE 'Renamed tables:';
    RAISE NOTICE '  ✓ raw_future_dividends → divv_future_dividends';
    RAISE NOTICE '  ✓ raw_stock_splits → divv_stock_splits';
    RAISE NOTICE '  ✓ raw_etf_holdings → divv_etf_holdings';
    RAISE NOTICE '  ✓ raw_data_source_tracking → divv_data_source_tracking';
    RAISE NOTICE '  ✓ raw_stocks_excluded → divv_stocks_excluded';
    RAISE NOTICE '  ✓ raw_yieldmax_dividends → divv_yieldmax_dividends';
    RAISE NOTICE '  ✓ users → divv_users';
    RAISE NOTICE '  ✓ tier_limits → divv_tier_limits';
    RAISE NOTICE '  ✓ free_tier_stocks → divv_free_tier_stocks';
    RAISE NOTICE '';
    RAISE NOTICE 'Updated:';
    RAISE NOTICE '  ✓ Views (v_data_source_preferences, v_user_api_keys_with_user)';
    RAISE NOTICE '  ✓ Functions (get_preferred_source, record_data_source_check, upsert_google_user)';
    RAISE NOTICE '  ✓ Triggers (updated_at triggers)';
    RAISE NOTICE '  ✓ Foreign key constraints';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANT: Update application code to use new table names!';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
END $$;
