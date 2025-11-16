-- Migration: Add YieldMax ETF Data Table
-- Created: 2025-11-16
-- Description: Creates table to store YieldMax ETF comprehensive data including
--              performance, fund details, distributions, and holdings

-- Create raw_yieldmax_etf_data table
CREATE TABLE IF NOT EXISTS raw_yieldmax_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Performance data (stored as JSON)
    performance_month_end JSONB,
    performance_quarter_end JSONB,

    -- Fund information
    fund_overview JSONB,
    investment_objective TEXT,
    fund_details JSONB,

    -- Distribution and holdings data
    distributions JSONB,
    top_10_holdings JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_ticker_scraped_at UNIQUE (ticker, scraped_at)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_yieldmax_ticker ON raw_yieldmax_etf_data(ticker);
CREATE INDEX IF NOT EXISTS idx_yieldmax_scraped_at ON raw_yieldmax_etf_data(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_yieldmax_ticker_scraped ON raw_yieldmax_etf_data(ticker, scraped_at DESC);

-- Create GIN indexes for JSONB columns to enable fast JSON queries
CREATE INDEX IF NOT EXISTS idx_yieldmax_performance_month ON raw_yieldmax_etf_data USING GIN (performance_month_end);
CREATE INDEX IF NOT EXISTS idx_yieldmax_performance_quarter ON raw_yieldmax_etf_data USING GIN (performance_quarter_end);
CREATE INDEX IF NOT EXISTS idx_yieldmax_fund_details ON raw_yieldmax_etf_data USING GIN (fund_details);
CREATE INDEX IF NOT EXISTS idx_yieldmax_distributions ON raw_yieldmax_etf_data USING GIN (distributions);
CREATE INDEX IF NOT EXISTS idx_yieldmax_holdings ON raw_yieldmax_etf_data USING GIN (top_10_holdings);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_yieldmax_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_yieldmax_updated_at
    BEFORE UPDATE ON raw_yieldmax_etf_data
    FOR EACH ROW
    EXECUTE FUNCTION update_yieldmax_updated_at();

-- Add comments for documentation
COMMENT ON TABLE raw_yieldmax_etf_data IS 'Stores comprehensive YieldMax ETF data including performance, distributions, and holdings';
COMMENT ON COLUMN raw_yieldmax_etf_data.ticker IS 'ETF ticker symbol (e.g., TSLY)';
COMMENT ON COLUMN raw_yieldmax_etf_data.fund_name IS 'Full name of the ETF';
COMMENT ON COLUMN raw_yieldmax_etf_data.performance_month_end IS 'Month-end performance metrics as JSON';
COMMENT ON COLUMN raw_yieldmax_etf_data.performance_quarter_end IS 'Quarter-end performance metrics as JSON';
COMMENT ON COLUMN raw_yieldmax_etf_data.fund_overview IS 'Fund overview information as JSON key-value pairs';
COMMENT ON COLUMN raw_yieldmax_etf_data.investment_objective IS 'Investment objective description text';
COMMENT ON COLUMN raw_yieldmax_etf_data.fund_details IS 'Fund details as JSON key-value pairs';
COMMENT ON COLUMN raw_yieldmax_etf_data.distributions IS 'Distribution/dividend data as JSON array';
COMMENT ON COLUMN raw_yieldmax_etf_data.top_10_holdings IS 'Top 10 holdings as JSON array';
COMMENT ON COLUMN raw_yieldmax_etf_data.scraped_at IS 'Timestamp when data was scraped';

-- Create view for latest data per ticker
CREATE OR REPLACE VIEW v_yieldmax_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    scraped_at,
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
ORDER BY ticker, scraped_at DESC;

COMMENT ON VIEW v_yieldmax_latest IS 'Latest scraped data for each YieldMax ETF ticker';

-- Grant appropriate permissions (adjust based on your RLS policies)
-- For now, allowing authenticated users to read
ALTER TABLE raw_yieldmax_etf_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to YieldMax data"
    ON raw_yieldmax_etf_data
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow service role full access to YieldMax data"
    ON raw_yieldmax_etf_data
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
