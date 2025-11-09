-- Migration: Add unique constraint to dividend_history table
-- This prevents duplicate dividends for the same symbol and ex_date

-- Step 1: Remove existing duplicates (keep the newest record for each symbol+ex_date)
-- We'll keep the record with the highest 'id' (most recently created) for each unique (symbol, ex_date)

WITH duplicates AS (
    SELECT
        id,
        symbol,
        ex_date,
        ROW_NUMBER() OVER (PARTITION BY symbol, ex_date ORDER BY created_at DESC, id DESC) as rn
    FROM dividend_history
)
DELETE FROM dividend_history
WHERE id IN (
    SELECT id FROM duplicates WHERE rn > 1
);

-- Step 2: Add unique constraint on (symbol, ex_date)
-- This ensures that only one dividend record can exist for each symbol on each ex_date
ALTER TABLE dividend_history
ADD CONSTRAINT unique_symbol_ex_date UNIQUE (symbol, ex_date);

-- Add helpful index if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_dividend_history_symbol_ex_date
ON dividend_history(symbol, ex_date);

-- Log the changes
DO $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    -- This would have been calculated before deletion
    RAISE NOTICE 'Successfully added unique constraint on dividend_history(symbol, ex_date)';
    RAISE NOTICE 'Future inserts will now use UPSERT to prevent duplicates';
END $$;
