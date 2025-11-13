-- ============================================================================
-- API Database Optimizations
-- ============================================================================
-- Materialized views, indexes, and functions to optimize API performance
-- Run this migration after the base schema is created
-- ============================================================================

-- ----------------------------------------------------------------------------
-- MATERIALIZED VIEWS
-- ----------------------------------------------------------------------------

-- High-yield stocks view (updated hourly)
-- Optimizes the /v1/screeners/high-yield endpoint
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_high_yield_stocks AS
SELECT
    symbol,
    company,
    exchange,
    type,
    price,
    dividend_yield,
    dividend_amount,
    sector,
    industry,
    market_cap,
    payout_ratio,
    dividend_frequency,
    ex_dividend_date,
    dividend_date as payment_date,
    updated_at
FROM raw_stocks
WHERE dividend_yield IS NOT NULL
  AND dividend_yield >= 4.0
  AND type = 'stock'
  AND price IS NOT NULL
  AND price > 0
ORDER BY dividend_yield DESC;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_mart_high_yield_yield
ON mart_high_yield_stocks(dividend_yield DESC);

CREATE INDEX IF NOT EXISTS idx_mart_high_yield_sector
ON mart_high_yield_stocks(sector);

COMMENT ON MATERIALIZED VIEW mart_high_yield_stocks IS
'Pre-computed high-yield stocks (yield >= 4.0%) for fast screener queries';


-- Dividend calendar view (updated daily)
-- Optimizes the /v1/dividends/calendar endpoint
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_dividend_calendar AS
SELECT
    d.symbol,
    d.ex_dividend_date,
    d.payment_date,
    d.amount,
    d.frequency,
    s.company,
    s.dividend_yield,
    s.sector,
    s.exchange,
    s.type
FROM raw_future_dividends d
LEFT JOIN raw_stocks s ON d.symbol = s.symbol
WHERE d.ex_dividend_date >= CURRENT_DATE
  AND d.ex_dividend_date <= CURRENT_DATE + INTERVAL '90 days'
ORDER BY d.ex_dividend_date;

-- Indexes for dividend calendar
CREATE INDEX IF NOT EXISTS idx_mart_div_calendar_date
ON mart_dividend_calendar(ex_dividend_date);

CREATE INDEX IF NOT EXISTS idx_mart_div_calendar_symbol
ON mart_dividend_calendar(symbol);

COMMENT ON MATERIALIZED VIEW mart_dividend_calendar IS
'Upcoming dividend events for the next 90 days';


-- Monthly payers view
-- Optimizes the /v1/screeners/monthly-payers endpoint
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_monthly_dividend_payers AS
SELECT
    symbol,
    company,
    exchange,
    type,
    price,
    dividend_yield,
    dividend_amount,
    sector,
    market_cap,
    payout_ratio,
    updated_at
FROM raw_stocks
WHERE dividend_frequency = 'monthly'
  AND dividend_yield IS NOT NULL
  AND dividend_yield > 0
  AND price IS NOT NULL
ORDER BY dividend_yield DESC;

-- Index for monthly payers
CREATE INDEX IF NOT EXISTS idx_mart_monthly_yield
ON mart_monthly_dividend_payers(dividend_yield DESC);

COMMENT ON MATERIALIZED VIEW mart_monthly_dividend_payers IS
'Stocks and ETFs that pay monthly dividends';


-- ETF holdings summary view
-- Optimizes the /v1/etfs/{symbol}/holdings endpoint
CREATE MATERIALIZED VIEW IF NOT EXISTS mart_etf_holdings_summary AS
SELECT
    etf_symbol,
    COUNT(*) as total_holdings,
    SUM(weight) as total_weight,
    jsonb_agg(
        jsonb_build_object(
            'symbol', holding_symbol,
            'company', company,
            'weight', weight,
            'shares', shares,
            'market_value', market_value,
            'sector', sector
        ) ORDER BY weight DESC
    ) FILTER (WHERE weight IS NOT NULL) as top_holdings
FROM raw_etf_holdings
GROUP BY etf_symbol;

-- Index for ETF holdings
CREATE INDEX IF NOT EXISTS idx_mart_etf_holdings_symbol
ON mart_etf_holdings_summary(etf_symbol);

COMMENT ON MATERIALIZED VIEW mart_etf_holdings_summary IS
'Aggregated ETF holdings data for fast retrieval';


-- ----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE
-- ----------------------------------------------------------------------------

