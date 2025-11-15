-- Migration: Fix Critical Security Vulnerabilities in Stored Procedures
-- Date: 2025-11-15
-- Description: Addresses 4 CRITICAL and 3 HIGH risk security issues in stored functions
-- Priority: CRITICAL - Deploy immediately

-- ============================================================================
-- CRITICAL FIX 1: SQL Injection in get_latest_dates_by_symbol()
-- ============================================================================

DROP FUNCTION IF EXISTS public.get_latest_dates_by_symbol(text, text);

CREATE OR REPLACE FUNCTION public.get_latest_dates_by_symbol(
    table_name text,
    date_col text DEFAULT 'date'::text
)
RETURNS TABLE(symbol text, latest_date date)
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
BEGIN
    -- Whitelist allowed tables to prevent SQL injection
    IF table_name NOT IN ('divv_stock_prices', 'divv_dividends', 'raw_hourly_prices') THEN
        RAISE EXCEPTION 'Invalid table name: %. Allowed tables: raw_stock_prices, raw_dividends, raw_hourly_prices', table_name;
    END IF;

    -- Whitelist allowed date columns
    IF date_col NOT IN ('date', 'ex_date', 'payment_date', 'timestamp') THEN
        RAISE EXCEPTION 'Invalid column name: %. Allowed columns: date, ex_date, payment_date, timestamp', date_col;
    END IF;

    -- Execute with validated inputs
    RETURN QUERY EXECUTE format('
        SELECT
            symbol::text,
            MAX(%I)::date as latest_date
        FROM %I
        GROUP BY symbol
        ORDER BY symbol
    ', date_col, table_name);
END;
$function$;

-- Revoke public access and grant only to service role
REVOKE EXECUTE ON FUNCTION public.get_latest_dates_by_symbol(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_latest_dates_by_symbol(text, text) TO service_role;

COMMENT ON FUNCTION public.get_latest_dates_by_symbol IS 'Get latest dates by symbol from whitelisted tables (service_role only)';

-- ============================================================================
-- CRITICAL FIX 2: Credential Exposure in get_user_secret()
-- ============================================================================

DROP FUNCTION IF EXISTS public.get_user_secret(uuid);

CREATE OR REPLACE FUNCTION public.get_user_secret(p_user_id uuid)
RETURNS text
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_user_secret TEXT;
  v_calling_user_id UUID;
BEGIN
  -- Get authenticated user ID
  v_calling_user_id := auth.uid();

  -- Only service_role can access user secrets
  IF auth.role() != 'service_role' THEN
    RAISE EXCEPTION 'Unauthorized: Service role required to access user secrets';
  END IF;

  -- Try snaptrade_users first (new location)
  SELECT encrypted_user_secret INTO v_user_secret
  FROM snaptrade_users
  WHERE user_id = p_user_id
  AND is_active = true
  LIMIT 1;

  -- Fallback to broker_connections (legacy)
  IF v_user_secret IS NULL THEN
    SELECT encrypted_credentials INTO v_user_secret
    FROM broker_connections
    WHERE user_id = p_user_id
    AND brokerage = 'SnapTrade'
    AND is_active = true
    ORDER BY created_at DESC
    LIMIT 1;
  END IF;

  RETURN v_user_secret;
END;
$function$;

-- Revoke all access and grant only to service role
REVOKE EXECUTE ON FUNCTION public.get_user_secret(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_user_secret(uuid) TO service_role;

COMMENT ON FUNCTION public.get_user_secret IS 'Get encrypted user secret for SnapTrade integration (service_role only)';

-- ============================================================================
-- CRITICAL FIX 3: Unauthorized Portfolio Access in refresh_marts_after_oauth()
-- ============================================================================

DROP FUNCTION IF EXISTS public.refresh_marts_after_oauth(uuid);

CREATE OR REPLACE FUNCTION public.refresh_marts_after_oauth(p_user_id uuid)
RETURNS TABLE(mart_name text, rows_affected bigint, execution_time_ms bigint)
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_start_time TIMESTAMP;
  v_end_time TIMESTAMP;
  v_rows_affected BIGINT;
  v_list_rows_affected BIGINT;
  v_calling_user_id UUID;
BEGIN
  -- Get authenticated user ID
  v_calling_user_id := auth.uid();

  -- Verify authentication
  IF v_calling_user_id IS NULL THEN
    RAISE EXCEPTION 'Authentication required';
  END IF;

  -- Only allow users to refresh their own data (or service_role)
  IF v_calling_user_id != p_user_id AND auth.role() != 'service_role' THEN
    RAISE EXCEPTION 'Unauthorized: Can only refresh own portfolio data';
  END IF;

  -- First, refresh mart_portfolio_enriched (detailed portfolio data)
  v_start_time := clock_timestamp();

  WITH portfolios_base AS (
    SELECT
      id AS portfolio_id,
      user_id,
      name,
      COALESCE(portfolio_currency, currency) AS portfolio_currency,
      total_value,
      cash_balance,
      snaptrade_account_id,
      account_number,
      is_active,
      created_at,
      updated_at
    FROM stg_portfolios
    WHERE is_active = TRUE
      AND user_id = p_user_id
  ),

  positions_from_snapshots AS (
    SELECT DISTINCT ON (rp.portfolio_id, pos->>'symbol')
      rp.portfolio_id,
      pos->'symbol'->'symbol'->>'symbol' AS symbol,
      pos->'symbol'->'symbol'->>'description' AS stock_name,
      (pos->>'units')::NUMERIC AS shares,
      (pos->>'price')::NUMERIC AS current_price,
      (pos->>'average_purchase_price')::NUMERIC AS average_price,
      ((pos->>'units')::NUMERIC * (pos->>'price')::NUMERIC) AS market_value,
      ((pos->>'units')::NUMERIC * (pos->>'average_purchase_price')::NUMERIC) AS cost_basis,
      (pos->>'open_pnl')::NUMERIC AS open_pnl,
      pos->'currency'->>'code' AS currency
    FROM raw_portfolios rp
    CROSS JOIN LATERAL jsonb_array_elements(rp.positions) AS pos
    WHERE rp.user_id = p_user_id
      AND rp.snapshot_date = (
        SELECT MAX(snapshot_date)
        FROM raw_portfolios rp2
        WHERE rp2.portfolio_id = rp.portfolio_id
          AND rp2.user_id = p_user_id
      )
      AND jsonb_array_length(COALESCE(rp.positions, '[]'::jsonb)) > 0
    ORDER BY rp.portfolio_id, pos->>'symbol', rp.created_at DESC
  ),

  positions_enriched AS (
    SELECT
      portfolio_id,
      jsonb_agg(
        jsonb_build_object(
          'symbol', p.symbol,
          'name', p.stock_name,
          'company', p.stock_name,
          'shares', p.shares,
          'current_price', p.current_price,
          'avg_cost_basis', p.average_price,
          'market_value', p.market_value,
          'cost_basis', p.cost_basis,
          'unrealized_gain_loss', p.open_pnl,
          'dividend_yield', COALESCE(s.dividend_yield, 0),
          'total_dividends', 0,
          'overall_rating', COALESCE(s.overall_rating, 'N/A'),
          'frequency', 'N/A',
          'annual_dividend_amount', COALESCE(s.annual_dividend_amount, 0)
        ) ORDER BY p.market_value DESC NULLS LAST
      ) AS positions_json,
      SUM(p.market_value) AS total_market_value,
      SUM(p.cost_basis) AS total_cost_basis,
      SUM(p.open_pnl) AS total_unrealized_gain_loss
    FROM positions_from_snapshots p
    LEFT JOIN dim_stocks s ON p.symbol = s.symbol
    WHERE p.shares > 0
    GROUP BY portfolio_id
  ),

  recent_activities AS (
    SELECT
      sp.id AS portfolio_id,
      jsonb_agg(
        jsonb_build_object(
          'id', ra.id,
          'symbol', ra.symbol,
          'type', ra.type,
          'amount', ra.amount,
          'shares', ra.shares,
          'price_per_share', ra.price_per_share,
          'date', ra.date,
          'created_at', ra.created_at,
          'currency', ra.currency
        ) ORDER BY ra.date DESC, ra.created_at DESC
      ) AS activities_json
    FROM (
      SELECT
        id,
        snaptrade_account_id,
        symbol,
        type,
        amount,
        shares,
        price_per_share,
        date,
        created_at,
        currency,
        ROW_NUMBER() OVER (PARTITION BY snaptrade_account_id ORDER BY date DESC, created_at DESC) AS rn
      FROM raw_activities
      WHERE user_id = p_user_id
    ) ra
    INNER JOIN stg_portfolios sp ON ra.snaptrade_account_id = sp.snaptrade_account_id
    WHERE ra.rn <= 50
    GROUP BY sp.id
  ),

  dividend_totals AS (
    SELECT
      sp.id AS portfolio_id,
      SUM(ra.amount) AS total_dividend_income
    FROM raw_activities ra
    INNER JOIN stg_portfolios sp ON ra.snaptrade_account_id = sp.snaptrade_account_id
    WHERE ra.type IN ('DIVIDEND', 'DIV')
      AND ra.user_id = p_user_id
    GROUP BY sp.id
  ),

  refreshed_enriched AS (
    INSERT INTO mart_portfolio_enriched (
      id,
      portfolio_id,
      user_id,
      name,
      portfolio_currency,
      total_value,
      total_cost_basis,
      total_unrealized_gain_loss,
      total_dividend_income,
      positions,
      activities,
      cash_balance,
      snaptrade_account_id,
      account_number,
      is_active,
      created_at,
      updated_at,
      mart_refreshed_at
    )
    SELECT
      gen_random_uuid(),
      p.portfolio_id,
      p.user_id,
      p.name,
      p.portfolio_currency,
      COALESCE(pe.total_market_value, p.total_value, 0),
      COALESCE(pe.total_cost_basis, 0),
      COALESCE(pe.total_unrealized_gain_loss, 0),
      COALESCE(dt.total_dividend_income, 0),
      COALESCE(pe.positions_json, '[]'::jsonb),
      COALESCE(ra.activities_json, '[]'::jsonb),
      p.cash_balance,
      p.snaptrade_account_id,
      p.account_number,
      p.is_active,
      p.created_at,
      p.updated_at,
      NOW()
    FROM portfolios_base p
    LEFT JOIN positions_enriched pe ON p.portfolio_id = pe.portfolio_id
    LEFT JOIN recent_activities ra ON p.portfolio_id = ra.portfolio_id
    LEFT JOIN dividend_totals dt ON p.portfolio_id = dt.portfolio_id
    ON CONFLICT (portfolio_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      portfolio_currency = EXCLUDED.portfolio_currency,
      total_value = EXCLUDED.total_value,
      total_cost_basis = EXCLUDED.total_cost_basis,
      total_unrealized_gain_loss = EXCLUDED.total_unrealized_gain_loss,
      total_dividend_income = EXCLUDED.total_dividend_income,
      positions = EXCLUDED.positions,
      activities = EXCLUDED.activities,
      cash_balance = EXCLUDED.cash_balance,
      is_active = EXCLUDED.is_active,
      updated_at = EXCLUDED.updated_at,
      mart_refreshed_at = NOW()
    RETURNING 1
  )
  SELECT COUNT(*) INTO v_rows_affected FROM refreshed_enriched;

  v_end_time := clock_timestamp();

  RETURN QUERY SELECT
    'mart_portfolio_enriched'::TEXT,
    v_rows_affected,
    EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::BIGINT;

  -- Second, refresh mart_portfolio_list_with_holdings (for GET /portfolios API)
  v_start_time := clock_timestamp();

  WITH portfolios_base AS (
    SELECT
      id AS portfolio_id,
      user_id,
      name,
      snaptrade_account_id,
      account_number,
      total_value,
      COALESCE(portfolio_currency, currency) AS currency,
      cash_balance,
      is_active,
      created_at,
      updated_at
    FROM stg_portfolios
    WHERE user_id = p_user_id
  ),

  -- Extract holdings from raw_portfolios JSONB
  holdings_from_snapshots AS (
    SELECT DISTINCT ON (rp.portfolio_id, pos->>'symbol')
      rp.portfolio_id,
      pos->'symbol'->'symbol'->>'symbol' AS symbol,
      pos->'symbol'->'symbol'->>'description' AS stock_name,
      (pos->>'units')::NUMERIC AS shares,
      (pos->>'price')::NUMERIC AS current_price,
      (pos->>'average_purchase_price')::NUMERIC AS average_price,
      ((pos->>'units')::NUMERIC * (pos->>'price')::NUMERIC) AS market_value,
      ((pos->>'units')::NUMERIC * (pos->>'average_purchase_price')::NUMERIC) AS cost_basis,
      (pos->>'open_pnl')::NUMERIC AS open_pnl,
      rp.snapshot_date
    FROM raw_portfolios rp
    CROSS JOIN LATERAL jsonb_array_elements(rp.positions) AS pos
    WHERE rp.user_id = p_user_id
      AND rp.snapshot_date = (
        SELECT MAX(snapshot_date)
        FROM raw_portfolios rp2
        WHERE rp2.portfolio_id = rp.portfolio_id
          AND rp2.user_id = p_user_id
      )
      AND jsonb_array_length(COALESCE(rp.positions, '[]'::jsonb)) > 0
    ORDER BY rp.portfolio_id, pos->>'symbol', rp.created_at DESC
  ),

  -- Enrich with dividend data
  holdings_enriched AS (
    SELECT
      h.portfolio_id,
      h.symbol,
      h.stock_name,
      h.shares,
      h.current_price,
      h.average_price,
      h.market_value,
      h.cost_basis,
      h.open_pnl,
      h.snapshot_date,
      COALESCE(s.dividend_yield, 0) AS dividend_yield,
      COALESCE(s.annual_dividend_amount, 0) AS annual_dividend_amount,
      COALESCE(s.dividend_frequency, 'N/A') AS frequency
    FROM holdings_from_snapshots h
    LEFT JOIN dim_stocks s ON h.symbol = s.symbol
    WHERE h.shares > 0
  ),

  -- Aggregate holdings summary per portfolio
  holdings_summary AS (
    SELECT
      portfolio_id,
      COUNT(*) AS holdings_count,
      SUM(shares) AS total_shares,
      SUM(market_value) AS total_market_value,
      SUM(cost_basis) AS holdings_total_cost_basis,
      SUM(open_pnl) AS total_unrealized_pnl,
      AVG(CASE WHEN dividend_yield > 0 THEN dividend_yield END) AS avg_dividend_yield,
      SUM(COALESCE(annual_dividend_amount, 0) * COALESCE(shares, 0)) / 12.0 AS estimated_monthly_dividends,
      MAX(snapshot_date) AS last_snapshot_date
    FROM holdings_enriched
    GROUP BY portfolio_id
  ),

  -- Create JSONB stocks array
  holdings_details AS (
    SELECT
      portfolio_id,
      jsonb_agg(
        jsonb_build_object(
          'symbol', symbol,
          'name', stock_name,
          'shares', shares,
          'price', current_price,
          'averagePrice', average_price,
          'marketValue', market_value,
          'costBasis', cost_basis,
          'cost_basis', cost_basis,
          'openPnl', open_pnl,
          'dividendYield', dividend_yield,
          'frequency', frequency,
          'annual_dividend', annual_dividend_amount,
          'annualDividendAmount', COALESCE(annual_dividend_amount, 0)
        ) ORDER BY market_value DESC NULLS LAST
      ) AS stocks_json
    FROM holdings_enriched
    GROUP BY portfolio_id
  ),

  refreshed_list AS (
    INSERT INTO mart_portfolio_list_with_holdings (
      portfolio_id,
      user_id,
      name,
      snaptrade_account_id,
      account_number,
      current_total_value,
      estimated_monthly_dividends,
      base_currency,
      cash_balance,
      holdings_count,
      total_shares_held,
      holdings_market_value,
      holdings_cost_basis,
      unrealized_gain_loss,
      avg_dividend_yield,
      unrealized_gain_loss_percent,
      portfolio_yield_percent,
      last_snapshot_date,
      data_freshness,
      is_active,
      has_holdings,
      is_broker_connected,
      stocks_json,
      created_at,
      updated_at,
      mart_refreshed_at
    )
    SELECT
      p.portfolio_id,
      p.user_id,
      p.name,
      p.snaptrade_account_id,
      p.account_number,
      COALESCE(h.total_market_value, 0) + COALESCE(p.cash_balance, 0) AS current_total_value,
      h.estimated_monthly_dividends,
      p.currency AS base_currency,
      COALESCE(p.cash_balance, 0) AS cash_balance,
      COALESCE(h.holdings_count, 0) AS holdings_count,
      COALESCE(h.total_shares, 0) AS total_shares_held,
      COALESCE(h.total_market_value, 0) AS holdings_market_value,
      COALESCE(h.holdings_total_cost_basis, 0) AS holdings_cost_basis,
      COALESCE(h.total_unrealized_pnl, 0) AS unrealized_gain_loss,
      h.avg_dividend_yield,
      CASE
        WHEN h.holdings_total_cost_basis > 0 THEN
          (h.total_unrealized_pnl / h.holdings_total_cost_basis) * 100
        ELSE NULL
      END AS unrealized_gain_loss_percent,
      CASE
        WHEN h.total_market_value > 0 AND h.estimated_monthly_dividends IS NOT NULL THEN
          (h.estimated_monthly_dividends * 12 / h.total_market_value) * 100
        ELSE NULL
      END AS portfolio_yield_percent,
      h.last_snapshot_date,
      CASE
        WHEN h.last_snapshot_date >= CURRENT_DATE THEN 'current'
        WHEN h.last_snapshot_date >= CURRENT_DATE - INTERVAL '1 day' THEN 'recent'
        WHEN h.last_snapshot_date >= CURRENT_DATE - INTERVAL '7 days' THEN 'stale'
        ELSE 'outdated'
      END AS data_freshness,
      p.is_active,
      (h.holdings_count > 0) AS has_holdings,
      (p.snaptrade_account_id IS NOT NULL) AS is_broker_connected,
      COALESCE(hd.stocks_json, '[]'::jsonb) AS stocks_json,
      p.created_at,
      p.updated_at,
      NOW() AS mart_refreshed_at
    FROM portfolios_base p
    LEFT JOIN holdings_summary h ON p.portfolio_id = h.portfolio_id
    LEFT JOIN holdings_details hd ON p.portfolio_id = hd.portfolio_id
    ON CONFLICT (portfolio_id)
    DO UPDATE SET
      name = EXCLUDED.name,
      snaptrade_account_id = EXCLUDED.snaptrade_account_id,
      account_number = EXCLUDED.account_number,
      current_total_value = EXCLUDED.current_total_value,
      estimated_monthly_dividends = EXCLUDED.estimated_monthly_dividends,
      base_currency = EXCLUDED.base_currency,
      cash_balance = EXCLUDED.cash_balance,
      holdings_count = EXCLUDED.holdings_count,
      total_shares_held = EXCLUDED.total_shares_held,
      holdings_market_value = EXCLUDED.holdings_market_value,
      holdings_cost_basis = EXCLUDED.holdings_cost_basis,
      unrealized_gain_loss = EXCLUDED.unrealized_gain_loss,
      avg_dividend_yield = EXCLUDED.avg_dividend_yield,
      unrealized_gain_loss_percent = EXCLUDED.unrealized_gain_loss_percent,
      portfolio_yield_percent = EXCLUDED.portfolio_yield_percent,
      last_snapshot_date = EXCLUDED.last_snapshot_date,
      data_freshness = EXCLUDED.data_freshness,
      is_active = EXCLUDED.is_active,
      has_holdings = EXCLUDED.has_holdings,
      is_broker_connected = EXCLUDED.is_broker_connected,
      stocks_json = EXCLUDED.stocks_json,
      updated_at = EXCLUDED.updated_at,
      mart_refreshed_at = NOW()
    RETURNING 1
  )
  SELECT COUNT(*) INTO v_list_rows_affected FROM refreshed_list;

  v_end_time := clock_timestamp();

  RETURN QUERY SELECT
    'mart_portfolio_list_with_holdings'::TEXT,
    v_list_rows_affected,
    EXTRACT(MILLISECONDS FROM (v_end_time - v_start_time))::BIGINT;
END;
$function$;

-- Revoke public access and grant to authenticated users and service role
REVOKE EXECUTE ON FUNCTION public.refresh_marts_after_oauth(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.refresh_marts_after_oauth(uuid) TO authenticated, service_role;

COMMENT ON FUNCTION public.refresh_marts_after_oauth IS 'Refresh portfolio mart tables after OAuth connection (authenticated users only, own data only)';

-- ============================================================================
-- CRITICAL FIX 4: Credential Tampering in upsert_user_secret()
-- ============================================================================

DROP FUNCTION IF EXISTS public.upsert_user_secret(uuid, text, text);

CREATE OR REPLACE FUNCTION public.upsert_user_secret(
    p_user_id uuid,
    p_snaptrade_user_id text,
    p_encrypted_secret text
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_record_id UUID;
  v_calling_user_id UUID;
BEGIN
  -- Get authenticated user
  v_calling_user_id := auth.uid();

  -- Only service_role or the user themselves can upsert
  IF v_calling_user_id != p_user_id AND auth.role() != 'service_role' THEN
    RAISE EXCEPTION 'Unauthorized: Cannot modify other users credentials';
  END IF;

  -- Validate inputs to prevent injection of malicious data
  IF p_encrypted_secret IS NULL OR length(p_encrypted_secret) < 10 THEN
    RAISE EXCEPTION 'Invalid encrypted secret - must be at least 10 characters';
  END IF;

  IF p_snaptrade_user_id IS NULL OR length(p_snaptrade_user_id) < 5 THEN
    RAISE EXCEPTION 'Invalid SnapTrade user ID';
  END IF;

  -- Upsert into snaptrade_users (primary storage)
  INSERT INTO snaptrade_users (user_id, snaptrade_user_id, encrypted_user_secret, is_active, created_at, updated_at)
  VALUES (p_user_id, p_snaptrade_user_id, p_encrypted_secret, true, NOW(), NOW())
  ON CONFLICT (user_id)
  DO UPDATE SET
    snaptrade_user_id = p_snaptrade_user_id,
    encrypted_user_secret = p_encrypted_secret,
    is_active = true,
    updated_at = NOW()
  RETURNING id INTO v_record_id;

  -- Also update broker_connections for backward compatibility
  UPDATE broker_connections
  SET
    encrypted_credentials = p_encrypted_secret,
    is_active = true,
    updated_at = NOW()
  WHERE user_id = p_user_id
  AND brokerage = 'SnapTrade';

  -- If no broker_connection exists, create one
  IF NOT FOUND THEN
    INSERT INTO broker_connections (user_id, connection_id, brokerage, encrypted_credentials, is_active, created_at, updated_at)
    VALUES (p_user_id, p_snaptrade_user_id, 'SnapTrade', p_encrypted_secret, true, NOW(), NOW())
    ON CONFLICT (user_id) DO NOTHING;
  END IF;

  RETURN v_record_id;
END;
$function$;

-- Revoke public access and grant to authenticated users and service role
REVOKE EXECUTE ON FUNCTION public.upsert_user_secret(uuid, text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.upsert_user_secret(uuid, text, text) TO authenticated, service_role;

COMMENT ON FUNCTION public.upsert_user_secret IS 'Upsert encrypted SnapTrade user secret (authenticated users only, own data only)';

-- ============================================================================
-- HIGH PRIORITY FIX 5: Usage Manipulation in increment_key_usage()
-- ============================================================================

DROP FUNCTION IF EXISTS public.increment_key_usage(uuid);

CREATE OR REPLACE FUNCTION public.increment_key_usage(key_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
BEGIN
    -- Only service_role can call this (from rate limiter middleware)
    IF auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Unauthorized: Service role required';
    END IF;

    UPDATE divv_api_keys
    SET
        monthly_usage = monthly_usage + 1,
        minute_usage = minute_usage + 1,
        request_count = request_count + 1,
        last_used_at = NOW(),
        updated_at = NOW()
    WHERE id = key_id;
END;
$function$;

-- Revoke all access and grant only to service role
REVOKE EXECUTE ON FUNCTION public.increment_key_usage(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.increment_key_usage(uuid) TO service_role;

COMMENT ON FUNCTION public.increment_key_usage IS 'Increment API key usage counters (service_role only, called from rate limiter)';

-- ============================================================================
-- HIGH PRIORITY FIX 6: Unauthorized Tier Access in get_tier_limits()
-- ============================================================================

DROP FUNCTION IF EXISTS public.get_tier_limits(uuid);

CREATE OR REPLACE FUNCTION public.get_tier_limits(p_api_key_id uuid)
RETURNS TABLE(
    tier character varying,
    monthly_call_limit integer,
    calls_per_minute integer,
    burst_limit integer,
    stock_coverage jsonb,
    features jsonb
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_key_user_id UUID;
  v_calling_user_id UUID;
BEGIN
  -- Get the user who owns this API key
  SELECT user_id INTO v_key_user_id
  FROM divv_api_keys
  WHERE id = p_api_key_id
  AND is_active = true;

  -- If key doesn't exist or is inactive, return no rows
  IF v_key_user_id IS NULL THEN
    RETURN;
  END IF;

  -- Get authenticated user
  v_calling_user_id := auth.uid();

  -- Verify ownership (or allow service_role)
  IF auth.role() != 'service_role' AND v_calling_user_id != v_key_user_id THEN
    RAISE EXCEPTION 'Unauthorized: Can only view own API key limits';
  END IF;

  RETURN QUERY
  SELECT
      tl.tier,
      tl.monthly_call_limit,
      tl.calls_per_minute,
      tl.burst_limit,
      tl.stock_coverage,
      tl.features
  FROM divv_api_keys ak
  JOIN divv_tier_limits tl ON ak.tier = tl.tier
  WHERE ak.id = p_api_key_id AND ak.is_active = true;
END;
$function$;

-- Revoke public access and grant to authenticated users and service role
REVOKE EXECUTE ON FUNCTION public.get_tier_limits(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_tier_limits(uuid) TO authenticated, service_role;

COMMENT ON FUNCTION public.get_tier_limits IS 'Get tier limits for an API key (authenticated users only, own keys only)';

-- ============================================================================
-- HIGH PRIORITY FIX 7: Missing Access Control in cleanup_old_application_logs()
-- ============================================================================

DROP FUNCTION IF EXISTS public.cleanup_old_application_logs();

CREATE OR REPLACE FUNCTION public.cleanup_old_application_logs()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
  v_deleted_count INTEGER;
BEGIN
  -- Only service_role can cleanup logs
  IF auth.role() != 'service_role' THEN
    RAISE EXCEPTION 'Unauthorized: Admin/service role required';
  END IF;

  -- Delete old logs
  DELETE FROM application_logs
  WHERE timestamp < NOW() - INTERVAL '30 days';

  GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

  RAISE NOTICE 'Deleted % old application log records', v_deleted_count;
END;
$function$;

-- Revoke all access and grant only to service role
REVOKE EXECUTE ON FUNCTION public.cleanup_old_application_logs() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.cleanup_old_application_logs() TO service_role;

COMMENT ON FUNCTION public.cleanup_old_application_logs IS 'Delete application logs older than 30 days (service_role only)';

-- ============================================================================
-- MEDIUM PRIORITY FIX 8: Symbol Enumeration in is_symbol_accessible()
-- ============================================================================

DROP FUNCTION IF EXISTS public.is_symbol_accessible(character varying, character varying);

CREATE OR REPLACE FUNCTION public.is_symbol_accessible(
    p_symbol character varying,
    p_tier character varying
)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
    v_coverage_type VARCHAR(50);
    v_calling_user_id UUID;
    v_user_tier VARCHAR(50);
BEGIN
    -- Get authenticated user
    v_calling_user_id := auth.uid();

    -- Require authentication for non-service-role calls
    IF v_calling_user_id IS NULL AND auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Authentication required';
    END IF;

    -- If not service_role, verify the user actually has the tier they're querying
    IF auth.role() != 'service_role' THEN
        SELECT tier INTO v_user_tier
        FROM divv_api_keys
        WHERE user_id = v_calling_user_id
        AND is_active = true
        LIMIT 1;

        -- User can only check their own tier
        IF v_user_tier != p_tier THEN
            RAISE EXCEPTION 'Unauthorized: Can only check symbol access for own tier';
        END IF;
    END IF;

    -- Get coverage type for tier
    SELECT stock_coverage->>'type' INTO v_coverage_type
    FROM divv_tier_limits
    WHERE tier = p_tier;

    -- If tier doesn't exist, return false
    IF v_coverage_type IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Free tier: check sample list
    IF v_coverage_type = 'sample' THEN
        RETURN EXISTS (
            SELECT 1 FROM divv_free_tier_stocks WHERE symbol = p_symbol
        );
    END IF;

    -- US only: check if symbol is US-based
    IF v_coverage_type = 'us_only' THEN
        RETURN EXISTS (
            SELECT 1 FROM raw_stocks
            WHERE symbol = p_symbol AND exchange IN ('NASDAQ', 'NYSE', 'AMEX')
        );
    END IF;

    -- International/Global/Custom: all symbols accessible
    RETURN TRUE;
END;
$function$;

-- Revoke public access and grant to authenticated users and service role
REVOKE EXECUTE ON FUNCTION public.is_symbol_accessible(character varying, character varying) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_symbol_accessible(character varying, character varying) TO authenticated, service_role;

COMMENT ON FUNCTION public.is_symbol_accessible IS 'Check if symbol is accessible for a tier (authenticated users only, own tier only)';

-- ============================================================================
-- MEDIUM PRIORITY FIX 9: Unprotected Reset in reset_monthly_usage_counters()
-- ============================================================================

DROP FUNCTION IF EXISTS public.reset_monthly_usage_counters();

CREATE OR REPLACE FUNCTION public.reset_monthly_usage_counters()
RETURNS integer
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
    v_reset_count INTEGER;
BEGIN
    -- Only service_role can reset counters
    IF auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Unauthorized: Admin/service role required';
    END IF;

    UPDATE divv_api_keys
    SET
        monthly_usage = 0,
        monthly_usage_reset_at = NOW() + INTERVAL '1 month',
        updated_at = NOW()
    WHERE
        is_active = true
        AND monthly_usage_reset_at <= NOW();

    GET DIAGNOSTICS v_reset_count = ROW_COUNT;

    RAISE NOTICE 'Reset % API keys monthly usage counters', v_reset_count;

    RETURN v_reset_count;
END;
$function$;

-- Revoke all access and grant only to service role
REVOKE EXECUTE ON FUNCTION public.reset_monthly_usage_counters() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.reset_monthly_usage_counters() TO service_role;

COMMENT ON FUNCTION public.reset_monthly_usage_counters IS 'Reset monthly usage counters for expired periods (service_role only, typically called by cron)';

-- ============================================================================
-- LOW PRIORITY FIX 10: Missing Validation in upsert_google_user()
-- ============================================================================

DROP FUNCTION IF EXISTS public.upsert_google_user(character varying, character varying, character varying, text);

CREATE OR REPLACE FUNCTION public.upsert_google_user(
    p_google_id character varying,
    p_email character varying,
    p_name character varying,
    p_picture_url text
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
DECLARE
    v_user_id UUID;
BEGIN
    -- Only service_role can call this (after Google OAuth verification)
    IF auth.role() != 'service_role' THEN
        RAISE EXCEPTION 'Unauthorized: Must be called by OAuth handler';
    END IF;

    -- Validate email format
    IF p_email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$' THEN
        RAISE EXCEPTION 'Invalid email format: %', p_email;
    END IF;

    -- Validate google_id is not empty and has reasonable length
    IF p_google_id IS NULL OR length(p_google_id) < 10 THEN
        RAISE EXCEPTION 'Invalid google_id';
    END IF;

    -- Validate name is not empty
    IF p_name IS NULL OR length(p_name) < 1 THEN
        RAISE EXCEPTION 'Invalid name - cannot be empty';
    END IF;

    -- Try to find existing user by google_id
    SELECT id INTO v_user_id
    FROM divv_users
    WHERE google_id = p_google_id;

    IF v_user_id IS NOT NULL THEN
        -- Update existing user
        UPDATE divv_users
        SET
            email = p_email,
            name = p_name,
            picture_url = p_picture_url,
            last_login_at = NOW(),
            updated_at = NOW()
        WHERE id = v_user_id;

        RETURN v_user_id;
    ELSE
        -- Insert new user
        INSERT INTO divv_users (google_id, email, name, picture_url, last_login_at, created_at, updated_at)
        VALUES (p_google_id, p_email, p_name, p_picture_url, NOW(), NOW(), NOW())
        RETURNING id INTO v_user_id;

        RETURN v_user_id;
    END IF;
END;
$function$;

-- Revoke all access and grant only to service role
REVOKE EXECUTE ON FUNCTION public.upsert_google_user(character varying, character varying, character varying, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.upsert_google_user(character varying, character varying, character varying, text) TO service_role;

COMMENT ON FUNCTION public.upsert_google_user IS 'Upsert user from Google OAuth (service_role only, called from OAuth handler)';

-- ============================================================================
-- Migration complete
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Critical security fixes applied successfully';
    RAISE NOTICE '';
    RAISE NOTICE '🔒 Fixed Functions:';
    RAISE NOTICE '   CRITICAL:';
    RAISE NOTICE '   ✅ get_latest_dates_by_symbol() - Added whitelist validation';
    RAISE NOTICE '   ✅ get_user_secret() - Restricted to service_role only';
    RAISE NOTICE '   ✅ refresh_marts_after_oauth() - Added ownership check';
    RAISE NOTICE '   ✅ upsert_user_secret() - Added ownership check + validation';
    RAISE NOTICE '';
    RAISE NOTICE '   HIGH PRIORITY:';
    RAISE NOTICE '   ✅ increment_key_usage() - Restricted to service_role only';
    RAISE NOTICE '   ✅ get_tier_limits() - Added ownership verification';
    RAISE NOTICE '   ✅ cleanup_old_application_logs() - Restricted to service_role';
    RAISE NOTICE '';
    RAISE NOTICE '   MEDIUM PRIORITY:';
    RAISE NOTICE '   ✅ is_symbol_accessible() - Added authentication + tier verification';
    RAISE NOTICE '   ✅ reset_monthly_usage_counters() - Restricted to service_role';
    RAISE NOTICE '';
    RAISE NOTICE '   LOW PRIORITY:';
    RAISE NOTICE '   ✅ upsert_google_user() - Added validation + service_role restriction';
    RAISE NOTICE '';
    RAISE NOTICE '🔐 Access Control Summary:';
    RAISE NOTICE '   - All functions now have proper authentication/authorization';
    RAISE NOTICE '   - PUBLIC execute permissions revoked from all functions';
    RAISE NOTICE '   - Service_role required for admin functions';
    RAISE NOTICE '   - Authenticated users can only access their own data';
    RAISE NOTICE '';
    RAISE NOTICE '⚠️  IMPORTANT: Update your application code to ensure:';
    RAISE NOTICE '   1. API middleware uses service_role for rate limiting functions';
    RAISE NOTICE '   2. OAuth handlers use service_role credentials';
    RAISE NOTICE '   3. User-facing functions are called with authenticated user context';
END $$;
