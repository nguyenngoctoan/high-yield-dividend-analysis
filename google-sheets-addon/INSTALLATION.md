# Google Sheets Add-on Installation Guide

## Quick Install (3 Minutes)

### Method 1: Copy & Paste (Easiest)

#### Step 1: Open Apps Script
1. Open your Google Sheet (or create a new one)
2. Click `Extensions > Apps Script`
3. Delete any existing code in the editor

#### Step 2: Add the Code
1. Open `Code.gs` from this repository
2. Copy ALL the code (Ctrl+A, Ctrl+C)
3. Paste into the Apps Script editor
4. Click the save icon (💾) or press `Ctrl+S`
5. Name your project "Dividend API" (optional)

#### Step 3: Refresh Your Sheet
1. Close the Apps Script tab
2. Refresh your Google Sheet (F5 or reload page)
3. You should see a new menu: "Dividend API"

#### Step 4: Set Your API Key
1. Click `Dividend API > Set API Key` in the menu
2. Enter your API key in the dialog
3. Click `Save`

Get your free API key at: https://yourdomain.com/signup

#### Step 5: Authorize the Script
1. Try using a function: `=DIVV_PRICE("AAPL")`
2. You may see "Authorization required"
3. Click "Review Permissions"
4. Choose your Google account
5. Click "Advanced" → "Go to [Project Name] (unsafe)"
6. Click "Allow"

**Note**: This authorization is safe - you're authorizing your own script!

#### Step 6: Test Installation
In any cell, type:
```
=DIVV_API_STATUS()
```

You should see "Connected" if everything works!

### Method 2: Google Workspace Marketplace (Coming Soon)

Once published:
1. Open Google Sheet
2. Extensions > Add-ons > Get add-ons
3. Search "Dividend API"
4. Click install

## Using the Functions

### Basic Examples

Try these in any cell:

```
=DIVV_PRICE("AAPL")          → 150.25
=DIVV_YIELD("AAPL")          → 0.0052 (format as %)
=DIVV_ANNUAL("AAPL")         → 0.96
=DIVV_NEXT_DATE("AAPL")      → 2025-02-08
=DIVV_NAME("AAPL")           → Apple Inc.
```

### Create a Portfolio Tracker

1. Create column headers (Row 1):
   - A1: Symbol
   - B1: Name
   - C1: Price
   - D1: Yield
   - E1: Annual Dividend

2. Enter symbols in column A (A2, A3, A4...)

3. Use formulas:
   - B2: `=DIVV_NAME(A2)`
   - C2: `=DIVV_PRICE(A2)`
   - D2: `=DIVV_YIELD(A2)`
   - E2: `=DIVV_ANNUAL(A2)`

4. Drag formulas down for all symbols

5. Format:
   - Column C: Format > Number > Currency
   - Column D: Format > Number > Percent
   - Column E: Format > Number > Currency

### Use ARRAYFORMULA for Bulk Operations

Instead of copying formulas down, use ARRAYFORMULA:

```
=ARRAYFORMULA(IF(A2:A100="","",DIVV_PRICE(A2:A100)))
```

This applies the function to all rows at once!

## Troubleshooting

### "Authorization required"
First time using custom functions:
1. Use any DIVV function
2. Click "Review Permissions"
3. Choose your account
4. Click "Advanced" → "Go to [Project] (unsafe)"
5. Click "Allow"

This is safe - you're authorizing your own script!

### "#ERROR! API Key not set"
Your API key isn't configured:
1. Click `Dividend API > Set API Key` in menu
2. OR run `setApiKey("your-key")` in Apps Script
3. OR use `=DIVV_SET_KEY("your-key")` in a cell

### "#ERROR! Invalid API Key"
Your API key is wrong:
1. Go to https://yourdomain.com/api-keys
2. Copy your key exactly
3. Reset via menu: `Dividend API > Set API Key`

