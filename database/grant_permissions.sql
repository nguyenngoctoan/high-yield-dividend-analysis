-- Grant full permissions to service_role and anon roles on stocks_excluded table

-- First ensure the table exists
CREATE TABLE IF NOT EXISTS raw_stocks_excluded (
    symbol VARCHAR(20) PRIMARY KEY,
    reason TEXT,
    excluded_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    source VARCHAR(50),
    validation_attempts INT DEFAULT 1
);

-- Grant all privileges to postgres (superuser)
GRANT ALL PRIVILEGES ON TABLE raw_stocks_excluded TO postgres;

-- Grant all privileges to service_role
GRANT ALL PRIVILEGES ON TABLE raw_stocks_excluded TO service_role;

-- Grant all privileges to authenticated role
GRANT ALL PRIVILEGES ON TABLE raw_stocks_excluded TO authenticated;

-- Grant all privileges to anon role
GRANT ALL PRIVILEGES ON TABLE raw_stocks_excluded TO anon;

-- Also grant permissions on the raw_stocks table
GRANT ALL PRIVILEGES ON TABLE raw_stocks TO postgres;
GRANT ALL PRIVILEGES ON TABLE raw_stocks TO service_role;
GRANT ALL PRIVILEGES ON TABLE raw_stocks TO authenticated;
GRANT ALL PRIVILEGES ON TABLE raw_stocks TO anon;

-- Grant usage on all sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Make sure RLS is disabled
ALTER TABLE raw_stocks DISABLE ROW LEVEL SECURITY;
ALTER TABLE raw_stocks_excluded DISABLE ROW LEVEL SECURITY;

-- Verify permissions
SELECT
    grantee,
    privilege_type,
    table_name
FROM information_schema.role_table_grants
WHERE table_name IN ('raw_stocks', 'raw_stocks_excluded')
ORDER BY table_name, grantee;