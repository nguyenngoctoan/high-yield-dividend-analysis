# Dividend API - Google Sheets Add-on

Custom Google Sheets functions to fetch dividend stock data directly in your spreadsheets, similar to `GOOGLEFINANCE()`.

## Features

- **Real-time Stock Prices**: Get latest prices, changes, OHLCV data
- **Dividend Information**: Yields, amounts, dates, frequency, growth rates
- **ETF Data**: AUM, IV, expense ratios, investment strategies
- **Company Info**: Name, sector, industry, exchange, market cap
- **Portfolio Calculations**: Income projections, position values, yield on cost
- **Auto-refresh**: Data updates automatically
- **Custom Menu**: Easy setup via UI

## Quick Start

### 1. Install the Add-on

#### Method 1: Via Apps Script (Recommended)

1. Open your Google Sheet
2. Go to `Extensions > Apps Script`
3. Delete any existing code
4. Copy the entire contents of `Code.gs`
5. Paste into the Apps Script editor
6. Click `Save` (💾 icon)
7. Refresh your Google Sheet

#### Method 2: Create as Add-on (Advanced)

1. Follow Method 1 to add the script
2. Go to `Extensions > Apps Script > Deploy > New deployment`
3. Choose type: "Add-on"
4. Configure and deploy

### 2. Set Your API Key

#### Option A: Via Custom Menu (Easiest)

1. In your Google Sheet, go to `Dividend API > Set API Key`
2. Enter your API key in the dialog
3. Click `Save`

#### Option B: Via Script Editor

1. Go to `Extensions > Apps Script`
2. Click `Run > setApiKey`
3. Enter your API key when prompted

#### Option C: Via Function

In any cell:
```
=DIVV_SET_KEY("your-api-key-here")
```

Get your API key at: https://yourdomain.com/api-keys

### 3. Use Functions

In any cell, type:
```
=DIVV_PRICE("AAPL")
=DIVV_YIELD("AAPL")
=DIVV_ANNUAL("AAPL")
```

## Available Functions

### Price Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_PRICE(symbol)` | Latest close price | `=DIVV_PRICE("AAPL")` | 150.25 |
| `DIVV_CHANGE(symbol)` | Price change % | `=DIVV_CHANGE("AAPL")` | 0.025 |
| `DIVV_OPEN(symbol)` | Opening price | `=DIVV_OPEN("AAPL")` | 149.50 |
| `DIVV_HIGH(symbol)` | Day high | `=DIVV_HIGH("AAPL")` | 151.00 |
| `DIVV_LOW(symbol)` | Day low | `=DIVV_LOW("AAPL")` | 149.00 |
| `DIVV_VOLUME(symbol)` | Trading volume | `=DIVV_VOLUME("AAPL")` | 50000000 |

### Dividend Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_YIELD(symbol)` | Dividend yield | `=DIVV_YIELD("AAPL")` | 0.0052 |
| `DIVV_ANNUAL(symbol)` | Annual dividend (TTM) | `=DIVV_ANNUAL("AAPL")` | 0.96 |
| `DIVV_NEXT_DATE(symbol)` | Next ex-dividend date | `=DIVV_NEXT_DATE("AAPL")` | 2025-02-08 |
| `DIVV_NEXT_AMOUNT(symbol)` | Next dividend amount | `=DIVV_NEXT_AMOUNT("AAPL")` | 0.24 |
| `DIVV_FREQUENCY(symbol)` | Payment frequency | `=DIVV_FREQUENCY("AAPL")` | Quarterly |
| `DIVV_GROWTH(symbol)` | Dividend growth rate | `=DIVV_GROWTH("AAPL")` | 0.05 |
| `DIVV_PAYOUT_RATIO(symbol)` | Payout ratio | `=DIVV_PAYOUT_RATIO("AAPL")` | 0.15 |

### ETF Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_AUM(symbol)` | Assets under management | `=DIVV_AUM("SPY")` | 450000000000 |
| `DIVV_IV(symbol)` | Implied volatility | `=DIVV_IV("XYLD")` | 0.185 |
| `DIVV_STRATEGY(symbol)` | Investment strategy | `=DIVV_STRATEGY("XYLD")` | Covered Call |
| `DIVV_EXPENSE_RATIO(symbol)` | Expense ratio | `=DIVV_EXPENSE_RATIO("SPY")` | 0.0009 |

### Company Info Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_NAME(symbol)` | Company/ETF name | `=DIVV_NAME("AAPL")` | Apple Inc. |
| `DIVV_SECTOR(symbol)` | Sector | `=DIVV_SECTOR("AAPL")` | Technology |
| `DIVV_INDUSTRY(symbol)` | Industry | `=DIVV_INDUSTRY("AAPL")` | Consumer Electronics |
| `DIVV_EXCHANGE(symbol)` | Exchange | `=DIVV_EXCHANGE("AAPL")` | NASDAQ |
| `DIVV_MARKET_CAP(symbol)` | Market cap | `=DIVV_MARKET_CAP("AAPL")` | 3000000000000 |

