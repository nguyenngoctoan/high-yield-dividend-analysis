-- SQL Function for Getting Distinct Symbols with Price Data
-- This dramatically improves discovery performance by efficiently querying
-- which symbols already have price data, avoiding redundant validation

-- Drop existing function if it exists
DROP FUNCTION IF EXISTS get_distinct_symbols_with_prices();

-- Create function to get distinct symbols from raw_stock_prices
CREATE OR REPLACE FUNCTION get_distinct_symbols_with_prices()
RETURNS TABLE (
    symbol text
) AS $$
BEGIN
    -- Return distinct symbols that have at least one price record
    -- This is much faster than fetching all price records and deduplicating in Python
    RETURN QUERY
    SELECT DISTINCT raw_stock_prices.symbol::text
    FROM raw_stock_prices
    ORDER BY raw_stock_prices.symbol;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION get_distinct_symbols_with_prices() TO authenticated;
GRANT EXECUTE ON FUNCTION get_distinct_symbols_with_prices() TO anon;
GRANT EXECUTE ON FUNCTION get_distinct_symbols_with_prices() TO service_role;

-- Create index on symbol for better performance if not exists
CREATE INDEX IF NOT EXISTS idx_raw_stock_prices_symbol
ON raw_stock_prices(symbol);

-- Usage example:
-- SELECT * FROM get_distinct_symbols_with_prices();

COMMENT ON FUNCTION get_distinct_symbols_with_prices IS
'Returns distinct list of symbols that have price data. Used to skip validation during discovery phase.';
