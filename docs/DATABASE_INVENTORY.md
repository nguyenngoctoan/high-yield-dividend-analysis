# High-Yield Dividend Analysis Project - Complete Database Inventory

## Executive Summary

This project contains a rich dividend analysis database with comprehensive financial data across **9 core raw tables**, **6+ mart tables** (materialized views), and supporting infrastructure tables. The system tracks stock/ETF data, dividend metrics, price history, holdings, and various financial indicators valuable for dividend investors.

**Total Key Data Points: 100+ distinct financial metrics and data points**

---

## RAW TABLES (Primary Data Storage)

### 1. raw_stocks
**Purpose**: Core stock and ETF master data  
**Estimated Size**: 24,842 rows, ~219 MB

**Columns**:
- `id` (SERIAL PRIMARY KEY)
- `symbol` (VARCHAR 20, UNIQUE)
- `company` (TEXT)
- `name` (TEXT)
- `exchange` (VARCHAR 50)
- `exchange_short_name` (VARCHAR 50)
- `sector` (VARCHAR 100)
- `industry` (VARCHAR 100)
- `type` (VARCHAR 50) - 'stock', 'etf', 'trust'
- `is_etf` (BOOLEAN)
- `currency` (VARCHAR 10)
- `country` (VARCHAR 50)
- `ipo_date` (DATE)
- `market_cap` (BIGINT)
- `price` (DECIMAL 10,2) - Current price
- `volume` (BIGINT) - Current volume
- `pe_ratio` (DECIMAL 10,2)
- `dividend_yield` (DECIMAL 10,6) - Annual yield percentage
- `dividend_amount` (DECIMAL 10,4) - Annual dividend per share
- `dividend_frequency` (VARCHAR 50) - 'monthly', 'quarterly', 'annual', etc.
- `payout_ratio` (DECIMAL 10,6) - Dividend payout ratio %
- `ex_dividend_date` (DATE) - Upcoming ex-dividend date
- `dividend_date` (DATE) - Upcoming dividend payment date
- `description` (TEXT) - Business description
- `expense_ratio` (DECIMAL 10,6) - ETF expense ratio %
- `related_stock` (TEXT) - For YieldMax ETFs, the underlying stock
- `investment_strategy` (TEXT) - Strategy type (covered call, synthetic covered call, etc.)
- `holdings` (JSONB) - ETF holdings array
- `holdings_updated_at` (TIMESTAMP WITH TIME ZONE)
- `last_updated` (TIMESTAMP)
- `created_at` (TIMESTAMP)

**Indexes**: symbol (unique), dividend_yield, market_cap, sector, exchange, type, related_stock

---

### 2. raw_stock_prices
**Purpose**: Daily OHLCV price data with calculated metrics  
**Estimated Size**: 20,254,716 rows, ~7.5 GB

**Columns**:
- `id` (BIGSERIAL PRIMARY KEY)
- `symbol` (VARCHAR 20, NOT NULL)
- `date` (DATE, NOT NULL)
- `open` (NUMERIC 12,4)
- `high` (NUMERIC 12,4)
- `low` (NUMERIC 12,4)
- `close` (NUMERIC 12,4)
- `adj_close` (NUMERIC 12,4) - Adjusted for splits/dividends
- `volume` (BIGINT)
- `change` (NUMERIC 12,4)
- `change_percent` (NUMERIC 8,4)
- `vwap` (NUMERIC 12,4) - Volume-weighted average price
- `label` (TEXT)
- `change_over_time` (NUMERIC 12,4)
- `currency` (VARCHAR 10)
- `source` (VARCHAR 50) - Data source (FMP, Yahoo, AlphaVantage)
- `aum` (BIGINT) - Assets Under Management for ETFs
- `iv` (NUMERIC 10,4) - Implied Volatility
- `created_at` (TIMESTAMP WITH TIME ZONE)

**Indexes**: symbol, date, symbol+date, iv, aum

**Key Metrics Available**:
- OHLCV prices with adjusted close
- Daily volatility via VWAP
- AUM tracking over time for ETFs
- Implied volatility for options analysis

---

