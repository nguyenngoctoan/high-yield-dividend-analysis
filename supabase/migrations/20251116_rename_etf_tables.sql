-- Migration: Rename all raw_*_etf_data tables to raw_etfs_* format
-- Date: November 16, 2025
-- Purpose: Standardize ETF table naming convention
--
-- Tables affected:
-- raw_yieldmax_etf_data      → raw_etfs_yieldmax
-- raw_roundhill_etf_data     → raw_etfs_roundhill
-- raw_neos_etf_data          → raw_etfs_neos
-- raw_kurv_etf_data          → raw_etfs_kurv
-- raw_graniteshares_etf_data → raw_etfs_graniteshares
-- raw_defiance_etf_data      → raw_etfs_defiance
-- raw_globalx_etf_data       → raw_etfs_globalx
-- raw_purpose_etf_data       → raw_etfs_purpose

BEGIN;

-- ============================================================================
-- STEP 1: Drop existing views (they will be recreated with new table names)
-- ============================================================================

DROP VIEW IF EXISTS v_yieldmax_latest;
DROP VIEW IF EXISTS v_roundhill_latest;
DROP VIEW IF EXISTS v_neos_latest;
DROP VIEW IF EXISTS v_kurv_latest;
DROP VIEW IF EXISTS v_graniteshares_latest;
DROP VIEW IF EXISTS v_defiance_latest;
DROP VIEW IF EXISTS v_globalx_latest;
DROP VIEW IF EXISTS v_purpose_latest;

-- ============================================================================
-- STEP 2: Rename all tables
-- ============================================================================

-- YieldMax
ALTER TABLE IF EXISTS raw_yieldmax_etf_data
    RENAME TO raw_etfs_yieldmax;

-- Roundhill
ALTER TABLE IF EXISTS raw_roundhill_etf_data
    RENAME TO raw_etfs_roundhill;

-- Neos
ALTER TABLE IF EXISTS raw_neos_etf_data
    RENAME TO raw_etfs_neos;

-- Kurv
ALTER TABLE IF EXISTS raw_kurv_etf_data
    RENAME TO raw_etfs_kurv;

-- GraniteShares
ALTER TABLE IF EXISTS raw_graniteshares_etf_data
    RENAME TO raw_etfs_graniteshares;

-- Defiance
ALTER TABLE IF EXISTS raw_defiance_etf_data
    RENAME TO raw_etfs_defiance;

-- Global X (Canada)
ALTER TABLE IF EXISTS raw_globalx_etf_data
    RENAME TO raw_etfs_globalx;

-- Purpose
ALTER TABLE IF EXISTS raw_purpose_etf_data
    RENAME TO raw_etfs_purpose;

-- ============================================================================
-- STEP 3: Recreate views with new table names (preserving original structure)
-- ============================================================================

-- YieldMax Latest View (original structure from 20251116_add_yieldmax_etf_data.sql)
CREATE OR REPLACE VIEW v_yieldmax_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    performance_month_end,
    performance_quarter_end,
    fund_overview,
    investment_objective,
    fund_details,
    distributions,
    top_10_holdings,
    scraped_at,
    created_at,
    updated_at
FROM raw_etfs_yieldmax
ORDER BY ticker, scraped_at DESC;

-- Roundhill Latest View (original structure from 20251116_add_roundhill_etf_data.sql)
CREATE OR REPLACE VIEW v_roundhill_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    fund_details,
    performance_data,
    distributions,
    holdings,
    scraped_at,
    created_at,
    updated_at
FROM raw_etfs_roundhill
ORDER BY ticker, scraped_at DESC;

-- Neos Latest View (original structure from 20251116_add_neos_etf_data.sql)
CREATE OR REPLACE VIEW v_neos_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    fund_details,
    performance_data,
    distributions,
    holdings,
    scraped_at,
    created_at,
    updated_at
FROM raw_etfs_neos
ORDER BY ticker, scraped_at DESC;

-- Kurv Latest View (original structure from 20251116_add_kurv_etf_data.sql)
CREATE OR REPLACE VIEW v_kurv_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    fund_details,
    performance_data,
    distributions,
    holdings,
    scraped_at,
    created_at,
    updated_at
FROM raw_etfs_kurv
ORDER BY ticker, scraped_at DESC;

-- GraniteShares Latest View (original structure from 20251116_add_graniteshares_etf_data.sql)
CREATE OR REPLACE VIEW v_graniteshares_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    fund_details,
    performance_data,
    distributions,
    scraped_at,
    created_at,
    updated_at
