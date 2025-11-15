-- Migration: Add Comprehensive Indexes for All Tables
-- Date: 2025-11-15
-- Description: Ensures all tables have proper indexes for optimal query performance

-- ============================================================================
-- RAW_STOCKS TABLE INDEXES
-- ============================================================================

-- Primary key on symbol (should already exist, but ensuring)
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_stocks_pkey
    ON raw_stocks(symbol);

-- Filtering and sorting indexes
CREATE INDEX IF NOT EXISTS idx_raw_stocks_exchange
    ON raw_stocks(exchange) WHERE exchange IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_raw_stocks_type
    ON raw_stocks(type) WHERE type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_raw_stocks_sector
    ON raw_stocks(sector) WHERE sector IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_raw_stocks_industry
    ON raw_stocks(industry) WHERE industry IS NOT NULL;

-- Dividend-related indexes (commonly queried)
CREATE INDEX IF NOT EXISTS idx_raw_stocks_dividend_yield
    ON raw_stocks(dividend_yield DESC NULLS LAST) WHERE dividend_yield > 0;

CREATE INDEX IF NOT EXISTS idx_raw_stocks_has_dividends
    ON raw_stocks(dividend_yield) WHERE dividend_yield > 0;

-- Market cap for filtering/sorting
CREATE INDEX IF NOT EXISTS idx_raw_stocks_market_cap
    ON raw_stocks(market_cap DESC NULLS LAST) WHERE market_cap IS NOT NULL;

-- Price for filtering/sorting
CREATE INDEX IF NOT EXISTS idx_raw_stocks_price
    ON raw_stocks(price DESC NULLS LAST) WHERE price IS NOT NULL;

-- Composite index for common query patterns (exchange + type + dividend_yield)
CREATE INDEX IF NOT EXISTS idx_raw_stocks_exchange_type_yield
    ON raw_stocks(exchange, type, dividend_yield DESC NULLS LAST)
    WHERE dividend_yield > 0;

-- Composite index for sector filtering with dividend yield
CREATE INDEX IF NOT EXISTS idx_raw_stocks_sector_yield
    ON raw_stocks(sector, dividend_yield DESC NULLS LAST)
    WHERE sector IS NOT NULL AND dividend_yield > 0;

-- Updated timestamp for cache invalidation
CREATE INDEX IF NOT EXISTS idx_raw_stocks_updated_at
    ON raw_stocks(updated_at DESC);

-- P/E ratio index
CREATE INDEX IF NOT EXISTS idx_raw_stocks_pe_ratio
    ON raw_stocks(pe_ratio) WHERE pe_ratio IS NOT NULL;

-- Volume index
CREATE INDEX IF NOT EXISTS idx_raw_stocks_volume
    ON raw_stocks(volume DESC NULLS LAST) WHERE volume IS NOT NULL;

-- ============================================================================
-- RAW_STOCK_PRICES TABLE INDEXES
-- ============================================================================

-- Composite primary key (symbol, date) - should already exist
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_stock_prices_symbol_date
    ON raw_stock_prices(symbol, date DESC);

-- Date range queries
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_date
    ON raw_stock_prices(date DESC);

-- Symbol lookups (if not covered by composite index)
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_symbol
    ON raw_stock_prices(symbol);

-- Volume index for filtering
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_volume
    ON raw_stock_prices(volume DESC NULLS LAST) WHERE volume IS NOT NULL;

-- Price changes for analytics
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_change_percent
    ON raw_stock_prices(change_percent DESC NULLS LAST) WHERE change_percent IS NOT NULL;

-- Composite index for recent price queries (commonly used pattern)
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_recent
    ON raw_stock_prices(symbol, date DESC)
    INCLUDE (close, open, high, low, volume);

-- ============================================================================
-- RAW_DIVIDENDS TABLE INDEXES
-- ============================================================================

-- Composite primary key (symbol, ex_date) - should already exist
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_dividends_symbol_ex_date
    ON raw_dividends(symbol, ex_date DESC);

-- Ex-date for date range queries
CREATE INDEX IF NOT EXISTS idx_raw_dividends_ex_date
    ON raw_dividends(ex_date DESC);

-- Payment date for upcoming dividend tracking
CREATE INDEX IF NOT EXISTS idx_raw_dividends_payment_date
    ON raw_dividends(payment_date DESC) WHERE payment_date IS NOT NULL;

