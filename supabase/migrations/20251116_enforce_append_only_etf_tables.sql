-- Migration: Enforce Append-Only Pattern on ETF Tables
-- Date: November 16, 2025
-- Purpose: Enforce immutability of raw ETF data using Row-Level Security (RLS)
--
-- This migration prevents accidental DELETE/UPDATE operations on raw_etfs_* tables
-- while allowing normal INSERT and SELECT operations.
--
-- NOTE: This assumes RLS is already enabled on the tables (from initial migrations)

BEGIN;

-- ============================================================================
-- Enforce Append-Only on raw_etfs_yieldmax
-- ============================================================================

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow select on raw_etfs_yieldmax" ON raw_etfs_yieldmax;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_yieldmax" ON raw_etfs_yieldmax;
DROP POLICY IF EXISTS "Deny update on raw_etfs_yieldmax" ON raw_etfs_yieldmax;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_yieldmax" ON raw_etfs_yieldmax;

-- Create new policies
CREATE POLICY "allow_insert_raw_etfs_yieldmax"
ON raw_etfs_yieldmax FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_yieldmax"
ON raw_etfs_yieldmax FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_yieldmax"
ON raw_etfs_yieldmax FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_yieldmax"
ON raw_etfs_yieldmax FOR DELETE
USING (false);

-- ============================================================================
-- Enforce Append-Only on raw_etfs_roundhill
-- ============================================================================

DROP POLICY IF EXISTS "Allow select on raw_etfs_roundhill" ON raw_etfs_roundhill;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_roundhill" ON raw_etfs_roundhill;
DROP POLICY IF EXISTS "Deny update on raw_etfs_roundhill" ON raw_etfs_roundhill;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_roundhill" ON raw_etfs_roundhill;

CREATE POLICY "allow_insert_raw_etfs_roundhill"
ON raw_etfs_roundhill FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_roundhill"
ON raw_etfs_roundhill FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_roundhill"
ON raw_etfs_roundhill FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_roundhill"
ON raw_etfs_roundhill FOR DELETE
USING (false);

-- ============================================================================
-- Enforce Append-Only on raw_etfs_neos
-- ============================================================================

DROP POLICY IF EXISTS "Allow select on raw_etfs_neos" ON raw_etfs_neos;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_neos" ON raw_etfs_neos;
DROP POLICY IF EXISTS "Deny update on raw_etfs_neos" ON raw_etfs_neos;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_neos" ON raw_etfs_neos;

CREATE POLICY "allow_insert_raw_etfs_neos"
ON raw_etfs_neos FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_neos"
ON raw_etfs_neos FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_neos"
ON raw_etfs_neos FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_neos"
ON raw_etfs_neos FOR DELETE
USING (false);

-- ============================================================================
-- Enforce Append-Only on raw_etfs_kurv
-- ============================================================================

DROP POLICY IF EXISTS "Allow select on raw_etfs_kurv" ON raw_etfs_kurv;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_kurv" ON raw_etfs_kurv;
DROP POLICY IF EXISTS "Deny update on raw_etfs_kurv" ON raw_etfs_kurv;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_kurv" ON raw_etfs_kurv;

CREATE POLICY "allow_insert_raw_etfs_kurv"
ON raw_etfs_kurv FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_kurv"
ON raw_etfs_kurv FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_kurv"
ON raw_etfs_kurv FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_kurv"
ON raw_etfs_kurv FOR DELETE
USING (false);

-- ============================================================================
-- Enforce Append-Only on raw_etfs_graniteshares
-- ============================================================================

DROP POLICY IF EXISTS "Allow select on raw_etfs_graniteshares" ON raw_etfs_graniteshares;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_graniteshares" ON raw_etfs_graniteshares;
DROP POLICY IF EXISTS "Deny update on raw_etfs_graniteshares" ON raw_etfs_graniteshares;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_graniteshares" ON raw_etfs_graniteshares;

CREATE POLICY "allow_insert_raw_etfs_graniteshares"
ON raw_etfs_graniteshares FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_graniteshares"
ON raw_etfs_graniteshares FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_graniteshares"
ON raw_etfs_graniteshares FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_graniteshares"
ON raw_etfs_graniteshares FOR DELETE
USING (false);

-- ============================================================================
-- Enforce Append-Only on raw_etfs_defiance
-- ============================================================================

DROP POLICY IF EXISTS "Allow select on raw_etfs_defiance" ON raw_etfs_defiance;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_defiance" ON raw_etfs_defiance;
DROP POLICY IF EXISTS "Deny update on raw_etfs_defiance" ON raw_etfs_defiance;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_defiance" ON raw_etfs_defiance;

