-- Add user authentication columns to divv_api_keys table
-- This migration links API keys to authenticated users

-- Add user_id column
ALTER TABLE divv_api_keys
ADD COLUMN IF NOT EXISTS user_id VARCHAR(255);

-- Add tier/subscription level
ALTER TABLE divv_api_keys
ADD COLUMN IF NOT EXISTS tier VARCHAR(50) DEFAULT 'free';

-- Add tier constraint
ALTER TABLE divv_api_keys
ADD CONSTRAINT divv_api_keys_tier_check
CHECK (tier IN ('free', 'pro', 'enterprise'));

-- Add updated_at column for tracking changes
ALTER TABLE divv_api_keys
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create index on user_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_user_id ON divv_api_keys(user_id);

-- Create index on tier for filtering by subscription level
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_tier ON divv_api_keys(tier);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_divv_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_divv_api_keys_updated_at
    BEFORE UPDATE ON divv_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_divv_api_keys_updated_at();

-- Add comments to new columns
COMMENT ON COLUMN divv_api_keys.user_id IS 'Identifier for the authenticated user who owns this API key';
COMMENT ON COLUMN divv_api_keys.tier IS 'Subscription tier determining rate limits and features (free, pro, enterprise)';
COMMENT ON COLUMN divv_api_keys.updated_at IS 'Timestamp of last update to this record';

-- Optional: Add a view to get user API keys with usage stats
CREATE OR REPLACE VIEW v_user_api_keys AS
SELECT
    dak.id,
    dak.user_id,
    dak.name,
    dak.key_prefix,
    dak.tier,
    dak.created_at,
    dak.expires_at,
    dak.last_used_at,
    dak.request_count,
    dak.is_active,
    dak.updated_at,
    dak.metadata,
    CASE
        WHEN dak.expires_at IS NULL THEN true
        WHEN dak.expires_at > NOW() THEN true
        ELSE false
    END as is_valid,
    CASE
        WHEN dak.expires_at IS NOT NULL AND dak.expires_at < NOW() THEN 'expired'
        WHEN NOT dak.is_active THEN 'disabled'
        ELSE 'active'
    END as status
FROM divv_api_keys dak;

COMMENT ON VIEW v_user_api_keys IS 'Convenient view of user API keys with computed status fields';
