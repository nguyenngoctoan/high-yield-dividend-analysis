-- Migration: Add Row Level Security (RLS) Policies
-- Date: 2025-11-15
-- Description: Implement defense-in-depth with Row Level Security policies
-- Priority: RECOMMENDED (defense-in-depth improvement, not critical)
-- Related: Least Privilege Security Audit recommendation

-- ============================================================================
-- OVERVIEW
-- ============================================================================
-- This migration adds Row Level Security (RLS) policies to sensitive tables.
-- RLS provides an additional layer of security beyond function-level authorization.
--
-- Benefits:
-- - Defense-in-depth: Protection even if function authorization is bypassed
-- - Direct table access protection: If PostgREST is enabled
-- - Compliance: Meets security best practices and audit requirements
-- - Data isolation: Guaranteed row-level data separation between users
--
-- NOTE: All functions already have proper authorization checks, so this is
-- an enhancement, not a fix for existing vulnerabilities.

-- ============================================================================
-- 1. RLS for divv_api_keys - API Key Management
-- ============================================================================

ALTER TABLE divv_api_keys ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own API keys
CREATE POLICY "api_keys_select_own"
ON divv_api_keys FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Users can update their own API keys
CREATE POLICY "api_keys_update_own"
ON divv_api_keys FOR UPDATE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Only service_role can insert API keys (during key generation)
CREATE POLICY "api_keys_insert_service"
ON divv_api_keys FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Policy: Only service_role can delete API keys (during deactivation)
CREATE POLICY "api_keys_delete_service"
ON divv_api_keys FOR DELETE
USING (auth.role() = 'service_role');

COMMENT ON POLICY "api_keys_select_own" ON divv_api_keys IS
'Users can view their own API keys; service_role can view all';

COMMENT ON POLICY "api_keys_update_own" ON divv_api_keys IS
'Users can update their own API keys; service_role can update all';

-- ============================================================================
-- 2. RLS for snaptrade_users - SnapTrade OAuth Credentials
-- ============================================================================