### Portfolio Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_INCOME(symbol, shares)` | Annual dividend income | `=DIVV_INCOME("AAPL", 100)` | 96.00 |
| `DIVV_POSITION_VALUE(symbol, shares)` | Position value | `=DIVV_POSITION_VALUE("AAPL", 100)` | 15025.00 |
| `DIVV_YIELD_ON_COST(symbol, basis)` | Yield on cost | `=DIVV_YIELD_ON_COST("AAPL", 120)` | 0.008 |

### Utility Functions

| Function | Description | Example | Returns |
|----------|-------------|---------|---------|
| `DIVV_SEARCH(query)` | Search for symbol | `=DIVV_SEARCH("Apple")` | AAPL |
| `DIVV_API_STATUS()` | Check connection | `=DIVV_API_STATUS()` | Connected |
| `DIVV_RATE_LIMIT()` | Check usage | `=DIVV_RATE_LIMIT()` | 50/1000 requests |
| `DIVV_SUMMARY(symbol)` | Get multiple data points | `=DIVV_SUMMARY("AAPL")` | [Array] |

## Example Spreadsheet Templates

### 1. Basic Portfolio Tracker

| A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|
| **Symbol** | **Name** | **Shares** | **Price** | **Value** | **Annual Div** | **Annual Income** |
| AAPL | =DIVV_NAME(A2) | 100 | =DIVV_PRICE(A2) | =C2*D2 | =DIVV_ANNUAL(A2) | =C2*F2 |
| MSFT | =DIVV_NAME(A3) | 50 | =DIVV_PRICE(A3) | =C3*D3 | =DIVV_ANNUAL(A3) | =C3*F3 |
| **Total** | | =SUM(C2:C3) | | =SUM(E2:E3) | | =SUM(G2:G3) |

### 2. Dividend Calendar

| A | B | C | D | E |
|---|---|---|---|---|
| **Symbol** | **Name** | **Next Date** | **Next Amount** | **Frequency** |
| AAPL | =DIVV_NAME(A2) | =DIVV_NEXT_DATE(A2) | =DIVV_NEXT_AMOUNT(A2) | =DIVV_FREQUENCY(A2) |
| MSFT | =DIVV_NAME(A3) | =DIVV_NEXT_DATE(A3) | =DIVV_NEXT_AMOUNT(A3) | =DIVV_FREQUENCY(A3) |
| O | =DIVV_NAME(A4) | =DIVV_NEXT_DATE(A4) | =DIVV_NEXT_AMOUNT(A4) | =DIVV_FREQUENCY(A4) |

Sort by column C (Next Date) to see upcoming payments!

### 3. Covered Call ETF Screener

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| **Symbol** | **Name** | **Price** | **Yield** | **IV** | **Strategy** |
| XYLD | =DIVV_NAME(A2) | =DIVV_PRICE(A2) | =DIVV_YIELD(A2) | =DIVV_IV(A2) | =DIVV_STRATEGY(A2) |
| QYLD | =DIVV_NAME(A3) | =DIVV_PRICE(A3) | =DIVV_YIELD(A3) | =DIVV_IV(A3) | =DIVV_STRATEGY(A3) |
| RYLD | =DIVV_NAME(A4) | =DIVV_PRICE(A4) | =DIVV_YIELD(A4) | =DIVV_IV(A4) | =DIVV_STRATEGY(A4) |
| JEPI | =DIVV_NAME(A5) | =DIVV_PRICE(A5) | =DIVV_YIELD(A5) | =DIVV_IV(A5) | =DIVV_STRATEGY(A5) |

### 4. High-Yield Stock Finder

| A | B | C | D | E |
|---|---|---|---|---|
| **Symbol** | **Name** | **Sector** | **Yield** | **Annual Dividend** |
| T | =DIVV_NAME(A2) | =DIVV_SECTOR(A2) | =DIVV_YIELD(A2) | =DIVV_ANNUAL(A2) |
| VZ | =DIVV_NAME(A3) | =DIVV_SECTOR(A3) | =DIVV_YIELD(A3) | =DIVV_ANNUAL(A3) |
| MO | =DIVV_NAME(A4) | =DIVV_SECTOR(A4) | =DIVV_YIELD(A4) | =DIVV_ANNUAL(A4) |

Filter by yield > 5% to find high-yield opportunities!

### 5. Dividend Growth Tracker

| A | B | C | D | E | F |
|---|---|---|---|---|---|
| **Symbol** | **Name** | **Current Annual** | **Growth Rate** | **Projected Next Year** | **5-Year Projection** |
| AAPL | =DIVV_NAME(A2) | =DIVV_ANNUAL(A2) | =DIVV_GROWTH(A2) | =C2*(1+D2) | =C2*(1+D2)^5 |
| MSFT | =DIVV_NAME(A3) | =DIVV_ANNUAL(A3) | =DIVV_GROWTH(A3) | =C3*(1+D3) | =C3*(1+D3)^5 |

## Advanced Features

### Conditional Formatting

Highlight high-yield stocks:
1. Select yield column
2. Format > Conditional formatting
3. Format cells if: Greater than > 0.05 (5%)
4. Choose green background

