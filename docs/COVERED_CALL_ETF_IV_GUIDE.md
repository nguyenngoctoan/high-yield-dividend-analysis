# Covered Call ETF IV Analysis Guide

## Overview

This guide explains how to use Implied Volatility (IV) data for covered call ETFs using your Alpha Vantage Premium subscription. IV is a **critical indicator** for covered call ETFs as it directly correlates with distribution levels.

## Why IV Matters for Covered Call ETFs

### The Covered Call Strategy

Covered call ETFs generate income by:
1. Holding a portfolio of stocks (e.g., S&P 500 stocks)
2. Selling call options on those holdings
3. Collecting option premiums as income
4. Distributing that premium income to shareholders

### IV's Direct Impact on Distributions

**Implied Volatility drives option premium income**:

- **Higher IV** → **Higher option premiums** → **Higher distributions**
- **Lower IV** → **Lower option premiums** → **Lower distributions**

**Example**:
- When VIX is 15 (low volatility): XYLD might pay 0.40/share monthly
- When VIX is 30 (high volatility): XYLD might pay 0.60/share monthly

The IV of the underlying options directly determines how much premium the ETF can collect, and thus how much it can distribute to shareholders.

## What Was Implemented

### 1. Alpha Vantage Client Options Methods

Location: `lib/data_sources/alpha_vantage_client.py`

**New Methods**:
```python
# Fetch full options chain with IV and Greeks
fetch_options_chain(symbol, include_greeks=True)

# Fetch historical options data
fetch_historical_options(symbol, date_str='2025-01-01')

# Get simplified IV data
get_implied_volatility(symbol, contract_type='both')
```

### 2. IV Discovery Processor

Location: `lib/processors/iv_discovery_processor.py`

**Features**:
- Discovers IV from Alpha Vantage Premium options API
- Calculates separate call and put IV
- Tracks IV for covered call ETFs specifically
- Records source availability
- Updates database with IV data

### 3. Discovery Script

Location: `scripts/discover_iv_for_covered_call_etfs.py`

**Modes**:
- Test single symbol
- Discover all covered call ETFs
- Discover all liquid symbols

## Quick Start

### 1. Verify Alpha Vantage Premium Access

```bash
# Check your API key is configured
echo $ALPHA_VANTAGE_API_KEY

# Or check .env file
grep ALPHA_VANTAGE_API_KEY .env
```

### 2. Test with a Single Covered Call ETF

```bash
# Test with XYLD (Global X S&P 500 Covered Call ETF)
python scripts/discover_iv_for_covered_call_etfs.py --test XYLD
```

**Expected Output**:
```
Testing IV Discovery for XYPL
================================================================================
1. Testing Alpha Vantage Client...
✅ Alpha Vantage client initialized

2. Fetching options chain for XYLD...
✅ Found 234 option contracts

3. Calculating IV for XYLD...
✅ IV calculated successfully:
  Overall IV: 0.1845
  Call IV: 0.1823
  Put IV: 0.1867
  Contracts analyzed: 234

4. Testing IV Discovery Processor...
✅ IV Discovery successful:
  Source: AlphaVantage
  IV: 0.1845
  Call IV: 0.1823
  Put IV: 0.1867

================================================================================
✅ All tests passed!
================================================================================
```

### 3. Discover IV for All Covered Call ETFs

```bash
# Discover for all covered call ETFs
python scripts/discover_iv_for_covered_call_etfs.py

# Or limit to first 10
python scripts/discover_iv_for_covered_call_etfs.py --limit 10
```

## Usage Examples

### Python API

#### Quick IV Lookup
```python
from lib.processors.iv_discovery_processor import discover_iv

# Get IV for a single symbol
result = discover_iv('XYLD')

if result['success']:
    print(f"IV: {result['iv']:.4f}")
    print(f"Call IV: {result['call_iv']:.4f}")
    print(f"Put IV: {result['put_iv']:.4f}")
    print(f"Source: {result['source']}")
```