-- Stock symbol lookup (exact match)
CREATE INDEX IF NOT EXISTS idx_stocks_symbol_upper
ON raw_stocks(UPPER(symbol));

-- Company name search (trigram for fuzzy matching)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_stocks_company_gin
ON raw_stocks USING gin(company gin_trgm_ops);

-- Symbol search (trigram)
CREATE INDEX IF NOT EXISTS idx_stocks_symbol_gin
ON raw_stocks USING gin(symbol gin_trgm_ops);

-- Dividend yield for filtering
CREATE INDEX IF NOT EXISTS idx_stocks_dividend_yield
ON raw_stocks(dividend_yield DESC NULLS LAST)
WHERE dividend_yield IS NOT NULL;

-- Market cap for filtering
CREATE INDEX IF NOT EXISTS idx_stocks_market_cap
ON raw_stocks(market_cap DESC NULLS LAST)
WHERE market_cap IS NOT NULL;

-- Sector filtering
CREATE INDEX IF NOT EXISTS idx_stocks_sector
ON raw_stocks(sector)
WHERE sector IS NOT NULL;

-- Exchange filtering
CREATE INDEX IF NOT EXISTS idx_stocks_exchange
ON raw_stocks(exchange);

-- Type filtering
CREATE INDEX IF NOT EXISTS idx_stocks_type
ON raw_stocks(type);

-- Dividend frequency
CREATE INDEX IF NOT EXISTS idx_stocks_dividend_frequency
ON raw_stocks(dividend_frequency)
WHERE dividend_frequency IS NOT NULL;

-- Price history by symbol and date
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date
ON raw_stock_prices(symbol, date DESC);

-- Dividend history by symbol and date
CREATE INDEX IF NOT EXISTS idx_dividends_symbol_date
ON raw_dividends(symbol, date DESC);

-- Future dividends by ex-date
CREATE INDEX IF NOT EXISTS idx_future_dividends_ex_date
ON raw_future_dividends(ex_dividend_date)
WHERE ex_dividend_date >= CURRENT_DATE;

-- ETF holdings by ETF symbol
CREATE INDEX IF NOT EXISTS idx_etf_holdings_etf_symbol
ON raw_etf_holdings(etf_symbol);

-- ETF holdings by weight (for top holdings)
CREATE INDEX IF NOT EXISTS idx_etf_holdings_weight
ON raw_etf_holdings(etf_symbol, weight DESC);


-- ----------------------------------------------------------------------------
-- DATABASE FUNCTIONS
-- ----------------------------------------------------------------------------

