-- Migration: Update Pricing Tiers and Rate Limiting
-- Date: 2025-11-14
-- Description: Updates tier system to support new pricing structure with monthly + per-minute rate limits

-- ============================================================================
-- STEP 1: Add tier and user_id columns if they don't exist
-- ============================================================================

DO $$
BEGIN
    -- Add tier column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='divv_api_keys' AND column_name='tier') THEN
        ALTER TABLE divv_api_keys ADD COLUMN tier VARCHAR(50) DEFAULT 'free';
    END IF;

    -- Add user_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='divv_api_keys' AND column_name='user_id') THEN
        ALTER TABLE divv_api_keys ADD COLUMN user_id UUID;
    END IF;
END $$;

-- Drop old constraint if exists
ALTER TABLE divv_api_keys DROP CONSTRAINT IF EXISTS divv_api_keys_tier_check;

-- Add new constraint with updated tiers
ALTER TABLE divv_api_keys ADD CONSTRAINT divv_api_keys_tier_check
CHECK (tier IN ('free', 'starter', 'premium', 'professional', 'enterprise'));

-- Update existing 'pro' tier to 'premium' (backward compatibility)
UPDATE divv_api_keys SET tier = 'premium' WHERE tier = 'pro';

-- Create index on user_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_user_id ON divv_api_keys(user_id);

-- ============================================================================
-- STEP 2: Create tier limits configuration table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tier_limits (
    id SERIAL PRIMARY KEY,
    tier VARCHAR(50) NOT NULL UNIQUE,

    -- Monthly limits
    monthly_call_limit INTEGER NOT NULL,

    -- Per-minute limits
    calls_per_minute INTEGER NOT NULL,
    burst_limit INTEGER NOT NULL,

    -- Feature flags
    stock_coverage JSONB DEFAULT '{}'::jsonb,
    features JSONB DEFAULT '{}'::jsonb,

    -- Data access
    historical_years INTEGER,
    price_data_frequency VARCHAR(50), -- 'eod', 'hourly', '15min', '1min', 'realtime'

    -- Support & extras
    support_level VARCHAR(50),
    portfolio_limit INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT tier_limits_tier_check CHECK (tier IN ('free', 'starter', 'premium', 'professional', 'enterprise'))
);

-- Insert tier limits based on pricing document
INSERT INTO divv_tier_limits (
    tier, monthly_call_limit, calls_per_minute, burst_limit,
    stock_coverage, features, historical_years, price_data_frequency,
    support_level, portfolio_limit
) VALUES
    (
        'free',
        5000,
        10,
        20,
        '{"type": "sample", "count": 150, "description": "Dividend Aristocrats, Kings, and top yielders"}'::jsonb,
        '{"bulk_export": false, "webhooks": false, "bulk_endpoints": false}'::jsonb,
        1,
        'eod',
        'community',
        0
    ),
    (
        'starter',
        50000,
        30,
        60,
        '{"type": "us_only", "count": 3000, "description": "All US dividend-paying stocks"}'::jsonb,
        '{"bulk_export": true, "webhooks": false, "bulk_endpoints": true, "max_bulk_symbols": 50}'::jsonb,
        5,
        'eod',
        'email',
        1
    ),
    (
        'premium',
        250000,
        100,
        200,
        '{"type": "international", "count": 4600, "description": "US + Canada, UK, Germany, France, Australia"}'::jsonb,
        '{"bulk_export": true, "webhooks": true, "bulk_endpoints": true, "max_bulk_symbols": 200}'::jsonb,
        30,
        'hourly',
        'priority',
        3
    ),
    (
        'professional',
        1000000,
        300,
        600,
        '{"type": "global", "count": 8000, "description": "Global coverage (30+ countries)"}'::jsonb,
        '{"bulk_export": true, "webhooks": true, "bulk_endpoints": true, "max_bulk_symbols": 1000, "white_label": true}'::jsonb,
        100,
        'hourly',
        'dedicated',
        999999
    ),
    (
        'enterprise',
        999999999,
        1000,
        2000,
        '{"type": "custom", "count": 10000, "description": "Full global coverage + custom"}'::jsonb,
        '{"bulk_export": true, "webhooks": true, "bulk_endpoints": true, "max_bulk_symbols": 5000, "white_label": true, "custom_endpoints": true}'::jsonb,
        100,
        'hourly',
        'dedicated',
        999999
    )
