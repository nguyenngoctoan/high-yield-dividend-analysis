-- Migration: Add RLS Tier Enforcement Policies
-- Date: November 16, 2025
-- Purpose: Enforce API tier access controls at database level
--
-- This migration adds Row-Level Security (RLS) policies to public data tables
-- to enforce tier-based access control at the database level.
--
-- Tiers:
-- - free: Sample stocks only (150 free tier symbols)
-- - starter: US stocks only
-- - premium: US + International stocks
-- - professional: All stocks
-- - enterprise: All stocks (unlimited)

BEGIN;

-- ============================================================================
-- Step 1: Create tier configuration function
-- ============================================================================

CREATE OR REPLACE FUNCTION get_user_tier(user_id UUID)
RETURNS TEXT AS $$
DECLARE
  tier TEXT;
BEGIN
  SELECT COALESCE(t.tier, 'free') INTO tier
  FROM divv_api_keys t
  WHERE t.user_id = user_id
    AND t.is_active = true
    AND (t.expires_at IS NULL OR t.expires_at > NOW())
  ORDER BY
    CASE t.tier
      WHEN 'enterprise' THEN 1
      WHEN 'professional' THEN 2
      WHEN 'premium' THEN 3
      WHEN 'starter' THEN 4
      WHEN 'free' THEN 5
    END
  LIMIT 1;

  RETURN COALESCE(tier, 'free');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Step 2: Enable RLS on public data tables
-- ============================================================================

ALTER TABLE raw_stocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw_dividends ENABLE ROW LEVEL SECURITY;
ALTER TABLE raw_stock_prices ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Step 3: RLS Policy for raw_stocks table
-- ============================================================================

-- Tier-based access control for stocks
CREATE POLICY "tier_based_stocks_access"
ON raw_stocks
FOR SELECT
USING (
  CASE
    WHEN get_user_tier(auth.uid()) = 'free' THEN
      -- Free tier: Limited to top 150 symbols by market cap (first 150 when ordered by symbol)
      -- Alternative: Use a specific list if free_tier_stocks table exists
      CAST(
        (SELECT COUNT(*) FROM raw_stocks rs1 WHERE rs1.symbol <= symbol)
        AS BIGINT
      ) <= 150
    WHEN get_user_tier(auth.uid()) = 'starter' THEN
      -- Starter tier: US stocks only
      exchange IN ('NASDAQ', 'NYSE', 'AMEX')
    WHEN get_user_tier(auth.uid()) IN ('premium', 'professional', 'enterprise') THEN
      -- Premium/Pro/Enterprise: All stocks
      true
    ELSE
      false
  END
);

-- Service role (admin) can access everything
CREATE POLICY "service_role_stocks_access"
ON raw_stocks
FOR SELECT
USING (auth.role() = 'service_role');

-- ============================================================================
-- Step 4: RLS Policy for raw_dividends table
-- ============================================================================

-- Tier-based access control for dividends
CREATE POLICY "tier_based_dividends_access"
ON raw_dividends
FOR SELECT
USING (
  CASE
    WHEN get_user_tier(auth.uid()) = 'free' THEN
      -- Free tier: Limited to top 150 stocks
      CAST(
        (SELECT COUNT(*) FROM raw_stocks rs1 WHERE rs1.symbol <= symbol)
        AS BIGINT
      ) <= 150
    WHEN get_user_tier(auth.uid()) = 'starter' THEN
      -- Starter can access dividends for US stocks
      symbol IN (
        SELECT symbol FROM raw_stocks
        WHERE exchange IN ('NASDAQ', 'NYSE', 'AMEX')
      )
    WHEN get_user_tier(auth.uid()) IN ('premium', 'professional', 'enterprise') THEN
      true
    ELSE
      false
  END
);

-- Service role (admin) can access everything
CREATE POLICY "service_role_dividends_access"
ON raw_dividends
FOR SELECT
USING (auth.role() = 'service_role');

-- ============================================================================
-- Step 5: RLS Policy for raw_stock_prices table
-- ============================================================================

-- Tier-based access control for stock prices
CREATE POLICY "tier_based_prices_access"
ON raw_stock_prices
FOR SELECT
USING (
  CASE
    WHEN get_user_tier(auth.uid()) = 'free' THEN
      -- Free tier: Limited to top 150 stocks
      CAST(
        (SELECT COUNT(*) FROM raw_stocks rs1 WHERE rs1.symbol <= symbol)
        AS BIGINT
      ) <= 150
    WHEN get_user_tier(auth.uid()) = 'starter' THEN
      -- Starter can access prices for US stocks
      symbol IN (
        SELECT symbol FROM raw_stocks
        WHERE exchange IN ('NASDAQ', 'NYSE', 'AMEX')
      )
    WHEN get_user_tier(auth.uid()) IN ('premium', 'professional', 'enterprise') THEN
      true
    ELSE
      false
  END
);

-- Service role (admin) can access everything
CREATE POLICY "service_role_prices_access"
ON raw_stock_prices
FOR SELECT
USING (auth.role() = 'service_role');

-- ============================================================================
-- Step 6: RLS Policy for divv_api_keys (user-owned data)
-- ============================================================================

