-- Migration: Add Purpose ETF Data Table
-- Created: 2025-11-16
-- Description: Creates table to store Purpose Investments ETF comprehensive data including
--              performance, fund details, distributions, holdings, and Yield Shares specific data

-- Create raw_purpose_etf_data table
CREATE TABLE IF NOT EXISTS raw_purpose_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Generated column for date-based constraint
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Core fund metrics
    series VARCHAR(10),  -- ETF, F, A, I
    nav TEXT,
    aum TEXT,
    management_fee TEXT,
    mer TEXT,
    distribution_frequency TEXT,
    category TEXT,  -- Equity, Fixed Income, Cryptocurrency, Alternatives, Multi-Asset, Commodities, Cash Management
    current_yield TEXT,

    -- Additional core fields
    fund_structure TEXT,
    cusip TEXT,
    exchange TEXT,
    currency_hedged BOOLEAN,
    settlement TEXT,

    -- Fixed income specific fields
    duration TEXT,
    coupon TEXT,
    maturity_yield TEXT,

    -- Yield Shares specific fields
    underlying TEXT,  -- Underlying stock (MSFT, TSLA, etc.)

    -- JSON data structures for flexible storage
    fund_details JSONB,          -- Additional fund metadata
    portfolio_data JSONB,        -- Asset allocation, sector, holdings, option statistics
    distributions JSONB,         -- Distribution history
    performance_data JSONB,      -- Historical returns and performance metrics
    eligibilities JSONB,         -- DRIP, PACC, SWP, RRSP flags

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_purpose_ticker_scraped_date UNIQUE (ticker, scraped_date)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_purpose_ticker ON raw_purpose_etf_data(ticker);
CREATE INDEX IF NOT EXISTS idx_purpose_scraped_at ON raw_purpose_etf_data(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_purpose_scraped_date ON raw_purpose_etf_data(scraped_date DESC);
CREATE INDEX IF NOT EXISTS idx_purpose_ticker_scraped ON raw_purpose_etf_data(ticker, scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_purpose_category ON raw_purpose_etf_data(category);
CREATE INDEX IF NOT EXISTS idx_purpose_series ON raw_purpose_etf_data(series);
CREATE INDEX IF NOT EXISTS idx_purpose_underlying ON raw_purpose_etf_data(underlying);

-- Create GIN indexes for JSONB columns to enable fast JSON queries
CREATE INDEX IF NOT EXISTS idx_purpose_fund_details ON raw_purpose_etf_data USING GIN (fund_details);
CREATE INDEX IF NOT EXISTS idx_purpose_portfolio ON raw_purpose_etf_data USING GIN (portfolio_data);
CREATE INDEX IF NOT EXISTS idx_purpose_distributions ON raw_purpose_etf_data USING GIN (distributions);
CREATE INDEX IF NOT EXISTS idx_purpose_performance ON raw_purpose_etf_data USING GIN (performance_data);
CREATE INDEX IF NOT EXISTS idx_purpose_eligibilities ON raw_purpose_etf_data USING GIN (eligibilities);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_purpose_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_purpose_updated_at
    BEFORE UPDATE ON raw_purpose_etf_data
    FOR EACH ROW
    EXECUTE FUNCTION update_purpose_updated_at();

-- Add comments for documentation
COMMENT ON TABLE raw_purpose_etf_data IS 'Stores comprehensive Purpose Investments ETF data including performance, distributions, holdings, and Yield Shares option statistics';
COMMENT ON COLUMN raw_purpose_etf_data.ticker IS 'ETF ticker symbol (e.g., YTSL, BTCC, MSFY)';
COMMENT ON COLUMN raw_purpose_etf_data.fund_name IS 'Full name of the ETF';
COMMENT ON COLUMN raw_purpose_etf_data.scraped_at IS 'Timestamp when data was scraped';
COMMENT ON COLUMN raw_purpose_etf_data.scraped_date IS 'Date when data was scraped (derived from scraped_at timestamp)';
COMMENT ON COLUMN raw_purpose_etf_data.series IS 'Fund series (ETF, F, A, I)';
COMMENT ON COLUMN raw_purpose_etf_data.nav IS 'Net asset value';
COMMENT ON COLUMN raw_purpose_etf_data.aum IS 'Assets under management';
COMMENT ON COLUMN raw_purpose_etf_data.management_fee IS 'Management fee percentage';
COMMENT ON COLUMN raw_purpose_etf_data.mer IS 'Management expense ratio';
COMMENT ON COLUMN raw_purpose_etf_data.distribution_frequency IS 'Distribution schedule (Monthly, Quarterly, etc.)';
COMMENT ON COLUMN raw_purpose_etf_data.category IS 'ETF category (Equity, Fixed Income, Cryptocurrency, Alternatives, Multi-Asset, Commodities, Cash Management)';
COMMENT ON COLUMN raw_purpose_etf_data.current_yield IS 'Current yield percentage (especially for Yield Shares)';
COMMENT ON COLUMN raw_purpose_etf_data.fund_structure IS 'Legal structure (Investment Trust, Corporation, etc.)';
COMMENT ON COLUMN raw_purpose_etf_data.cusip IS 'CUSIP identifier';
COMMENT ON COLUMN raw_purpose_etf_data.exchange IS 'Trading exchange (NEOE, NEO, etc.)';
COMMENT ON COLUMN raw_purpose_etf_data.currency_hedged IS 'Whether the fund is currency hedged';
COMMENT ON COLUMN raw_purpose_etf_data.settlement IS 'Settlement period (T+1, T+2, etc.)';
COMMENT ON COLUMN raw_purpose_etf_data.duration IS 'Duration in years (fixed income only)';
COMMENT ON COLUMN raw_purpose_etf_data.coupon IS 'Coupon rate (fixed income only)';
COMMENT ON COLUMN raw_purpose_etf_data.maturity_yield IS 'Yield to maturity (fixed income only)';
COMMENT ON COLUMN raw_purpose_etf_data.underlying IS 'Underlying stock for Yield Shares ETFs (MSFT, TSLA, NVDA, etc.)';
COMMENT ON COLUMN raw_purpose_etf_data.fund_details IS 'Additional fund metadata as JSON';
COMMENT ON COLUMN raw_purpose_etf_data.portfolio_data IS 'Portfolio data including asset allocation, sector allocation, holdings, option statistics (for Yield Shares)';
COMMENT ON COLUMN raw_purpose_etf_data.distributions IS 'Distribution history as JSON array';
COMMENT ON COLUMN raw_purpose_etf_data.performance_data IS 'Historical returns and performance metrics';
COMMENT ON COLUMN raw_purpose_etf_data.eligibilities IS 'Program eligibility flags (DRIP, PACC, SWP, RRSP)';

-- Create view for latest data per ticker
CREATE OR REPLACE VIEW v_purpose_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    scraped_at,
    scraped_date,
    series,
    nav,
    aum,
    management_fee,
    mer,
    distribution_frequency,
    category,
    current_yield,
    fund_structure,
    cusip,
    exchange,
    currency_hedged,
    settlement,
    duration,
    coupon,
    maturity_yield,
    underlying,
    fund_details,
    portfolio_data,
    distributions,
    performance_data,
    eligibilities,
    created_at,
    updated_at
FROM raw_purpose_etf_data
ORDER BY ticker, scraped_date DESC, scraped_at DESC;

COMMENT ON VIEW v_purpose_latest IS 'Latest scraped data for each Purpose Investments ETF ticker';

-- Grant appropriate permissions (adjust based on your RLS policies)
ALTER TABLE raw_purpose_etf_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to Purpose data"
    ON raw_purpose_etf_data
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow service role full access to Purpose data"
    ON raw_purpose_etf_data
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