Highlight upcoming dividends:
1. Select next date column
2. Format cells if: Date is before > [7 days from now]
3. Choose yellow background

### Data Validation

Create dropdown of symbols:
1. Create list of symbols in column A
2. Data > Data validation
3. Criteria: List from range
4. Select your symbol list

### Charts and Visualizations

**Portfolio Allocation Pie Chart**:
1. Select position values
2. Insert > Chart > Pie chart
3. Customize labels with symbols

**Dividend Income Timeline**:
1. Create monthly income projections
2. Insert > Chart > Line chart
3. Track income over time

### Automation with Google Sheets

**Auto-refresh on schedule**:
```javascript
// In Apps Script editor, add this trigger
function onEdit(e) {
  // Refresh data when specific cell is edited
  SpreadsheetApp.flush();
}
```

**Send dividend alerts**:
```javascript
function checkDividends() {
  var sheet = SpreadsheetApp.getActiveSheet();
  // Check for dividends in next 7 days
  // Send email notifications
}
```

## Formatting Tips

### Format Numbers

**Currency** (Prices, Dividends):
```
Format > Number > Currency
```

**Percentage** (Yields, Changes):
```
Format > Number > Percent
```

**Large Numbers** (AUM, Market Cap):
```
Format > Number > Custom number format
#,##0,,"M"  (for millions)
#,##0,,,"B" (for billions)
```

### Custom Number Formats

```
Yield: 0.00%
Price: $#,##0.00
Large numbers: #,##0.0,,"B"
Dates: mmm dd, yyyy
```

## Error Handling

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `API Key not set` | No API key configured | Run `Dividend API > Set API Key` |
| `Invalid API Key` | Wrong key | Check your key at yourdomain.com |
| `Rate limit exceeded` | Too many requests | Wait or upgrade plan |
| `API Request Failed` | Network/server issue | Check connection, try again |
| `N/A` | Data not available | Stock may not pay dividends |

## Performance Optimization

### Best Practices

1. **Use ARRAYFORMULA** for bulk operations:
```
=ARRAYFORMULA(DIVV_PRICE(A2:A100))
```

2. **Cache results** in separate cells:
```
Don't: =DIVV_PRICE("AAPL") * 100
Do: =D2 * 100  (where D2 has =DIVV_PRICE("AAPL"))
```

3. **Limit auto-refresh**:
- Functions refresh when sheet opens or edits are made
- Use static values for historical data

4. **Batch with DIVV_SUMMARY**:
```
=DIVV_SUMMARY("AAPL")
Returns: [Price, Yield, Annual Div, Next Date, Next Amount]
```

### Quotas and Limits

Google Sheets quotas:
- **UrlFetchApp**: 20,000 calls/day
- **Execution time**: 6 min/execution
- **Triggers**: 90 min/day

Plan your API usage accordingly!

## API Tiers

| Tier | Requests/Month | Rate Limit | Cost |
|------|----------------|------------|------|
| Free | 1,000 | 10/min | $0 |
| Pro | 100,000 | 100/min | $29/mo |
| Enterprise | Unlimited | 1000/min | Custom |

## Troubleshooting

### Functions Not Updating

1. Force recalculation: Edit any cell and press Enter
2. Use menu: `Dividend API > Refresh All Data`
3. Close and reopen the sheet

### #ERROR! Messages

- Check API key is set correctly
- Verify symbol exists: `=DIVV_SEARCH("Company Name")`
- Check API status: `=DIVV_API_STATUS()`

### Slow Performance

1. Reduce number of API calls
2. Use ARRAYFORMULA for ranges
3. Cache results in separate cells
4. Consider upgrading API tier for faster limits

### Authorization Issues

1. First use requires authorization
2. Go to `Extensions > Apps Script`
3. Run any function
4. Grant permissions when prompted

## Share Your Spreadsheet

**Important**: When sharing:
1. Each user needs their own API key
2. Users should run `Dividend API > Set API Key`
3. API keys are stored per-user (not in the sheet)

## Template Gallery

Pre-built templates available:
- Portfolio Tracker
- Dividend Calendar
- High-Yield Screener
- Covered Call ETF Dashboard
- Income Projection Calculator

Get templates at: https://templates.yourdomain.com

## Support

- **Documentation**: https://docs.yourdomain.com
- **API Keys**: https://yourdomain.com/api-keys
- **Community**: https://community.yourdomain.com
- **Support**: support@yourdomain.com
- **GitHub**: https://github.com/yourusername/dividend-api

## Contributing

Found a bug or have a feature request?
1. Open issue on GitHub
2. Submit pull request
3. Join our community forum

## License

MIT License - See LICENSE file for details

## Version History

- **v1.0** (2025-11-13): Initial release
  - Core price and dividend functions
  - ETF data with IV support
  - Portfolio calculation functions
  - Custom menu integration
  - Auto-refresh capabilities
  - Batch summary function

## What's Next?

Coming soon:
- ✅ Historical price arrays
- ✅ Dividend history arrays
- ✅ Portfolio performance tracking
- ✅ Sector allocation analysis
- ✅ Real-time alerts
- ✅ Advanced screeners
