-- Staging model: Flattened ETF distribution data
-- Combines data from YieldMax, Roundhill, NEOS, and Defiance ETF tables
-- into a unified, normalized format

-- Drop existing table if exists
DROP TABLE IF EXISTS stg_etf_distributions CASCADE;

-- Create staging table for flattened distribution data
CREATE TABLE stg_etf_distributions (
    id BIGSERIAL PRIMARY KEY,

    -- ETF identification
    ticker TEXT NOT NULL,
    fund_name TEXT,
    provider TEXT NOT NULL, -- YieldMax, Roundhill, NEOS, Defiance

    -- Distribution dates
    declaration_date DATE,
    ex_date DATE,
    record_date DATE,
    payable_date DATE,

    -- Distribution amount
    distribution_amount NUMERIC(10, 4),
    distribution_amount_text TEXT, -- Original text value (e.g., "$0.1620", "—")

    -- Additional distribution metadata
    return_of_capital_pct NUMERIC(5, 2), -- ROC percentage
    distribution_frequency TEXT, -- Monthly, Weekly, Quarterly, etc.
    distribution_note TEXT, -- For special cases like XDIV, NVDW

    -- Data quality
    is_valid BOOLEAN DEFAULT true, -- false if missing key data
    raw_data JSONB, -- Original distribution record

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    CONSTRAINT unique_distribution UNIQUE (ticker, provider, ex_date)
);

-- Create indexes for common queries
CREATE INDEX idx_stg_etf_dist_ticker ON stg_etf_distributions(ticker);
CREATE INDEX idx_stg_etf_dist_provider ON stg_etf_distributions(provider);
CREATE INDEX idx_stg_etf_dist_ex_date ON stg_etf_distributions(ex_date);
CREATE INDEX idx_stg_etf_dist_payable_date ON stg_etf_distributions(payable_date);
CREATE INDEX idx_stg_etf_dist_ticker_ex_date ON stg_etf_distributions(ticker, ex_date);

-- Add comment
COMMENT ON TABLE stg_etf_distributions IS 'Staging table: Flattened distribution data from all ETF providers (YieldMax, Roundhill, NEOS, Defiance)';

-- Create view for latest distributions per ticker
CREATE OR REPLACE VIEW v_latest_etf_distributions AS
SELECT DISTINCT ON (ticker)
    ticker,
    fund_name,
    provider,
    declaration_date,
    ex_date,
    record_date,
    payable_date,
    distribution_amount,
    distribution_frequency,
    return_of_capital_pct
FROM stg_etf_distributions
WHERE is_valid = true
  AND ex_date IS NOT NULL
ORDER BY ticker, ex_date DESC;

COMMENT ON VIEW v_latest_etf_distributions IS 'Latest distribution for each ETF ticker';

-- Grant permissions
GRANT SELECT ON stg_etf_distributions TO anon, authenticated;
GRANT SELECT ON v_latest_etf_distributions TO anon, authenticated;
