# ETF Metadata Query Reference

This document provides useful SQL queries for analyzing the ETF metadata (related_stock and investment_strategy) fields.

## Summary Statistics

### Total Classified ETFs
```sql
SELECT
    COUNT(*) as total_classified_etfs,
    COUNT(DISTINCT investment_strategy) as strategy_types,
    COUNT(DISTINCT related_stock) as unique_related_stocks
FROM stocks
WHERE investment_strategy IS NOT NULL;
```
**Result**: 279 ETFs classified into 19 strategy types

## Strategy Analysis

### ETFs by Strategy Type
```sql
SELECT
    investment_strategy,
    COUNT(*) as etf_count,
    ROUND(AVG(dividend_yield::numeric), 4) as avg_yield,
    ROUND(MIN(dividend_yield::numeric), 4) as min_yield,
    ROUND(MAX(dividend_yield::numeric), 4) as max_yield
FROM stocks
WHERE investment_strategy IS NOT NULL
GROUP BY investment_strategy
ORDER BY avg_yield DESC;
```

### Top Strategy Types by Yield
| Strategy | ETF Count | Avg Yield |
|----------|-----------|-----------|
| Short Treasury | 1 | 142.12% |
| Short Option Income | 4 | 118.62% |
| Bitcoin Covered Call | 1 | 74.81% |
| Synthetic Covered Call | 30 | 69.01% |
| Portfolio Covered Call | 10 | 59.28% |

## Finding ETFs by Underlying Stock

### Tesla-Based ETFs
```sql
SELECT symbol, name, dividend_yield, investment_strategy
FROM stocks
WHERE related_stock = 'TSLA'
ORDER BY dividend_yield DESC;
```

### All NVIDIA-Based ETFs
```sql
SELECT symbol, name, dividend_yield, investment_strategy
FROM stocks
WHERE related_stock = 'NVDA'
ORDER BY dividend_yield DESC;
```

### S&P 500 Based ETFs
```sql
SELECT symbol, name, dividend_yield, investment_strategy
FROM stocks
WHERE related_stock = 'SPY'
ORDER BY dividend_yield DESC;
```

### Nasdaq 100 Based ETFs
```sql
SELECT symbol, name, dividend_yield, investment_strategy
FROM stocks
WHERE related_stock = 'QQQ'
ORDER BY dividend_yield DESC;
```

## Strategy-Specific Queries

### All 0DTE Covered Call ETFs
```sql
SELECT symbol, name, related_stock, dividend_yield
FROM stocks
WHERE investment_strategy = '0DTE Covered Call'
ORDER BY dividend_yield DESC;
```

### All Synthetic Covered Call ETFs
```sql
SELECT symbol, name, related_stock, dividend_yield
FROM stocks
WHERE investment_strategy = 'Synthetic Covered Call'
ORDER BY dividend_yield DESC;
```

### Short Strategy ETFs
```sql
SELECT symbol, name, related_stock, dividend_yield
FROM stocks
WHERE investment_strategy LIKE '%Short%'
ORDER BY dividend_yield DESC;
```

### Leveraged + Income ETFs
```sql
SELECT symbol, name, related_stock, dividend_yield
FROM stocks
WHERE investment_strategy = 'Leveraged + Income'
ORDER BY dividend_yield DESC;
```

## Top Performers

### Top 20 Highest Yielding Option Income ETFs
```sql
SELECT
    symbol,
    name,
    related_stock,
    investment_strategy,
    ROUND(dividend_yield::numeric, 4) as yield
FROM stocks
WHERE investment_strategy IS NOT NULL
AND dividend_yield IS NOT NULL
ORDER BY dividend_yield DESC
LIMIT 20;
```

### Top ETFs by Strategy
```sql
SELECT DISTINCT ON (investment_strategy)
    investment_strategy,
    symbol,
    name,
    related_stock,
    ROUND(dividend_yield::numeric, 4) as yield
FROM stocks
WHERE investment_strategy IS NOT NULL
AND dividend_yield IS NOT NULL
ORDER BY investment_strategy, dividend_yield DESC;
```

## Portfolio Construction

### Find Complementary Strategies
```sql
-- Find one ETF from each strategy type for diversification
SELECT DISTINCT ON (investment_strategy)
    investment_strategy,
    symbol,
    name,
    related_stock,
    ROUND(dividend_yield::numeric, 4) as yield,
    ROUND(expense_ratio::numeric, 6) as expense_ratio
FROM stocks
WHERE investment_strategy IS NOT NULL
AND dividend_yield IS NOT NULL
ORDER BY investment_strategy, dividend_yield DESC;
```