### "#ERROR! Rate limit exceeded"
Too many API requests:
- **Free tier**: 10 requests/minute, 1000/month
- **Solution**: Wait a minute, or upgrade to Pro
- Check usage: `=DIVV_RATE_LIMIT()`

### Functions Not Updating
Google Sheets caches results:
1. Edit any cell and press Enter (forces recalc)
2. Use menu: `Dividend API > Refresh All Data`
3. Close and reopen the sheet
4. Change a parameter to force update

### Slow Performance
Lots of API calls:
1. Use `DIVV_SUMMARY()` to get multiple data points in one call
2. Use ARRAYFORMULA for bulk operations
3. Reduce recalculation: Cache results in separate cells
4. Consider upgrading to Pro tier for faster rate limits

### "Script function not found"
Apps Script not saved properly:
1. Go to Extensions > Apps Script
2. Make sure Code.gs is saved
3. Refresh your Google Sheet
4. Try again

### Custom Menu Not Appearing
Reload required:
1. Refresh your Google Sheet (F5)
2. Wait a few seconds
3. Check Extensions menu
4. If still missing, run `onOpen()` manually in Apps Script

## Advanced Configuration

### Programmatic API Key Setup

In Apps Script editor, run this once:

```javascript
function setupMyKey() {
  setApiKey('your-api-key-here');
  Logger.log('API key saved!');
}
```

Then use: Run > Run function > setupMyKey

### Change API Base URL

In Code.gs, find:
```javascript
const API_BASE_URL = 'https://api.yourdomain.com/v1';
```

Change to your self-hosted API or development server.

### Add Custom Functions

You can extend with your own functions:

```javascript
function DIVV_MY_CUSTOM(symbol) {
  try {
    const data = callAPI(`/custom-endpoint/${symbol}`);
    return data.custom_field || 'N/A';
  } catch (error) {
    return error.message;
  }
}
```

Save, refresh sheet, and use: `=DIVV_MY_CUSTOM("AAPL")`

### Create Scheduled Triggers

Auto-refresh data daily:

1. Apps Script editor > Triggers (clock icon)
2. Add Trigger
3. Function: `refreshAllData`
4. Event: Time-driven > Day timer
5. Time: 9-10am (after market close)
6. Save

### Custom Menu Items

