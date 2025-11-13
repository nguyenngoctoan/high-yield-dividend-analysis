-- Add auto_excluded column to raw_excluded_symbols table
-- This tracks symbols that were automatically excluded due to no price data

-- Add column if it doesn't exist
ALTER TABLE raw_excluded_symbols
ADD COLUMN IF NOT EXISTS auto_excluded BOOLEAN DEFAULT FALSE;

-- Add comment
COMMENT ON COLUMN raw_excluded_symbols.auto_excluded IS
'True if symbol was automatically excluded (e.g., no price data from any source)';

-- Create index for querying auto-excluded symbols
CREATE INDEX IF NOT EXISTS idx_raw_excluded_symbols_auto_excluded
ON raw_excluded_symbols(auto_excluded) WHERE auto_excluded = TRUE;

-- Update existing records to mark them as manually excluded
UPDATE raw_excluded_symbols
SET auto_excluded = FALSE
WHERE auto_excluded IS NULL;

-- Show stats
SELECT
    COUNT(*) as total_excluded,
    COUNT(*) FILTER (WHERE auto_excluded = TRUE) as auto_excluded,
    COUNT(*) FILTER (WHERE auto_excluded = FALSE) as manually_excluded
FROM raw_excluded_symbols;