### Compare Related Stocks
```sql
-- Compare all ETFs tracking the same underlying
SELECT
    related_stock,
    COUNT(*) as etf_count,
    ROUND(AVG(dividend_yield::numeric), 4) as avg_yield,
    ROUND(MAX(dividend_yield::numeric), 4) as max_yield,
    STRING_AGG(symbol, ', ' ORDER BY dividend_yield DESC) as symbols
FROM stocks
WHERE investment_strategy IS NOT NULL
AND related_stock NOT LIKE 'Multiple%'
GROUP BY related_stock
HAVING COUNT(*) > 1
ORDER BY etf_count DESC;
```

## Multi-Asset Strategies

### Find All Portfolio/Multi-Asset ETFs
```sql
SELECT symbol, name, related_stock, investment_strategy, dividend_yield
FROM stocks
WHERE related_stock LIKE 'Multiple%'
ORDER BY dividend_yield DESC NULLS LAST;
```

## Provider Analysis

### YieldMax ETFs by Type
```sql
SELECT
    CASE
        WHEN investment_strategy LIKE '%0DTE%' THEN '0DTE Strategies'
        WHEN investment_strategy LIKE '%Short%' THEN 'Short Strategies'
        WHEN investment_strategy LIKE '%Portfolio%' THEN 'Portfolio Strategies'
        WHEN investment_strategy = 'Synthetic Covered Call' THEN 'Single Stock'
        ELSE 'Other'
    END as strategy_group,
    COUNT(*) as count,
    ROUND(AVG(dividend_yield::numeric), 4) as avg_yield
FROM stocks
WHERE name ILIKE '%yieldmax%'
GROUP BY strategy_group
ORDER BY avg_yield DESC;
```

### Global X Covered Call Suite
```sql
SELECT symbol, name, related_stock, dividend_yield
FROM stocks
WHERE (name ILIKE '%global x%' AND name ILIKE '%covered call%')
OR symbol IN ('QYLD', 'XYLD', 'RYLD', 'QYLG', 'XYLG')
ORDER BY dividend_yield DESC NULLS LAST;
```

## Advanced Analysis

### Correlation of Yield to Expense Ratio by Strategy
```sql
SELECT
    investment_strategy,
    COUNT(*) as etf_count,
    ROUND(AVG(dividend_yield::numeric), 4) as avg_yield,
    ROUND(AVG(expense_ratio::numeric), 6) as avg_expense_ratio,
    ROUND(CORR(dividend_yield, expense_ratio)::numeric, 4) as yield_expense_corr
FROM stocks
WHERE investment_strategy IS NOT NULL
AND dividend_yield IS NOT NULL
AND expense_ratio IS NOT NULL
GROUP BY investment_strategy
ORDER BY avg_yield DESC;
```

### Market Cap vs Yield by Strategy
```sql
SELECT
    investment_strategy,
    COUNT(*) as etf_count,
    ROUND(AVG(dividend_yield::numeric), 4) as avg_yield,
    ROUND(AVG(aum::numeric), 0) as avg_aum
FROM stocks
WHERE investment_strategy IS NOT NULL
AND aum IS NOT NULL
GROUP BY investment_strategy
ORDER BY avg_yield DESC;
```

## Export for Analysis

### Export All Classified ETFs
```sql
COPY (
    SELECT
        symbol,
        name,
        related_stock,
        investment_strategy,
        dividend_yield,
        expense_ratio,
        aum,
        exchange
    FROM stocks
    WHERE investment_strategy IS NOT NULL
    ORDER BY investment_strategy, dividend_yield DESC NULLS LAST
) TO '/path/to/export/classified_etfs.csv' WITH CSV HEADER;
```

## Notes

- **related_stock**: The underlying stock or asset the ETF tracks
  - Single stocks: TSLA, NVDA, AAPL, etc.
  - Indices: SPY, QQQ, IWM, DIA
  - Crypto: BTC, ETH
  - Multiple: For multi-asset/portfolio strategies

- **investment_strategy**: The type of option/income strategy
  - 19 distinct strategies identified
  - Ranges from aggressive (Short Option Income) to conservative (Buffered Premium Income)
  - Yields correlate with strategy risk profile
