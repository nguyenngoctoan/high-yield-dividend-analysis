# Dividend API - Excel Add-in

Custom Excel functions to fetch dividend stock data directly in your spreadsheets, similar to `YAHOOFINANCE()`.

## Features

- **Real-time Stock Prices**: Get latest prices, changes, OHLCV data
- **Dividend Information**: Yields, amounts, dates, frequency, growth rates
- **ETF Data**: AUM, IV, expense ratios, investment strategies
- **Company Info**: Name, sector, industry, exchange, market cap
- **Portfolio Calculations**: Income projections, position values, yield on cost
- **No External Dependencies**: Works with native Excel VBA

## Quick Start

### 1. Install the Add-in

1. Open Excel
2. Press `Alt + F11` to open VBA Editor
3. Go to `File > Import File...`
4. Select `DividendAPI.bas`
5. Close VBA Editor

### 2. Configure Your API Key

1. Create a sheet named "Settings"
2. In cell `A1`, type: `API Key`
3. In cell `A2`, paste your Dividend API key
4. Get your API key at: https://yourdomain.com/api-keys

### 3. Use Functions

In any cell, type:
```excel
=DIVV_PRICE("AAPL")
=DIVV_YIELD("AAPL")
=DIVV_ANNUAL("AAPL")
```

## Available Functions

### Price Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_PRICE(symbol)` | Latest close price | `=DIVV_PRICE("AAPL")` | 150.25 |
| `DIVV_CHANGE(symbol)` | Price change % | `=DIVV_CHANGE("AAPL")` | 2.5% |

### Dividend Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_YIELD(symbol)` | Dividend yield | `=DIVV_YIELD("AAPL")` | 0.52% |
| `DIVV_ANNUAL(symbol)` | Annual dividend | `=DIVV_ANNUAL("AAPL")` | 0.96 |
| `DIVV_NEXT_DATE(symbol)` | Next ex-div date | `=DIVV_NEXT_DATE("AAPL")` | 2025-02-08 |
| `DIVV_NEXT_AMOUNT(symbol)` | Next div amount | `=DIVV_NEXT_AMOUNT("AAPL")` | 0.24 |
| `DIVV_FREQUENCY(symbol)` | Payment frequency | `=DIVV_FREQUENCY("AAPL")` | Quarterly |

### ETF Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_AUM(symbol)` | Assets under mgmt | `=DIVV_AUM("SPY")` | 450000000000 |
| `DIVV_IV(symbol)` | Implied volatility | `=DIVV_IV("XYLD")` | 18.5% |
| `DIVV_STRATEGY(symbol)` | Investment strategy | `=DIVV_STRATEGY("XYLD")` | Covered Call |

### Company Info Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_NAME(symbol)` | Company name | `=DIVV_NAME("AAPL")` | Apple Inc. |
| `DIVV_SECTOR(symbol)` | Sector | `=DIVV_SECTOR("AAPL")` | Technology |
| `DIVV_INDUSTRY(symbol)` | Industry | `=DIVV_INDUSTRY("AAPL")` | Consumer Electronics |

### Utility Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_API_STATUS()` | Check connection | `=DIVV_API_STATUS()` | Connected |
| `DIVV_REFRESH()` | Refresh all data | `=DIVV_REFRESH()` | Refreshed at... |

## Example Portfolio Tracker

Create a simple portfolio tracker:

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| **Symbol** | **Name** | **Price** | **Yield** | **Annual Div** | **Next Date** |
| AAPL | =DIVV_NAME(A2) | =DIVV_PRICE(A2) | =DIVV_YIELD(A2) | =DIVV_ANNUAL(A2) | =DIVV_NEXT_DATE(A2) |
| MSFT | =DIVV_NAME(A3) | =DIVV_PRICE(A3) | =DIVV_YIELD(A3) | =DIVV_ANNUAL(A3) | =DIVV_NEXT_DATE(A3) |
| XYLD | =DIVV_NAME(A4) | =DIVV_PRICE(A4) | =DIVV_YIELD(A4) | =DIVV_ANNUAL(A4) | =DIVV_NEXT_DATE(A4) |

## Advanced Examples

### Portfolio Income Calculator

```excel
' Calculate annual income for a position
=DIVV_ANNUAL(A2) * B2  ' where B2 is shares owned

' Position value
=DIVV_PRICE(A2) * B2

' Total portfolio yield
=SUM(D2:D10) / SUM(E2:E10)  ' Total annual income / Total investment
```

### Covered Call ETF Screener

| Symbol | Name | IV | AUM | Strategy |
|--------|------|----|----|----------|
| XYLD | =DIVV_NAME(A2) | =DIVV_IV(A2) | =DIVV_AUM(A2) | =DIVV_STRATEGY(A2) |
| QYLD | =DIVV_NAME(A3) | =DIVV_IV(A3) | =DIVV_AUM(A3) | =DIVV_STRATEGY(A3) |
| RYLD | =DIVV_NAME(A4) | =DIVV_IV(A4) | =DIVV_AUM(A4) | =DIVV_STRATEGY(A4) |

### Dividend Growth Tracker

```excel
' Track dividend growth year-over-year
=DIVV_ANNUAL(A2)  ' Current annual dividend

' Compare with previous year's data (stored in column C)
=(B2 - C2) / C2  ' Growth rate
```

## Formatting Tips

### Format as Currency
1. Select cells with price/dividend data
2. Right-click > Format Cells
3. Choose Currency, 2 decimal places

### Format as Percentage
1. Select cells with yield/change data
2. Right-click > Format Cells
3. Choose Percentage, 2 decimal places

### Auto-refresh
- Press `Ctrl + Alt + F9` to force recalculation
- Or create a button with `=DIVV_REFRESH()` macro

## Error Handling

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `ERROR: API Key not found` | API key not set | Add key to Settings!A2 |
| `ERROR: 401` | Invalid API key | Check your API key |
| `ERROR: 429` | Rate limit exceeded | Wait or upgrade plan |
| `N/A` | Data not available | Stock may not pay dividends |

## Performance Tips

1. **Minimize API calls**: Cache results in cells, don't recalculate unnecessarily
2. **Use manual calculation**: `Formulas > Calculation Options > Manual`
3. **Batch requests**: Pull multiple symbols at once
4. **Refresh strategically**: Use `DIVV_REFRESH()` only when needed

## API Tiers

| Tier | Requests/Month | Rate Limit | Cost |
|------|----------------|------------|------|
| Free | 1,000 | 10/min | $0 |
| Pro | 100,000 | 100/min | $29/mo |
| Enterprise | Unlimited | 1000/min | Custom |

## Troubleshooting

### Functions Not Working

1. **Enable macros**: File > Options > Trust Center > Trust Center Settings > Macro Settings > Enable all macros
2. **Check VBA module**: Press Alt+F11, verify DividendAPI module exists
3. **Verify API key**: Check Settings!A2 has your API key

### Slow Performance

1. Set calculation to manual: Formulas > Calculation Options > Manual
2. Reduce number of API calls
3. Use `DIVV_REFRESH()` only when needed

### #NAME? Error

- Function not recognized
- Check that DividendAPI.bas is properly imported
- Verify macro security settings

## Support

- **Documentation**: https://docs.yourdomain.com
- **API Keys**: https://yourdomain.com/api-keys
- **Support**: support@yourdomain.com
- **GitHub**: https://github.com/yourusername/dividend-api

## License

MIT License - See LICENSE file for details

## Version History

- **v1.0** (2025-11-13): Initial release
  - Core price and dividend functions
  - ETF data support
  - Basic portfolio calculations
