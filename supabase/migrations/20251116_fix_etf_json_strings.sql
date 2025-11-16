-- Migration: Fix JSON strings in ETF tables
-- Date: November 16, 2025
-- Purpose: Convert JSONB string types to proper JSONB objects/arrays
--
-- Issue: Some ETF tables have JSONB columns storing JSON strings instead of objects
-- Tables affected: raw_etfs_roundhill, raw_etfs_defiance
--
-- Example of issue:
--   WRONG: '"{\"key\": \"value\"}"'  (JSONB string containing JSON)
--   RIGHT: '{"key": "value"}'        (JSONB object)

BEGIN;

-- ============================================================================
-- STEP 1: Fix raw_etfs_roundhill
-- ============================================================================

-- Fix fund_overview (JSONB strings → JSONB objects)
-- The #>>'{}'operator extracts the JSON string value, then ::jsonb parses it
UPDATE raw_etfs_roundhill
SET fund_overview = (fund_overview#>>'{}')::jsonb
WHERE jsonb_typeof(fund_overview) = 'string';

-- Fix performance_data (JSONB strings → JSONB objects)
UPDATE raw_etfs_roundhill
SET performance_data = (performance_data#>>'{}')::jsonb
WHERE jsonb_typeof(performance_data) = 'string';

-- Fix fund_details (JSONB strings → JSONB objects)
UPDATE raw_etfs_roundhill
SET fund_details = (fund_details#>>'{}')::jsonb
WHERE jsonb_typeof(fund_details) = 'string';

-- Fix distributions (JSONB strings → JSONB arrays/objects)
UPDATE raw_etfs_roundhill
SET distributions = (distributions#>>'{}')::jsonb
WHERE jsonb_typeof(distributions) = 'string';

-- Fix holdings (JSONB strings → JSONB arrays/objects)
UPDATE raw_etfs_roundhill
SET holdings = (holdings#>>'{}')::jsonb
WHERE jsonb_typeof(holdings) = 'string';

-- ============================================================================
-- STEP 2: Fix raw_etfs_defiance
-- ============================================================================

-- Fix fund_details (JSONB strings → JSONB objects)
UPDATE raw_etfs_defiance
SET fund_details = (fund_details#>>'{}')::jsonb
WHERE jsonb_typeof(fund_details) = 'string';

-- Fix performance_data (JSONB strings → JSONB objects)
UPDATE raw_etfs_defiance
SET performance_data = (performance_data#>>'{}')::jsonb
WHERE jsonb_typeof(performance_data) = 'string';

-- Fix distributions (JSONB strings → JSONB arrays/objects)
UPDATE raw_etfs_defiance
SET distributions = (distributions#>>'{}')::jsonb
WHERE jsonb_typeof(distributions) = 'string';

-- Fix holdings (JSONB strings → JSONB arrays/objects)
UPDATE raw_etfs_defiance
SET holdings = (holdings#>>'{}')::jsonb
WHERE jsonb_typeof(holdings) = 'string';

-- ============================================================================
-- STEP 3: Verify fixes
-- ============================================================================

DO $$
DECLARE
    roundhill_fund_details_strings INT;
    roundhill_distributions_strings INT;
    defiance_fund_details_strings INT;
    defiance_distributions_strings INT;
BEGIN
    -- Count remaining strings in Roundhill
    SELECT
        COUNT(CASE WHEN jsonb_typeof(fund_details) = 'string' THEN 1 END),
        COUNT(CASE WHEN jsonb_typeof(distributions) = 'string' THEN 1 END)
    INTO roundhill_fund_details_strings, roundhill_distributions_strings
    FROM raw_etfs_roundhill;

    -- Count remaining strings in Defiance
    SELECT
        COUNT(CASE WHEN jsonb_typeof(fund_details) = 'string' THEN 1 END),
        COUNT(CASE WHEN jsonb_typeof(distributions) = 'string' THEN 1 END)
    INTO defiance_fund_details_strings, defiance_distributions_strings
    FROM raw_etfs_defiance;

    RAISE NOTICE '=== Migration Complete ===';
    RAISE NOTICE 'Remaining JSON strings:';
    RAISE NOTICE '  raw_etfs_roundhill.fund_details: %', roundhill_fund_details_strings;
    RAISE NOTICE '  raw_etfs_roundhill.distributions: %', roundhill_distributions_strings;
    RAISE NOTICE '  raw_etfs_defiance.fund_details: %', defiance_fund_details_strings;
    RAISE NOTICE '  raw_etfs_defiance.distributions: %', defiance_distributions_strings;
    RAISE NOTICE '';

    IF roundhill_fund_details_strings > 0 OR roundhill_distributions_strings > 0 OR
       defiance_fund_details_strings > 0 OR defiance_distributions_strings > 0 THEN
        RAISE WARNING 'Some JSON strings remain - they may be NULL or empty strings';
    ELSE
        RAISE NOTICE '✅ All JSON strings successfully converted to objects/arrays';
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- Verification Queries (run after migration)
-- ============================================================================

-- Check Roundhill
-- SELECT
--     ticker,
--     jsonb_typeof(fund_details) as fund_details_type,
--     jsonb_typeof(distributions) as distributions_type
-- FROM raw_etfs_roundhill
-- LIMIT 5;

-- Check Defiance
-- SELECT
--     ticker,
--     jsonb_typeof(fund_details) as fund_details_type,
--     jsonb_typeof(distributions) as distributions_type
-- FROM raw_etfs_defiance
-- LIMIT 5;

-- Count by type
-- SELECT
--     'roundhill' as table_name,
--     jsonb_typeof(fund_details) as type,
--     COUNT(*) as count
-- FROM raw_etfs_roundhill
-- GROUP BY jsonb_typeof(fund_details)
-- UNION ALL
-- SELECT
--     'defiance',
--     jsonb_typeof(fund_details),
--     COUNT(*)
-- FROM raw_etfs_defiance
-- GROUP BY jsonb_typeof(fund_details)
-- ORDER BY table_name, type;
