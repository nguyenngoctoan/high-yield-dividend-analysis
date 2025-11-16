-- Migration: Create ETF Time Series Materialized Views
-- Date: November 16, 2025
-- Purpose: Create materialized views for time series analysis of ETF metrics
--
-- These views extract key metrics from JSONB columns and create normalized
-- time series data for tracking ETF performance, distributions, and fund metrics over time
--
-- Views created:
-- - mv_etf_timeseries_nav: NAV and fund price history
-- - mv_etf_timeseries_distributions: Distribution history and rates
-- - mv_etf_timeseries_performance: Performance metrics over time
-- - mv_etf_timeseries_all_providers: Combined view of all ETF metrics

BEGIN;

-- ============================================================================
-- Create NAV and Price Time Series View
-- ============================================================================

CREATE MATERIALIZED VIEW mv_etf_timeseries_nav AS
SELECT
    'yieldmax'::text as provider,
    ticker,
    fund_name,
    scraped_at::date as snapshot_date,
    scraped_at,
    -- Extract NAV from fund_overview if available
    (fund_overview->>'nav')::numeric as nav,
    (fund_overview->>'nav_change')::numeric as nav_change,
    (fund_overview->>'nav_change_percent')::numeric as nav_change_percent,
    -- Extract price data
    (fund_overview->>'price')::numeric as current_price,
    (fund_overview->>'premium_discount')::numeric as premium_discount_pct
FROM raw_etfs_yieldmax
UNION ALL
SELECT 'roundhill', ticker, fund_name, scraped_at::date, scraped_at,
    (fund_details->>'nav')::numeric,
    (fund_details->>'nav_change')::numeric,
    (fund_details->>'nav_change_pct')::numeric,
    (fund_details->>'price')::numeric,
    (fund_details->>'premium_discount')::numeric
FROM raw_etfs_roundhill
UNION ALL
SELECT 'neos', ticker, fund_name, scraped_at::date, scraped_at,
    (fund_details->>'nav')::numeric,
    (fund_details->>'nav_change')::numeric,
    (fund_details->>'nav_change_pct')::numeric,
    (fund_details->>'price')::numeric,
    (fund_details->>'premium_discount')::numeric
FROM raw_etfs_neos
UNION ALL
SELECT 'kurv', ticker, fund_name, scraped_at::date, scraped_at,
    (fund_details->>'nav')::numeric,
    (fund_details->>'nav_change')::numeric,
    (fund_details->>'nav_change_pct')::numeric,
    (fund_details->>'price')::numeric,
    (fund_details->>'premium_discount')::numeric
FROM raw_etfs_kurv
UNION ALL
SELECT 'graniteshares', ticker, fund_name, scraped_at::date, scraped_at,
    (fund_details->>'nav')::numeric,
    (fund_details->>'nav_change')::numeric,
    (fund_details->>'nav_change_pct')::numeric,
    (fund_details->>'price')::numeric,
    (fund_details->>'premium_discount')::numeric
FROM raw_etfs_graniteshares
UNION ALL
SELECT 'defiance', ticker, fund_name, scraped_at::date, scraped_at,
    (fund_details->>'nav')::numeric,
    (fund_details->>'nav_change')::numeric,
    (fund_details->>'nav_change_pct')::numeric,
    (fund_details->>'price')::numeric,
    (fund_details->>'premium_discount')::numeric
FROM raw_etfs_defiance
UNION ALL
SELECT 'globalx', ticker, fund_name, scraped_at::date, scraped_at,
    (fund_details->>'nav')::numeric,
    (fund_details->>'nav_change')::numeric,
    (fund_details->>'nav_change_pct')::numeric,
    (fund_details->>'price')::numeric,
    (fund_details->>'premium_discount')::numeric
FROM raw_etfs_globalx
UNION ALL
SELECT 'purpose', ticker, fund_name, scraped_at::date, scraped_at,
    (fund_details->>'nav')::numeric,
    (fund_details->>'nav_change')::numeric,
    (fund_details->>'nav_change_pct')::numeric,
    (fund_details->>'price')::numeric,
    (fund_details->>'premium_discount')::numeric
FROM raw_etfs_purpose
ORDER BY provider, ticker, snapshot_date DESC;

-- Create index for faster queries
CREATE INDEX idx_mv_etf_timeseries_nav_ticker_date
ON mv_etf_timeseries_nav(ticker, snapshot_date DESC);

CREATE INDEX idx_mv_etf_timeseries_nav_provider
ON mv_etf_timeseries_nav(provider);

-- ============================================================================
-- Create Distribution History Time Series View
-- ============================================================================

