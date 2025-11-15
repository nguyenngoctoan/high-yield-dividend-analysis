-- Verification Script for Security Fixes
-- Run this after applying the security migration to verify fixes are in place

\echo '=========================================='
\echo 'Security Fixes Verification Script'
\echo 'Testing function access controls...'
\echo '=========================================='
\echo ''

-- ============================================================================
-- Test 1: Verify PUBLIC access revoked
-- ============================================================================

\echo 'Test 1: Checking if PUBLIC execute permissions are revoked...'

SELECT
    p.proname as function_name,
    CASE
        WHEN has_function_privilege('public', p.oid, 'EXECUTE') THEN '❌ VULNERABLE - Public can execute'
        ELSE '✅ SECURE - Public access revoked'
    END as security_status
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
    'get_latest_dates_by_symbol',
    'get_user_secret',
    'increment_key_usage',
    'get_tier_limits',
    'is_symbol_accessible',
    'refresh_marts_after_oauth',
    'reset_monthly_usage_counters',
    'cleanup_old_application_logs',
    'upsert_user_secret',
    'upsert_google_user'
  )
ORDER BY p.proname;

\echo ''

-- ============================================================================
-- Test 2: Verify SECURITY DEFINER flag
-- ============================================================================

\echo 'Test 2: Checking SECURITY DEFINER status...'

SELECT
    p.proname as function_name,
    CASE p.prosecdef
        WHEN true THEN '✅ SECURITY DEFINER (expected for most)'
        ELSE 'ℹ️  SECURITY INVOKER'
    END as security_mode
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
    'get_latest_dates_by_symbol',
    'get_user_secret',
    'increment_key_usage',
    'get_tier_limits',
    'is_symbol_accessible',
    'refresh_marts_after_oauth',
    'reset_monthly_usage_counters',
    'cleanup_old_application_logs',
    'upsert_user_secret',
    'upsert_google_user'
  )
ORDER BY p.proname;

\echo ''

-- ============================================================================
-- Test 3: Check function grants to service_role
-- ============================================================================

\echo 'Test 3: Checking service_role permissions...'

SELECT
    p.proname as function_name,
    CASE
        WHEN has_function_privilege('service_role', p.oid, 'EXECUTE') THEN '✅ Service role can execute'
        ELSE '❌ WARNING - Service role cannot execute'
    END as service_role_access
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
    'get_latest_dates_by_symbol',
    'get_user_secret',
    'increment_key_usage',
    'get_tier_limits',
    'is_symbol_accessible',
    'refresh_marts_after_oauth',
    'reset_monthly_usage_counters',
    'cleanup_old_application_logs',
    'upsert_user_secret',
    'upsert_google_user'
  )
ORDER BY p.proname;

\echo ''

-- ============================================================================
-- Test 4: Check function grants to authenticated role
-- ============================================================================

\echo 'Test 4: Checking authenticated user permissions...'

SELECT
    p.proname as function_name,
    CASE
        WHEN has_function_privilege('authenticated', p.oid, 'EXECUTE') THEN '✅ Authenticated can execute'
        ELSE 'ℹ️  Authenticated cannot execute (service_role only)'
    END as authenticated_access,
    CASE
        WHEN p.proname IN ('get_tier_limits', 'is_symbol_accessible', 'refresh_marts_after_oauth', 'upsert_user_secret')
             AND has_function_privilege('authenticated', p.oid, 'EXECUTE') THEN '✅ EXPECTED'
        WHEN p.proname IN ('get_user_secret', 'increment_key_usage', 'reset_monthly_usage_counters', 'cleanup_old_application_logs', 'get_latest_dates_by_symbol', 'upsert_google_user')
             AND NOT has_function_privilege('authenticated', p.oid, 'EXECUTE') THEN '✅ EXPECTED'
        ELSE '⚠️  CHECK CONFIG'
    END as expected_state
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
    'get_latest_dates_by_symbol',
    'get_user_secret',
    'increment_key_usage',
    'get_tier_limits',
    'is_symbol_accessible',
    'refresh_marts_after_oauth',
    'reset_monthly_usage_counters',
    'cleanup_old_application_logs',
    'upsert_user_secret',
    'upsert_google_user'
  )
ORDER BY p.proname;

\echo ''

-- ============================================================================
-- Test 5: Verify function comments (documentation)
-- ============================================================================

\echo 'Test 5: Checking function documentation...'

SELECT
    p.proname as function_name,
    CASE
        WHEN pg_catalog.obj_description(p.oid, 'pg_proc') IS NOT NULL THEN '✅ Documented'
        ELSE '⚠️  No comment'
    END as has_comment,
    pg_catalog.obj_description(p.oid, 'pg_proc') as comment
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
    'get_latest_dates_by_symbol',
    'get_user_secret',
    'increment_key_usage',
    'get_tier_limits',
    'is_symbol_accessible',
    'refresh_marts_after_oauth',
    'reset_monthly_usage_counters',
    'cleanup_old_application_logs',
    'upsert_user_secret',
    'upsert_google_user'
  )
ORDER BY p.proname;

\echo ''

-- ============================================================================
-- Test 6: Summary Report
-- ============================================================================

\echo '=========================================='
\echo 'Security Verification Summary'
\echo '=========================================='

WITH function_security AS (
    SELECT
        p.proname,
        NOT has_function_privilege('public', p.oid, 'EXECUTE') as public_revoked,
        has_function_privilege('service_role', p.oid, 'EXECUTE') as service_role_granted,
        p.prosecdef as is_security_definer,
        pg_catalog.obj_description(p.oid, 'pg_proc') IS NOT NULL as has_documentation
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
      AND p.proname IN (
        'get_latest_dates_by_symbol',
        'get_user_secret',
        'increment_key_usage',
        'get_tier_limits',
        'is_symbol_accessible',
        'refresh_marts_after_oauth',
        'reset_monthly_usage_counters',
        'cleanup_old_application_logs',
        'upsert_user_secret',
        'upsert_google_user'
      )
)
SELECT
    COUNT(*) as total_functions,
    SUM(CASE WHEN public_revoked THEN 1 ELSE 0 END) as public_access_revoked,
    SUM(CASE WHEN service_role_granted THEN 1 ELSE 0 END) as service_role_access,
    SUM(CASE WHEN is_security_definer THEN 1 ELSE 0 END) as security_definer_count,
    SUM(CASE WHEN has_documentation THEN 1 ELSE 0 END) as documented_count,
    CASE
        WHEN SUM(CASE WHEN public_revoked THEN 1 ELSE 0 END) = COUNT(*)
         AND SUM(CASE WHEN service_role_granted THEN 1 ELSE 0 END) = COUNT(*)
        THEN '✅ ALL SECURITY CHECKS PASSED'
        ELSE '❌ SECURITY ISSUES FOUND - Review above'
    END as overall_status
FROM function_security;

\echo ''
\echo 'Verification complete!'
\echo ''
\echo 'Expected Results:'
\echo '  - Total Functions: 10'
\echo '  - Public Access Revoked: 10'
\echo '  - Service Role Access: 10'
\echo '  - Security Definer: 10'
\echo '  - Documented: 10'
\echo '  - Overall Status: ✅ ALL SECURITY CHECKS PASSED'
\echo ''
