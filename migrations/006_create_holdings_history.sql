-- Create holdings_history table for tracking ETF holdings changes over time
-- Date: October 12, 2025

BEGIN;

-- Create holdings_history table
CREATE TABLE IF NOT EXISTS holdings_history (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    holdings JSONB NOT NULL,
    holdings_count INTEGER,
    data_source VARCHAR(50) DEFAULT 'FMP',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint: one record per symbol per day
    CONSTRAINT holdings_history_symbol_date_unique UNIQUE (symbol, date)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_holdings_history_symbol ON holdings_history(symbol);
CREATE INDEX IF NOT EXISTS idx_holdings_history_date ON holdings_history(date);
CREATE INDEX IF NOT EXISTS idx_holdings_history_symbol_date ON holdings_history(symbol, date);

-- GIN index for JSONB queries
CREATE INDEX IF NOT EXISTS idx_holdings_history_holdings ON holdings_history USING GIN (holdings);

-- Comments
COMMENT ON TABLE holdings_history IS 'Historical ETF holdings data - tracks portfolio composition changes over time';
COMMENT ON COLUMN holdings_history.symbol IS 'ETF symbol';
COMMENT ON COLUMN holdings_history.date IS 'Date of holdings snapshot';
COMMENT ON COLUMN holdings_history.holdings IS 'Array of holdings (same structure as stocks.holdings)';
COMMENT ON COLUMN holdings_history.holdings_count IS 'Number of holdings in the portfolio';
COMMENT ON COLUMN holdings_history.data_source IS 'Source of holdings data (FMP, Yahoo, etc.)';

COMMIT;

-- Example queries:

-- Get holdings history for a specific ETF
-- SELECT date, holdings_count, holdings
-- FROM holdings_history
-- WHERE symbol = 'SPY'
-- ORDER BY date DESC;

-- Compare holdings between two dates
-- WITH current_holdings AS (
--     SELECT jsonb_array_elements(holdings)->>'asset' as asset,
--            (jsonb_array_elements(holdings)->>'weightPercentage')::numeric as weight
--     FROM holdings_history
--     WHERE symbol = 'SPY' AND date = '2025-10-12'
-- ),
-- previous_holdings AS (
--     SELECT jsonb_array_elements(holdings)->>'asset' as asset,
--            (jsonb_array_elements(holdings)->>'weightPercentage')::numeric as weight
--     FROM holdings_history
--     WHERE symbol = 'SPY' AND date = '2025-09-12'
-- )
-- SELECT
--     COALESCE(c.asset, p.asset) as asset,
--     c.weight as current_weight,
--     p.weight as previous_weight,
--     (c.weight - p.weight) as weight_change
-- FROM current_holdings c
-- FULL OUTER JOIN previous_holdings p ON c.asset = p.asset
-- WHERE c.weight IS DISTINCT FROM p.weight
-- ORDER BY ABS(COALESCE(c.weight, 0) - COALESCE(p.weight, 0)) DESC;

-- Find ETFs that changed their holdings on a specific date
-- SELECT symbol, date, holdings_count
-- FROM holdings_history h1
-- WHERE date = '2025-10-12'
--   AND EXISTS (
--       SELECT 1 FROM holdings_history h2
--       WHERE h2.symbol = h1.symbol
--         AND h2.date < h1.date
--         AND h2.holdings IS DISTINCT FROM h1.holdings
--       ORDER BY h2.date DESC
--       LIMIT 1
--   );
