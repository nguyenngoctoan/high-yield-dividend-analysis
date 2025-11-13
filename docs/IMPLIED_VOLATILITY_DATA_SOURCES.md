# Implied Volatility (IV) Data Sources

## Overview

Implied Volatility (IV) is a metric derived from options pricing that represents the market's expectation of future price volatility. Unlike historical volatility (which we can calculate from price data), IV requires access to options chain data.

## Current Status

**None of our current free data sources (FMP, AlphaVantage free tier, Yahoo Finance) provide reliable, production-ready IV data.**

## Detailed Source Analysis

### 1. Yahoo Finance (via yfinance)

**Availability**: ⚠️ **Partially Available (Not Recommended)**

**Details**:
- IV is included in the options chain data via `ticker.option_chain()`
- Accessible through the `impliedVolatility` column in the returned DataFrame

**Code Example**:
```python
import yfinance as yf

ticker = yf.Ticker("AAPL")
options = ticker.option_chain(date='2025-12-19')  # Specify expiry date

# Access calls and puts
calls = options.calls  # Contains 'impliedVolatility' column
puts = options.puts    # Contains 'impliedVolatility' column

# Get IV for specific strike
iv = calls[calls['strike'] == 150.0]['impliedVolatility'].values[0]
```

**Limitations**:
- ❌ **Known bugs**: Yahoo Finance IV calculations have documented inaccuracies
- ❌ **After-hours issues**: Most errors occur during after-market hours
- ❌ **Simplistic calculation**: Yahoo uses a basic IV calculation method
- ❌ **Unstable values**: When values are unstable, Yahoo may default them to 0%
- ❌ **No API key**: No official API means no support or reliability guarantees
- ❌ **Rate limiting**: Unofficial scraping may get blocked

**Verdict**: Not suitable for production use due to reliability issues.

---

### 2. Financial Modeling Prep (FMP)

**Availability**: ❌ **Not Available**

**Details**:
- FMP does NOT provide options chain data in their standard API
- Their documentation mentions "real-time pricing data and implied volatility" for options trading analysis, but no actual endpoints exist
- FMP focuses on fundamentals, financial statements, and price data

**What FMP Does Provide**:
- Historical price volatility (standard deviation)
- Technical indicators
- Real-time stock prices
- Fundamentals and company data

**Verdict**: No options or IV data available.

---

### 3. Alpha Vantage

**Availability**: ✅ **Available (Premium Only)**

**Details**:
- Alpha Vantage offers two options chain functions:
  - `REALTIME_OPTIONS` - Real-time options chains with IV and Greeks
  - `HISTORICAL_OPTIONS` - Historical options chains (15+ years history)

**Features**:
- ✅ Implied Volatility included
- ✅ Greeks included (delta, gamma, theta, vega, rho)
- ✅ Bid/ask prices
- ✅ Volume and open interest
- ✅ Historical data (15+ years)

**API Example**:
```python
# Realtime options with IV
url = "https://www.alphavantage.co/query"
params = {
    'function': 'REALTIME_OPTIONS',
    'symbol': 'AAPL',
    'require_greeks': 'true',  # Enable IV and Greeks
    'apikey': 'YOUR_API_KEY'
}
```

**Pricing Requirements**:
- ❌ **Not available on free tier**
- Requires premium membership:
  - 600 requests/min plan
  - OR 1200 requests/min plan

**Verdict**: Excellent for IV data, but requires paid subscription.

---

## Recommended Options Data APIs

If you need production-grade IV data, consider these specialized providers:

### 1. **Polygon.io** (Highly Recommended)

**Features**:
- ✅ Real-time options trades and quotes
- ✅ Implied volatility and all Greeks
- ✅ Complete OPRA feed (all U.S. options exchanges)
- ✅ Historical options data
- ✅ WebSocket streaming support
- ✅ Excellent documentation and support

**Pricing**: Starts at $29/month for options data

**Website**: https://polygon.io/

---

### 2. **Tradier**

**Features**:
- ✅ Real-time options chains
- ✅ Implied volatility and Greeks
- ✅ Market data and execution capabilities
- ✅ Historical options data
- ✅ REST API and WebSocket streaming

