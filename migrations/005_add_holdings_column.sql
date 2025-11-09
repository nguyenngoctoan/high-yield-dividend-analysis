-- Migration: Add holdings JSON column to stocks table
-- Date: 2025-10-12
-- Purpose: Store ETF holdings data as JSON for comprehensive portfolio analysis

-- Add holdings column (JSONB for better performance and querying)
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS holdings JSONB;

-- Add holdings_updated_at timestamp to track when holdings were last fetched
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS holdings_updated_at TIMESTAMP WITH TIME ZONE;

-- Create index on holdings for JSON queries
CREATE INDEX IF NOT EXISTS idx_stocks_holdings
ON stocks USING GIN (holdings)
WHERE holdings IS NOT NULL;

-- Create index on holdings_updated_at for filtering stale data
CREATE INDEX IF NOT EXISTS idx_stocks_holdings_updated_at
ON stocks(holdings_updated_at)
WHERE holdings_updated_at IS NOT NULL;

-- Add comment explaining the holdings structure
COMMENT ON COLUMN stocks.holdings IS 'JSON array of ETF holdings with structure: [{asset, name, weightPercentage, sharesNumber, marketValue, cusip, updatedAt}]';

-- Example query to find ETFs holding a specific stock
-- SELECT symbol, name,
--        jsonb_array_elements(holdings) as holding
-- FROM stocks
-- WHERE holdings @> '[{"asset": "TSLA"}]';

-- Example query to get top holdings for an ETF
-- SELECT symbol,
--        jsonb_array_elements(holdings)->>'asset' as holding_symbol,
--        jsonb_array_elements(holdings)->>'weightPercentage' as weight
-- FROM stocks
-- WHERE symbol = 'TSLY'
-- ORDER BY (jsonb_array_elements(holdings)->>'weightPercentage')::numeric DESC
-- LIMIT 10;
