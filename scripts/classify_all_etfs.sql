-- Comprehensive ETF Classification for ALL ETFs
-- Classifies 8,900+ ETFs into strategy types and identifies underlying assets
-- Date: 2025-10-12

BEGIN;

-- =============================================================================
-- EQUITY INDEX ETFs
-- =============================================================================

-- S&P 500
UPDATE stocks SET
    investment_strategy = 'Broad Market Index',
    related_stock = 'SPY'
WHERE name ILIKE '%s&p 500%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Nasdaq 100
UPDATE stocks SET
    investment_strategy = 'Tech-Heavy Index',
    related_stock = 'QQQ'
WHERE (name ILIKE '%nasdaq%100%' OR name ILIKE '%nasdaq-100%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Russell 2000
UPDATE stocks SET
    investment_strategy = 'Small Cap Index',
    related_stock = 'IWM'
WHERE name ILIKE '%russell%2000%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Dow Jones
UPDATE stocks SET
    investment_strategy = 'Blue Chip Index',
    related_stock = 'DIA'
WHERE (name ILIKE '%dow%jones%' OR name ILIKE '%dow 30%' OR name ILIKE '%djia%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Total Market
UPDATE stocks SET
    investment_strategy = 'Total Market',
    related_stock = 'VTI'
WHERE (name ILIKE '%total%market%' OR name ILIKE '%total%stock%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- SECTOR & INDUSTRY ETFs
-- =============================================================================

-- Technology
UPDATE stocks SET
    investment_strategy = 'Sector - Technology',
    related_stock = 'XLK'
WHERE (name ILIKE '%tech%' OR name ILIKE '%information technology%' OR name ILIKE '%software%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%bio%';

-- Healthcare
UPDATE stocks SET
    investment_strategy = 'Sector - Healthcare',
    related_stock = 'XLV'
WHERE (name ILIKE '%health%' OR name ILIKE '%medical%' OR name ILIKE '%pharma%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Financials / Banks
UPDATE stocks SET
    investment_strategy = 'Sector - Financials',
    related_stock = 'XLF'
WHERE (name ILIKE '%financial%' OR name ILIKE '%bank%' OR name ILIKE '%insurance%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Energy
UPDATE stocks SET
    investment_strategy = 'Sector - Energy',
    related_stock = 'XLE'
WHERE (name ILIKE '%energy%' OR name ILIKE '%oil%' OR name ILIKE '%gas%' OR name ILIKE '%petroleum%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%natural gas%storage%';

-- Consumer
UPDATE stocks SET
    investment_strategy = CASE
        WHEN name ILIKE '%consumer discretionary%' OR name ILIKE '%consumer cyclical%' THEN 'Sector - Consumer Discretionary'
        WHEN name ILIKE '%consumer staples%' OR name ILIKE '%consumer defensive%' THEN 'Sector - Consumer Staples'
        ELSE 'Sector - Consumer'
    END,
    related_stock = CASE
        WHEN name ILIKE '%staples%' THEN 'XLP'
        ELSE 'XLY'
    END
WHERE name ILIKE '%consumer%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Real Estate / REITs
UPDATE stocks SET
    investment_strategy = 'Sector - Real Estate',
    related_stock = 'XLRE'
WHERE (name ILIKE '%real estate%' OR name ILIKE '%reit%' OR name ILIKE '%property%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Utilities
UPDATE stocks SET
    investment_strategy = 'Sector - Utilities',
    related_stock = 'XLU'
WHERE name ILIKE '%utilit%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Industrials
UPDATE stocks SET
    investment_strategy = 'Sector - Industrials',
    related_stock = 'XLI'
WHERE (name ILIKE '%industrial%' OR name ILIKE '%manufacturing%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Materials
UPDATE stocks SET
    investment_strategy = 'Sector - Materials',
    related_stock = 'XLB'
WHERE (name ILIKE '%material%' OR name ILIKE '%mining%' OR name ILIKE '%metal%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%rare earth%';

-- Communication Services
UPDATE stocks SET
    investment_strategy = 'Sector - Communication Services',
    related_stock = 'XLC'
WHERE (name ILIKE '%communication%' OR name ILIKE '%media%' OR name ILIKE '%telecom%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Semiconductors
UPDATE stocks SET
    investment_strategy = 'Industry - Semiconductors',
    related_stock = 'SMH'
WHERE (name ILIKE '%semiconductor%' OR name ILIKE '%chip%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Biotech
UPDATE stocks SET
    investment_strategy = 'Industry - Biotechnology',
    related_stock = 'IBB'
WHERE (name ILIKE '%biotech%' OR name ILIKE '%genomic%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Aerospace & Defense
UPDATE stocks SET
    investment_strategy = 'Industry - Aerospace & Defense',
    related_stock = 'ITA'
WHERE (name ILIKE '%aerospace%' OR name ILIKE '%defense%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Gold/Silver/Precious Metals
UPDATE stocks SET
    investment_strategy = 'Commodity - Precious Metals',
    related_stock = CASE
        WHEN name ILIKE '%gold%' THEN 'GLD'
        WHEN name ILIKE '%silver%' THEN 'SLV'
        ELSE 'Multiple (Precious Metals)'
    END
WHERE (name ILIKE '%gold%' OR name ILIKE '%silver%' OR name ILIKE '%precious metal%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- INTERNATIONAL / GEOGRAPHIC ETFs
-- =============================================================================

-- International Developed
UPDATE stocks SET
    investment_strategy = 'International Developed',
    related_stock = 'EFA'
WHERE (name ILIKE '%eafe%' OR name ILIKE '%developed%market%' OR name ILIKE '%international%developed%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Emerging Markets
UPDATE stocks SET
    investment_strategy = 'Emerging Markets',
    related_stock = 'EEM'
WHERE name ILIKE '%emerging%market%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- China
UPDATE stocks SET
    investment_strategy = 'Geographic - China',
    related_stock = 'FXI'
WHERE (name ILIKE '%china%' OR name ILIKE '%chinese%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Europe
UPDATE stocks SET
    investment_strategy = 'Geographic - Europe',
    related_stock = 'VGK'
WHERE (name ILIKE '%europe%' OR name ILIKE '%euro stoxx%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%emerging%';

-- Japan
UPDATE stocks SET
    investment_strategy = 'Geographic - Japan',
    related_stock = 'EWJ'
WHERE (name ILIKE '%japan%' OR name ILIKE '%nikkei%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Other Asia
UPDATE stocks SET
    investment_strategy = 'Geographic - Asia Pacific',
    related_stock = 'Multiple (Asia)'
WHERE (name ILIKE '%asia%' OR name ILIKE '%pacific%' OR name ILIKE '%korea%' OR name ILIKE '%india%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Canada
UPDATE stocks SET
    investment_strategy = 'Geographic - Canada',
    related_stock = 'EWC'
WHERE (symbol LIKE '%.TO' OR name ILIKE '%canada%' OR name ILIKE '%canadian%' OR name ILIKE '%tsx%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%bank%'
AND name NOT ILIKE '%covered call%';

-- Latin America
UPDATE stocks SET
    investment_strategy = 'Geographic - Latin America',
    related_stock = 'Multiple (LatAm)'
WHERE (name ILIKE '%latin%america%' OR name ILIKE '%brazil%' OR name ILIKE '%mexico%' OR name ILIKE '%colombia%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Middle East
UPDATE stocks SET
    investment_strategy = 'Geographic - Middle East',
    related_stock = 'Multiple (Middle East)'
WHERE (name ILIKE '%middle east%' OR name ILIKE '%israel%' OR name ILIKE '%saudi%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- FIXED INCOME / BOND ETFs
-- =============================================================================

-- Treasury Bonds
UPDATE stocks SET
    investment_strategy = CASE
        WHEN name ILIKE '%short%term%' OR name ILIKE '%1-3%' THEN 'Bonds - Short-Term Treasury'
        WHEN name ILIKE '%intermediate%' OR name ILIKE '%7-10%' THEN 'Bonds - Intermediate Treasury'
        WHEN name ILIKE '%long%' OR name ILIKE '%20+%' OR name ILIKE '%20 year%' THEN 'Bonds - Long-Term Treasury'
        ELSE 'Bonds - Treasury'
    END,
    related_stock = CASE
        WHEN name ILIKE '%short%' THEN 'SHY'
        WHEN name ILIKE '%long%' THEN 'TLT'
        ELSE 'IEF'
    END
WHERE name ILIKE '%treasury%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Corporate Bonds
UPDATE stocks SET
    investment_strategy = 'Bonds - Corporate',
    related_stock = 'LQD'
WHERE (name ILIKE '%corporate%bond%' OR name ILIKE '%investment grade%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- High Yield Bonds
UPDATE stocks SET
    investment_strategy = 'Bonds - High Yield',
    related_stock = 'HYG'
WHERE (name ILIKE '%high%yield%' OR name ILIKE '%junk%bond%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Municipal Bonds
UPDATE stocks SET
    investment_strategy = 'Bonds - Municipal',
    related_stock = 'MUB'
WHERE (name ILIKE '%municipal%' OR name ILIKE '%muni%bond%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Aggregate Bonds
UPDATE stocks SET
    investment_strategy = 'Bonds - Aggregate',
    related_stock = 'AGG'
WHERE (name ILIKE '%aggregate%bond%' OR name ILIKE '%total bond%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Inflation-Protected
UPDATE stocks SET
    investment_strategy = 'Bonds - Inflation Protected',
    related_stock = 'TIP'
WHERE (name ILIKE '%tips%' OR name ILIKE '%inflation%linked%' OR name ILIKE '%inflation%protected%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- STYLE / FACTOR ETFs
-- =============================================================================

-- Growth
UPDATE stocks SET
    investment_strategy = 'Factor - Growth',
    related_stock = 'IWF'
WHERE name ILIKE '%growth%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%dividend%';

-- Value
UPDATE stocks SET
    investment_strategy = 'Factor - Value',
    related_stock = 'IWD'
WHERE name ILIKE '%value%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Dividend/Income (non-covered call)
UPDATE stocks SET
    investment_strategy = 'Factor - Dividend',
    related_stock = 'VYM'
WHERE (name ILIKE '%dividend%' OR name ILIKE '%income%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%covered call%'
AND name NOT ILIKE '%option%';

-- Momentum
UPDATE stocks SET
    investment_strategy = 'Factor - Momentum',
    related_stock = 'MTUM'
WHERE name ILIKE '%momentum%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Quality
UPDATE stocks SET
    investment_strategy = 'Factor - Quality',
    related_stock = 'QUAL'
WHERE name ILIKE '%quality%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Low Volatility
UPDATE stocks SET
    investment_strategy = 'Factor - Low Volatility',
    related_stock = 'USMV'
WHERE (name ILIKE '%low%volatility%' OR name ILIKE '%minimum%volatility%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Multi-Factor
UPDATE stocks SET
    investment_strategy = 'Factor - Multi-Factor',
    related_stock = 'Multiple (Factors)'
WHERE name ILIKE '%multi%factor%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- ESG / THEMATIC ETFs
-- =============================================================================

-- ESG General
UPDATE stocks SET
    investment_strategy = 'Thematic - ESG',
    related_stock = 'Multiple (ESG)'
WHERE (name ILIKE '%esg%' OR name ILIKE '%sustainable%' OR name ILIKE '%responsible%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Clean Energy / Climate
UPDATE stocks SET
    investment_strategy = 'Thematic - Clean Energy',
    related_stock = 'ICLN'
WHERE (name ILIKE '%clean%energy%' OR name ILIKE '%renewable%' OR name ILIKE '%solar%' OR name ILIKE '%wind%' OR name ILIKE '%climate%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- AI / Artificial Intelligence
UPDATE stocks SET
    investment_strategy = 'Thematic - AI',
    related_stock = 'Multiple (AI)'
WHERE (name ILIKE '%artificial%intelligence%' OR name ILIKE '% ai %' OR name ILIKE '%machine learning%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Robotics & Automation
UPDATE stocks SET
    investment_strategy = 'Thematic - Robotics',
    related_stock = 'ROBO'
WHERE (name ILIKE '%robot%' OR name ILIKE '%automation%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Cloud Computing
UPDATE stocks SET
    investment_strategy = 'Thematic - Cloud Computing',
    related_stock = 'SKYY'
WHERE (name ILIKE '%cloud%' OR name ILIKE '%saas%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Cybersecurity
UPDATE stocks SET
    investment_strategy = 'Thematic - Cybersecurity',
    related_stock = 'HACK'
WHERE (name ILIKE '%cyber%' OR name ILIKE '%security%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Electric Vehicles
UPDATE stocks SET
    investment_strategy = 'Thematic - Electric Vehicles',
    related_stock = 'DRIV'
WHERE (name ILIKE '%electric%vehicle%' OR name ILIKE '%ev%' OR name ILIKE '%autonomous%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Metaverse / Gaming
UPDATE stocks SET
    investment_strategy = 'Thematic - Metaverse/Gaming',
    related_stock = 'Multiple (Gaming)'
WHERE (name ILIKE '%metaverse%' OR name ILIKE '%gaming%' OR name ILIKE '%esports%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- CRYPTO / BLOCKCHAIN ETFs
-- =============================================================================

-- Bitcoin
UPDATE stocks SET
    investment_strategy = 'Crypto - Bitcoin',
    related_stock = 'BTC'
WHERE (name ILIKE '%bitcoin%' OR name ILIKE '%btc%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Ethereum
UPDATE stocks SET
    investment_strategy = 'Crypto - Ethereum',
    related_stock = 'ETH'
WHERE (name ILIKE '%ethereum%' OR name ILIKE '%ether%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Blockchain
UPDATE stocks SET
    investment_strategy = 'Crypto - Blockchain',
    related_stock = 'Multiple (Blockchain)'
WHERE (name ILIKE '%blockchain%' OR name ILIKE '%crypto%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- LEVERAGED / INVERSE ETFs
-- =============================================================================

-- Leveraged (2x, 3x)
UPDATE stocks SET
    investment_strategy = CASE
        WHEN name ILIKE '%3x%' OR name ILIKE '%ultra pro%' OR name ILIKE '%triple%' THEN 'Leveraged - 3x'
        WHEN name ILIKE '%2x%' OR name ILIKE '%ultra%' OR name ILIKE '%double%' THEN 'Leveraged - 2x'
        ELSE 'Leveraged'
    END,
    related_stock = CASE
        WHEN name ILIKE '%s&p%' THEN 'SPY'
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%russell%' THEN 'IWM'
        ELSE 'Multiple'
    END
WHERE (name ILIKE '%leveraged%' OR name ILIKE '%ultra%' OR name ILIKE '%2x%' OR name ILIKE '%3x%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- Inverse / Short
UPDATE stocks SET
    investment_strategy = 'Inverse/Short',
    related_stock = CASE
        WHEN name ILIKE '%s&p%' THEN 'SPY'
        WHEN name ILIKE '%nasdaq%' THEN 'QQQ'
        WHEN name ILIKE '%russell%' THEN 'IWM'
        ELSE 'Multiple'
    END
WHERE (name ILIKE '%inverse%' OR name ILIKE '%short%' OR name ILIKE '%bear%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL
AND name NOT ILIKE '%short%term%'
AND name NOT ILIKE '%short%duration%';

-- =============================================================================
-- EQUAL WEIGHT / ALTERNATIVE WEIGHTING
-- =============================================================================

-- Equal Weight
UPDATE stocks SET
    investment_strategy = 'Equal Weight',
    related_stock = CASE
        WHEN name ILIKE '%s&p 500%' THEN 'RSP'
        ELSE 'Multiple'
    END
WHERE name ILIKE '%equal%weight%'
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- BUFFER / DEFINED OUTCOME ETFs
-- =============================================================================

-- Buffer/Defined Outcome
UPDATE stocks SET
    investment_strategy = 'Buffered/Defined Outcome',
    related_stock = 'SPY'
WHERE (name ILIKE '%buffer%' OR name ILIKE '%defined outcome%' OR name ILIKE '%target income%')
AND name ILIKE '%etf%'
AND investment_strategy IS NULL;

-- =============================================================================
-- CATCH-ALL for remaining ETFs
-- =============================================================================

-- Generic ETF classification
UPDATE stocks SET
    investment_strategy = 'Other ETF',
    related_stock = 'Multiple'
WHERE name ILIKE '%etf%'
AND investment_strategy IS NULL;

COMMIT;

-- =============================================================================
-- SUMMARY REPORT
-- =============================================================================

SELECT
    investment_strategy,
    COUNT(*) as etf_count,
    ROUND(AVG(dividend_yield::numeric), 4) as avg_yield
FROM stocks
WHERE investment_strategy IS NOT NULL
GROUP BY investment_strategy
ORDER BY etf_count DESC
LIMIT 50;

SELECT
    'Total Classified ETFs' as metric,
    COUNT(*) as count
FROM stocks
WHERE investment_strategy IS NOT NULL
AND name ILIKE '%etf%';