ON CONFLICT (tier) DO UPDATE SET
    monthly_call_limit = EXCLUDED.monthly_call_limit,
    calls_per_minute = EXCLUDED.calls_per_minute,
    burst_limit = EXCLUDED.burst_limit,
    stock_coverage = EXCLUDED.stock_coverage,
    features = EXCLUDED.features,
    historical_years = EXCLUDED.historical_years,
    price_data_frequency = EXCLUDED.price_data_frequency,
    support_level = EXCLUDED.support_level,
    portfolio_limit = EXCLUDED.portfolio_limit,
    updated_at = NOW();

-- ============================================================================
-- STEP 3: Add monthly usage tracking to divv_api_keys
-- ============================================================================

-- Add columns for monthly usage tracking if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='divv_api_keys' AND column_name='monthly_usage') THEN
        ALTER TABLE divv_api_keys ADD COLUMN monthly_usage INTEGER DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='divv_api_keys' AND column_name='monthly_usage_reset_at') THEN
        ALTER TABLE divv_api_keys ADD COLUMN monthly_usage_reset_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '1 month';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='divv_api_keys' AND column_name='minute_usage') THEN
        ALTER TABLE divv_api_keys ADD COLUMN minute_usage INTEGER DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name='divv_api_keys' AND column_name='minute_window_start') THEN
        ALTER TABLE divv_api_keys ADD COLUMN minute_window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- Create index for faster rate limit lookups
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_monthly_reset
    ON divv_api_keys(monthly_usage_reset_at) WHERE is_active = true;

-- ============================================================================
-- STEP 4: Create rate limit tracking table (for distributed systems)
-- ============================================================================