FROM raw_etfs_graniteshares
ORDER BY ticker, scraped_at DESC;

-- Defiance Latest View (original structure from 20251116_add_defiance_etf_data.sql)
CREATE OR REPLACE VIEW v_defiance_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    fund_details,
    performance_data,
    distributions,
    holdings,
    scraped_at,
    created_at,
    updated_at
FROM raw_etfs_defiance
ORDER BY ticker, scraped_at DESC;

-- Global X Latest View (original structure from 20251116_add_globalx_etf_data.sql)
CREATE OR REPLACE VIEW v_globalx_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    fund_details,
    performance_data,
    distributions,
    holdings,
    scraped_at,
    created_at,
    updated_at
FROM raw_etfs_globalx
ORDER BY ticker, scraped_at DESC;

-- Purpose Latest View (original structure from 20251116_add_purpose_etf_data.sql)
CREATE OR REPLACE VIEW v_purpose_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    scraped_at,
    scraped_date,
    series,
    nav,
    aum,
    management_fee,
    mer,
    distribution_frequency,
    category,
    current_yield,
    fund_structure,
    cusip,
    exchange,
    currency_hedged,
    settlement,
    duration,
    coupon,
    maturity_yield,
    underlying,
    fund_details,
    portfolio_data,
    distributions,
    performance_data,
    eligibilities,
    created_at,
    updated_at
FROM raw_etfs_purpose
ORDER BY ticker, scraped_date DESC, scraped_at DESC;

-- ============================================================================
-- STEP 4: Verify migration
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '=== Migration Complete ===';
    RAISE NOTICE 'Renamed tables:';
    RAISE NOTICE '  - raw_yieldmax_etf_data      → raw_etfs_yieldmax';
    RAISE NOTICE '  - raw_roundhill_etf_data     → raw_etfs_roundhill';
    RAISE NOTICE '  - raw_neos_etf_data          → raw_etfs_neos';
    RAISE NOTICE '  - raw_kurv_etf_data          → raw_etfs_kurv';
    RAISE NOTICE '  - raw_graniteshares_etf_data → raw_etfs_graniteshares';
    RAISE NOTICE '  - raw_defiance_etf_data      → raw_etfs_defiance';
    RAISE NOTICE '  - raw_globalx_etf_data       → raw_etfs_globalx';
    RAISE NOTICE '  - raw_purpose_etf_data       → raw_etfs_purpose';
    RAISE NOTICE '';
    RAISE NOTICE 'Recreated views:';
    RAISE NOTICE '  - v_yieldmax_latest';
    RAISE NOTICE '  - v_roundhill_latest';
    RAISE NOTICE '  - v_neos_latest';
    RAISE NOTICE '  - v_kurv_latest';
    RAISE NOTICE '  - v_graniteshares_latest';
    RAISE NOTICE '  - v_defiance_latest';
    RAISE NOTICE '  - v_globalx_latest';
    RAISE NOTICE '  - v_purpose_latest';
END $$;

COMMIT;

-- ============================================================================
-- Verification Queries (run these after migration)
-- ============================================================================

-- Check all tables exist with new names
-- SELECT tablename FROM pg_tables WHERE tablename LIKE 'raw_etfs_%' ORDER BY tablename;

-- Check all views exist
-- SELECT viewname FROM pg_views WHERE viewname LIKE 'v_%_latest' ORDER BY viewname;

-- Verify data integrity (row counts should match)
-- SELECT 'raw_etfs_yieldmax' as table_name, COUNT(*) FROM raw_etfs_yieldmax
-- UNION ALL SELECT 'raw_etfs_roundhill', COUNT(*) FROM raw_etfs_roundhill
-- UNION ALL SELECT 'raw_etfs_neos', COUNT(*) FROM raw_etfs_neos
-- UNION ALL SELECT 'raw_etfs_kurv', COUNT(*) FROM raw_etfs_kurv
-- UNION ALL SELECT 'raw_etfs_graniteshares', COUNT(*) FROM raw_etfs_graniteshares
-- UNION ALL SELECT 'raw_etfs_defiance', COUNT(*) FROM raw_etfs_defiance
-- UNION ALL SELECT 'raw_etfs_globalx', COUNT(*) FROM raw_etfs_globalx
-- UNION ALL SELECT 'raw_etfs_purpose', COUNT(*) FROM raw_etfs_purpose;
