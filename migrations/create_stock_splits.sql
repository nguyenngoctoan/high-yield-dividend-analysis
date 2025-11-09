-- Create stock_splits table for tracking stock split events
-- This table stores historical stock splits with their ratios and dates

CREATE TABLE IF NOT EXISTS stock_splits (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    split_date DATE NOT NULL,

    -- Split ratio stored multiple ways for flexibility
    split_ratio NUMERIC(12, 8),        -- Decimal representation (e.g., 2:1 = 2.0, 3:2 = 1.5)
    numerator INTEGER,                  -- For 3:2 split, this is 3
    denominator INTEGER,                -- For 3:2 split, this is 2
    split_string VARCHAR(20),           -- Human-readable format (e.g., "3:2", "2-for-1")

    -- Additional information
    description TEXT,                   -- Optional description from data provider
    source VARCHAR(50),                 -- Data source (FMP, AlphaVantage, Yahoo)

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_symbol_split_date UNIQUE (symbol, split_date)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_splits_symbol ON stock_splits(symbol);
CREATE INDEX IF NOT EXISTS idx_splits_date ON stock_splits(split_date);
CREATE INDEX IF NOT EXISTS idx_splits_symbol_date ON stock_splits(symbol, split_date DESC);

-- Foreign key to stocks table
ALTER TABLE stock_splits
ADD CONSTRAINT fk_splits_symbol
FOREIGN KEY (symbol) REFERENCES stocks(symbol) ON DELETE CASCADE;

-- Comments
COMMENT ON TABLE stock_splits IS 'Historical stock split events with ratios and dates';
COMMENT ON COLUMN stock_splits.split_ratio IS 'Decimal representation of split (2:1 = 2.0, 3:2 = 1.5)';
COMMENT ON COLUMN stock_splits.numerator IS 'Numerator of split ratio (3 in 3:2 split)';
COMMENT ON COLUMN stock_splits.denominator IS 'Denominator of split ratio (2 in 3:2 split)';
COMMENT ON COLUMN stock_splits.split_string IS 'Human-readable split format from data provider';

-- Grant permissions
GRANT ALL ON stock_splits TO postgres, anon, authenticated, service_role;
GRANT USAGE, SELECT ON SEQUENCE stock_splits_id_seq TO postgres, anon, authenticated, service_role;
