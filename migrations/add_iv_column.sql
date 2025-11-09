-- Add IV (Implied Volatility) column to stock_prices table
-- This tracks the implied volatility of stocks/ETFs over time

-- Add the iv column
ALTER TABLE stock_prices
ADD COLUMN IF NOT EXISTS iv NUMERIC(10,4);

-- Add comment explaining the column
COMMENT ON COLUMN stock_prices.iv IS 'Implied Volatility - measures expected volatility of the underlying asset';

-- Create index for efficient IV queries
CREATE INDEX IF NOT EXISTS idx_stock_prices_iv
ON stock_prices(symbol, date, iv)
WHERE iv IS NOT NULL;

-- Grant permissions (following existing pattern)
ALTER TABLE stock_prices ENABLE ROW LEVEL SECURITY;
