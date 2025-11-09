-- Populate related_stock and investment_strategy for YieldMax and other option income ETFs
-- Date: 2025-10-12

-- =============================================================================
-- YieldMax Single-Stock ETFs (Option Income Strategy)
-- =============================================================================

-- AAPL (Apple)
UPDATE stocks SET related_stock = 'AAPL', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'APLY';

-- ABNB (Airbnb)
UPDATE stocks SET related_stock = 'ABNB', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'ABNY';

-- AMD (Advanced Micro Devices)
UPDATE stocks SET related_stock = 'AMD', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'AMDY';

-- AMZN (Amazon)
UPDATE stocks SET related_stock = 'AMZN', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'AMZY';

-- BABA (Alibaba)
UPDATE stocks SET related_stock = 'BABA', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'BABO';

-- BRK.B (Berkshire Hathaway)
UPDATE stocks SET related_stock = 'BRK.B', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'BRKC';

-- COIN (Coinbase)
UPDATE stocks SET related_stock = 'COIN', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'CONY';

-- CRCL (Circle)
UPDATE stocks SET related_stock = 'CRCL', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'CRCO';

-- CVNA (Carvana)
UPDATE stocks SET related_stock = 'CVNA', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'CVNY';

-- DIS (Disney)
UPDATE stocks SET related_stock = 'DIS', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'DISO';

-- DKNG (DraftKings)
UPDATE stocks SET related_stock = 'DKNG', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'DRAY';

-- META (Facebook/Meta)
UPDATE stocks SET related_stock = 'META', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'FBY';

-- GOOGL (Google/Alphabet)
UPDATE stocks SET related_stock = 'GOOGL', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'GOOY';

-- HIMS (Hims & Hers)
UPDATE stocks SET related_stock = 'HIMS', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'HIYY';

-- HOOD (Robinhood)
UPDATE stocks SET related_stock = 'HOOD', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'HOOY';

-- JPM (JPMorgan Chase)
UPDATE stocks SET related_stock = 'JPM', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'JPMO';

-- MRNA (Moderna)
UPDATE stocks SET related_stock = 'MRNA', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'MRNY';

-- MSFT (Microsoft)
UPDATE stocks SET related_stock = 'MSFT', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'MSFO';

-- MSTR (MicroStrategy)
UPDATE stocks SET related_stock = 'MSTR', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'MSTY';

-- NFLX (Netflix)
UPDATE stocks SET related_stock = 'NFLX', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'NFLY';

-- NVDA (NVIDIA)
UPDATE stocks SET related_stock = 'NVDA', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'NVDY';

-- ARKK (ARK Innovation ETF)
UPDATE stocks SET related_stock = 'ARKK', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'OARK';

-- PLTR (Palantir)
UPDATE stocks SET related_stock = 'PLTR', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'PLTY';

-- PYPL (PayPal)
UPDATE stocks SET related_stock = 'PYPL', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'PYPY';

-- SMCI (Super Micro Computer)
UPDATE stocks SET related_stock = 'SMCI', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'SMCY';

-- SNOW (Snowflake)
UPDATE stocks SET related_stock = 'SNOW', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'SNOY';

-- SQ (Block/Square)
UPDATE stocks SET related_stock = 'SQ', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'SQY';

-- TSLA (Tesla)
UPDATE stocks SET related_stock = 'TSLA', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'TSLY';

-- TSM (Taiwan Semiconductor)
UPDATE stocks SET related_stock = 'TSM', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'TSMY';

-- XOM (Exxon Mobil)
UPDATE stocks SET related_stock = 'XOM', investment_strategy = 'Synthetic Covered Call' WHERE symbol = 'XOMO';

-- =============================================================================
-- YieldMax Short/Inverse Strategy ETFs
-- =============================================================================

-- Short NVDA
UPDATE stocks SET related_stock = 'NVDA', investment_strategy = 'Short Option Income' WHERE symbol = 'DIPS';

-- Short COIN
UPDATE stocks SET related_stock = 'COIN', investment_strategy = 'Short Option Income' WHERE symbol = 'FIAT';

