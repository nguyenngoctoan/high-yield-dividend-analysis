-- Comprehensive ETF Metadata Population Script
-- Automatically classifies all income/covered call ETFs based on name patterns
-- Date: 2025-10-12

-- =============================================================================
-- PART 1: Global X Covered Call ETFs
-- =============================================================================

-- S&P 500 Covered Call
UPDATE stocks SET
    related_stock = 'SPY',
    investment_strategy = 'Index Covered Call'
WHERE symbol IN ('XYLD', 'XYLG') AND investment_strategy IS NULL;

-- Nasdaq 100 Covered Call
UPDATE stocks SET
    related_stock = 'QQQ',
    investment_strategy = 'Index Covered Call'
WHERE symbol IN ('QYLD', 'QYLG', 'QRMI') AND investment_strategy IS NULL;

-- Russell 2000 Covered Call
UPDATE stocks SET
    related_stock = 'IWM',
    investment_strategy = 'Index Covered Call'
WHERE symbol IN ('RYLD') AND investment_strategy IS NULL;

-- Dow Jones Covered Call
UPDATE stocks SET
    related_stock = 'DIA',
    investment_strategy = 'Index Covered Call'
WHERE symbol IN ('DJIA') AND investment_strategy IS NULL;

-- MSCI EAFE Covered Call
UPDATE stocks SET
    related_stock = 'EFA',
    investment_strategy = 'International Covered Call'
WHERE symbol IN ('XYLD') AND investment_strategy IS NULL;

-- =============================================================================
-- PART 2: JPMorgan Premium Income/Equity ETFs
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Equity Premium Income',
    related_stock = CASE
        WHEN name ILIKE '%equity premium%' THEN 'Multiple (Equity)'
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%s&p 500%' THEN 'SPY'
        ELSE 'Multiple'
    END
WHERE (symbol LIKE 'J%' AND name ILIKE '%jpmorgan%premium%')
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 3: Neos/Innovator Premium Income ETFs
-- =============================================================================

-- Neos Enhanced Income ETFs
UPDATE stocks SET
    investment_strategy = 'Options-Based Income',
    related_stock = CASE
        WHEN name ILIKE '%s&p 500%' THEN 'SPY'
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%russell%' THEN 'IWM'
        WHEN name ILIKE '%bitcoin%' THEN 'BTC'
        WHEN name ILIKE '%aggregate%' THEN 'AGG'
        ELSE 'Multiple'
    END
WHERE (name ILIKE '%neos%' OR symbol LIKE 'SPY%' OR symbol LIKE 'QQQ%')
AND name ILIKE '%income%'
AND investment_strategy IS NULL;

-- Innovator Premium Income Barrier ETFs
UPDATE stocks SET
    investment_strategy = 'Buffered Premium Income',
    related_stock = 'SPY'
WHERE name ILIKE '%innovator%premium income%barrier%'
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 4: Defiance Leveraged + Income ETFs
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Leveraged + Income',
    related_stock = CASE
        WHEN symbol = 'AMDU' THEN 'AMD'
        WHEN symbol = 'NVDU' THEN 'NVDA'
        WHEN symbol = 'TSLU' THEN 'TSLA'
        ELSE UPPER(SUBSTRING(symbol FROM 1 FOR LENGTH(symbol)-2))
    END
WHERE name ILIKE '%defiance%leveraged%income%'
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 5: Covered Call ETFs (Generic Pattern Matching)
-- =============================================================================

-- Covered Call on specific indices/stocks
UPDATE stocks SET
    investment_strategy = 'Covered Call',
    related_stock = CASE
        WHEN name ILIKE '%s&p 500%' OR name ILIKE '%sp 500%' OR name ILIKE '%s&p500%' THEN 'SPY'
        WHEN name ILIKE '%nasdaq%100%' OR name ILIKE '%nasdaq-100%' THEN 'QQQ'
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%russell%2000%' OR name ILIKE '%russell 2000%' THEN 'IWM'
        WHEN name ILIKE '%dow%jones%' OR name ILIKE '%dow 30%' THEN 'DIA'
        WHEN name ILIKE '%msci%eafe%' THEN 'EFA'
        WHEN name ILIKE '%emerging%market%' THEN 'EEM'
        WHEN name ILIKE '%dividend%' THEN 'Multiple (Dividend)'
        WHEN name ILIKE '%bank%' THEN 'Multiple (Banks)'
        WHEN name ILIKE '%energy%' THEN 'Multiple (Energy)'
        WHEN name ILIKE '%real estate%' OR name ILIKE '%reit%' THEN 'Multiple (Real Estate)'
        WHEN name ILIKE '%tech%' OR name ILIKE '%technology%' THEN 'Multiple (Tech)'
        WHEN name ILIKE '%equity%' THEN 'Multiple (Equity)'
        ELSE 'Multiple'
    END