#### Batch Discovery for Covered Call ETFs
```python
from lib.processors.iv_discovery_processor import discover_covered_call_etf_iv

# Discover for all covered call ETFs
summary = discover_covered_call_etf_iv(limit=None, force_rediscover=False)

print(f"Processed: {summary['processed']}")
print(f"Successfully found IV: {summary['successful']}")
print(f"Success rate: {summary['success_rate']}")
print(f"ETFs: {', '.join(summary['etfs_analyzed'][:10])}")
```

#### Using the Processor Directly
```python
from lib.processors.iv_discovery_processor import IVDiscoveryProcessor

processor = IVDiscoveryProcessor()

# Discover and store IV
success = processor.process_and_store('QYLD', force_rediscover=False)

if success:
    print("IV stored in database")

# Get statistics
stats = processor.get_statistics()
print(f"Total processed: {stats['total_processed']}")
print(f"Successful: {stats['successful']}")
```

### SQL Queries

#### Get Latest IV for Covered Call ETFs
```sql
SELECT
    s.symbol,
    s.name,
    s.investment_strategy,
    p.date,
    p.close as price,
    p.iv as implied_volatility,
    p.iv * 100 as iv_percentage
FROM raw_stocks s
INNER JOIN raw_stock_prices p ON s.symbol = p.symbol
WHERE s.is_etf = true
  AND LOWER(s.investment_strategy) LIKE '%covered call%'
  AND p.iv IS NOT NULL
  AND p.date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY p.iv DESC, s.symbol;
```

#### Track IV Over Time
```sql
SELECT
    symbol,
    date,
    close,
    iv,
    LAG(iv) OVER (PARTITION BY symbol ORDER BY date) as prev_iv,
    iv - LAG(iv) OVER (PARTITION BY symbol ORDER BY date) as iv_change
FROM raw_stock_prices
WHERE symbol = 'XYLD'
  AND iv IS NOT NULL
  AND date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date DESC;
```

#### Compare IV Across Covered Call ETFs
```sql
WITH latest_iv AS (
    SELECT DISTINCT ON (symbol)
        symbol,
        date,
        iv,
        close
    FROM raw_stock_prices
    WHERE iv IS NOT NULL
    ORDER BY symbol, date DESC
)
SELECT
    s.symbol,
    s.name,
    li.iv as current_iv,
    li.close as price,
    (li.iv * li.close * 100) as annualized_premium_estimate
FROM raw_stocks s
INNER JOIN latest_iv li ON s.symbol = li.symbol
WHERE s.is_etf = true
  AND LOWER(s.investment_strategy) LIKE '%covered call%'
ORDER BY li.iv DESC;
```

#### Monthly Distribution Prediction Model
```sql
-- Estimate monthly distribution based on IV and price
-- Rule of thumb: Monthly distribution ≈ (Price × IV × √(1/12))
SELECT
    s.symbol,
    s.name,
    p.close as price,
    p.iv,
    (p.close * p.iv * SQRT(1.0/12)) as estimated_monthly_distribution,
    d.amount as actual_latest_distribution,
    d.date as distribution_date
FROM raw_stocks s
INNER JOIN LATERAL (
    SELECT close, iv, date
    FROM raw_stock_prices
    WHERE symbol = s.symbol AND iv IS NOT NULL
    ORDER BY date DESC
    LIMIT 1
) p ON true
LEFT JOIN LATERAL (
    SELECT amount, date
    FROM raw_dividends
    WHERE symbol = s.symbol
    ORDER BY date DESC
    LIMIT 1
) d ON true
WHERE s.is_etf = true
  AND LOWER(s.investment_strategy) LIKE '%covered call%'
ORDER BY estimated_monthly_distribution DESC;
```

## Popular Covered Call ETFs