CREATE MATERIALIZED VIEW mv_etf_timeseries_distributions AS
WITH distributions_data AS (
    SELECT
        'yieldmax'::text as provider,
        ticker,
        fund_name,
        scraped_at,
        scraped_at::date as snapshot_date,
        distributions
    FROM raw_etfs_yieldmax
    UNION ALL
    SELECT 'roundhill', ticker, fund_name, scraped_at, scraped_at::date, distributions
    FROM raw_etfs_roundhill
    UNION ALL
    SELECT 'neos', ticker, fund_name, scraped_at, scraped_at::date, distributions
    FROM raw_etfs_neos
    UNION ALL
    SELECT 'kurv', ticker, fund_name, scraped_at, scraped_at::date, distributions
    FROM raw_etfs_kurv
    UNION ALL
    SELECT 'graniteshares', ticker, fund_name, scraped_at, scraped_at::date, distributions
    FROM raw_etfs_graniteshares
    UNION ALL
    SELECT 'defiance', ticker, fund_name, scraped_at, scraped_at::date, distributions
    FROM raw_etfs_defiance
    UNION ALL
    SELECT 'globalx', ticker, fund_name, scraped_at, scraped_at::date, distributions
    FROM raw_etfs_globalx
    UNION ALL
    SELECT 'purpose', ticker, fund_name, scraped_at, scraped_at::date, distributions
    FROM raw_etfs_purpose
)
SELECT
    provider,
    ticker,
    fund_name,
    snapshot_date,
    scraped_at,
    -- Distribution details (varies by provider)
    (distributions->>'most_recent_distribution')::numeric as most_recent_distribution,
    (distributions->>'distribution_rate')::numeric as distribution_rate,
    (distributions->>'distribution_frequency')::text as distribution_frequency,
    (distributions->>'annualized_yield')::numeric as annualized_yield,
    distributions as raw_distributions_json
FROM distributions_data
ORDER BY provider, ticker, snapshot_date DESC;

CREATE INDEX idx_mv_etf_timeseries_distributions_ticker_date
ON mv_etf_timeseries_distributions(ticker, snapshot_date DESC);

CREATE INDEX idx_mv_etf_timeseries_distributions_provider
ON mv_etf_timeseries_distributions(provider);

-- ============================================================================
-- Create Performance Metrics Time Series View
-- ============================================================================

CREATE MATERIALIZED VIEW mv_etf_timeseries_performance AS
WITH performance_data AS (
    SELECT
        'yieldmax'::text as provider,
        ticker,
        fund_name,
        scraped_at,
        scraped_at::date as snapshot_date,
        performance_month_end,
        performance_quarter_end
    FROM raw_etfs_yieldmax
    UNION ALL
    SELECT 'roundhill', ticker, fund_name, scraped_at, scraped_at::date,
        performance_data, NULL
    FROM raw_etfs_roundhill
    UNION ALL
    SELECT 'neos', ticker, fund_name, scraped_at, scraped_at::date,
        performance_data, NULL
    FROM raw_etfs_neos
    UNION ALL
    SELECT 'kurv', ticker, fund_name, scraped_at, scraped_at::date,
        performance_data, NULL
    FROM raw_etfs_kurv
    UNION ALL
    SELECT 'graniteshares', ticker, fund_name, scraped_at, scraped_at::date,
        performance_data, NULL
    FROM raw_etfs_graniteshares
    UNION ALL
    SELECT 'defiance', ticker, fund_name, scraped_at, scraped_at::date,
        performance_data, NULL
    FROM raw_etfs_defiance
    UNION ALL
    SELECT 'globalx', ticker, fund_name, scraped_at, scraped_at::date,
        performance_data, NULL
    FROM raw_etfs_globalx
    UNION ALL
    SELECT 'purpose', ticker, fund_name, scraped_at, scraped_at::date,
        performance_data, NULL
    FROM raw_etfs_purpose
)
SELECT
    provider,
    ticker,
    fund_name,
    snapshot_date,
    scraped_at,
    -- Month-end performance
    (performance_month_end->>'1_month')::numeric as perf_1m,
    (performance_month_end->>'3_month')::numeric as perf_3m,
    (performance_month_end->>'6_month')::numeric as perf_6m,
    (performance_month_end->>'1_year')::numeric as perf_1y,
    (performance_month_end->>'3_year')::numeric as perf_3y,
    (performance_month_end->>'5_year')::numeric as perf_5y,
    (performance_month_end->>'since_inception')::numeric as perf_inception,
    -- Quarter-end performance (if available)
    (performance_quarter_end->>'1_month')::numeric as perf_q_1m,
    (performance_quarter_end->>'3_month')::numeric as perf_q_3m,
    (performance_quarter_end->>'since_inception')::numeric as perf_q_inception
