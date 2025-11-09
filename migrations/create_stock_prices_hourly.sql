-- Create stock_prices_hourly table for intraday price tracking
-- This table stores hourly price snapshots during market hours

CREATE TABLE IF NOT EXISTS stock_prices_hourly (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,  -- Full timestamp with hour
    date DATE NOT NULL,               -- Date for easy querying
    hour INTEGER NOT NULL,            -- Hour (0-23) for easy filtering

    -- Price data
    price NUMERIC(12, 4),
    open NUMERIC(12, 4),
    high NUMERIC(12, 4),
    low NUMERIC(12, 4),
    close NUMERIC(12, 4),
    volume BIGINT,

    -- Change metrics
    change NUMERIC(12, 4),
    change_percent NUMERIC(8, 4),

    -- Additional metrics
    vwap NUMERIC(12, 4),              -- Volume-weighted average price
    trade_count INTEGER,               -- Number of trades in the hour

    -- Metadata
    currency VARCHAR(10) DEFAULT 'USD',
    source VARCHAR(50),                -- Data source (FMP, AlphaVantage, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_symbol_timestamp UNIQUE (symbol, timestamp)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_hourly_symbol ON stock_prices_hourly(symbol);
CREATE INDEX IF NOT EXISTS idx_hourly_date ON stock_prices_hourly(date);
CREATE INDEX IF NOT EXISTS idx_hourly_timestamp ON stock_prices_hourly(timestamp);
CREATE INDEX IF NOT EXISTS idx_hourly_symbol_date ON stock_prices_hourly(symbol, date);
CREATE INDEX IF NOT EXISTS idx_hourly_symbol_timestamp ON stock_prices_hourly(symbol, timestamp DESC);

-- Foreign key to stocks table
ALTER TABLE stock_prices_hourly
ADD CONSTRAINT fk_hourly_symbol
FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE;

-- Comments
COMMENT ON TABLE stock_prices_hourly IS 'Hourly intraday price data for stocks and ETFs during market hours';
COMMENT ON COLUMN stock_prices_hourly.timestamp IS 'Full timestamp for the hourly snapshot (e.g., 2025-10-09 14:00:00)';
COMMENT ON COLUMN stock_prices_hourly.hour IS 'Hour of day (0-23) in market timezone for easy filtering';
COMMENT ON COLUMN stock_prices_hourly.vwap IS 'Volume-weighted average price for the hour';
