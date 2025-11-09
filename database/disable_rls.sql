-- Disable Row-Level Security (RLS) on all tables
-- This allows full access using the anon key

-- First, create raw_stocks_excluded table if it doesn't exist
CREATE TABLE IF NOT EXISTS raw_stocks_excluded (
    symbol VARCHAR(20) PRIMARY KEY,
    reason TEXT,
    excluded_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    source VARCHAR(50),
    validation_attempts INT DEFAULT 1
);

-- Disable RLS on raw_stocks table
ALTER TABLE IF EXISTS raw_stocks DISABLE ROW LEVEL SECURITY;

-- Disable RLS on raw_stocks_excluded table
ALTER TABLE IF EXISTS raw_stocks_excluded DISABLE ROW LEVEL SECURITY;

-- Drop all existing policies on raw_stocks table
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Drop all policies on raw_stocks table
    FOR r IN (SELECT policyname FROM pg_policies WHERE tablename = 'raw_stocks')
    LOOP
        EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(r.policyname) || ' ON raw_stocks';
    END LOOP;

    -- Drop all policies on raw_stocks_excluded table
    FOR r IN (SELECT policyname FROM pg_policies WHERE tablename = 'raw_stocks_excluded')
    LOOP
        EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(r.policyname) || ' ON raw_stocks_excluded';
    END LOOP;
END $$;

-- Grant full permissions to anon role
GRANT ALL ON raw_stocks TO anon;
GRANT ALL ON raw_stocks_excluded TO anon;

-- Grant usage on sequences if they exist
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon;

-- Verify RLS is disabled
SELECT
    schemaname,
    tablename,
    rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('raw_stocks', 'raw_stocks_excluded');