-- Symbol lookups
CREATE INDEX IF NOT EXISTS idx_raw_dividends_symbol
    ON raw_dividends(symbol);

-- Dividend amount for high-yield searches
CREATE INDEX IF NOT EXISTS idx_raw_dividends_amount
    ON raw_dividends(amount DESC NULLS LAST) WHERE amount > 0;

-- Declaration date
CREATE INDEX IF NOT EXISTS idx_raw_dividends_declaration_date
    ON raw_dividends(declaration_date DESC) WHERE declaration_date IS NOT NULL;

-- Composite index for recent dividends by symbol
CREATE INDEX IF NOT EXISTS idx_raw_dividends_recent
    ON raw_dividends(symbol, ex_date DESC)
    INCLUDE (amount, payment_date);

-- ============================================================================
-- RAW_STOCKS_EXCLUDED TABLE INDEXES
-- ============================================================================

-- Primary key on symbol
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_stocks_excluded_pkey
    ON divv_stocks_excluded(symbol);

-- Exclusion date for cleanup/auditing
CREATE INDEX IF NOT EXISTS idx_raw_stocks_excluded_excluded_at
    ON divv_stocks_excluded(excluded_at DESC);

-- Reason for reporting
CREATE INDEX IF NOT EXISTS idx_raw_stocks_excluded_reason
    ON divv_stocks_excluded(reason) WHERE reason IS NOT NULL;

-- Source tracking
CREATE INDEX IF NOT EXISTS idx_raw_stocks_excluded_source
    ON divv_stocks_excluded(source) WHERE source IS NOT NULL;

-- ============================================================================
-- USERS TABLE INDEXES (OAuth authentication)
-- ============================================================================