### 3. raw_dividends (formerly dividend_history)
**Purpose**: Historical dividend payment records  
**Estimated Size**: 686,000+ rows, ~250 MB

**Columns**:
- `id` (BIGSERIAL PRIMARY KEY)
- `symbol` (VARCHAR 20, NOT NULL)
- `date` (DATE, NOT NULL) - Ex-dividend date
- `amount` (DECIMAL 10,4) - Dividend per share
- `adj_dividend` (DECIMAL 10,4) - Adjusted dividend
- `record_date` (DATE)
- `payment_date` (DATE)
- `declaration_date` (DATE)
- `label` (TEXT)
- `frequency` (TEXT) - Dividend frequency
- `currency` (VARCHAR 10)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Constraints**: UNIQUE (symbol, date) - One dividend per ex-date

**Indexes**: symbol, date, symbol+date DESC, payment_date

**Key Dividend Metrics Available**:
- Historical dividend per share amounts
- Dividend frequency tracking
- Complete dividend calendar dates
- Dividend growth calculations (5+ years history)

---

### 4. raw_stock_prices_hourly
**Purpose**: Intraday hourly price data during market hours  
**Estimated Size**: Varies based on retention policy

**Columns**:
- `id` (BIGSERIAL PRIMARY KEY)
- `symbol` (VARCHAR 20, NOT NULL)
- `timestamp` (TIMESTAMPTZ, NOT NULL) - Full timestamp
- `date` (DATE)
- `hour` (INTEGER) - Hour of day (0-23)
- `price` (NUMERIC 12,4)
- `open` (NUMERIC 12,4)
- `high` (NUMERIC 12,4)
- `low` (NUMERIC 12,4)
- `close` (NUMERIC 12,4)
- `volume` (BIGINT)
- `change` (NUMERIC 12,4)
- `change_percent` (NUMERIC 8,4)
- `vwap` (NUMERIC 12,4)
- `adj_close` (NUMERIC 12,4)
- `trade_count` (INTEGER)
- `currency` (VARCHAR 10)
- `source` (VARCHAR 50)
- `created_at` (TIMESTAMPTZ)

**Constraints**: UNIQUE (symbol, timestamp)

**Indexes**: symbol, date, timestamp, symbol+date, symbol+timestamp DESC

**Intraday Metrics Available**:
- Hourly OHLCV prices
- Hourly volume and trade counts
- Intraday volatility (VWAP)
- Hourly price momentum

---

### 5. raw_stock_splits
**Purpose**: Historical stock split events  
**Estimated Size**: Variable (rare events)

**Columns**:
- `id` (BIGSERIAL PRIMARY KEY)
- `symbol` (VARCHAR 20, NOT NULL)
- `split_date` (DATE, NOT NULL)
- `split_ratio` (NUMERIC 12,8) - Decimal (e.g., 2:1 = 2.0)
- `numerator` (INTEGER) - Split ratio numerator
- `denominator` (INTEGER) - Split ratio denominator
- `split_string` (VARCHAR 20) - Human-readable (e.g., "2-for-1")
- `description` (TEXT)
- `source` (VARCHAR 50)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)

**Constraints**: UNIQUE (symbol, split_date)

**Indexes**: symbol, date, symbol+date DESC

**Data Available**:
- Complete stock split history
- Split ratios in multiple formats
- Needed for accurate price adjustment

---

### 6. raw_holdings_history
**Purpose**: ETF holdings snapshots tracked over time  
**Estimated Size**: Variable (depends on ETF universe)

**Columns**:
- `id` (BIGSERIAL PRIMARY KEY)
- `symbol` (VARCHAR 20, NOT NULL) - ETF symbol
- `date` (DATE, NOT NULL)
- `holdings` (JSONB, NOT NULL) - Array of holdings objects
- `holdings_count` (INTEGER) - Number of holdings
- `data_source` (VARCHAR 50) - 'FMP', 'Yahoo', etc.
- `created_at` (TIMESTAMP WITH TIME ZONE)

**Constraints**: UNIQUE (symbol, date)

**Indexes**: symbol, date, symbol+date, holdings (GIN index)