Add your own menu options in `onOpen()`:

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Dividend API')
    .addItem('Set API Key', 'showApiKeyDialog')
    .addItem('Refresh All Data', 'refreshAllData')
    .addItem('Your Custom Action', 'yourFunction')
    .addToUi();
}
```

## Sharing Your Spreadsheet

### Important: API Keys Are User-Specific

When you share your sheet:
- ✅ Your functions are shared
- ✅ Your formulas work for others
- ❌ Your API key is NOT shared

**Each user needs their own API key!**

### Setup for Shared Sheets

1. Share sheet as template
2. Instruct users to:
   - Get free API key at yourdomain.com
   - Click `Dividend API > Set API Key`
   - Enter their own key

### Team API Keys

For teams:
1. Get a team/organization API key
2. Each member sets the same key
3. Usage counts toward team quota

## Performance Optimization

### Best Practices

1. **Use ARRAYFORMULA** for ranges:
```
=ARRAYFORMULA(DIVV_PRICE(A2:A100))
```
Better than 100 separate calls!

2. **Cache results** in cells:
```
Don't: =DIVV_PRICE("AAPL") * 100
Do: =C2 * 100 (where C2 = DIVV_PRICE("AAPL"))
```

3. **Use DIVV_SUMMARY()** for multiple data points:
```
=DIVV_SUMMARY("AAPL")
Returns: [Price, Yield, Annual Div, Next Date, Next Amount]
```

One API call instead of five!

4. **Limit auto-refresh**:
- Don't reference volatile cells unnecessarily
- Use static values where appropriate
- Manual triggers for heavy sheets

### Google Sheets Quotas

Be aware of limits:
- **UrlFetchApp**: 20,000 calls/day
- **Script runtime**: 6 minutes/execution
- **Triggers**: 90 minutes/day total

Plan accordingly!

## Security Best Practices

### API Key Storage

✅ **Good**: Keys stored in PropertiesService (user-specific)
✅ **Safe to share**: Others can't see your key
✅ **Easy rotation**: Just reset via menu

❌ **Don't**: Put API key in a cell
❌ **Don't**: Share keys publicly
❌ **Don't**: Use production keys for testing

### Permissions

The add-on requests:
- **Internet access**: To call API
- **User properties**: To store API key
- **Spreadsheet access**: To read symbols and write results

All necessary for functionality.

### Revoke Access

To remove authorization:
1. Google Account > Security
2. Third-party apps with account access
3. Find your Apps Script project
4. Remove access

## Common Use Cases

### 1. Simple Dividend Tracker
```
| Symbol | Price | Yield | Annual Div |
| AAPL   | =DIVV_PRICE(A2) | =DIVV_YIELD(A2) | =DIVV_ANNUAL(A2) |
```

### 2. Income Calculator
```
| Symbol | Shares | Annual Div | Annual Income |
| AAPL   | 100    | =DIVV_ANNUAL(A2) | =B2*C2 |
```

### 3. Dividend Calendar
```
| Symbol | Next Date | Next Amount | Days Until |
| AAPL   | =DIVV_NEXT_DATE(A2) | =DIVV_NEXT_AMOUNT(A2) | =B2-TODAY() |
```

Sort by "Days Until" to see upcoming payments!

### 4. Portfolio Dashboard
Use `=DIVV_SUMMARY(A2)` to get everything at once:
```
=INDEX(DIVV_SUMMARY(A2), 1, 1)  → Price
=INDEX(DIVV_SUMMARY(A2), 2, 1)  → Yield
=INDEX(DIVV_SUMMARY(A2), 3, 1)  → Annual Dividend
```

## Getting Help

### Resources
- **Documentation**: https://docs.yourdomain.com/google-sheets
- **Video Tutorials**: https://yourdomain.com/tutorials
- **API Reference**: https://docs.yourdomain.com/api
- **Support Email**: support@yourdomain.com

### Community
- **Forum**: https://community.yourdomain.com
- **Discord**: https://discord.gg/yourdomain
- **Reddit**: r/dividendapi
- **GitHub**: https://github.com/yourusername/dividend-api

### Report Issues
Found a bug?
1. Check existing issues on GitHub
2. Create new issue with:
   - Steps to reproduce
   - Error message
   - Screenshot if helpful

## FAQ

**Q: Is this free?**
A: Yes! Free tier includes 1,000 requests/month. Pro tier ($29/mo) has higher limits.

**Q: Do I need Google Workspace?**
A: No, works with free Gmail accounts too!

**Q: Can I use on mobile?**
A: Yes! Google Sheets mobile app supports custom functions.

**Q: Does it work offline?**
A: No, requires internet. But you can copy values for offline use.

**Q: How often does data update?**
A: Functions fetch fresh data each time. Google Sheets caches results, so force refresh if needed.

**Q: Can I publish as public add-on?**
A: Yes! Follow Google's add-on publishing guide. (We may do this officially)

**Q: Is my API key safe?**
A: Yes, stored securely in PropertiesService, not visible to others.

## Updates and Versioning

### Updating the Add-on

When new version is released:
1. Go to Extensions > Apps Script
2. Select all code (Ctrl+A)
3. Delete
4. Copy new version from repository
5. Paste and save
6. Refresh your sheet

### Auto-Update (Marketplace Version)

Once published on Marketplace:
- Updates install automatically
- You'll see notification in sheet
- No manual action needed

## Next Steps

1. ✅ Install add-on
2. ✅ Set API key
3. ✅ Test basic functions
4. ⬜ Build portfolio tracker
5. ⬜ Explore advanced functions
6. ⬜ Check out templates
7. ⬜ Join community
8. ⬜ Share your use cases!

Happy tracking! 📊📈
