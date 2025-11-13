-- API Keys and Authentication
-- Create tables for API key management, rate limiting, and usage tracking

-- API Keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    key_name VARCHAR(255),
    key_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 hash of the API key
    key_prefix VARCHAR(20) NOT NULL, -- First 8 characters for identification (e.g., "sk_live_abc123de")
    tier VARCHAR(50) DEFAULT 'free', -- free, pro, enterprise
    is_active BOOLEAN DEFAULT true,
    request_count BIGINT DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}', -- Additional metadata (email, company, etc.)

    -- Indexes for fast lookups
    CONSTRAINT api_keys_tier_check CHECK (tier IN ('free', 'pro', 'enterprise'))
);

-- Create indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);
CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys(created_at DESC);

-- API Usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    request_size BIGINT,
    response_size BIGINT,
    ip_address INET,
    user_agent TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    request_date DATE GENERATED ALWAYS AS (DATE(created_at)) STORED
);

-- Create indexes for api_usage
CREATE INDEX IF NOT EXISTS idx_api_usage_api_key_id ON api_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_request_date ON api_usage(request_date DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_status_code ON api_usage(status_code);

-- Materialized view for daily usage statistics
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_api_usage_daily AS
SELECT
    api_key_id,
    request_date,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE status_code >= 200 AND status_code < 300) as successful_requests,
    COUNT(*) FILTER (WHERE status_code >= 400) as error_requests,
    AVG(response_time_ms) as avg_response_time_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) as p95_response_time_ms,
    SUM(request_size) as total_request_size,
    SUM(response_size) as total_response_size,
    COUNT(DISTINCT ip_address) as unique_ips,
    ARRAY_AGG(DISTINCT endpoint) as endpoints_used
FROM api_usage
GROUP BY api_key_id, request_date;

-- Create indexes for the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_api_usage_daily_key_date
    ON mv_api_usage_daily(api_key_id, request_date DESC);

-- Function to refresh the usage stats (run daily)
CREATE OR REPLACE FUNCTION refresh_api_usage_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_api_usage_daily;
END;
$$ LANGUAGE plpgsql;

-- Rate limit tracking table (for persistent rate limiting across restarts)
CREATE TABLE IF NOT EXISTS rate_limit_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier VARCHAR(255) NOT NULL, -- api_key:id or ip:address
    window_type VARCHAR(20) NOT NULL, -- minute, hour, day
    tokens_remaining DECIMAL(10, 2) NOT NULL,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(identifier, window_type, window_start)
);

-- Create indexes for rate_limit_state
CREATE INDEX IF NOT EXISTS idx_rate_limit_identifier ON rate_limit_state(identifier);
CREATE INDEX IF NOT EXISTS idx_rate_limit_window_end ON rate_limit_state(window_end);

-- Function to clean up expired rate limit states (run hourly)
CREATE OR REPLACE FUNCTION cleanup_expired_rate_limits()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rate_limit_state
    WHERE window_end < NOW() - INTERVAL '1 day';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE api_keys IS 'Stores API keys for authentication and authorization';
COMMENT ON TABLE api_usage IS 'Tracks individual API requests for analytics and billing';
COMMENT ON TABLE rate_limit_state IS 'Persistent storage for rate limiting state';
COMMENT ON MATERIALIZED VIEW mv_api_usage_daily IS 'Daily aggregated statistics for API usage';

COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the API key for secure storage';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 8 characters of key for user identification (e.g., sk_live_abc123de)';
COMMENT ON COLUMN api_keys.tier IS 'Subscription tier determining rate limits and features';
COMMENT ON COLUMN api_keys.metadata IS 'Additional metadata like email, company name, notes';

-- Sample data for testing (optional - comment out for production)
-- DO $$
-- DECLARE
--     test_key_hash VARCHAR(64);
-- BEGIN
--     -- Example: API key "sk_test_abc123" hashed with SHA-256
--     test_key_hash := encode(sha256('sk_test_abc123'::bytea), 'hex');
--
--     INSERT INTO api_keys (user_id, key_name, key_hash, key_prefix, tier, metadata)
--     VALUES (
--         'test_user_001',
--         'Development Key',
--         test_key_hash,
--         'sk_test_',
--         'free',
--         '{"email": "test@example.com", "company": "Test Co"}'::jsonb
--     )
--     ON CONFLICT (key_hash) DO NOTHING;
-- END $$;

-- Grant permissions (adjust for your security requirements)
-- GRANT SELECT, INSERT, UPDATE ON api_keys TO api_user;
-- GRANT SELECT, INSERT ON api_usage TO api_user;
-- GRANT SELECT ON mv_api_usage_daily TO api_user;