FROM performance_data
ORDER BY provider, ticker, snapshot_date DESC;

CREATE INDEX idx_mv_etf_timeseries_performance_ticker_date
ON mv_etf_timeseries_performance(ticker, snapshot_date DESC);

CREATE INDEX idx_mv_etf_timeseries_performance_provider
ON mv_etf_timeseries_performance(provider);

-- ============================================================================
-- Create Combined ETF Metrics Time Series View
-- ============================================================================

CREATE MATERIALIZED VIEW mv_etf_timeseries_summary AS
SELECT
    n.provider,
    n.ticker,
    n.fund_name,
    n.snapshot_date,
    n.scraped_at,
    -- NAV metrics
    n.nav,
    n.nav_change,
    n.nav_change_percent,
    n.current_price,
    n.premium_discount_pct,
    -- Distribution metrics
    d.most_recent_distribution,
    d.distribution_rate,
    d.distribution_frequency,
    d.annualized_yield,
    -- Performance metrics
    p.perf_1m,
    p.perf_3m,
    p.perf_6m,
    p.perf_1y,
    p.perf_3y,
    p.perf_5y,
    p.perf_inception
FROM mv_etf_timeseries_nav n
LEFT JOIN mv_etf_timeseries_distributions d
    ON n.provider = d.provider
    AND n.ticker = d.ticker
    AND n.scraped_at = d.scraped_at
LEFT JOIN mv_etf_timeseries_performance p
    ON n.provider = p.provider
    AND n.ticker = p.ticker
    AND n.scraped_at = p.scraped_at
ORDER BY n.provider, n.ticker, n.snapshot_date DESC;

CREATE INDEX idx_mv_etf_timeseries_summary_ticker_date
ON mv_etf_timeseries_summary(ticker, snapshot_date DESC);

CREATE INDEX idx_mv_etf_timeseries_summary_provider
ON mv_etf_timeseries_summary(provider);

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    nav_count INT;
    dist_count INT;
    perf_count INT;
    summary_count INT;
BEGIN
    SELECT COUNT(*) INTO nav_count FROM mv_etf_timeseries_nav;
    SELECT COUNT(*) INTO dist_count FROM mv_etf_timeseries_distributions;
    SELECT COUNT(*) INTO perf_count FROM mv_etf_timeseries_performance;
    SELECT COUNT(*) INTO summary_count FROM mv_etf_timeseries_summary;

    RAISE NOTICE '=== Time Series Materialized Views Created ===';
    RAISE NOTICE 'mv_etf_timeseries_nav: % rows', nav_count;
    RAISE NOTICE 'mv_etf_timeseries_distributions: % rows', dist_count;
    RAISE NOTICE 'mv_etf_timeseries_performance: % rows', perf_count;
    RAISE NOTICE 'mv_etf_timeseries_summary: % rows', summary_count;
    RAISE NOTICE '✅ All views created successfully';
END $$;

COMMIT;

-- ============================================================================
-- Useful Queries (examples for using the views)
-- ============================================================================

-- Example 1: NAV trend for a specific ticker
-- SELECT snapshot_date, nav, nav_change_percent
-- FROM mv_etf_timeseries_nav
-- WHERE ticker = 'TSLY'
-- ORDER BY snapshot_date DESC
-- LIMIT 30;

-- Example 2: Distribution history for a ticker
-- SELECT snapshot_date, most_recent_distribution, distribution_rate, annualized_yield
-- FROM mv_etf_timeseries_distributions
-- WHERE ticker = 'QYLD'
-- ORDER BY snapshot_date DESC
-- LIMIT 30;

-- Example 3: Compare performance across providers
-- SELECT provider, ticker, snapshot_date, perf_1m, perf_3m, perf_1y
-- FROM mv_etf_timeseries_performance
-- WHERE snapshot_date >= CURRENT_DATE - INTERVAL '30 days'
-- ORDER BY provider, ticker, snapshot_date DESC;

-- Example 4: Latest metrics for all ETFs
-- SELECT provider, ticker, snapshot_date, nav, current_price, distribution_rate, perf_1y
-- FROM mv_etf_timeseries_summary
-- WHERE snapshot_date = (SELECT MAX(snapshot_date) FROM mv_etf_timeseries_summary)
-- ORDER BY provider, ticker;

-- Example 5: Find ETFs with best recent distribution rates
-- SELECT ticker, fund_name, provider, distribution_rate, snapshot_date
-- FROM mv_etf_timeseries_distributions
-- WHERE snapshot_date >= CURRENT_DATE - INTERVAL '7 days'
--   AND distribution_rate IS NOT NULL
-- ORDER BY distribution_rate DESC NULLS LAST
-- LIMIT 20;
