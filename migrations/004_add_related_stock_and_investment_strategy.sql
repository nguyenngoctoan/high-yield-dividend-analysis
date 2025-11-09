-- Migration: Add related_stock and investment_strategy columns to stocks table
-- Date: 2025-10-12
-- Description: Add columns for ETF underlying stock relationship and investment strategy

-- Add related_stock column (for YieldMax ETFs, stores the underlying stock symbol like TSLA, NVDA, etc.)
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS related_stock TEXT;

-- Add investment_strategy column (stores the strategy type: covered call, synthetic covered call, etc.)
ALTER TABLE stocks
ADD COLUMN IF NOT EXISTS investment_strategy TEXT;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_stocks_related_stock
ON stocks(related_stock)
WHERE related_stock IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_stocks_investment_strategy
ON stocks(investment_strategy)
WHERE investment_strategy IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN stocks.related_stock IS 'For ETFs: the underlying stock symbol (e.g., TSLA for TSLY)';
COMMENT ON COLUMN stocks.investment_strategy IS 'Investment strategy type (e.g., covered call, synthetic covered call, put writing)';
