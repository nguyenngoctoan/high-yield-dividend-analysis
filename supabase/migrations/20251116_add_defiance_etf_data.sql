-- Migration: Add Defiance ETF Data Table
-- Created: 2025-11-16
-- Description: Creates table to store Defiance ETF comprehensive data including
--              performance, fund details, distributions, and holdings

-- Create raw_defiance_etf_data table
CREATE TABLE IF NOT EXISTS raw_defiance_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Generated column for date-based constraint
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Fund metrics extracted from page
    expense_ratio TEXT,
    inception_date TEXT,
    distribution_rate TEXT,
    distribution_frequency TEXT,
    sec_yield_30day TEXT,
    nav TEXT,
    market_price TEXT,
    premium_discount TEXT,

    -- JSON data structures for flexible storage
    fund_details JSONB,
    performance_data JSONB,
    distributions JSONB,
    holdings JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_defiance_ticker_scraped_date UNIQUE (ticker, scraped_date)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_defiance_ticker ON raw_defiance_etf_data(ticker);
CREATE INDEX IF NOT EXISTS idx_defiance_scraped_at ON raw_defiance_etf_data(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_defiance_scraped_date ON raw_defiance_etf_data(scraped_date DESC);
CREATE INDEX IF NOT EXISTS idx_defiance_ticker_scraped ON raw_defiance_etf_data(ticker, scraped_at DESC);

-- Create GIN indexes for JSONB columns to enable fast JSON queries
CREATE INDEX IF NOT EXISTS idx_defiance_fund_details ON raw_defiance_etf_data USING GIN (fund_details);
CREATE INDEX IF NOT EXISTS idx_defiance_performance ON raw_defiance_etf_data USING GIN (performance_data);
CREATE INDEX IF NOT EXISTS idx_defiance_distributions ON raw_defiance_etf_data USING GIN (distributions);
CREATE INDEX IF NOT EXISTS idx_defiance_holdings ON raw_defiance_etf_data USING GIN (holdings);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_defiance_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_defiance_updated_at
    BEFORE UPDATE ON raw_defiance_etf_data
    FOR EACH ROW
    EXECUTE FUNCTION update_defiance_updated_at();

-- Add comments for documentation
COMMENT ON TABLE raw_defiance_etf_data IS 'Stores comprehensive Defiance ETF data including performance, distributions, and holdings';
COMMENT ON COLUMN raw_defiance_etf_data.ticker IS 'ETF ticker symbol (e.g., QQQY)';
COMMENT ON COLUMN raw_defiance_etf_data.fund_name IS 'Full name of the ETF';
COMMENT ON COLUMN raw_defiance_etf_data.scraped_at IS 'Timestamp when data was scraped';
COMMENT ON COLUMN raw_defiance_etf_data.scraped_date IS 'Date when data was scraped (derived from scraped_at timestamp)';
COMMENT ON COLUMN raw_defiance_etf_data.expense_ratio IS 'Expense ratio as text (e.g., "0.99%")';
COMMENT ON COLUMN raw_defiance_etf_data.inception_date IS 'Fund inception date (format: MM/DD/YYYY)';
COMMENT ON COLUMN raw_defiance_etf_data.distribution_rate IS 'Distribution rate as text';
COMMENT ON COLUMN raw_defiance_etf_data.distribution_frequency IS 'Distribution frequency (e.g., "Weekly", "Monthly")';
COMMENT ON COLUMN raw_defiance_etf_data.sec_yield_30day IS '30-day SEC yield';
COMMENT ON COLUMN raw_defiance_etf_data.nav IS 'Net asset value';
COMMENT ON COLUMN raw_defiance_etf_data.market_price IS 'Market price';
COMMENT ON COLUMN raw_defiance_etf_data.premium_discount IS 'Premium/discount to NAV';
COMMENT ON COLUMN raw_defiance_etf_data.fund_details IS 'Fund details as JSON key-value pairs (CUSIP, exchange, etc.)';
COMMENT ON COLUMN raw_defiance_etf_data.performance_data IS 'Performance metrics as JSON (1mo, 3mo, 6mo, YTD, 1yr, inception)';
COMMENT ON COLUMN raw_defiance_etf_data.distributions IS 'Distribution/dividend data as JSON array';
COMMENT ON COLUMN raw_defiance_etf_data.holdings IS 'Top 10 fund holdings as JSON array';

-- Create view for latest data per ticker
CREATE OR REPLACE VIEW v_defiance_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    scraped_at,
    scraped_date,
    expense_ratio,
    inception_date,
    distribution_rate,
    distribution_frequency,
    sec_yield_30day,
    nav,
    market_price,
    premium_discount,
    fund_details,
    performance_data,
    distributions,
    holdings,
    created_at,
    updated_at
FROM raw_defiance_etf_data
ORDER BY ticker, scraped_date DESC, scraped_at DESC;

COMMENT ON VIEW v_defiance_latest IS 'Latest scraped data for each Defiance ETF ticker';

-- Grant appropriate permissions (adjust based on your RLS policies)
-- For now, allowing authenticated users to read
ALTER TABLE raw_defiance_etf_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to Defiance data"
    ON raw_defiance_etf_data
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow service role full access to Defiance data"
    ON raw_defiance_etf_data
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