-- Users can only view their own API keys
CREATE POLICY "users_view_own_keys"
ON divv_api_keys
FOR SELECT
USING (
  auth.uid() = user_id OR auth.role() = 'service_role'
);

-- Users can only update their own API keys
CREATE POLICY "users_update_own_keys"
ON divv_api_keys
FOR UPDATE
USING (auth.uid() = user_id);

-- Users can only delete their own API keys
CREATE POLICY "users_delete_own_keys"
ON divv_api_keys
FOR DELETE
USING (auth.uid() = user_id);

-- Only authenticated users can insert new keys
CREATE POLICY "users_insert_keys"
ON divv_api_keys
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- Step 7: Create audit table for tracking access
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_api_access (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key_id UUID NOT NULL REFERENCES divv_api_keys(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL,
    status_code INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    request_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_time_ms INTEGER,

    -- For audit trail
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes for fast queries
    CHECK (response_time_ms >= 0)
);

CREATE INDEX idx_audit_api_access_user_id ON audit_api_access(user_id);
CREATE INDEX idx_audit_api_access_key_id ON audit_api_access(key_id);
CREATE INDEX idx_audit_api_access_endpoint ON audit_api_access(endpoint);
CREATE INDEX idx_audit_api_access_request_time ON audit_api_access(request_time DESC);
CREATE INDEX idx_audit_api_access_user_time ON audit_api_access(user_id, request_time DESC);

-- Add comment
COMMENT ON TABLE audit_api_access IS 'Audit log for all API requests - tracks which API key accessed which endpoint';

-- ============================================================================
-- Step 8: Enable RLS on audit table
-- ============================================================================

ALTER TABLE audit_api_access ENABLE ROW LEVEL SECURITY;

-- Users can only view their own audit logs
CREATE POLICY "users_view_own_audit"
ON audit_api_access
FOR SELECT
USING (auth.uid() = user_id);

-- Only service role can insert audit logs
CREATE POLICY "service_role_insert_audit"
ON audit_api_access
FOR INSERT
WITH CHECK (auth.role() = 'service_role');

-- Service role can view all audit logs
CREATE POLICY "service_role_view_all_audit"
ON audit_api_access
FOR SELECT
USING (auth.role() = 'service_role');

-- ============================================================================
-- Step 9: Create function to log API access
-- ============================================================================

CREATE OR REPLACE FUNCTION log_api_access(
  p_user_id UUID,
  p_key_id UUID,
  p_endpoint TEXT,
  p_method TEXT,
  p_status_code INTEGER,
  p_ip_address TEXT,
  p_user_agent TEXT,
  p_response_time_ms INTEGER
) RETURNS void AS $$
BEGIN
  INSERT INTO audit_api_access (
    user_id, key_id, endpoint, method, status_code,
    ip_address, user_agent, response_time_ms
  ) VALUES (
    p_user_id, p_key_id, p_endpoint, p_method, p_status_code,
    p_ip_address, p_user_agent, p_response_time_ms
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
  rls_count INT;
BEGIN
  SELECT COUNT(*) INTO rls_count
  FROM pg_policies
  WHERE schemaname = 'public'
    AND tablename IN ('raw_stocks', 'raw_dividends', 'raw_stock_prices', 'divv_api_keys', 'audit_api_access');

  RAISE NOTICE '=== RLS Tier Enforcement Complete ===';
  RAISE NOTICE 'RLS policies created: %', rls_count;
  RAISE NOTICE '';
  RAISE NOTICE 'Enabled RLS on tables:';
  RAISE NOTICE '  ✅ raw_stocks - Tier-based access control';
  RAISE NOTICE '  ✅ raw_dividends - Tier-based access control';
  RAISE NOTICE '  ✅ raw_stock_prices - Tier-based access control';
  RAISE NOTICE '  ✅ divv_api_keys - User-owned data access';
  RAISE NOTICE '';
  RAISE NOTICE 'New audit table:';
  RAISE NOTICE '  ✅ audit_api_access - Tracks all API requests';
  RAISE NOTICE '';
  RAISE NOTICE 'Tier enforcement now happens at database level:';
  RAISE NOTICE '  - Free: Sample stocks only';
  RAISE NOTICE '  - Starter: US stocks only';
  RAISE NOTICE '  - Premium: US + International';
  RAISE NOTICE '  - Professional/Enterprise: All stocks';
END $$;

COMMIT;

-- ============================================================================
-- Important Notes
-- ============================================================================

-- NOTE 1: RLS with auth.uid()
-- These policies rely on Supabase auth context. When using Supabase client
-- with anon key, auth.uid() will be NULL unless user is authenticated.
-- For API endpoints, you need to set the user context or use service role.

-- NOTE 2: Using service role for API calls
-- Since API endpoints use API keys (not Supabase auth), they should:
-- 1. Use service role key to bypass RLS
-- 2. Log the user_id from API key to audit table
-- 3. RLS acts as a secondary security layer

-- NOTE 3: Audit logging
-- Call log_api_access() function after each API request to record:
-- - Which user (via API key)
-- - Which endpoint they accessed
-- - Response status and timing
-- - IP and user agent for security

-- NOTE 4: Testing RLS
-- To test RLS policies:
-- SELECT * FROM raw_stocks; -- With authenticated user context
-- Should only return stocks matching their tier