**Holdings JSON Structure**:
```json
[
  {
    "asset": "AAPL",
    "name": "Apple Inc",
    "weightPercentage": 7.5,
    "sharesNumber": 1000000,
    "marketValue": 150000000,
    "cusip": "037833100",
    "updatedAt": "2025-11-13"
  }
]
```

**ETF Data Available**:
- Top holdings by weight
- Sector allocation
- Holdings composition changes
- Historical portfolio tracking

---

### 7. raw_yieldmax_dividends
**Purpose**: YieldMax ETF dividend announcements from press releases  
**Estimated Size**: Growing (1000s of records)

**Columns**:
- `id` (BIGSERIAL PRIMARY KEY)
- `symbol` (TEXT, NOT NULL)
- `name` (TEXT)
- `amount` (NUMERIC 10,4) - Total dividend amount
- `amount_per_share` (NUMERIC 10,4) - Per-share amount
- `ex_date` (DATE)
- `payment_date` (DATE)
- `record_date` (DATE)
- `frequency` (TEXT) - 'weekly', 'monthly', etc.
- `source_url` (TEXT) - Globe Newswire article link
- `scraped_at` (TIMESTAMP WITH TIME ZONE)
- `created_at` (TIMESTAMP WITH TIME ZONE)
- `updated_at` (TIMESTAMP WITH TIME ZONE)

**Constraints**: UNIQUE (symbol, ex_date)

**Indexes**: symbol, ex_date, payment_date, scraped_at

**YieldMax-Specific Data**:
- Weekly dividend distributions
- Option strategy income tracking
- Press release sources

---

### 8. raw_excluded_symbols
**Purpose**: Tracking of symbols excluded from analysis  
**Estimated Size**: Variable

**Columns**:
- `symbol` (VARCHAR 20, PRIMARY KEY)
- `reason` (TEXT) - Exclusion reason
- `excluded_at` (TIMESTAMP WITH TIME ZONE)
- `updated_at` (TIMESTAMP WITH TIME ZONE)
- `source` (VARCHAR 50) - Discovery source
- `validation_attempts` (INT)
- `auto_excluded` (BOOLEAN) - Auto vs manual exclusion

**Data Available**:
- Exclusion audit trail
- Validation failure tracking

---

### 9. raw_stocks_excluded
**Purpose**: Alternative exclusion tracking  
**Estimated Size**: Variable

**Columns**:
- `symbol` (VARCHAR 20, PRIMARY KEY)
- `reason` (TEXT)
- `excluded_at` (TIMESTAMP WITH TIME ZONE)
- `updated_at` (TIMESTAMP WITH TIME ZONE)
- `source` (VARCHAR 50)
- `validation_attempts` (INT)

---

## MART TABLES (Materialized Views for API)

These are pre-computed, optimized views for fast API queries.

### 1. mart_high_yield_stocks
**Purpose**: Pre-filtered high-yield dividend stocks (yield >= 4%)  
**Estimated Size**: ~1,000-5,000 rows

**Data**: Stocks filtered by dividend_yield >= 4.0%

---

### 2. mart_dividend_calendar
**Purpose**: Upcoming dividend events (next 90 days)  
**Estimated Size**: ~50,000 rows

**Data**: Future dividend dates with company info

---

### 3. mart_monthly_dividend_payers
**Purpose**: Stocks/ETFs paying monthly dividends  
**Estimated Size**: ~2,000-5,000 rows

**Data**: Monthly payers ranked by yield

---

### 4. mart_etf_holdings_summary
**Purpose**: Aggregated ETF holdings with top holdings  
**Estimated Size**: Variable

**Data**: ETF composition with top 10 holdings as JSON

---

### 5. mart_portfolio_current_holdings (custom)
**Purpose**: Current portfolio holdings

---

### 6. mart_portfolio_list_with_holdings (custom)
**Purpose**: Portfolio list with aggregated data

---

## SUPPORTING TABLES

### raw_data_source_tracking
**Purpose**: Tracks which data sources have which data types  
**Key Fields**: symbol, data_type, source, has_data, last_checked_at, last_successful_fetch_at

**Supported Data Types**: aum, dividends, volume, iv, prices, company_info  
**Supported Sources**: FMP, AlphaVantage, Yahoo

