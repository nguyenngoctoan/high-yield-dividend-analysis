-- Migration: Create Data Source Tracking Table
-- Date: 2025-11-13
-- Description: Tracks which data sources have specific data types for each symbol
--              to avoid redundant API calls and optimize data fetching

-- Create data source tracking table
CREATE TABLE IF NOT EXISTS raw_data_source_tracking (
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    has_data BOOLEAN DEFAULT false,
    last_checked_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    last_successful_fetch_at TIMESTAMP WITH TIME ZONE,
    fetch_attempts INT DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),

    -- Composite primary key: one record per symbol+data_type+source combination
    PRIMARY KEY (symbol, data_type, source)
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_data_source_tracking_symbol
    ON raw_data_source_tracking(symbol);

CREATE INDEX IF NOT EXISTS idx_data_source_tracking_data_type
    ON raw_data_source_tracking(data_type);

CREATE INDEX IF NOT EXISTS idx_data_source_tracking_has_data
    ON raw_data_source_tracking(has_data) WHERE has_data = true;

CREATE INDEX IF NOT EXISTS idx_data_source_tracking_last_checked
    ON raw_data_source_tracking(last_checked_at);

-- Composite index for common query pattern: find best source for a symbol+data_type
CREATE INDEX IF NOT EXISTS idx_data_source_tracking_lookup
    ON raw_data_source_tracking(symbol, data_type, has_data, source);

-- Add trigger to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_data_source_tracking_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_data_source_tracking_updated_at BEFORE UPDATE
ON raw_data_source_tracking FOR EACH ROW
EXECUTE PROCEDURE update_data_source_tracking_updated_at();

-- Add comments for documentation
COMMENT ON TABLE raw_data_source_tracking IS 'Tracks which data sources (FMP, AlphaVantage, Yahoo) have specific data types (AUM, dividends, IV, volume) for each symbol to optimize API usage';
COMMENT ON COLUMN raw_data_source_tracking.symbol IS 'Stock/ETF ticker symbol';
COMMENT ON COLUMN raw_data_source_tracking.data_type IS 'Type of data: aum, dividends, volume, iv, prices, company_info';
COMMENT ON COLUMN raw_data_source_tracking.source IS 'Data source: FMP, AlphaVantage, Yahoo';
COMMENT ON COLUMN raw_data_source_tracking.has_data IS 'True if this source has this data type for this symbol';
COMMENT ON COLUMN raw_data_source_tracking.last_checked_at IS 'Last time we checked this source for this data type';
COMMENT ON COLUMN raw_data_source_tracking.last_successful_fetch_at IS 'Last time we successfully fetched data from this source';
COMMENT ON COLUMN raw_data_source_tracking.fetch_attempts IS 'Number of times we attempted to fetch this data type';
COMMENT ON COLUMN raw_data_source_tracking.notes IS 'Additional notes or error messages';

-- Create helper view for quick lookup of best sources
CREATE OR REPLACE VIEW v_data_source_preferences AS
SELECT
    symbol,
    data_type,
    -- Get the preferred source (first successful source, ordered by priority)
    (
        SELECT source
        FROM raw_data_source_tracking t2
        WHERE t2.symbol = t1.symbol
          AND t2.data_type = t1.data_type
          AND t2.has_data = true
        ORDER BY
            CASE source
                WHEN 'FMP' THEN 1
                WHEN 'Yahoo' THEN 2
                WHEN 'AlphaVantage' THEN 3
                ELSE 4
            END,
            last_successful_fetch_at DESC NULLS LAST
        LIMIT 1
    ) AS preferred_source,
    -- Get all sources that have this data
    array_agg(source ORDER BY source) FILTER (WHERE has_data = true) AS available_sources,
    -- Get timestamp of most recent successful fetch
    MAX(last_successful_fetch_at) FILTER (WHERE has_data = true) AS last_successful_fetch
FROM raw_data_source_tracking t1
GROUP BY symbol, data_type;

COMMENT ON VIEW v_data_source_preferences IS 'Provides preferred data source for each symbol+data_type combination based on availability and priority';

-- Create function to get preferred source
CREATE OR REPLACE FUNCTION get_preferred_source(
    p_symbol VARCHAR(20),
    p_data_type VARCHAR(50)
)
RETURNS VARCHAR(50)
LANGUAGE plpgsql
AS $$
DECLARE
    v_source VARCHAR(50);
BEGIN
    SELECT preferred_source INTO v_source
    FROM v_data_source_preferences
    WHERE symbol = p_symbol AND data_type = p_data_type;

    RETURN v_source;
END;
$$;

COMMENT ON FUNCTION get_preferred_source IS 'Returns the preferred data source for a given symbol and data type';

-- Create function to record data source check
CREATE OR REPLACE FUNCTION record_data_source_check(
    p_symbol VARCHAR(20),
    p_data_type VARCHAR(50),
    p_source VARCHAR(50),
    p_has_data BOOLEAN,
    p_notes TEXT DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO raw_data_source_tracking (
        symbol,
        data_type,
        source,
        has_data,
        last_checked_at,
        last_successful_fetch_at,
        fetch_attempts,
        notes
    ) VALUES (
        p_symbol,
        p_data_type,
        p_source,
        p_has_data,
        TIMEZONE('utc'::text, NOW()),
        CASE WHEN p_has_data THEN TIMEZONE('utc'::text, NOW()) ELSE NULL END,
        1,
        p_notes
    )
    ON CONFLICT (symbol, data_type, source)
    DO UPDATE SET
        has_data = p_has_data,
        last_checked_at = TIMEZONE('utc'::text, NOW()),
        last_successful_fetch_at = CASE
            WHEN p_has_data THEN TIMEZONE('utc'::text, NOW())
            ELSE raw_data_source_tracking.last_successful_fetch_at
        END,
        fetch_attempts = raw_data_source_tracking.fetch_attempts + 1,
        notes = COALESCE(p_notes, raw_data_source_tracking.notes);
END;
$$;

COMMENT ON FUNCTION record_data_source_check IS 'Records the result of checking a data source for a specific data type';

-- Verification
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Created table: raw_data_source_tracking';
    RAISE NOTICE 'Created view: v_data_source_preferences';
    RAISE NOTICE 'Created function: get_preferred_source(symbol, data_type)';
    RAISE NOTICE 'Created function: record_data_source_check(symbol, data_type, source, has_data, notes)';
    RAISE NOTICE '';
    RAISE NOTICE 'Supported data types: aum, dividends, volume, iv, prices, company_info';
    RAISE NOTICE 'Supported sources: FMP, AlphaVantage, Yahoo';
END $$;