**Pricing**: Free developer account with limited data

**Website**: https://tradier.com/

---

### 3. **Market Data API**

**Features**:
- ✅ Real-time options data
- ✅ IV and Greeks (delta, gamma, theta, vega)
- ✅ Historical options data
- ✅ Google Sheets integration
- ✅ Simple REST API

**Pricing**: Starts at $29/month

**Website**: https://www.marketdata.app/

---

### 4. **Intrinio**

**Features**:
- ✅ Extensive options data
- ✅ Real-time and historical prices
- ✅ Implied volatility and Greeks
- ✅ Enterprise-grade reliability
- ✅ Options flow data

**Pricing**: Custom enterprise pricing

**Website**: https://intrinio.com/

---

## Alternative Approaches

### 1. Calculate Historical Volatility Instead

If you don't need implied volatility specifically, you can calculate historical volatility from price data:

```python
import pandas as pd
import numpy as np

def calculate_historical_volatility(prices, window=30, trading_days=252):
    """
    Calculate annualized historical volatility.

    Args:
        prices: Series of closing prices
        window: Lookback window in days
        trading_days: Trading days per year (252 for stocks)

    Returns:
        Historical volatility as decimal (e.g., 0.25 = 25%)
    """
    # Calculate daily returns
    returns = np.log(prices / prices.shift(1))

    # Calculate rolling standard deviation
    volatility = returns.rolling(window=window).std()

    # Annualize
    annual_volatility = volatility * np.sqrt(trading_days)

    return annual_volatility

# Example usage
import yfinance as yf

ticker = yf.Ticker("AAPL")
hist = ticker.history(period="1y")
hv = calculate_historical_volatility(hist['Close'], window=30)

print(f"Current 30-day HV: {hv.iloc[-1]:.2%}")
```

**Pros**:
- ✅ Free - uses only price data
- ✅ Reliable calculation
- ✅ No API dependencies

**Cons**:
- ❌ Backward-looking (what happened)
- ❌ Not forward-looking (what market expects)
- ❌ Different from implied volatility

---

### 2. VIX as Proxy for Market Volatility

For broad market volatility, use the VIX (CBOE Volatility Index):

```python
import yfinance as yf

vix = yf.Ticker("^VIX")
vix_data = vix.history(period="1mo")
current_vix = vix_data['Close'].iloc[-1]

print(f"Current VIX: {current_vix:.2f}")
```

**Pros**:
- ✅ Free and reliable
- ✅ Represents market-wide implied volatility
- ✅ Widely used benchmark

**Cons**:
- ❌ Only for S&P 500 overall market
- ❌ Not symbol-specific
- ❌ Not suitable for individual stock analysis

---

## Implementation Recommendations

### For Your Current System

Given your current free data sources, here are the options:

#### Option 1: Skip IV for Now (Recommended)
- Focus on other metrics (AUM, dividends, volume, historical volatility)
- Add IV later when budget allows for premium API

#### Option 2: Use Historical Volatility
- Calculate from existing price data
- Add a `historical_volatility` column instead of `iv`
- More reliable than Yahoo's IV

#### Option 3: Add Yahoo IV with Caveats
- Implement Yahoo IV extraction via yfinance
- Add strong data quality checks
- Flag unreliable values (0%, extreme outliers)
- Include disclaimer about data quality
- Only use during market hours

#### Option 4: Upgrade to Alpha Vantage Premium
- Best paid option among current providers
- Already integrated into your system
- Simply enable `REALTIME_OPTIONS` function

### Recommended Implementation (Option 2)

Add historical volatility calculation to your system:

```python
# In lib/processors/volatility_processor.py

from typing import Optional, Dict, Any
import numpy as np
import pandas as pd

class VolatilityProcessor:
    """Calculate and store historical volatility."""

    def calculate_hv(self, prices_df: pd.DataFrame,
                     windows: list = [30, 60, 90]) -> Dict[str, float]:
        """
        Calculate historical volatility for multiple windows.

        Returns:
            Dict with keys like 'hv_30d', 'hv_60d', 'hv_90d'
        """
        results = {}

        # Calculate daily returns
        returns = np.log(prices_df['close'] / prices_df['close'].shift(1))

        for window in windows:
            # Rolling standard deviation
            vol = returns.rolling(window=window).std()
            # Annualize (252 trading days)
            annual_vol = vol.iloc[-1] * np.sqrt(252)
            results[f'hv_{window}d'] = float(annual_vol)

        return results
```

