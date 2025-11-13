-- SQL Function for Bulk Latest Date Fetching
-- This dramatically improves performance by replacing thousands of individual queries with one
-- Performance gain: ~24,000 queries -> 1 query (saves 5-10 minutes)

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS get_latest_dates_by_symbol(text, text);

-- Create function to get latest dates for all symbols in a single query
CREATE OR REPLACE FUNCTION get_latest_dates_by_symbol(
    table_name text,
    date_col text DEFAULT 'date'
)
RETURNS TABLE (
    symbol text,
    latest_date date
) AS $$
BEGIN
    -- Use dynamic SQL to support different tables and date columns
    -- This function works for both raw_stock_prices and raw_dividends
    RETURN QUERY EXECUTE format('
        SELECT
            symbol::text,
            MAX(%I)::date as latest_date
        FROM %I
        GROUP BY symbol
        ORDER BY symbol
    ', date_col, table_name);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_latest_dates_by_symbol(text, text) TO authenticated;
GRANT EXECUTE ON FUNCTION get_latest_dates_by_symbol(text, text) TO anon;

-- Create index on (symbol, date) for better performance if not exists
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_symbol_date
ON raw_stock_prices(symbol, date DESC);

CREATE INDEX IF NOT EXISTS idx_raw_dividends_symbol_exdate
ON raw_dividends(symbol, ex_date DESC);

-- Usage examples:
-- Get latest price dates for all symbols:
--   SELECT * FROM get_latest_dates_by_symbol('raw_stock_prices', 'date');
--
-- Get latest dividend dates for all symbols:
--   SELECT * FROM get_latest_dates_by_symbol('raw_dividends', 'ex_date');

COMMENT ON FUNCTION get_latest_dates_by_symbol IS
'Bulk fetch latest dates for all symbols. Replaces thousands of individual queries with one efficient query.';
