-- Create raw_yieldmax_dividends table
-- Stores dividend data scraped from YieldMax ETF announcements

CREATE TABLE IF NOT EXISTS public.raw_yieldmax_dividends (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL,
    name TEXT,
    amount NUMERIC(10, 4),
    amount_per_share NUMERIC(10, 4),
    ex_date DATE,
    payment_date DATE,
    record_date DATE,
    frequency TEXT,
    source_url TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT raw_yieldmax_dividends_symbol_ex_date_key UNIQUE (symbol, ex_date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_symbol ON public.raw_yieldmax_dividends(symbol);
CREATE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_ex_date ON public.raw_yieldmax_dividends(ex_date);
CREATE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_payment_date ON public.raw_yieldmax_dividends(payment_date);
CREATE INDEX IF NOT EXISTS idx_raw_yieldmax_dividends_scraped_at ON public.raw_yieldmax_dividends(scraped_at);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_raw_yieldmax_dividends_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_raw_yieldmax_dividends_updated_at_trigger
    BEFORE UPDATE ON public.raw_yieldmax_dividends
    FOR EACH ROW
    EXECUTE FUNCTION update_raw_yieldmax_dividends_updated_at();

-- Add comments
COMMENT ON TABLE public.raw_yieldmax_dividends IS 'Stores dividend data scraped from YieldMax ETF announcements from Globe Newswire';
COMMENT ON COLUMN public.raw_yieldmax_dividends.symbol IS 'Stock ticker symbol';
COMMENT ON COLUMN public.raw_yieldmax_dividends.name IS 'Full name of the ETF';
COMMENT ON COLUMN public.raw_yieldmax_dividends.amount IS 'Total dividend amount';
COMMENT ON COLUMN public.raw_yieldmax_dividends.amount_per_share IS 'Dividend amount per share';
COMMENT ON COLUMN public.raw_yieldmax_dividends.ex_date IS 'Ex-dividend date';
COMMENT ON COLUMN public.raw_yieldmax_dividends.payment_date IS 'Payment date';
COMMENT ON COLUMN public.raw_yieldmax_dividends.record_date IS 'Record date';
COMMENT ON COLUMN public.raw_yieldmax_dividends.frequency IS 'Dividend frequency (e.g., weekly, monthly)';
COMMENT ON COLUMN public.raw_yieldmax_dividends.source_url IS 'URL of the article where this dividend was announced';
COMMENT ON COLUMN public.raw_yieldmax_dividends.scraped_at IS 'When this record was scraped';

-- Enable Row Level Security (optional, can be adjusted based on needs)
ALTER TABLE public.raw_yieldmax_dividends ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed)
CREATE POLICY "Allow all operations on raw_yieldmax_dividends"
    ON public.raw_yieldmax_dividends
    FOR ALL
    USING (true)
    WITH CHECK (true);
