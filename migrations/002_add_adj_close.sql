-- Add adj_close (adjusted close) column to price tables
-- Adjusted close accounts for stock splits, dividends, and other corporate actions
-- This is essential for accurate historical analysis and portfolio tracking

-- Add adj_close to stock_prices table (daily prices)
ALTER TABLE stock_prices
ADD COLUMN IF NOT EXISTS adj_close NUMERIC(12, 4);

-- Add adj_close to stock_prices_hourly table
ALTER TABLE stock_prices_hourly
ADD COLUMN IF NOT EXISTS adj_close NUMERIC(12, 4);

-- Create indexes for adj_close for performance
CREATE INDEX IF NOT EXISTS idx_stock_prices_adj_close ON stock_prices(symbol, date, adj_close);
CREATE INDEX IF NOT EXISTS idx_hourly_adj_close ON stock_prices_hourly(symbol, timestamp, adj_close);

-- Comments
COMMENT ON COLUMN stock_prices.adj_close IS 'Adjusted close price accounting for splits, dividends, and corporate actions';
COMMENT ON COLUMN stock_prices_hourly.adj_close IS 'Adjusted close price accounting for splits, dividends, and corporate actions';

-- Note: For existing data, run the backfill script to populate adj_close from FMP API
