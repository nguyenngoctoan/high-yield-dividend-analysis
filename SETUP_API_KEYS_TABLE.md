# Setup API Keys Table

## Database Table Creation

To enable API key management, you need to create the `divv_api_keys` table in your Supabase database.

### Step 1: Access Supabase SQL Editor

1. Go to your Supabase project dashboard
2. Click on "SQL Editor" in the left sidebar
3. Click "New query"

### Step 2: Run This SQL

Copy and paste the following SQL into the editor and click "Run":

```sql
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_key_hash ON divv_api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_expires_at ON divv_api_keys(expires_at);
CREATE INDEX IF NOT EXISTS idx_divv_api_keys_created_at ON divv_api_keys(created_at DESC);

-- Add table comment
COMMENT ON TABLE divv_api_keys IS 'API keys for authenticating requests to the Dividend API';

-- Add column comments
COMMENT ON COLUMN divv_api_keys.id IS 'Unique identifier for the API key';
COMMENT ON COLUMN divv_api_keys.name IS 'User-friendly name for the API key';
COMMENT ON COLUMN divv_api_keys.key_hash IS 'SHA-256 hash of the actual API key';
COMMENT ON COLUMN divv_api_keys.key_prefix IS 'First few characters of the key for display (e.g., sk_live_1234)';
COMMENT ON COLUMN divv_api_keys.created_at IS 'When the key was created';
COMMENT ON COLUMN divv_api_keys.expires_at IS 'When the key expires (NULL means never expires)';
COMMENT ON COLUMN divv_api_keys.last_used_at IS 'Last time the key was used to make a request';
COMMENT ON COLUMN divv_api_keys.request_count IS 'Total number of requests made with this key';
COMMENT ON COLUMN divv_api_keys.is_active IS 'Whether the key is active (can be disabled without deleting)';
COMMENT ON COLUMN divv_api_keys.metadata IS 'Additional metadata (rate limits, permissions, etc.)';
```

### Step 3: Enable Row Level Security (RLS)

For security, enable RLS on the table:

```sql
-- Enable RLS
ALTER TABLE divv_api_keys ENABLE ROW LEVEL SECURITY;

-- Create policy to allow service role full access
CREATE POLICY "Service role can manage API keys"
ON divv_api_keys
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

### Step 4: Verify Table Creation

Run this query to verify the table was created:

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'divv_api_keys'
ORDER BY ordinal_position;
```

You should see all 10 columns listed.

## Table Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `name` | VARCHAR(255) | User-friendly name for the key |
| `key_hash` | VARCHAR(255) | SHA-256 hash of the actual key |
| `key_prefix` | VARCHAR(20) | Displayable prefix (e.g., sk_live_1234) |
| `created_at` | TIMESTAMP | When the key was created |
| `expires_at` | TIMESTAMP | Expiration date (NULL = never expires) |
| `last_used_at` | TIMESTAMP | Last usage timestamp |
| `request_count` | INTEGER | Total number of API requests |
| `is_active` | BOOLEAN | Whether the key is active |
| `metadata` | JSONB | Additional data (rate limits, etc.) |

## Expiry Options

The UI allows users to set:
- **Never** - `expires_at` is NULL
- **7 days** - `expires_at` = current_date + 7 days
- **30 days** - `expires_at` = current_date + 30 days
- **90 days** - `expires_at` = current_date + 90 days
- **1 year** - `expires_at` = current_date + 365 days

## Security Features

1. **Key Hashing**: Actual API keys are hashed with SHA-256 before storage
2. **One-time Display**: Keys are shown only once after creation
3. **Key Prefix**: Only first 20 chars visible after creation for identification
4. **Expiry**: Automatic expiration support
5. **Soft Delete**: Keys can be deactivated without deletion
6. **RLS**: Row Level Security protects the data

## Next Steps

After creating the table:
1. The API Keys page at `/api-keys` will be fully functional
2. Users can create, view, and delete API keys
3. Keys will be securely stored in the database
4. Integration with the actual API authentication is ready

## Testing

To test the table:

```sql
-- Insert a test key
INSERT INTO divv_api_keys (name, key_hash, key_prefix, expires_at)
VALUES (
    'Test Key',
    'test_hash_value_here',
    'sk_live_1234',
    NOW() + INTERVAL '30 days'
);

-- Query all keys
SELECT id, name, key_prefix, created_at, expires_at, request_count
FROM divv_api_keys
ORDER BY created_at DESC;

-- Delete test key
DELETE FROM divv_api_keys WHERE name = 'Test Key';
```

## Migration File Location

The migration SQL is saved at:
```
/migrations/create_divv_api_keys.sql
```

You can also run it directly from there if needed.