---

### API Infrastructure Tables
- `api_keys` - API key management
- `api_usage` - API usage tracking
- `rate_limit_state` - Rate limit state management
- `divv_api_keys` - Divv API integration

---

## COMPLETE DATA POINT INVENTORY BY CATEGORY

### Stock Information (raw_stocks)
1. Symbol (unique identifier)
2. Company name
3. Exchange (NYSE, NASDAQ, TSX, etc.)
4. Exchange short name
5. Sector classification
6. Industry classification
7. Stock type (stock, etf, trust)
8. Is ETF flag
9. Currency
10. Country
11. IPO date
12. Market capitalization
13. Current price
14. Current trading volume

### Dividend Metrics (raw_stocks + raw_dividends)
15. Dividend yield (%) - annual percentage
16. Dividend amount per share
17. Dividend frequency (monthly, quarterly, annual)
18. Payout ratio (%)
19. Ex-dividend date (upcoming)
20. Dividend payment date (upcoming)
21. Dividend declaration date (historical)
22. Dividend record date
23. Adjusted dividend (for splits)
24. Dividend growth rates (historical calculation)
25. Consecutive dividend increase years (Dividend Aristocrats metric)
26. Dividend history (5+ years of records)

### Price Data (raw_stock_prices)
27. Open price
28. High price
29. Low price
30. Close price
31. Adjusted close price
32. Trading volume
33. Price change (points)
34. Price change (percent)
35. VWAP (Volume-Weighted Average Price)
36. Price label/description
37. Change over time (%)
38. Daily price data with history (20M+ records)

### Volatility & Options (raw_stock_prices)
39. Implied Volatility (IV)
40. Intraday volatility (via VWAP)

### Assets Under Management (raw_stock_prices)
41. AUM - Assets Under Management for ETFs (time-series daily tracking)

### Hourly/Intraday Data (raw_stock_prices_hourly)
42. Hourly open
43. Hourly high
44. Hourly low
45. Hourly close
46. Hourly adjusted close
47. Hourly volume
48. Hourly trade count
49. Hourly VWAP
50. Hourly price change
51. Hourly price change percent
52. Hour of day (0-23 categorization)

### Corporate Actions (raw_stock_splits)
53. Stock split date
54. Stock split ratio (decimal format)
55. Stock split numerator
56. Stock split denominator
57. Stock split description

### ETF-Specific Data (raw_stocks)
58. Expense ratio (%)
59. Fund family
60. ETF description
61. Related underlying stock (for single-stock ETFs)
62. Investment strategy type (covered call, synthetic covered call, etc.)
63. Holdings count
64. Holdings composition (JSONB array)
65. Holdings updated timestamp

### ETF Holdings Details (raw_holdings_history)
66. Holding symbol
67. Holding name
68. Holding weight (%)
69. Holding shares number
70. Holding market value
71. Holding CUSIP
72. Holding sector
73. Holdings snapshot date
74. Top 10 holdings by weight

### YieldMax-Specific Data (raw_yieldmax_dividends)
75. YieldMax dividend amount
76. YieldMax dividend per share
77. YieldMax dividend frequency
78. YieldMax payment dates
79. YieldMax source URL (press release)
80. YieldMax announcement date

### Data Quality & Tracking
81. Last updated timestamp
82. Data source identifier
83. Currency indicator
84. Creation timestamp
85. Validation status
86. Exclusion reason
87. Validation attempt count

### Performance Metrics (Calculated)
88. 5-year dividend growth rate
89. 3-year dividend growth rate
90. 1-year dividend growth rate
91. 10-year dividend growth rate
92. Consecutive years of dividend payments
93. Dividend increase consistency
94. Dividend suspension count/history
95. Payout ratio trend
96. Yield trend over time

### Portfolio Analysis (Potential)
97. Portfolio position weight (%)
98. Portfolio dividend income contribution
99. Portfolio yield weighted by position
100. Portfolio performance vs benchmark

### Data Source Tracking
101. Preferred source for each data type
102. Last successful fetch timestamp
103. Fetch attempt count
104. Data availability by source
105. Source-specific notes/errors

---

