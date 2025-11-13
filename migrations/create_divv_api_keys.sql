-- Create API Keys table
CREATE TABLE IF NOT EXISTS divv_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    request_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index on key_hash for fast lookups
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_key_hash ON divv_api_keys(key_hash);

-- Create index on expires_at for cleanup queries
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_expires_at ON divv_api_keys(expires_at);

-- Create index on created_at for sorting
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_created_at ON divv_api_keys(created_at DESC);

-- Add comment to table
COMMENT ON TABLE divv_api_keys IS 'API keys for authenticating requests to the Dividend API';

-- Add comments to columns
COMMENT ON COLUMN divv_api_keys.name IS 'User-friendly name for the API key';
COMMENT ON COLUMN divv_api_keys.key_hash IS 'SHA-256 hash of the actual API key';
COMMENT ON COLUMN divv_api_keys.key_prefix IS 'First few characters of the key for display (e.g., sk_live_1234)';
COMMENT ON COLUMN divv_api_keys.expires_at IS 'When the key expires (NULL means never expires)';
COMMENT ON COLUMN divv_api_keys.last_used_at IS 'Last time the key was used to make a request';
COMMENT ON COLUMN divv_api_keys.request_count IS 'Total number of requests made with this key';
COMMENT ON COLUMN divv_api_keys.is_active IS 'Whether the key is active (can be disabled without deleting)';
COMMENT ON COLUMN divv_api_keys.metadata IS 'Additional metadata (rate limits, permissions, etc.)';