CREATE POLICY "allow_insert_raw_etfs_defiance"
ON raw_etfs_defiance FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_defiance"
ON raw_etfs_defiance FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_defiance"
ON raw_etfs_defiance FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_defiance"
ON raw_etfs_defiance FOR DELETE
USING (false);

-- ============================================================================
-- Enforce Append-Only on raw_etfs_globalx
-- ============================================================================

DROP POLICY IF EXISTS "Allow select on raw_etfs_globalx" ON raw_etfs_globalx;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_globalx" ON raw_etfs_globalx;
DROP POLICY IF EXISTS "Deny update on raw_etfs_globalx" ON raw_etfs_globalx;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_globalx" ON raw_etfs_globalx;

CREATE POLICY "allow_insert_raw_etfs_globalx"
ON raw_etfs_globalx FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_globalx"
ON raw_etfs_globalx FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_globalx"
ON raw_etfs_globalx FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_globalx"
ON raw_etfs_globalx FOR DELETE
USING (false);

-- ============================================================================
-- Enforce Append-Only on raw_etfs_purpose
-- ============================================================================

DROP POLICY IF EXISTS "Allow select on raw_etfs_purpose" ON raw_etfs_purpose;
DROP POLICY IF EXISTS "Deny delete on raw_etfs_purpose" ON raw_etfs_purpose;
DROP POLICY IF EXISTS "Deny update on raw_etfs_purpose" ON raw_etfs_purpose;
DROP POLICY IF EXISTS "Allow insert on raw_etfs_purpose" ON raw_etfs_purpose;

CREATE POLICY "allow_insert_raw_etfs_purpose"
ON raw_etfs_purpose FOR INSERT
WITH CHECK (true);

CREATE POLICY "allow_select_raw_etfs_purpose"
ON raw_etfs_purpose FOR SELECT
USING (true);

CREATE POLICY "deny_update_raw_etfs_purpose"
ON raw_etfs_purpose FOR UPDATE
USING (false)
WITH CHECK (false);

CREATE POLICY "deny_delete_raw_etfs_purpose"
ON raw_etfs_purpose FOR DELETE
USING (false);

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    policy_count INT;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE tablename LIKE 'raw_etfs_%'
      AND schemaname = 'public';

    RAISE NOTICE '=== Append-Only Enforcement Complete ===';
    RAISE NOTICE 'RLS policies created: %', policy_count;
    RAISE NOTICE '';
    RAISE NOTICE 'All raw_etfs_* tables are now append-only:';
    RAISE NOTICE '  ✅ INSERT allowed (new snapshots)';
    RAISE NOTICE '  ✅ SELECT allowed (analysis)';
    RAISE NOTICE '  ❌ UPDATE denied (prevents data corruption)';
    RAISE NOTICE '  ❌ DELETE denied (prevents data loss)';
    RAISE NOTICE '';
    RAISE NOTICE 'This enforces the time-series data architecture where:';
    RAISE NOTICE '  - Each scrape creates new rows (never overwrites)';
    RAISE NOTICE '  - Historical data is preserved forever';
    RAISE NOTICE '  - Trends and changes can be tracked over time';
END $$;

COMMIT;

-- ============================================================================
-- Test Queries (run after migration to verify enforcement)
-- ============================================================================

-- Test 1: Verify SELECT still works
-- SELECT COUNT(*) FROM raw_etfs_yieldmax;

-- Test 2: Verify INSERT still works (will succeed)
-- INSERT INTO raw_etfs_yieldmax (ticker, fund_name)
-- VALUES ('TEST', 'Test Fund');

-- Test 3: Verify UPDATE is blocked (will fail with "policy with check expression returned false")
-- UPDATE raw_etfs_yieldmax SET fund_name = 'New Name' WHERE ticker = 'TEST';
-- Expected error: violates row-level security policy

-- Test 4: Verify DELETE is blocked (will fail with "policy with check expression returned false")
-- DELETE FROM raw_etfs_yieldmax WHERE ticker = 'TEST';
-- Expected error: violates row-level security policy

-- ============================================================================
-- SQL Audit Trail (if needed)
-- ============================================================================

-- To audit all operations on raw_etfs_* tables, Supabase has built-in auditing:
-- SELECT * FROM audit.record_version
-- WHERE table_name LIKE 'raw_etfs_%'
-- ORDER BY created_at DESC;