## API-OPTIMIZED FUNCTIONS

The database includes several optimized functions for API queries:

### `get_high_yield_stocks()`
Returns: symbol, company, exchange, price, dividend_yield, market_cap, payout_ratio, sector

### `search_stocks()`
Returns: Fuzzy-matched stocks with relevance scoring

### `get_dividend_summary()`
Returns: Complete dividend info including current, history count, and next payment

### `refresh_api_materialized_views()`
Refreshes all mart tables for API freshness

---

## DATA INTEGRITY CONSTRAINTS

- **Symbol Uniqueness**: raw_stocks.symbol is UNIQUE
- **Price Uniqueness**: (symbol, date) is UNIQUE in raw_stock_prices
- **Dividend Uniqueness**: (symbol, ex_date) is UNIQUE in raw_dividends
- **Holdings Uniqueness**: (symbol, date) is UNIQUE in raw_holdings_history
- **Hourly Uniqueness**: (symbol, timestamp) is UNIQUE in raw_stock_prices_hourly
- **Stock Split Uniqueness**: (symbol, split_date) is UNIQUE in raw_stock_splits

---

## DATA VOLUME SUMMARY

| Table | Rows | Size | Records/Day |
|-------|------|------|-------------|
| raw_stocks | 24,842 | 219 MB | - |
| raw_stock_prices | 20,254,716 | 7.5 GB | ~10-20K |
| raw_dividends | 686,000+ | 250 MB | ~100-200 |
| raw_stock_prices_hourly | Variable | - | ~5-10K |
| raw_stock_splits | Variable | - | <10 |
| raw_holdings_history | Variable | - | 10-50 |
| raw_yieldmax_dividends | Variable | - | 5-20 |

**Total Local Database**: ~10 GB  
**Proposed Remote (Marts Only)**: ~50-100 MB

---

## KEY INSIGHTS FOR API EXPOSURE

### Most Valuable Data Points for Investors

1. **Dividend Yield & Metrics** (Top Priority)
   - Current yield, payout ratio, growth rates
   - Consistency metrics (consecutive years, increases/decreases)
   - Frequency patterns (monthly vs quarterly payers)

2. **Holdings Analysis** (ETF-specific)
   - Top holdings by weight
   - Sector allocation
   - Holdings composition changes

3. **Dividend Calendar** (Time-sensitive)
   - Upcoming ex-dates and payment dates
   - Announced amounts
   - YieldMax weekly distributions

4. **Price & Performance** (Fundamental)
   - Current price with trends
   - Volume analysis
   - Adjusted close for accurate calculations

5. **Historical Data** (Analysis)
   - 5+ years of dividend history
   - Price history for technical analysis
   - Corporate actions (splits)

6. **Volatility & Risk** (Advanced)
   - IV for options-based strategies
   - Intraday VWAP
   - Volume analysis

### Recommended API Endpoints Based on Available Data

- `/v1/stocks/{symbol}` - Complete stock profile with all metrics
- `/v1/stocks/{symbol}/dividends` - Dividend history + future calendar
- `/v1/stocks/{symbol}/price-history` - OHLCV with adjusted close
- `/v1/etfs/{symbol}/holdings` - ETF composition
- `/v1/screeners/high-yield` - Filtered by yield, sector, market cap
- `/v1/screeners/monthly-payers` - Monthly dividend stocks
- `/v1/dividends/calendar` - Upcoming events
- `/v1/stocks/search` - Fuzzy search by symbol/company
- `/v1/portfolio/analyze` - Portfolio dividend analysis
- `/v1/stocks/{symbol}/metrics` - Dividend growth, payout ratio, etc.

---

## CONCLUSION

This database is feature-rich with **100+ distinct data points** across **9 core tables** plus **6+ mart tables**. It provides comprehensive dividend analysis capabilities suitable for:

- Dividend screeners
- Portfolio analysis tools
- Historical research
- ETF analysis
- Dividend calendar tracking
- Income planning
- Volatility analysis
- Corporate action tracking

The data spans **20M+ price records**, **686K+ dividend records**, and **24,842+ stocks/ETFs**, making it a substantial investment database ready for sophisticated API exposure.

