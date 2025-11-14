# DIVV Functions - Quick Reference Card

## 📊 Price Functions

```excel
=DIVV_PRICE("AAPL")          Latest close price
=DIVV_CHANGE("AAPL")         Price change %
=DIVV_OPEN("AAPL")           Opening price (Sheets)
=DIVV_HIGH("AAPL")           Day high (Sheets)
=DIVV_LOW("AAPL")            Day low (Sheets)
=DIVV_VOLUME("AAPL")         Trading volume (Sheets)
```

## 💰 Dividend Functions

```excel
=DIVV_YIELD("AAPL")          Dividend yield
=DIVV_ANNUAL("AAPL")         Annual dividend (TTM)
=DIVV_NEXT_DATE("AAPL")      Next ex-dividend date
=DIVV_NEXT_AMOUNT("AAPL")    Next dividend amount
=DIVV_FREQUENCY("AAPL")      Payment frequency
=DIVV_GROWTH("AAPL")         Dividend growth rate (Sheets)
=DIVV_PAYOUT_RATIO("AAPL")   Payout ratio (Sheets)
```

## 📈 ETF Functions

```excel
=DIVV_AUM("SPY")             Assets under management
=DIVV_IV("XYLD")             Implied volatility
=DIVV_STRATEGY("XYLD")       Investment strategy
=DIVV_EXPENSE_RATIO("SPY")   Expense ratio (Sheets)
```

## 🏢 Company Info

```excel
=DIVV_NAME("AAPL")           Company/ETF name
=DIVV_SECTOR("AAPL")         Sector
=DIVV_INDUSTRY("AAPL")       Industry
=DIVV_EXCHANGE("AAPL")       Exchange (Sheets)
=DIVV_MARKET_CAP("AAPL")     Market capitalization (Sheets)
```

## 💼 Portfolio Functions (Sheets)

```excel
=DIVV_INCOME("AAPL", 100)              Annual dividend income
=DIVV_POSITION_VALUE("AAPL", 100)      Position value
=DIVV_YIELD_ON_COST("AAPL", 120)       Yield on cost
```

## 🔧 Utility Functions

```excel
=DIVV_API_STATUS()           Check connection status
=DIVV_RATE_LIMIT()           Check usage (Sheets)
=DIVV_SEARCH("Apple")        Search for symbol (Sheets)
=DIVV_SUMMARY("AAPL")        Get multiple data points (Sheets)
=DIVV_REFRESH()              Force refresh (Excel)
```

## 🚀 Quick Start Examples

### Portfolio Tracker
```
| Symbol | Name              | Price    | Yield | Annual Div |
|--------|-------------------|----------|-------|------------|
| AAPL   | =DIVV_NAME(A2)    | =DIVV_PRICE(A2) | =DIVV_YIELD(A2) | =DIVV_ANNUAL(A2) |
```

### Income Calculator
```
| Symbol | Shares | Annual Div        | Annual Income    |
|--------|--------|-------------------|------------------|
| AAPL   | 100    | =DIVV_ANNUAL(A2)  | =B2*C2           |
```

### Dividend Calendar
```
| Symbol | Next Date            | Next Amount           | Days Until  |
|--------|----------------------|-----------------------|-------------|
| AAPL   | =DIVV_NEXT_DATE(A2)  | =DIVV_NEXT_AMOUNT(A2) | =B2-TODAY() |
```

### Covered Call ETF Dashboard
```
| Symbol | Price           | IV              | Monthly Est.        |
|--------|-----------------|-----------------|---------------------|
| XYLD   | =DIVV_PRICE(A2) | =DIVV_IV(A2)    | =B2*C2*SQRT(1/12)   |
```

## 💡 Pro Tips

### Excel
- Enable macros: File > Options > Trust Center
- Store API key in Settings!A2
- Force refresh: Ctrl+Alt+F9 or =DIVV_REFRESH()
- Manual calculation: Formulas > Calculation Options > Manual

### Google Sheets
- Use ARRAYFORMULA: `=ARRAYFORMULA(DIVV_PRICE(A2:A100))`
- Batch data: `=DIVV_SUMMARY("AAPL")` returns [Price, Yield, Div, Date, Amount]
- Format as %: Select cells > Format > Number > Percent
- Format as $: Select cells > Format > Number > Currency

## 🎯 Common Formulas

**Total Portfolio Value**:
```excel
=SUMPRODUCT(Shares, DIVV_PRICE(Symbols))
```

**Total Annual Income**:
```excel
=SUMPRODUCT(Shares, DIVV_ANNUAL(Symbols))
```

**Portfolio Yield**:
```excel
=TotalAnnualIncome / TotalPortfolioValue
```

**Yield on Cost**:
```excel
=DIVV_ANNUAL(Symbol) / CostBasis
```

**Dividend Growth Projection (5 years)**:
```excel
=DIVV_ANNUAL(Symbol) * (1 + DIVV_GROWTH(Symbol))^5
```

## ⚙️ Installation

### Excel (3 steps)
1. Import DividendAPI.bas (Alt+F11 > File > Import)
2. Add API key to Settings!A2
3. Use functions!

### Google Sheets (3 steps)
1. Extensions > Apps Script > Paste Code.gs
2. Dividend API menu > Set API Key
3. Use functions!

## 🔗 Resources

- **Get API Key**: https://yourdomain.com/api-keys
- **Documentation**: https://docs.yourdomain.com
- **Templates**: https://templates.yourdomain.com
- **Support**: support@yourdomain.com

## 📞 Support

**Error Messages**:
- "API Key not set" → Set key in Settings!A2 (Excel) or menu (Sheets)
- "Invalid API Key" → Get new key at yourdomain.com
- "Rate limit exceeded" → Wait 1 minute or upgrade to Pro
- "N/A" → Data not available for this symbol

**Need Help?**
- Email: support@yourdomain.com
- Forum: community.yourdomain.com
- Discord: discord.gg/yourdomain

---

**Free Tier**: 1,000 requests/month | **Pro**: $29/mo, unlimited symbols
**Get started**: yourdomain.com/signup
