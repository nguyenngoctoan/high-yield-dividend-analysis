-- Migration: Add Global X Canada ETF Data Table
-- Created: 2025-11-16
-- Description: Creates table to store Global X Canada ETF comprehensive data including
--              performance, fund details, distributions, holdings, and covered call specific data
--              Supports 107 ETFs across 13 categories with covered call metrics

-- Create raw_globalx_etf_data table
CREATE TABLE IF NOT EXISTS raw_globalx_etf_data (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    fund_name TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Generated column for date-based constraint
    scraped_date DATE GENERATED ALWAYS AS ((scraped_at AT TIME ZONE 'UTC')::DATE) STORED,

    -- Core fund metrics
    cusip TEXT,
    inception_date TEXT,
    nav TEXT,
    market_price TEXT,
    premium_discount TEXT,
    management_fee TEXT,
    mer TEXT,
    ter TEXT,
    net_assets TEXT,
    distribution_yield TEXT,
    distribution_frequency TEXT,
    category TEXT,  -- Cash & Fixed Income, Corporate Class, Thematic, Enhanced Growth, Equity Essentials, Covered Call, Commodities, Cryptocurrency, Precious Metals, Asset Allocation, BetaPro

    -- Covered call specific fields (for covered call ETFs)
    average_coverage TEXT,
    moneyness TEXT,
    option_yield TEXT,
    dividend_yield TEXT,

    -- Additional core fields
    benchmark_index TEXT,
    most_recent_distribution TEXT,
    trailing_yield_12m TEXT,
    leverage_ratio TEXT,  -- For Enhanced and BetaPro products (e.g., "1.25x", "2x")
    expense_ratio TEXT,

    -- JSON data structures for flexible storage
    fund_details JSONB,          -- Additional fund metadata, benchmark, risk rating, investment objective
    holdings JSONB,              -- Top 10 holdings with security name and weight
    distributions JSONB,         -- Distribution history with ex-div, record, payment dates
    performance_data JSONB,      -- Annualized performance (1mo, 3mo, 6mo, YTD, 1yr, 3yr, 5yr, 10yr, inception) and calendar year returns
    sector_allocation JSONB,     -- Sector breakdown (for equity ETFs)
    geographic_allocation JSONB, -- Geographic breakdown (for global ETFs)

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_globalx_ticker_scraped_date UNIQUE (ticker, scraped_date)
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_globalx_ticker ON raw_globalx_etf_data(ticker);
CREATE INDEX IF NOT EXISTS idx_globalx_scraped_at ON raw_globalx_etf_data(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_globalx_scraped_date ON raw_globalx_etf_data(scraped_date DESC);
CREATE INDEX IF NOT EXISTS idx_globalx_ticker_scraped ON raw_globalx_etf_data(ticker, scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_globalx_category ON raw_globalx_etf_data(category);
CREATE INDEX IF NOT EXISTS idx_globalx_inception_date ON raw_globalx_etf_data(inception_date);

-- Create GIN indexes for JSONB columns to enable fast JSON queries
CREATE INDEX IF NOT EXISTS idx_globalx_fund_details ON raw_globalx_etf_data USING GIN (fund_details);
CREATE INDEX IF NOT EXISTS idx_globalx_holdings ON raw_globalx_etf_data USING GIN (holdings);
CREATE INDEX IF NOT EXISTS idx_globalx_distributions ON raw_globalx_etf_data USING GIN (distributions);
CREATE INDEX IF NOT EXISTS idx_globalx_performance ON raw_globalx_etf_data USING GIN (performance_data);
CREATE INDEX IF NOT EXISTS idx_globalx_sector_allocation ON raw_globalx_etf_data USING GIN (sector_allocation);
CREATE INDEX IF NOT EXISTS idx_globalx_geographic_allocation ON raw_globalx_etf_data USING GIN (geographic_allocation);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_globalx_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_globalx_updated_at
    BEFORE UPDATE ON raw_globalx_etf_data
    FOR EACH ROW
    EXECUTE FUNCTION update_globalx_updated_at();

-- Add comments for documentation
COMMENT ON TABLE raw_globalx_etf_data IS 'Stores comprehensive Global X Canada ETF data including performance, distributions, holdings, covered call metrics, and leveraged product data. Covers 107 ETFs across 13 categories.';
COMMENT ON COLUMN raw_globalx_etf_data.ticker IS 'ETF ticker symbol (e.g., ENCC, CNDX, SHLD, CASH)';
COMMENT ON COLUMN raw_globalx_etf_data.fund_name IS 'Full name of the ETF';
COMMENT ON COLUMN raw_globalx_etf_data.scraped_at IS 'Timestamp when data was scraped';
COMMENT ON COLUMN raw_globalx_etf_data.scraped_date IS 'Date when data was scraped (derived from scraped_at timestamp)';
COMMENT ON COLUMN raw_globalx_etf_data.cusip IS 'CUSIP identifier';
COMMENT ON COLUMN raw_globalx_etf_data.inception_date IS 'Fund inception date';
COMMENT ON COLUMN raw_globalx_etf_data.nav IS 'Net asset value';
COMMENT ON COLUMN raw_globalx_etf_data.market_price IS 'Current market price';
COMMENT ON COLUMN raw_globalx_etf_data.premium_discount IS 'Premium or discount to NAV';
COMMENT ON COLUMN raw_globalx_etf_data.management_fee IS 'Management fee percentage';
COMMENT ON COLUMN raw_globalx_etf_data.mer IS 'Management expense ratio';
COMMENT ON COLUMN raw_globalx_etf_data.ter IS 'Trading expense ratio';
COMMENT ON COLUMN raw_globalx_etf_data.net_assets IS 'Total assets under management';
COMMENT ON COLUMN raw_globalx_etf_data.distribution_yield IS 'Annualized distribution yield percentage';
COMMENT ON COLUMN raw_globalx_etf_data.distribution_frequency IS 'Distribution schedule (Monthly, Quarterly, Annual, etc.)';
COMMENT ON COLUMN raw_globalx_etf_data.category IS 'ETF category (Cash & Fixed Income, Corporate Class, Thematic, Enhanced Growth, Equity Essentials, Covered Call - Index, Covered Call - Sector, Enhanced Covered Call, Commodities - Covered Call, Cryptocurrency - Covered Call, Precious Metals, Asset Allocation, BetaPro)';
COMMENT ON COLUMN raw_globalx_etf_data.average_coverage IS 'Average covered call coverage percentage (covered call ETFs only)';
COMMENT ON COLUMN raw_globalx_etf_data.moneyness IS 'Average moneyness of options (covered call ETFs only)';
COMMENT ON COLUMN raw_globalx_etf_data.option_yield IS 'Option annualized yield (covered call ETFs only)';
COMMENT ON COLUMN raw_globalx_etf_data.dividend_yield IS 'Dividend yield from underlying holdings (covered call ETFs only)';
COMMENT ON COLUMN raw_globalx_etf_data.benchmark_index IS 'Benchmark index name';
COMMENT ON COLUMN raw_globalx_etf_data.most_recent_distribution IS 'Most recent distribution amount per unit';
COMMENT ON COLUMN raw_globalx_etf_data.trailing_yield_12m IS '12-month trailing yield';
COMMENT ON COLUMN raw_globalx_etf_data.leverage_ratio IS 'Leverage ratio for Enhanced Growth and BetaPro products (e.g., "1.25x", "2x")';
COMMENT ON COLUMN raw_globalx_etf_data.expense_ratio IS 'Total expense ratio';
COMMENT ON COLUMN raw_globalx_etf_data.fund_details IS 'Additional fund metadata including investment objective, risk rating, reasons to consider, documents';
COMMENT ON COLUMN raw_globalx_etf_data.holdings IS 'Top 10 holdings with security name and weight percentage';
COMMENT ON COLUMN raw_globalx_etf_data.distributions IS 'Distribution history with ex-dividend date, record date, payment date, amount, and period';
COMMENT ON COLUMN raw_globalx_etf_data.performance_data IS 'Performance metrics including annualized returns (1mo-inception) and calendar year returns';
COMMENT ON COLUMN raw_globalx_etf_data.sector_allocation IS 'Sector allocation breakdown (equity ETFs)';
COMMENT ON COLUMN raw_globalx_etf_data.geographic_allocation IS 'Geographic allocation breakdown (global/international ETFs)';

-- Create view for latest data per ticker
CREATE OR REPLACE VIEW v_globalx_latest AS
SELECT DISTINCT ON (ticker)
    id,
    ticker,
    fund_name,
    url,
    scraped_at,
    scraped_date,
    cusip,
    inception_date,
    nav,
    market_price,
    premium_discount,
    management_fee,
    mer,
    ter,
    net_assets,
    distribution_yield,
    distribution_frequency,
    category,
    average_coverage,
    moneyness,
    option_yield,
    dividend_yield,
    benchmark_index,
    most_recent_distribution,
    trailing_yield_12m,
    leverage_ratio,
    expense_ratio,
    fund_details,
    holdings,
    distributions,
    performance_data,
    sector_allocation,
    geographic_allocation,
    created_at,
    updated_at
FROM raw_globalx_etf_data
ORDER BY ticker, scraped_date DESC, scraped_at DESC;

COMMENT ON VIEW v_globalx_latest IS 'Latest scraped data for each Global X Canada ETF ticker';

-- Grant appropriate permissions (adjust based on your RLS policies)
ALTER TABLE raw_globalx_etf_data ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to Global X data"
    ON raw_globalx_etf_data
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Allow service role full access to Global X data"
    ON raw_globalx_etf_data
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