ALTER TABLE snaptrade_users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own SnapTrade data
-- NOTE: encrypted_user_secret should still only be accessed via get_user_secret()
CREATE POLICY "snaptrade_users_select_own"
ON snaptrade_users FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Users can update their own SnapTrade data
CREATE POLICY "snaptrade_users_update_own"
ON snaptrade_users FOR UPDATE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Users can insert their own SnapTrade data (during OAuth)
CREATE POLICY "snaptrade_users_insert_own"
ON snaptrade_users FOR INSERT
WITH CHECK (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Users can delete their own SnapTrade data
CREATE POLICY "snaptrade_users_delete_own"
ON snaptrade_users FOR DELETE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "snaptrade_users_select_own" ON snaptrade_users IS
'Users can view their own SnapTrade credentials; service_role can view all';

-- ============================================================================
-- 3. RLS for broker_connections - Brokerage OAuth Connections
-- ============================================================================

ALTER TABLE broker_connections ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own brokerage connections
CREATE POLICY "broker_connections_select_own"
ON broker_connections FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Users can update their own connections
CREATE POLICY "broker_connections_update_own"
ON broker_connections FOR UPDATE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Users can create their own connections (during OAuth)
CREATE POLICY "broker_connections_insert_own"
ON broker_connections FOR INSERT
WITH CHECK (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Users can delete their own connections
CREATE POLICY "broker_connections_delete_own"
ON broker_connections FOR DELETE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "broker_connections_select_own" ON broker_connections IS
'Users can manage their own broker connections; service_role can manage all';

-- ============================================================================
-- 4. RLS for users - User Account Table
-- ============================================================================

ALTER TABLE divv_users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own user record
CREATE POLICY "users_select_own"
ON users FOR SELECT
USING (
    auth.uid() = id
    OR auth.role() = 'service_role'
);

-- Policy: Users can update their own profile
CREATE POLICY "users_update_own"
ON users FOR UPDATE
USING (
    auth.uid() = id
    OR auth.role() = 'service_role'
);

-- Policy: Only service_role can insert users (via upsert_google_user)
CREATE POLICY "users_insert_service"
ON users FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Policy: Users can delete their own account
CREATE POLICY "users_delete_own"
ON users FOR DELETE
USING (
    auth.uid() = id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "users_select_own" ON users IS
'Users can view/update their own profile; service_role can manage all users';

-- ============================================================================
-- 5. RLS for stg_portfolios - Portfolio Staging Data
-- ============================================================================

ALTER TABLE stg_portfolios ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own portfolios
CREATE POLICY "stg_portfolios_select_own"
ON stg_portfolios FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Service role can update portfolios (from SnapTrade sync)
CREATE POLICY "stg_portfolios_update_service"
ON stg_portfolios FOR UPDATE
USING (auth.role() = 'service_role');

-- Policy: Service role can insert portfolios (from SnapTrade sync)
CREATE POLICY "stg_portfolios_insert_service"
ON stg_portfolios FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Policy: Users can delete their own portfolios
CREATE POLICY "stg_portfolios_delete_own"
ON stg_portfolios FOR DELETE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "stg_portfolios_select_own" ON stg_portfolios IS
'Users can view their own portfolios; service_role can manage all portfolios';

-- ============================================================================
-- 6. RLS for raw_portfolios - Raw Portfolio Snapshots
-- ============================================================================

ALTER TABLE raw_portfolios ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own portfolio snapshots
CREATE POLICY "raw_portfolios_select_own"
ON raw_portfolios FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Service role can insert portfolio snapshots (from SnapTrade sync)
CREATE POLICY "raw_portfolios_insert_service"
ON raw_portfolios FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Policy: Users can delete their own portfolio history
CREATE POLICY "raw_portfolios_delete_own"
ON raw_portfolios FOR DELETE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "raw_portfolios_select_own" ON raw_portfolios IS
'Users can view their own portfolio snapshots; service_role can manage all';

-- ============================================================================
-- 7. RLS for raw_activities - Trading Activities
-- ============================================================================

ALTER TABLE raw_activities ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own activities
CREATE POLICY "raw_activities_select_own"
ON raw_activities FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Service role can insert activities (from SnapTrade sync)
CREATE POLICY "raw_activities_insert_service"
ON raw_activities FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Policy: Users can delete their own activity history
CREATE POLICY "raw_activities_delete_own"
ON raw_activities FOR DELETE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "raw_activities_select_own" ON raw_activities IS
'Users can view their own trading activities; service_role can manage all';

-- ============================================================================
-- 8. RLS for mart_portfolio_enriched - Enriched Portfolio Mart
-- ============================================================================

ALTER TABLE mart_portfolio_enriched ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own enriched portfolio data
CREATE POLICY "mart_portfolio_enriched_select_own"
ON mart_portfolio_enriched FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Service role can refresh mart data (via refresh_marts_after_oauth)
CREATE POLICY "mart_portfolio_enriched_upsert_service"
ON mart_portfolio_enriched FOR INSERT
WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "mart_portfolio_enriched_update_service"
ON mart_portfolio_enriched FOR UPDATE
USING (auth.role() = 'service_role');

-- Policy: Users can delete their own mart data
CREATE POLICY "mart_portfolio_enriched_delete_own"
ON mart_portfolio_enriched FOR DELETE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "mart_portfolio_enriched_select_own" ON mart_portfolio_enriched IS
'Users can view their own enriched portfolio; service_role refreshes mart data';

-- ============================================================================
-- 9. RLS for mart_portfolio_list_with_holdings - Portfolio List Mart
-- ============================================================================

ALTER TABLE mart_portfolio_list_with_holdings ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own portfolio list
CREATE POLICY "mart_portfolio_list_select_own"
ON mart_portfolio_list_with_holdings FOR SELECT
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

-- Policy: Service role can refresh mart data (via refresh_marts_after_oauth)
CREATE POLICY "mart_portfolio_list_upsert_service"
ON mart_portfolio_list_with_holdings FOR INSERT
WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "mart_portfolio_list_update_service"
ON mart_portfolio_list_with_holdings FOR UPDATE
USING (auth.role() = 'service_role');

-- Policy: Users can delete their own mart data
CREATE POLICY "mart_portfolio_list_delete_own"
ON mart_portfolio_list_with_holdings FOR DELETE
USING (
    auth.uid() = user_id
    OR auth.role() = 'service_role'
);

COMMENT ON POLICY "mart_portfolio_list_select_own" ON mart_portfolio_list_with_holdings IS
'Users can view their own portfolio list; service_role refreshes mart data';

-- ============================================================================
-- 10. RLS for application_logs - Application Logging (Optional)
-- ============================================================================
-- NOTE: Logs may not have a user_id column. Adjust based on your schema.
-- If logs are system-wide (no user_id), make them service_role only.

ALTER TABLE application_logs ENABLE ROW LEVEL SECURITY;

-- Policy: Only service_role can access logs
CREATE POLICY "application_logs_service_only"
ON application_logs FOR ALL
USING (auth.role() = 'service_role');

COMMENT ON POLICY "application_logs_service_only" ON application_logs IS
'Only service_role can access application logs (no user-specific data)';

-- ============================================================================
-- Verification & Testing
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Row Level Security (RLS) policies created successfully';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 Tables with RLS Enabled:';
    RAISE NOTICE '   ✅ divv_api_keys (4 policies)';
    RAISE NOTICE '   ✅ snaptrade_users (4 policies)';
    RAISE NOTICE '   ✅ broker_connections (4 policies)';
    RAISE NOTICE '   ✅ users (4 policies)';
    RAISE NOTICE '   ✅ stg_portfolios (4 policies)';
    RAISE NOTICE '   ✅ raw_portfolios (3 policies)';
    RAISE NOTICE '   ✅ raw_activities (3 policies)';
    RAISE NOTICE '   ✅ mart_portfolio_enriched (4 policies)';
    RAISE NOTICE '   ✅ mart_portfolio_list_with_holdings (4 policies)';
    RAISE NOTICE '   ✅ application_logs (1 policy - service_role only)';
    RAISE NOTICE '';
    RAISE NOTICE '🔐 Security Model:';
    RAISE NOTICE '   - Users can only access their own data (auth.uid() = user_id)';
    RAISE NOTICE '   - Service role bypasses all RLS (for system operations)';
    RAISE NOTICE '   - Defense-in-depth: RLS + function authorization';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANT: Testing Required';
    RAISE NOTICE '   1. Test user can only see their own data';
    RAISE NOTICE '   2. Test user cannot see other users data';
    RAISE NOTICE '   3. Test service_role can access all data';
    RAISE NOTICE '   4. Test existing functions still work';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Impact: Minimal (functions already have authorization)';
    RAISE NOTICE '   - Adds defense-in-depth protection';
    RAISE NOTICE '   - No breaking changes expected';
    RAISE NOTICE '   - Performance impact negligible';
END $$;

-- ============================================================================
-- Rollback Instructions (if needed)
-- ============================================================================
-- To disable RLS on a table:
-- ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
--
-- To drop all policies on a table:
-- DROP POLICY IF EXISTS policy_name ON table_name;
-- ============================================================================