### Global X Family (NASDAQ-100, S&P 500, Russell 2000)
- **QYLD** - NASDAQ-100 Covered Call ETF
  - Highest distributions typically
  - Tech-heavy portfolio
  - Most volatile underlying (higher IV potential)

- **XYLD** - S&P 500 Covered Call ETF
  - Moderate distributions
  - Diversified large-cap portfolio
  - Most popular covered call ETF

- **RYLD** - Russell 2000 Covered Call ETF
  - Small-cap exposure
  - Higher volatility than S&P 500
  - Potentially higher IV

### JPMorgan
- **JEPI** - Equity Premium Income ETF
  - Active management
  - Equity-linked notes + covered calls
  - More sophisticated strategy
  - Lower expense ratio than Global X

- **JEPQ** - NASDAQ Equity Premium Income ETF
  - NASDAQ-focused version of JEPI
  - Tech exposure with income generation

### Other Notable Covered Call ETFs
- **DIVO** - Amplify CWP Enhanced Dividend Income ETF
- **SVOL** - Simplify Volatility Premium ETF
- **NUSI** - Nationwide Risk-Managed Income ETF

## Interpreting IV for Distributions

### IV Ranges and What They Mean

| IV Range | Market Conditions | Expected Distributions | Strategy Effectiveness |
|----------|-------------------|----------------------|----------------------|
| < 0.15 (15%) | Very calm markets | Low distributions | Poor time for covered calls |
| 0.15-0.20 | Normal volatility | Normal distributions | Typical covered call returns |
| 0.20-0.30 | Elevated volatility | Higher distributions | Good time for covered calls |
| > 0.30 (30%) | High volatility | Very high distributions | Excellent for income |

### Call vs Put IV

For covered call ETFs, **call IV is more important**:

- **Call IV**: What the ETF is selling → Directly affects income
- **Put IV**: Protection cost → Less relevant for covered call strategy

**Example**:
```python
result = discover_iv('XYLD')
# Call IV: 0.1823 → This determines premium income
# Put IV: 0.1867 → Less relevant for covered calls
```

### IV vs VIX

- **VIX**: Market-wide volatility index (S&P 500 options)
- **Symbol IV**: Specific to that stock/ETF's options

**Correlation**:
- S&P 500 covered call ETFs (XYLD) → High correlation with VIX
- Tech covered call ETFs (QYLD) → Can deviate from VIX
- Small-cap covered call ETFs (RYLD) → May have higher IV than VIX

## Automation and Monitoring

### Daily IV Update Script

```python
#!/usr/bin/env python3
"""Daily IV update for covered call ETFs"""

from lib.processors.iv_discovery_processor import discover_covered_call_etf_iv

def main():
    print("Updating IV for covered call ETFs...")

    summary = discover_covered_call_etf_iv(
        limit=None,  # Process all
        force_rediscover=False  # Use cache when available
    )

    print(f"Updated IV for {summary['successful']} ETFs")

    # Send alert if average IV changes significantly
    # (Add your alerting logic here)

if __name__ == '__main__':
    main()
```

### Add to Cron

```bash
# Update IV daily at 4:15 PM (after market close)
15 16 * * 1-5 cd /path/to/project && python scripts/discover_iv_for_covered_call_etfs.py
```

### Slack/Email Alerts for IV Changes

```python
def alert_on_iv_changes():
    """Alert when IV changes significantly"""
    query = """
        WITH iv_changes AS (
            SELECT
                symbol,
                iv,
                LAG(iv) OVER (PARTITION BY symbol ORDER BY date) as prev_iv,
                ((iv - LAG(iv) OVER (PARTITION BY symbol ORDER BY date))
                 / LAG(iv) OVER (PARTITION BY symbol ORDER BY date)) * 100 as pct_change
            FROM raw_stock_prices
            WHERE iv IS NOT NULL
              AND date >= CURRENT_DATE - INTERVAL '2 days'
        )
        SELECT symbol, iv, prev_iv, pct_change
        FROM iv_changes
        WHERE ABS(pct_change) > 10  -- 10% change
          AND prev_iv IS NOT NULL
    """

    # Execute query and send alerts
    # (Add your alerting logic here)
```

