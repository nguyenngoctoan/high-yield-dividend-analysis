-- Migration: Update YieldMax ETF Data Table with Date-based Constraint
-- Created: 2025-11-16
-- Description: Adds scraped_date column and updates unique constraint to use date instead of timestamp

-- Add scraped_date column
ALTER TABLE raw_yieldmax_etf_data
ADD COLUMN IF NOT EXISTS scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED;

-- Drop the old timestamp-based constraint
ALTER TABLE raw_yieldmax_etf_data
DROP CONSTRAINT IF EXISTS unique_ticker_scraped_at;

-- Add new date-based unique constraint
ALTER TABLE raw_yieldmax_etf_data
ADD CONSTRAINT unique_ticker_scraped_date UNIQUE (ticker, scraped_date);

-- Create index on scraped_date
CREATE INDEX IF NOT EXISTS idx_yieldmax_scraped_date ON raw_yieldmax_etf_data(scraped_date DESC);

-- Update the view to use the new column
CREATE OR REPLACE VIEW v_yieldmax_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    scraped_at,
    scraped_date,
    performance_month_end,
    performance_quarter_end,
    fund_overview,
    investment_objective,
    fund_details,
    distributions,
    top_10_holdings,
    created_at,
    updated_at
FROM raw_yieldmax_etf_data
ORDER BY ticker, scraped_date DESC, scraped_at DESC;

COMMENT ON COLUMN raw_yieldmax_etf_data.scraped_date IS 'Date when data was scraped (derived from scraped_at timestamp)';
