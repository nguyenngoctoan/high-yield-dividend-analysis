-- Add fundamental data columns to raw_stocks for GOOGLEFINANCE parity
-- Migration: 20251114_add_fundamental_data

-- Add missing fundamental data columns
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS shares_outstanding bigint;
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS year_high numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS year_low numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS avg_volume bigint;
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS change numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS change_percent numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS previous_close numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS price_avg_50 numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS price_avg_200 numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS eps numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS day_high numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS day_low numeric(12,4);
ALTER TABLE raw_stocks ADD COLUMN IF NOT EXISTS open_price numeric(12,4);

-- Add comments for documentation
COMMENT ON COLUMN raw_stocks.shares_outstanding IS 'Total shares outstanding';
COMMENT ON COLUMN raw_stocks.year_high IS '52-week high price';
COMMENT ON COLUMN raw_stocks.year_low IS '52-week low price';
COMMENT ON COLUMN raw_stocks.avg_volume IS 'Average trading volume';
COMMENT ON COLUMN raw_stocks.change IS 'Daily price change amount';
COMMENT ON COLUMN raw_stocks.change_percent IS 'Daily price change percentage';
COMMENT ON COLUMN raw_stocks.previous_close IS 'Previous closing price';
COMMENT ON COLUMN raw_stocks.price_avg_50 IS '50-day moving average';
COMMENT ON COLUMN raw_stocks.price_avg_200 IS '200-day moving average';
COMMENT ON COLUMN raw_stocks.eps IS 'Earnings per share (TTM)';
COMMENT ON COLUMN raw_stocks.day_high IS 'Today high price';
COMMENT ON COLUMN raw_stocks.day_low IS 'Today low price';
COMMENT ON COLUMN raw_stocks.open_price IS 'Today opening price';