-- Fast high-yield screener function
CREATE OR REPLACE FUNCTION get_high_yield_stocks(
    min_yield_pct float DEFAULT 4.0,
    min_market_cap_val bigint DEFAULT NULL,
    sector_filter text[] DEFAULT NULL,
    exchange_filter text[] DEFAULT NULL,
    exclude_etfs_flag boolean DEFAULT false,
    limit_count int DEFAULT 100
)
RETURNS TABLE(
    symbol text,
    company text,
    exchange text,
    price float,
    dividend_yield float,
    market_cap bigint,
    payout_ratio float,
    sector text
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.symbol::text,
        s.company::text,
        s.exchange::text,
        s.price::float,
        s.dividend_yield::float,
        s.market_cap::bigint,
        s.payout_ratio::float,
        s.sector::text
    FROM raw_stocks s
    WHERE s.dividend_yield >= min_yield_pct
      AND s.dividend_yield IS NOT NULL
      AND (min_market_cap_val IS NULL OR s.market_cap >= min_market_cap_val)
      AND (sector_filter IS NULL OR s.sector = ANY(sector_filter))
      AND (exchange_filter IS NULL OR s.exchange = ANY(exchange_filter))
      AND (NOT exclude_etfs_flag OR s.type != 'etf')
    ORDER BY s.dividend_yield DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_high_yield_stocks IS
'Fast screener function for high-yield dividend stocks with flexible filtering';


-- Function to search stocks (fuzzy matching)
CREATE OR REPLACE FUNCTION search_stocks(
    search_query text,
    type_filter text DEFAULT NULL,
    limit_count int DEFAULT 20
)
RETURNS TABLE(
    symbol text,
    company text,
    exchange text,
    type text,
    relevance float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.symbol::text,
        s.company::text,
        s.exchange::text,
        s.type::text,
        GREATEST(
            similarity(s.symbol, search_query) * 2,  -- Weight symbol matches higher
            similarity(COALESCE(s.company, ''), search_query),
            similarity(COALESCE(s.sector, ''), search_query) * 0.5
        )::float as relevance
    FROM raw_stocks s
    WHERE (s.symbol ILIKE '%' || search_query || '%'
           OR s.company ILIKE '%' || search_query || '%'
           OR s.sector ILIKE '%' || search_query || '%')
      AND (type_filter IS NULL OR s.type = type_filter)
    ORDER BY relevance DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION search_stocks IS
'Fuzzy search function for stocks by symbol, company, or sector';


-- Function to get dividend summary for a stock
CREATE OR REPLACE FUNCTION get_dividend_summary(
    stock_symbol text,
    history_years int DEFAULT 5
)
RETURNS json AS $$
DECLARE
    summary json;
BEGIN
    SELECT json_build_object(
        'symbol', stock_symbol,
        'current', (
            SELECT json_build_object(
                'yield', dividend_yield,
                'annual_amount', dividend_amount,
                'frequency', dividend_frequency,
                'payout_ratio', payout_ratio,
                'ex_date', ex_dividend_date,
                'payment_date', dividend_date
            )
            FROM raw_stocks
            WHERE symbol = stock_symbol
        ),
        'history_count', (
            SELECT COUNT(*)
            FROM raw_dividends
            WHERE symbol = stock_symbol
              AND date >= CURRENT_DATE - (history_years || ' years')::interval
        ),
        'next_payment', (
            SELECT json_build_object(
                'ex_date', ex_dividend_date,
                'payment_date', payment_date,
                'amount', amount
            )
            FROM raw_future_dividends
            WHERE symbol = stock_symbol
              AND ex_dividend_date >= CURRENT_DATE
            ORDER BY ex_dividend_date
            LIMIT 1
        )
    ) INTO summary;

    RETURN summary;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_dividend_summary IS
'Get comprehensive dividend summary for a stock including current, history count, and next payment';


-- ----------------------------------------------------------------------------
-- REFRESH FUNCTIONS FOR MATERIALIZED VIEWS
-- ----------------------------------------------------------------------------

-- Function to refresh all API materialized views
CREATE OR REPLACE FUNCTION refresh_api_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mart_high_yield_stocks;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mart_dividend_calendar;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mart_monthly_dividend_payers;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mart_etf_holdings_summary;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION refresh_api_materialized_views IS
'Refresh all materialized views used by the API (run this hourly via cron)';


-- ----------------------------------------------------------------------------
-- STATISTICS UPDATE
-- ----------------------------------------------------------------------------

-- Analyze tables for query optimization
ANALYZE raw_stocks;
ANALYZE raw_stock_prices;
ANALYZE raw_dividends;
ANALYZE raw_future_dividends;
ANALYZE raw_etf_holdings;


-- ----------------------------------------------------------------------------
-- SUMMARY
-- ----------------------------------------------------------------------------

-- Display optimization summary
DO $$
DECLARE
    high_yield_count int;
    calendar_count int;
    monthly_count int;
    etf_count int;
BEGIN
    SELECT COUNT(*) INTO high_yield_count FROM mart_high_yield_stocks;
    SELECT COUNT(*) INTO calendar_count FROM mart_dividend_calendar;
    SELECT COUNT(*) INTO monthly_count FROM mart_monthly_dividend_payers;
    SELECT COUNT(*) INTO etf_count FROM mart_etf_holdings_summary;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'API OPTIMIZATIONS INSTALLED';
    RAISE NOTICE '========================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Materialized Views:';
    RAISE NOTICE '  - mart_high_yield_stocks: % rows', high_yield_count;
    RAISE NOTICE '  - mart_dividend_calendar: % rows', calendar_count;
    RAISE NOTICE '  - mart_monthly_dividend_payers: % rows', monthly_count;
    RAISE NOTICE '  - mart_etf_holdings_summary: % rows', etf_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes: 20+ performance indexes created';
    RAISE NOTICE 'Functions: 4 helper functions installed';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Set up cron job to refresh views hourly:';
    RAISE NOTICE '     SELECT refresh_api_materialized_views();';
    RAISE NOTICE '';
    RAISE NOTICE '  2. Monitor view refresh times';
    RAISE NOTICE '  3. Adjust refresh frequency as needed';
    RAISE NOTICE '========================================';
END $$;