-- Short MSTR
UPDATE stocks SET related_stock = 'MSTR', investment_strategy = 'Short Option Income' WHERE symbol = 'WNTR';

-- Short Treasury (T)
UPDATE stocks SET related_stock = 'T-Bills', investment_strategy = 'Short Treasury' WHERE symbol = 'CRSH';

-- Short Nasdaq 100
UPDATE stocks SET related_stock = 'QQQ', investment_strategy = 'Short Option Income' WHERE symbol = 'YQQQ';

-- =============================================================================
-- YieldMax Index & 0DTE Strategy ETFs
-- =============================================================================

-- Nasdaq 100 0DTE
UPDATE stocks SET related_stock = 'QQQ', investment_strategy = '0DTE Covered Call' WHERE symbol = 'QDTY';

-- Russell 2000 0DTE
UPDATE stocks SET related_stock = 'IWM', investment_strategy = '0DTE Covered Call' WHERE symbol = 'RDTY';

-- S&P 500 0DTE
UPDATE stocks SET related_stock = 'SPY', investment_strategy = '0DTE Covered Call' WHERE symbol = 'SDTY';

-- =============================================================================
-- YieldMax Portfolio/Multi-Asset ETFs
-- =============================================================================

-- AI & Tech Portfolio
UPDATE stocks SET related_stock = 'Multiple (AI/Tech)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'GPTY';

-- AI Option Income (General)
UPDATE stocks SET related_stock = 'Multiple (AI)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'AIYY';

-- Semiconductor Portfolio
UPDATE stocks SET related_stock = 'Multiple (Semiconductors)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'CHPY';

-- Crypto Industry & Tech Portfolio
UPDATE stocks SET related_stock = 'Multiple (Crypto/Tech)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'LFGY';

-- Dorsey Wright Featured 5
UPDATE stocks SET related_stock = 'Multiple (DW Featured 5)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'FEAT';

-- Dorsey Wright Hybrid 5
UPDATE stocks SET related_stock = 'Multiple (DW Hybrid 5)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'FIVY';

-- Magnificent 7 Fund
UPDATE stocks SET related_stock = 'Multiple (Mag 7)', investment_strategy = 'Fund of Funds Covered Call' WHERE symbol = 'YMAG';

-- Universe Fund (Fund of Funds)
UPDATE stocks SET related_stock = 'Multiple (Universe)', investment_strategy = 'Fund of Funds Covered Call' WHERE symbol = 'YMAX';

-- Target 12 Big 50
UPDATE stocks SET related_stock = 'Multiple (Big 50)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'BIGY';

-- Real Estate Option Income
UPDATE stocks SET related_stock = 'Multiple (Real Estate)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'RNTY';

-- Ultra Option Income
UPDATE stocks SET related_stock = 'Multiple (Ultra)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'ULTY';

-- Gold Miners
UPDATE stocks SET related_stock = 'GDX', investment_strategy = 'Sector Covered Call' WHERE symbol = 'GDXY';

-- =============================================================================
-- YieldMax Crypto/Bitcoin ETFs
-- =============================================================================

-- Bitcoin Option Income
UPDATE stocks SET related_stock = 'BTC', investment_strategy = 'Bitcoin Covered Call' WHERE symbol = 'YBIT';

-- XYZ Option Income (if crypto-related)
UPDATE stocks SET related_stock = 'Multiple (Crypto)', investment_strategy = 'Portfolio Covered Call' WHERE symbol = 'XYZY';

-- =============================================================================
-- Show Results
-- =============================================================================
SELECT
    symbol,
    name,
    related_stock,
    investment_strategy,
    dividend_yield
FROM stocks
WHERE investment_strategy IS NOT NULL
ORDER BY
    CASE
        WHEN investment_strategy LIKE '%0DTE%' THEN 1
        WHEN investment_strategy LIKE '%Short%' THEN 2
        WHEN investment_strategy LIKE '%Portfolio%' THEN 3
        WHEN investment_strategy LIKE '%Fund of Funds%' THEN 4
        ELSE 5
    END,
    symbol;
