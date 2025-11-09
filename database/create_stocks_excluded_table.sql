
CREATE TABLE IF NOT EXISTS raw_stocks_excluded (
    symbol VARCHAR(20) PRIMARY KEY,
    reason TEXT,
    excluded_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    source VARCHAR(50),
    validation_attempts INT DEFAULT 1
);

-- Create an index on symbol for faster lookups
CREATE INDEX IF NOT EXISTS idx_raw_stocks_excluded_symbol ON raw_stocks_excluded(symbol);

-- Create an index on excluded_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_raw_stocks_excluded_excluded_at ON raw_stocks_excluded(excluded_at);

-- Add a trigger to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_raw_stocks_excluded_updated_at BEFORE UPDATE
ON raw_stocks_excluded FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE raw_stocks_excluded IS 'Tracks symbols that have been excluded from the raw_stocks table due to validation failures or other criteria';
COMMENT ON COLUMN raw_stocks_excluded.symbol IS 'Stock ticker symbol';
COMMENT ON COLUMN raw_stocks_excluded.reason IS 'Reason for exclusion (e.g., no price data, mutual fund, etc.)';
COMMENT ON COLUMN raw_stocks_excluded.excluded_at IS 'Timestamp when the symbol was first excluded';
COMMENT ON COLUMN raw_stocks_excluded.updated_at IS 'Timestamp of the last update to this record';
COMMENT ON COLUMN raw_stocks_excluded.source IS 'Source that originally discovered this symbol (FMP, Alpha Vantage, etc.)';
COMMENT ON COLUMN raw_stocks_excluded.validation_attempts IS 'Number of times validation was attempted for this symbol';