CREATE TABLE IF NOT EXISTS rate_limit_tracking (
    id BIGSERIAL PRIMARY KEY,
    api_key_id UUID NOT NULL REFERENCES divv_api_keys(id) ON DELETE CASCADE,

    -- Monthly tracking
    monthly_usage INTEGER DEFAULT 0,
    monthly_period_start DATE NOT NULL,
    monthly_period_end DATE NOT NULL,

    -- Minute tracking (sliding window)
    minute_usage INTEGER DEFAULT 0,
    minute_window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    minute_window_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Metadata
    last_request_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(api_key_id, monthly_period_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_limit_tracking_api_key
    ON rate_limit_tracking(api_key_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_tracking_period
    ON rate_limit_tracking(monthly_period_start DESC);
CREATE INDEX IF NOT EXISTS idx_rate_limit_tracking_minute_window
    ON rate_limit_tracking(minute_window_end);

-- ============================================================================
-- STEP 5: Create sample stock list for free tier
-- ============================================================================

CREATE TABLE IF NOT EXISTS free_tier_stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(255),
    category VARCHAR(50), -- 'aristocrat', 'king', 'high_yield'
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT free_tier_stocks_category_check CHECK (category IN ('aristocrat', 'king', 'high_yield'))
);

CREATE INDEX IF NOT EXISTS idx_free_tier_stocks_category ON divv_free_tier_stocks(category);
CREATE INDEX IF NOT EXISTS idx_free_tier_stocks_symbol ON divv_free_tier_stocks(symbol);

-- Populate with initial sample stocks (top dividend aristocrats & kings)
INSERT INTO divv_free_tier_stocks (symbol, name, category) VALUES
    -- Dividend Kings (50+ years)
    ('JNJ', 'Johnson & Johnson', 'king'),
    ('PG', 'Procter & Gamble', 'king'),
    ('KO', 'Coca-Cola', 'king'),
    ('CL', 'Colgate-Palmolive', 'king'),
    ('PEP', 'PepsiCo', 'king'),
    ('TGT', 'Target', 'king'),
    ('LOW', 'Lowe''s', 'king'),
    ('MMM', '3M', 'king'),
    ('ABT', 'Abbott Laboratories', 'king'),
    ('GWW', 'W.W. Grainger', 'king'),

    -- Dividend Aristocrats (25+ years)
    ('AAPL', 'Apple', 'aristocrat'),
    ('MSFT', 'Microsoft', 'aristocrat'),
    ('ADP', 'Automatic Data Processing', 'aristocrat'),
    ('AFL', 'Aflac', 'aristocrat'),
    ('ALB', 'Albemarle', 'aristocrat'),
    ('APD', 'Air Products & Chemicals', 'aristocrat'),
    ('BDX', 'Becton Dickinson', 'aristocrat'),
    ('BF.B', 'Brown-Forman', 'aristocrat'),
    ('CAT', 'Caterpillar', 'aristocrat'),
    ('CB', 'Chubb', 'aristocrat'),
    ('CHD', 'Church & Dwight', 'aristocrat'),
    ('CINF', 'Cincinnati Financial', 'aristocrat'),
    ('CLX', 'Clorox', 'aristocrat'),
    ('CTAS', 'Cintas', 'aristocrat'),
    ('DOV', 'Dover', 'aristocrat'),
    ('ECL', 'Ecolab', 'aristocrat'),
    ('ED', 'Consolidated Edison', 'aristocrat'),
    ('EMR', 'Emerson Electric', 'aristocrat'),
    ('ESS', 'Essex Property Trust', 'aristocrat'),
    ('EXPD', 'Expeditors International', 'aristocrat'),

    -- High yield stocks
    ('T', 'AT&T', 'high_yield'),
    ('VZ', 'Verizon', 'high_yield'),
    ('MO', 'Altria', 'high_yield'),
    ('ABBV', 'AbbVie', 'high_yield'),
    ('PM', 'Philip Morris', 'high_yield'),
    ('IBM', 'IBM', 'high_yield'),
    ('DUK', 'Duke Energy', 'high_yield'),
    ('SO', 'Southern Company', 'high_yield'),
    ('D', 'Dominion Energy', 'high_yield'),
    ('XOM', 'Exxon Mobil', 'high_yield')
ON CONFLICT (symbol) DO NOTHING;

-- ============================================================================
-- STEP 6: Helper functions
-- ============================================================================

-- Function to get tier limits for an API key
CREATE OR REPLACE FUNCTION get_tier_limits(p_api_key_id UUID)
RETURNS TABLE (
    tier VARCHAR(50),
    monthly_call_limit INTEGER,
    calls_per_minute INTEGER,
    burst_limit INTEGER,
    stock_coverage JSONB,
    features JSONB
) AS $$
BEGIN
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
$$ LANGUAGE plpgsql;

-- Function to check if symbol is accessible by tier
CREATE OR REPLACE FUNCTION is_symbol_accessible(p_symbol VARCHAR(20), p_tier VARCHAR(50))
RETURNS BOOLEAN AS $$
DECLARE
    v_coverage_type VARCHAR(50);
BEGIN
    -- Get coverage type for tier
    SELECT stock_coverage->>'type' INTO v_coverage_type
    FROM divv_tier_limits
    WHERE tier = p_tier;

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
$$ LANGUAGE plpgsql;

-- Function to reset monthly usage counters (run via cron)
CREATE OR REPLACE FUNCTION reset_monthly_usage_counters()
RETURNS INTEGER AS $$
DECLARE
    v_reset_count INTEGER;
BEGIN
    UPDATE divv_api_keys
    SET
        monthly_usage = 0,
        monthly_usage_reset_at = NOW() + INTERVAL '1 month',
        updated_at = NOW()
    WHERE
        is_active = true
        AND monthly_usage_reset_at <= NOW();

    GET DIAGNOSTICS v_reset_count = ROW_COUNT;

    RETURN v_reset_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STEP 7: Create view for API key limits
-- ============================================================================

CREATE OR REPLACE VIEW v_api_keys_with_limits AS
SELECT
    ak.id,
    ak.user_id,
    ak.name,
    ak.key_prefix,
    ak.tier,
    ak.is_active,
    ak.monthly_usage,
    ak.monthly_usage_reset_at,
    ak.request_count,
    ak.last_used_at,
    ak.created_at,

    -- Tier limits
    tl.monthly_call_limit,
    tl.calls_per_minute,
    tl.burst_limit,
    tl.stock_coverage,
    tl.features,
    tl.historical_years,
    tl.price_data_frequency,
    tl.support_level,
    tl.portfolio_limit,

    -- Calculated fields
    CASE
        WHEN ak.monthly_usage >= tl.monthly_call_limit THEN true
        ELSE false
    END as monthly_limit_exceeded,

    (tl.monthly_call_limit - ak.monthly_usage) as monthly_calls_remaining,

    ROUND(100.0 * ak.monthly_usage / NULLIF(tl.monthly_call_limit, 0), 2) as usage_percentage

FROM divv_api_keys ak
LEFT JOIN divv_tier_limits tl ON ak.tier = tl.tier;

COMMENT ON VIEW v_api_keys_with_limits IS 'API keys with their tier limits and usage statistics';

-- ============================================================================
-- STEP 8: Create function to increment usage (called from middleware)
-- ============================================================================

CREATE OR REPLACE FUNCTION increment_key_usage(key_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE divv_api_keys
    SET
        monthly_usage = monthly_usage + 1,
        minute_usage = minute_usage + 1,
        request_count = request_count + 1,
        last_used_at = NOW(),
        updated_at = NOW()
    WHERE id = key_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION increment_key_usage IS 'Increment usage counters for an API key (called by rate limiter middleware)';

-- ============================================================================
-- STEP 9: Comments for documentation
-- ============================================================================

COMMENT ON TABLE divv_tier_limits IS 'Configuration table storing rate limits and features for each pricing tier';
COMMENT ON TABLE rate_limit_tracking IS 'Tracks API usage for rate limiting in distributed systems';
COMMENT ON TABLE divv_free_tier_stocks IS 'Curated list of stocks accessible to free tier users';

COMMENT ON COLUMN divv_api_keys.monthly_usage IS 'Number of API calls made this month';
COMMENT ON COLUMN divv_api_keys.monthly_usage_reset_at IS 'When the monthly usage counter resets';
COMMENT ON COLUMN divv_api_keys.minute_usage IS 'Number of API calls in current minute window';
COMMENT ON COLUMN divv_api_keys.minute_window_start IS 'Start of current minute rate limit window';

-- ============================================================================
-- STEP 10: Grant permissions (adjust as needed)
-- ============================================================================

-- GRANT SELECT ON tier_limits TO api_user;
-- GRANT SELECT, UPDATE ON divv_api_keys TO api_user;
-- GRANT SELECT, INSERT, UPDATE ON rate_limit_tracking TO api_user;
-- GRANT SELECT ON free_tier_stocks TO api_user;
-- GRANT SELECT ON v_api_keys_with_limits TO api_user;

-- ============================================================================
-- Migration complete
-- ============================================================================

-- Show summary
DO $$
BEGIN
    RAISE NOTICE '✅ Pricing tiers migration completed successfully';
    RAISE NOTICE '   - Updated tier constraint to include: free, starter, premium, professional, enterprise';
    RAISE NOTICE '   - Created tier_limits table with rate limits and features';
    RAISE NOTICE '   - Added monthly and per-minute usage tracking';
    RAISE NOTICE '   - Created free_tier_stocks sample list (40 stocks)';
    RAISE NOTICE '   - Created helper functions for tier management';
    RAISE NOTICE '   - Created v_api_keys_with_limits view';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Current tier limits:';
    RAISE NOTICE '   Free:          5,000/month,  10/min (burst: 20)';
    RAISE NOTICE '   Starter:      50,000/month,  30/min (burst: 60)';
    RAISE NOTICE '   Premium:     250,000/month, 100/min (burst: 200)';
    RAISE NOTICE '   Professional: 1M/month,     300/min (burst: 600)';
    RAISE NOTICE '   Enterprise:   Unlimited,   1000/min (burst: 2000)';
END $$;