-- These should already exist from create_users_table_v2.sql, but ensuring
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id
    ON divv_users(google_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
    ON divv_users(email);

CREATE INDEX IF NOT EXISTS idx_users_tier
    ON divv_users(tier);

CREATE INDEX IF NOT EXISTS idx_users_created_at
    ON divv_users(created_at DESC);

-- Active divv_users filter
CREATE INDEX IF NOT EXISTS idx_users_is_active
    ON divv_users(is_active) WHERE is_active = true;

-- Last login tracking
CREATE INDEX IF NOT EXISTS idx_users_last_login_at
    ON divv_users(last_login_at DESC NULLS LAST);

-- ============================================================================
-- DIVV_API_KEYS TABLE INDEXES
-- ============================================================================

-- These should already exist from create_divv_api_keys.sql, but ensuring
CREATE UNIQUE INDEX IF NOT EXISTS idx_divv_api_keys_key_hash
    ON divv_api_keys(key_hash);

CREATE INDEX IF NOT EXISTS idx_divv_api_keys_expires_at
    ON divv_api_keys(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_divv_api_keys_created_at
    ON divv_api_keys(created_at DESC);

-- User ID for user's keys lookup
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_user_id
    ON divv_api_keys(user_id) WHERE user_id IS NOT NULL;

-- Active keys filter
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_is_active
    ON divv_api_keys(is_active) WHERE is_active = true;

-- Tier-based filtering
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_tier
    ON divv_api_keys(tier) WHERE tier IS NOT NULL;

-- Last used tracking
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_last_used_at
    ON divv_api_keys(last_used_at DESC NULLS LAST);

-- Request count for analytics
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_request_count
    ON divv_api_keys(request_count DESC);

-- Composite index for active, non-expired keys
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_active_valid
    ON divv_api_keys(is_active, expires_at)
    WHERE is_active = true AND (expires_at IS NULL OR expires_at > NOW());

-- ============================================================================
-- RAW_DATA_SOURCE_TRACKING TABLE INDEXES
-- ============================================================================

-- These should already exist from create_data_source_tracking.sql, but ensuring
CREATE INDEX IF NOT EXISTS idx_data_source_tracking_symbol
    ON divv_data_source_tracking(symbol);

CREATE INDEX IF NOT EXISTS idx_data_source_tracking_data_type
    ON divv_data_source_tracking(data_type);

CREATE INDEX IF NOT EXISTS idx_data_source_tracking_has_data
    ON divv_data_source_tracking(has_data) WHERE has_data = true;

CREATE INDEX IF NOT EXISTS idx_data_source_tracking_last_checked
    ON divv_data_source_tracking(last_checked_at);

CREATE INDEX IF NOT EXISTS idx_data_source_tracking_lookup
    ON divv_data_source_tracking(symbol, data_type, has_data, source);

-- Last successful fetch for staleness detection
CREATE INDEX IF NOT EXISTS idx_data_source_tracking_last_successful
    ON divv_data_source_tracking(last_successful_fetch_at DESC NULLS LAST);

-- ============================================================================
-- RAW_YIELDMAX_DIVIDENDS TABLE INDEXES (if exists)
-- ============================================================================

-- Primary key
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_symbol_ex_date
    ON divv_yieldmax_dividends(symbol, ex_date DESC);

-- Date indexes
CREATE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_ex_date
    ON divv_yieldmax_dividends(ex_date DESC);

CREATE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_payment_date
    ON divv_yieldmax_dividends(payment_date DESC) WHERE payment_date IS NOT NULL;

-- Symbol lookup
CREATE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_symbol
    ON divv_yieldmax_dividends(symbol);

-- ============================================================================
-- STOCK_SPLITS TABLE INDEXES (if exists)
-- ============================================================================

-- Composite primary key
CREATE UNIQUE INDEX IF NOT EXISTS idx_stock_splits_symbol_date
    ON divv_stock_splits(symbol, split_date DESC);

-- Date range queries
CREATE INDEX IF NOT EXISTS idx_stock_splits_date
    ON divv_stock_splits(split_date DESC);

-- Symbol lookup
CREATE INDEX IF NOT EXISTS idx_stock_splits_symbol
    ON divv_stock_splits(symbol);

-- ============================================================================
-- HOLDINGS_HISTORY TABLE INDEXES (if exists)
-- ============================================================================

-- Composite index for portfolio tracking
CREATE INDEX IF NOT EXISTS idx_holdings_history_user_symbol
    ON divv_holdings_history(user_id, symbol, date DESC);

-- User's holdings
CREATE INDEX IF NOT EXISTS idx_holdings_history_user_id
    ON divv_holdings_history(user_id);

-- Date-based queries
CREATE INDEX IF NOT EXISTS idx_holdings_history_date
    ON divv_holdings_history(date DESC);

-- Symbol holdings tracking
CREATE INDEX IF NOT EXISTS idx_holdings_history_symbol
    ON divv_holdings_history(symbol);

-- ============================================================================
-- VERIFICATION AND COMMENTS
-- ============================================================================

COMMENT ON INDEX idx_raw_stocks_dividend_yield IS 'Optimizes dividend yield filtering and sorting';
COMMENT ON INDEX idx_raw_stock_prices_recent IS 'Optimizes recent price lookups with included columns';
COMMENT ON INDEX idx_raw_dividends_recent IS 'Optimizes recent dividend lookups with included columns';
COMMENT ON INDEX idx_divv_api_keys_active_valid IS 'Optimizes lookup of valid, active API keys';

-- Verification message
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    RAISE NOTICE '============================================================';
    RAISE NOTICE 'Comprehensive Index Migration Completed Successfully!';
    RAISE NOTICE '============================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Total indexes in public schema: %', index_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Key optimizations applied:';
    RAISE NOTICE '  ✓ Primary key indexes on all tables';
    RAISE NOTICE '  ✓ Foreign key indexes for joins';
    RAISE NOTICE '  ✓ Filtering indexes (sector, exchange, type, etc.)';
    RAISE NOTICE '  ✓ Sorting indexes (dividend_yield, market_cap, date, etc.)';
    RAISE NOTICE '  ✓ Composite indexes for common query patterns';
    RAISE NOTICE '  ✓ Partial indexes with WHERE clauses for efficiency';
    RAISE NOTICE '  ✓ Covering indexes with INCLUDE columns';
    RAISE NOTICE '';
    RAISE NOTICE 'Performance impact:';
    RAISE NOTICE '  • Symbol lookups: O(log n) instead of O(n)';
    RAISE NOTICE '  • Date range queries: Optimized with DESC indexes';
    RAISE NOTICE '  • Dividend filtering: Partial indexes reduce index size';
    RAISE NOTICE '  • API key validation: Hash lookup is now instant';
    RAISE NOTICE '';
    RAISE NOTICE '============================================================';
END $$;