## Best Practices

### 1. Update Frequency
- **Daily**: After market close for covered call ETFs you track
- **Weekly**: For broader coverage of all ETFs
- **On-demand**: During high volatility periods (VIX > 25)

### 2. Data Quality
- ✅ Use Alpha Vantage Premium (reliable, includes Greeks)
- ✅ Track both call and put IV separately
- ✅ Store historical IV for trend analysis
- ❌ Don't rely on Yahoo Finance IV (unreliable)

### 3. Analysis
- Compare IV to historical averages
- Look at IV percentile (where is current IV vs historical range?)
- Track IV term structure (near-term vs long-term)
- Correlate IV with actual distributions

### 4. Strategy
- **High IV periods** → Good time to evaluate covered call ETFs
- **Low IV periods** → Consider other income strategies
- **IV rising** → Distributions likely to increase
- **IV falling** → Distributions likely to decrease

## Troubleshooting

### No IV Data Found

**Possible Causes**:
1. Symbol doesn't have options
   - Not all ETFs have options
   - Check if symbol is optionable

2. API rate limit reached
   - Alpha Vantage Premium: 600-1200 req/min
   - Add delays between requests if needed

3. Premium subscription not active
   - Verify REALTIME_OPTIONS access
   - Test with `--test XYLD`

### IV Seems Wrong

**Check**:
1. Market hours: IV calculations best during trading hours
2. Expiration dates: Near-term options may have different IV
3. Strike selection: ATM options give most accurate IV
4. Sample size: More contracts = more reliable average

### Performance Issues

**Optimize**:
1. Use `limit` parameter for testing
2. Enable data source tracking (caches preferences)
3. Run during off-peak hours
4. Process in batches

## Integration with Existing Workflows

### Add to Daily Update Script

```bash
# In daily_update_v3_parallel.sh or similar
echo "Discovering IV for covered call ETFs..."
python scripts/discover_iv_for_covered_call_etfs.py --limit 50

echo "IV discovery complete"
```

### Dashboard/Reporting

Query latest IV data for your dashboard:
```python
def get_covered_call_etf_dashboard():
    query = """
        SELECT
            s.symbol,
            s.name,
            p.close,
            p.iv,
            d.amount as last_distribution,
            (p.close * p.iv * SQRT(1.0/12)) as estimated_monthly_dist
        FROM raw_stocks s
        INNER JOIN LATERAL (
            SELECT close, iv
            FROM raw_stock_prices
            WHERE symbol = s.symbol AND iv IS NOT NULL
            ORDER BY date DESC LIMIT 1
        ) p ON true
        LEFT JOIN LATERAL (
            SELECT amount
            FROM raw_dividends
            WHERE symbol = s.symbol
            ORDER BY date DESC LIMIT 1
        ) d ON true
        WHERE LOWER(s.investment_strategy) LIKE '%covered call%'
        ORDER BY p.iv DESC
    """
    # Execute and return results
```

## Related Documentation

- **IV Data Sources**: `docs/IMPLIED_VOLATILITY_DATA_SOURCES.md`
- **Data Source Tracking**: `docs/DATA_SOURCE_TRACKING.md`
- **Alpha Vantage Client**: `lib/data_sources/alpha_vantage_client.py`
- **IV Processor**: `lib/processors/iv_discovery_processor.py`

## Support

For issues or questions:
1. Check Alpha Vantage Premium status
2. Test with `--test XYLD` command
3. Review logs for error messages
4. Verify API quota usage

---

**Remember**: IV is a forward-looking indicator. High IV today suggests the potential for higher distributions in the coming period, assuming the ETF continues its covered call strategy with similar parameters.