WHERE name ILIKE '%covered call%'
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 6: Buy-Write Strategy ETFs
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Buy-Write Strategy',
    related_stock = CASE
        WHEN name ILIKE '%s&p 500%' OR name ILIKE '%bxm%' THEN 'SPY'
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%russell%' THEN 'IWM'
        ELSE 'Multiple'
    END
WHERE (name ILIKE '%buy%write%' OR name ILIKE '%buywrite%' OR name ILIKE '%bxm%')
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 7: Option Income Strategy ETFs (General)
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Option Income Strategy',
    related_stock = CASE
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%s&p%' THEN 'SPY'
        WHEN name ILIKE '%equity%' THEN 'Multiple (Equity)'
        WHEN name ILIKE '%multi-asset%' THEN 'Multiple (Multi-Asset)'
        ELSE 'Multiple'
    END
WHERE name ILIKE '%option income%'
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 8: Premium Income ETFs (General)
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Premium Income',
    related_stock = CASE
        WHEN name ILIKE '%equity%' THEN 'Multiple (Equity)'
        WHEN name ILIKE '%dividend%' THEN 'Multiple (Dividend)'
        WHEN name ILIKE '%high yield%' THEN 'Multiple (High Yield)'
        WHEN name ILIKE '%multi-asset%' THEN 'Multiple (Multi-Asset)'
        ELSE 'Multiple'
    END
WHERE name ILIKE '%premium%income%'
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 9: Calamos Strategy ETFs
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Structured Income',
    related_stock = CASE
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%s&p%' THEN 'SPY'
        WHEN name ILIKE '%equity%' THEN 'Multiple (Equity)'
        ELSE 'Multiple'
    END
WHERE name ILIKE '%calamos%'
AND (name ILIKE '%income%' OR name ILIKE '%protective%' OR name ILIKE '%structured%')
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 10: Grayscale Crypto Premium Income
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Crypto Premium Income',
    related_stock = CASE
        WHEN name ILIKE '%bitcoin%' THEN 'BTC'
        WHEN name ILIKE '%ethereum%' THEN 'ETH'
        ELSE 'Multiple (Crypto)'
    END
WHERE name ILIKE '%grayscale%'
AND name ILIKE '%premium%income%'
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 11: REX/Astria Option Income ETFs
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'AI-Driven Option Income',
    related_stock = CASE
        WHEN name ILIKE '%s&p%' THEN 'SPY'
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%equity%' THEN 'Multiple (Equity)'
        ELSE 'Multiple'
    END
WHERE (name ILIKE '%rex%' OR name ILIKE '%astria%')
AND (name ILIKE '%premium%income%' OR name ILIKE '%option income%')
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 12: Enhanced/Tactical Income ETFs
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Enhanced Income',
    related_stock = CASE
        WHEN name ILIKE '%dividend%' THEN 'Multiple (Dividend)'
        WHEN name ILIKE '%equity%' THEN 'Multiple (Equity)'
        WHEN name ILIKE '%multi-asset%' THEN 'Multiple (Multi-Asset)'
        WHEN name ILIKE '%volatility%' THEN 'Multiple (Vol-Managed)'
        ELSE 'Multiple'
    END
WHERE (name ILIKE '%enhanced%income%' OR name ILIKE '%tactical%income%')
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 13: Canadian Covered Call ETFs (.TO suffix)
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Canadian Covered Call',
    related_stock = CASE
        WHEN name ILIKE '%bank%' THEN 'Multiple (Canadian Banks)'
        WHEN name ILIKE '%tsx%' THEN 'XIU'
        WHEN name ILIKE '%dividend%' THEN 'Multiple (Canadian Dividend)'
        ELSE 'Multiple (Canadian Equity)'
    END
WHERE symbol LIKE '%.TO'
AND name ILIKE '%covered call%'
AND investment_strategy IS NULL;

-- =============================================================================
-- PART 14: Asian/International Covered Call ETFs
-- =============================================================================

UPDATE stocks SET
    investment_strategy = 'Index Covered Call',
    related_stock = CASE
        WHEN name ILIKE '%kospi%' OR name ILIKE '%korea%200%' THEN 'KOSPI 200'
        WHEN name ILIKE '%s&p%dividend%' THEN 'Multiple (S&P Dividend)'
        WHEN name ILIKE '%morningstar%' THEN 'Multiple (Multi-Asset)'
        ELSE 'Multiple (International)'
    END
WHERE symbol LIKE '%.KS'
AND name ILIKE '%covered call%'
AND investment_strategy IS NULL;

-- =============================================================================
-- Show Results Summary
-- =============================================================================

SELECT
    investment_strategy,
    COUNT(*) as count,
    ROUND(AVG(dividend_yield::numeric), 4) as avg_yield
FROM stocks
WHERE investment_strategy IS NOT NULL
GROUP BY investment_strategy
ORDER BY count DESC;

-- =============================================================================
-- Show newly tagged ETFs
-- =============================================================================

SELECT
    symbol,
    name,
    related_stock,
    investment_strategy
FROM stocks
WHERE investment_strategy IS NOT NULL
ORDER BY investment_strategy, symbol
LIMIT 100;
