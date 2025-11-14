-- Create Users table for Google OAuth authentication
-- This table stores authenticated user information from Google OAuth

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    picture_url TEXT,
    tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb,

    CONSTRAINT users_tier_check CHECK (tier IN ('free', 'pro', 'enterprise'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_tier ON users(tier);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Add comments
COMMENT ON TABLE users IS 'Authenticated users via Google OAuth';
COMMENT ON COLUMN users.google_id IS 'Google OAuth user ID (sub claim from JWT)';
COMMENT ON COLUMN users.email IS 'User email address from Google';
COMMENT ON COLUMN users.name IS 'User display name from Google';
COMMENT ON COLUMN users.picture_url IS 'URL to user profile picture from Google';
COMMENT ON COLUMN users.tier IS 'Subscription tier (free, pro, enterprise)';
COMMENT ON COLUMN users.is_active IS 'Whether the user account is active';
COMMENT ON COLUMN users.last_login_at IS 'Timestamp of last successful login';
COMMENT ON COLUMN users.metadata IS 'Additional user metadata (preferences, settings, etc.)';

-- Add trigger to update updated_at
CREATE OR REPLACE FUNCTION update_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_users_updated_at();

-- Update divv_api_keys to change user_id type and add foreign key
DO $$
BEGIN
    -- Drop the dependent view first
    DROP VIEW IF EXISTS v_user_api_keys CASCADE;
    DROP VIEW IF EXISTS v_user_api_keys_with_user CASCADE;

    -- Drop the foreign key constraint if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'divv_api_keys_user_id_fkey'
    ) THEN
        ALTER TABLE divv_api_keys DROP CONSTRAINT divv_api_keys_user_id_fkey;
    END IF;

    -- Change user_id column type from VARCHAR to UUID
    -- This will only work if the column is empty or contains valid UUIDs
    BEGIN
        ALTER TABLE divv_api_keys
        ALTER COLUMN user_id TYPE UUID USING user_id::UUID;
    EXCEPTION
        WHEN OTHERS THEN
            -- If conversion fails, drop and recreate the column
            ALTER TABLE divv_api_keys DROP COLUMN IF EXISTS user_id CASCADE;
            ALTER TABLE divv_api_keys ADD COLUMN user_id UUID;
    END;

    -- Now add the foreign key constraint
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'divv_api_keys_user_id_fkey'
    ) THEN
        ALTER TABLE divv_api_keys
        ADD CONSTRAINT divv_api_keys_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Recreate the view for user API keys with user information
CREATE OR REPLACE VIEW v_user_api_keys_with_user AS
SELECT
    dak.id,
    dak.user_id,
    u.email,
    u.name as user_name,
    u.picture_url,
    dak.name as key_name,
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
FROM divv_api_keys dak
LEFT JOIN users u ON dak.user_id = u.id;

COMMENT ON VIEW v_user_api_keys_with_user IS 'API keys with associated user information';

-- Create a function to get or create user from Google OAuth data
CREATE OR REPLACE FUNCTION upsert_google_user(
    p_google_id VARCHAR(255),
    p_email VARCHAR(255),
    p_name VARCHAR(255),
    p_picture_url TEXT
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    -- Try to find existing user by google_id
    SELECT id INTO v_user_id
    FROM users
    WHERE google_id = p_google_id;

    IF v_user_id IS NOT NULL THEN
        -- Update existing user
        UPDATE users
        SET
            email = p_email,
            name = p_name,
            picture_url = p_picture_url,
            last_login_at = NOW()
        WHERE id = v_user_id;

        RETURN v_user_id;
    ELSE
        -- Insert new user
        INSERT INTO users (google_id, email, name, picture_url, last_login_at)
        VALUES (p_google_id, p_email, p_name, p_picture_url, NOW())
        RETURNING id INTO v_user_id;

        RETURN v_user_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION upsert_google_user IS 'Get or create user from Google OAuth login data';