---

## Future Integration Plan

When you're ready to add IV data:

1. **Add Alpha Vantage Premium** (easiest integration)
   - Already have Alpha Vantage client
   - Just add `REALTIME_OPTIONS` function
   - Update data source tracker

2. **Or Add Polygon.io** (best quality)
   - Create new `PolygonClient` class
   - Similar pattern to existing clients
   - Update data source tracker

3. **Update Schema**
   ```sql
   -- Already exists in raw_stock_prices
   ALTER TABLE raw_stock_prices
   ADD COLUMN IF NOT EXISTS iv DECIMAL(10, 6);

   -- Add options-specific table for full chain
   CREATE TABLE raw_options_chain (
       symbol VARCHAR(20),
       expiry_date DATE,
       strike DECIMAL(10, 2),
       option_type VARCHAR(4),  -- 'call' or 'put'
       implied_volatility DECIMAL(10, 6),
       delta DECIMAL(10, 6),
       gamma DECIMAL(10, 6),
       theta DECIMAL(10, 6),
       vega DECIMAL(10, 6),
       volume BIGINT,
       open_interest BIGINT,
       last_price DECIMAL(10, 4),
       bid DECIMAL(10, 4),
       ask DECIMAL(10, 4),
       updated_at TIMESTAMP,
       PRIMARY KEY (symbol, expiry_date, strike, option_type)
   );
   ```

4. **Update Data Source Tracker**
   - Add IV to supported data types
   - Track which source provides IV
   - Record reliability metrics

---

## Summary & Recommendations

### Current Situation
- ❌ FMP: No options/IV data
- ⚠️ Yahoo: Has IV but unreliable
- ✅ Alpha Vantage: Has IV but requires premium subscription

### Best Path Forward

**Short Term (Free)**:
1. Use historical volatility calculated from price data
2. Use VIX as market-wide volatility indicator
3. Add to data source tracker as "not yet available"

**Medium Term (Budget Available)**:
1. Upgrade to Alpha Vantage Premium ($99-199/month)
2. Or add Polygon.io ($29+/month for options)
3. Implement IV discovery processor
4. Update data source tracking system

**Long Term**:
1. Compare multiple IV sources
2. Blend IV data from multiple providers
3. Add IV-based screening and analysis
4. Build volatility surface visualizations

### Cost Comparison

| Provider | Monthly Cost | IV Data | Historical Options | Real-time | Support |
|----------|--------------|---------|-------------------|-----------|---------|
| Yahoo Finance | Free | ⚠️ Unreliable | ❌ No | ⚠️ Limited | ❌ None |
| Alpha Vantage Premium | $99-199 | ✅ Yes | ✅ 15+ years | ✅ Yes | ✅ Good |
| Polygon.io | $29+ | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Excellent |
| Tradier | Free (dev) | ✅ Limited | ⚠️ Limited | ✅ Yes | ⚠️ Limited |
| Market Data API | $29+ | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Good |

---

## Questions?

- **Do I need IV right now?** - Probably not if you're focused on dividend stocks and ETFs. Historical volatility is sufficient for most analyses.

- **What's the cheapest reliable option?** - Polygon.io or Market Data API at $29/month

- **Can I calculate IV myself?** - Not easily. IV requires solving the Black-Scholes equation in reverse, which needs current options prices.

- **Should I use Yahoo's IV?** - Only if you need rough estimates and can tolerate errors. Not recommended for production or trading decisions.

---

## Related Documentation

- Data Source Tracking: `docs/DATA_SOURCE_TRACKING.md`
- Implementation Summary: `IMPLEMENTATION_SUMMARY.md`
- Client Implementations: `lib/data_sources/`
