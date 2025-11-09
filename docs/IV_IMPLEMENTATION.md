# Implied Volatility (IV) Implementation

## Overview

The system now tracks **Implied Volatility (IV)** for stocks and ETFs over time. IV is stored in the `stock_prices` table alongside other price metrics.

## What is Implied Volatility?

Implied Volatility (IV) represents the market's expectation of future volatility for an underlying asset. It's derived from option prices and indicates how much the market expects the asset's price to move.

- **High IV**: Market expects significant price movements (higher risk/uncertainty)
- **Low IV**: Market expects stable prices (lower risk/uncertainty)
- **Units**: Expressed as an annualized percentage (e.g., 25.50 = 25.50%)

## Database Schema

### stock_prices Table

The `iv` column has been added to track implied volatility:

```sql
Column:  iv
Type:    NUMERIC(10,4)
Purpose: Store implied volatility as a percentage (e.g., 25.5000 = 25.5%)
Index:   idx_stock_prices_iv (symbol, date, iv) WHERE iv IS NOT NULL
```

### Migration

Migration file: `migrations/add_iv_column.sql`

To apply (if not already applied):
```bash
PGPASSWORD=postgres psql -h localhost -p 5434 -U postgres -d postgres -f migrations/add_iv_column.sql
```

## Data Sources

Implied Volatility can be fetched from multiple sources:

### 1. yfinance (Yahoo Finance)
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
info = ticker.info

# IV might be available in option data
options_dates = ticker.options
if options_dates:
    opt_chain = ticker.option_chain(options_dates[0])
    # Calculate IV from options data
```

### 2. FMP API (Financial Modeling Prep)
The FMP API may provide IV data in their options endpoints.

### 3. Alpha Vantage
Alpha Vantage has options data that includes implied volatility.

## Usage Examples

### Query IV Data

```sql
-- Get recent IV for a symbol
SELECT symbol, date, close, iv
FROM stock_prices
WHERE symbol = 'AAPL'
  AND iv IS NOT NULL
ORDER BY date DESC
LIMIT 30;

-- Find high volatility stocks
SELECT symbol, date, iv
FROM stock_prices
WHERE date = CURRENT_DATE
  AND iv > 50
ORDER BY iv DESC;

-- Track IV changes over time
SELECT
    symbol,
    date,
    iv,
    LAG(iv) OVER (PARTITION BY symbol ORDER BY date) as prev_iv,
    iv - LAG(iv) OVER (PARTITION BY symbol ORDER BY date) as iv_change
FROM stock_prices
WHERE symbol = 'TSLA'
  AND iv IS NOT NULL
ORDER BY date DESC
LIMIT 30;

-- Average IV by symbol (last 30 days)
SELECT
    symbol,
    AVG(iv) as avg_iv_30d,
    MIN(iv) as min_iv_30d,
    MAX(iv) as max_iv_30d,
    STDDEV(iv) as iv_volatility
FROM stock_prices
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
  AND iv IS NOT NULL
GROUP BY symbol
HAVING COUNT(*) >= 20
ORDER BY avg_iv_30d DESC;
```

### Python Integration

```python
from supabase_helpers import get_supabase_client, supabase_select

# Fetch IV data for a symbol
supabase = get_supabase_client()
result = supabase.table('stock_prices')\
    .select('symbol,date,close,iv')\
    .eq('symbol', 'AAPL')\
    .not_.is_('iv', 'null')\
    .order('date', desc=True)\
    .limit(30)\
    .execute()

iv_data = result.data
```

## Implementation Notes

### Data Collection

To collect IV data, you'll need to:

1. **Update data fetching scripts** (e.g., `fetch_hourly_prices.py`, `update_stock.py`)
2. **Add IV extraction logic** from chosen data source
3. **Include IV in upsert operations** when updating `stock_prices`

### Example Integration

```python
# In update_stock.py or similar script
def fetch_stock_data_with_iv(symbol):
    """Fetch stock data including implied volatility."""
    import yfinance as yf

    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1d")

    if hist.empty:
        return None

    # Get basic price data
    latest = hist.iloc[-1]

    # Try to get IV from options (if available)
    iv = None
    try:
        options_dates = ticker.options
        if options_dates:
            opt_chain = ticker.option_chain(options_dates[0])
            # Calculate IV from ATM options
            calls = opt_chain.calls
            if not calls.empty:
                atm_calls = calls.iloc[len(calls)//2]  # Approximate ATM
                iv = atm_calls.get('impliedVolatility')
    except:
        pass

    return {
        'symbol': symbol,
        'date': latest.name.date(),
        'close': latest['Close'],
        'open': latest['Open'],
        'high': latest['High'],
        'low': latest['Low'],
        'volume': latest['Volume'],
        'iv': iv  # Will be NULL if not available
    }
```

## Querying IV in Stock Screeners

When building stock screeners or analytics, you can filter by IV:

```python
# High volatility ETFs
high_vol_etfs = supabase.table('stock_prices')\
    .select('symbol,close,iv')\
    .eq('date', 'CURRENT_DATE')\
    .gte('iv', 40)\
    .order('iv', desc=True)\
    .execute()

# Low volatility dividend stocks
stable_dividend_stocks = supabase.table('stock_prices')\
    .select('stock_prices.symbol,stock_prices.iv,stocks.dividend_yield')\
    .join('stocks', 'stock_prices.symbol', 'stocks.symbol')\
    .lte('iv', 20)\
    .gte('stocks.dividend_yield', 3)\
    .execute()
```

## Performance Considerations

- **Index**: The `idx_stock_prices_iv` index optimizes queries filtering by symbol, date, and IV
- **NULL values**: IV will be NULL when not available - this is expected
- **Data freshness**: IV changes frequently - update daily for historical analysis

## Future Enhancements

1. **Automated IV Collection**: Add IV fetching to daily update scripts
2. **IV Percentile Rankings**: Calculate IV percentile relative to historical ranges
3. **IV Alerts**: Notify when IV spikes or drops significantly
4. **IV Charts**: Visualize IV trends alongside price movements
5. **Options Strategy Recommendations**: Based on current IV levels

## Related Metrics

Consider tracking these related volatility metrics:

- **Historical Volatility (HV)**: Actual price volatility over time
- **IV Rank**: Current IV percentile vs. 52-week range
- **IV Percentile**: Percentage of days in past year with lower IV
- **Beta**: Stock volatility relative to market

## References

- [Investopedia: Implied Volatility](https://www.investopedia.com/terms/i/iv.asp)
- [CBOE Volatility Index (VIX)](https://www.cboe.com/tradable_products/vix/)
- [Options Greeks and IV](https://www.investopedia.com/trading/using-the-greeks-to-understand-options/)

---

**Migration Date**: October 11, 2025
**Status**: ✅ Column added, ready for data collection
**Next Steps**: Implement IV data fetching in price update scripts
