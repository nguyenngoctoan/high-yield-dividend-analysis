-- Migration: Add ETF-specific fields to stocks and stock_prices tables
-- Date: 2025-10-04
-- Description: Adds expense_ratio and description to stocks, AUM to stock_prices for time-series tracking

-- 1. Add expense_ratio and description to stocks table (static/slow-changing data)
ALTER TABLE raw_stocks
ADD COLUMN IF NOT EXISTS expense_ratio DECIMAL(10, 6),
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add comments for documentation
COMMENT ON COLUMN raw_stocks.expense_ratio IS 'ETF expense ratio (e.g., 0.0075 = 0.75%)';
COMMENT ON COLUMN raw_stocks.description IS 'Company/ETF description or business summary';

-- 2. Add AUM to raw_stock_prices table (time-series data that changes daily)
ALTER TABLE raw_stock_prices
ADD COLUMN IF NOT EXISTS aum BIGINT;

-- Add comment for documentation
COMMENT ON COLUMN raw_stock_prices.aum IS 'Assets Under Management for ETFs (in dollars), tracked over time';

-- Create index for AUM queries if needed
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_aum ON raw_stock_prices(aum) WHERE aum IS NOT NULL;

-- Verification queries
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Added to raw_stocks: expense_ratio (DECIMAL), description (TEXT)';
    RAISE NOTICE 'Added to raw_stock_prices: aum (BIGINT)';
END $$;
