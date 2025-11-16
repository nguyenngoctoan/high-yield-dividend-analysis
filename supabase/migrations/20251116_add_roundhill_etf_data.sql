-- Migration: Add Roundhill ETF Data Table
-- Created: 2025-11-16
-- Description: Creates table to store Roundhill ETF comprehensive data including
--              performance, fund details, distributions, and holdings

-- Create raw_roundhill_etf_data table
CREATE TABLE IF NOT EXISTS raw_roundhill_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Generated column for date-based constraint
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Fund metrics extracted from page
    expense_ratio TEXT,
    launch_date TEXT,
    holdings_count TEXT,

    -- JSON data structures for flexible storage
    fund_overview JSONB,
    performance_data JSONB,
    fund_details JSONB,
    distributions JSONB,
    holdings JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_roundhill_ticker_scraped_date UNIQUE (ticker, scraped_date)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_roundhill_ticker ON raw_roundhill_etf_data(ticker);
CREATE INDEX IF NOT EXISTS idx_roundhill_scraped_at ON raw_roundhill_etf_data(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_roundhill_scraped_date ON raw_roundhill_etf_data(scraped_date DESC);
CREATE INDEX IF NOT EXISTS idx_roundhill_ticker_scraped ON raw_roundhill_etf_data(ticker, scraped_at DESC);

-- Create GIN indexes for JSONB columns to enable fast JSON queries
CREATE INDEX IF NOT EXISTS idx_roundhill_fund_overview ON raw_roundhill_etf_data USING GIN (fund_overview);
CREATE INDEX IF NOT EXISTS idx_roundhill_performance ON raw_roundhill_etf_data USING GIN (performance_data);
CREATE INDEX IF NOT EXISTS idx_roundhill_fund_details ON raw_roundhill_etf_data USING GIN (fund_details);
CREATE INDEX IF NOT EXISTS idx_roundhill_distributions ON raw_roundhill_etf_data USING GIN (distributions);
CREATE INDEX IF NOT EXISTS idx_roundhill_holdings ON raw_roundhill_etf_data USING GIN (holdings);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_roundhill_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_roundhill_updated_at
    BEFORE UPDATE ON raw_roundhill_etf_data
    FOR EACH ROW
    EXECUTE FUNCTION update_roundhill_updated_at();

-- Add comments for documentation
COMMENT ON TABLE raw_roundhill_etf_data IS 'Stores comprehensive Roundhill ETF data including performance, distributions, and holdings';
COMMENT ON COLUMN raw_roundhill_etf_data.ticker IS 'ETF ticker symbol (e.g., METV)';
COMMENT ON COLUMN raw_roundhill_etf_data.fund_name IS 'Full name of the ETF';
COMMENT ON COLUMN raw_roundhill_etf_data.scraped_at IS 'Timestamp when data was scraped';
COMMENT ON COLUMN raw_roundhill_etf_data.scraped_date IS 'Date when data was scraped (derived from scraped_at timestamp)';
COMMENT ON COLUMN raw_roundhill_etf_data.expense_ratio IS 'Expense ratio as text (e.g., "0.95%")';
COMMENT ON COLUMN raw_roundhill_etf_data.launch_date IS 'Fund launch date';
COMMENT ON COLUMN raw_roundhill_etf_data.holdings_count IS 'Number of holdings in the fund';
COMMENT ON COLUMN raw_roundhill_etf_data.fund_overview IS 'Fund overview information as JSON key-value pairs';
COMMENT ON COLUMN raw_roundhill_etf_data.performance_data IS 'Performance metrics as JSON';
COMMENT ON COLUMN raw_roundhill_etf_data.fund_details IS 'Fund details as JSON key-value pairs';
COMMENT ON COLUMN raw_roundhill_etf_data.distributions IS 'Distribution/dividend data as JSON array';
COMMENT ON COLUMN raw_roundhill_etf_data.holdings IS 'Fund holdings as JSON array';

-- Create view for latest data per ticker
CREATE OR REPLACE VIEW v_roundhill_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    scraped_at,
    scraped_date,
    expense_ratio,
    launch_date,
    holdings_count,
    fund_overview,
    performance_data,
    fund_details,
    distributions,
    holdings,
    created_at,
    updated_at
FROM raw_roundhill_etf_data
ORDER BY ticker, scraped_date DESC, scraped_at DESC;

COMMENT ON VIEW v_roundhill_latest IS 'Latest scraped data for each Roundhill ETF ticker';

-- Grant appropriate permissions (adjust based on your RLS policies)
-- For now, allowing authenticated users to read
ALTER TABLE raw_roundhill_etf_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to Roundhill data"
    ON raw_roundhill_etf_data
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow service role full access to Roundhill data"
    ON raw_roundhill_etf_data
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
