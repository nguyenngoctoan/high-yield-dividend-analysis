# Excel Add-in Installation Guide

## Quick Install (5 Minutes)

### Step 1: Download the Add-in
1. Download `DividendAPI.bas` from this repository
2. Save it to a known location on your computer

### Step 2: Import into Excel
1. Open Microsoft Excel
2. Press `Alt + F11` (Windows) or `Fn + Option + F11` (Mac) to open VBA Editor
3. In VBA Editor, go to `File > Import File...`
4. Navigate to and select `DividendAPI.bas`
5. Click `Open`

You should now see "DividendAPI" in your modules list.

### Step 3: Enable Macros
1. Close VBA Editor
2. Go to `File > Options > Trust Center`
3. Click `Trust Center Settings`
4. Select `Macro Settings`
5. Choose `Enable all macros` (or `Disable all macros with notification`)
6. Click `OK`

**Note**: You may need to restart Excel for changes to take effect.

### Step 4: Create Settings Sheet
1. In your Excel workbook, create a new sheet
2. Rename it to "Settings" (important!)
3. In cell `A1`, type: `API Key`
4. In cell `A2`, paste your Dividend API key

Get your free API key at: https://yourdomain.com/signup

### Step 5: Test Installation
1. In any cell, type: `=DIVV_API_STATUS()`
2. Press Enter
3. You should see "Connected" if everything is working

If you see an error, double-check:
- Settings sheet exists and is named correctly
- API key is in cell Settings!A2
- Macros are enabled
- You have internet connection

## Using the Functions

### Basic Examples

Try these in any cell:

```excel
=DIVV_PRICE("AAPL")          → 150.25
=DIVV_YIELD("AAPL")          → 0.52%
=DIVV_ANNUAL("AAPL")         → 0.96
=DIVV_NEXT_DATE("AAPL")      → 2025-02-08
=DIVV_NAME("AAPL")           → Apple Inc.
```

### Create a Portfolio Tracker

1. Create column headers:
   - A1: Symbol
   - B1: Name
   - C1: Price
   - D1: Yield
   - E1: Annual Dividend

2. Enter symbols in column A (A2, A3, A4, etc.)

3. Use formulas:
   - B2: `=DIVV_NAME(A2)`
   - C2: `=DIVV_PRICE(A2)`
   - D2: `=DIVV_YIELD(A2)`
   - E2: `=DIVV_ANNUAL(A2)`

4. Copy formulas down for all symbols

## Troubleshooting

### "Compile Error: Invalid outside procedure"
- Make sure you imported the entire .bas file
- Don't copy/paste code manually, use File > Import

### "#NAME?" Error
- Functions not recognized
- Check that DividendAPI module is imported
- Verify macros are enabled
- Restart Excel

### "ERROR: API Key not found"
- Settings sheet doesn't exist or is misnamed
- API key not in Settings!A2
- Check spelling of sheet name (case sensitive)

### "ERROR: 401 - Unauthorized"
- Invalid API key
- Get new key at: https://yourdomain.com/api-keys
- Make sure you copied the full key

### Functions Return Old Data
- Excel caches function results
- Force refresh: Press `Ctrl + Alt + F9` (Windows) or `Cmd + Shift + F9` (Mac)
- Or use `=DIVV_REFRESH()` function

### Slow Performance
- Excel is calculating too many formulas
- Switch to manual calculation: Formulas > Calculation Options > Manual
- Refresh with F9 when needed

## Advanced Configuration

### Change API Base URL
1. Open VBA Editor (`Alt + F11`)
2. Find the line: `Private Const API_BASE_URL As String = "https://api.yourdomain.com/v1"`
3. Change to your custom URL if using self-hosted API
4. Save and close VBA Editor

### Change API Key Location
1. Open VBA Editor
2. Find: `Private Const API_KEY_CELL As String = "Settings!A2"`
3. Change to your preferred location (e.g., "Config!B5")
4. Save and close

### Add Custom Functions
You can extend the add-in with your own functions:

```vba
Public Function DIVV_CUSTOM(symbol As String) As Variant
    ' Your custom logic here
    Dim response As String
    response = CallAPI("/your-endpoint/" & symbol)
    ' Parse and return
End Function
```

## Security Best Practices

### Protecting Your API Key

**Warning**: Excel files can be shared, and anyone with access can see your API key!

**Best Practices**:
1. Don't share workbooks with API keys embedded
2. Hide the Settings sheet:
   - Right-click Settings tab > Hide
3. Password protect the workbook:
   - Review > Protect Workbook
4. Use environment-specific keys:
   - Personal key for personal sheets
   - Team key for shared sheets
5. Rotate keys regularly:
   - Generate new key
   - Update Settings!A2
   - Revoke old key

### For Shared Workbooks
1. Create a template without API key
2. Instruct users to add their own key
3. Or use a shared team key with usage limits

## Updates and Versioning

### Updating the Add-in
1. Download new version of `DividendAPI.bas`
2. In VBA Editor, right-click "DividendAPI" module
3. Select "Remove DividendAPI"
4. Go to File > Import File...
5. Select new version
6. Refresh your workbook

### Version Checking
Add this to any cell to check version:
```excel
' (Will be added in future update)
=DIVV_VERSION()
```

## Getting Help

### Resources
- **Documentation**: https://docs.yourdomain.com/excel
- **Video Tutorials**: https://yourdomain.com/tutorials
- **API Reference**: https://docs.yourdomain.com/api
- **Support Email**: support@yourdomain.com

### Community
- **Forum**: https://community.yourdomain.com
- **Discord**: https://discord.gg/yourdomain
- **Reddit**: r/dividendapi

### Common Questions

**Q: Do I need Excel 365?**
A: No, works with Excel 2010 and later (Windows/Mac)

**Q: Can I use on Mac?**
A: Yes! VBA works on Mac Excel too

**Q: Does it work offline?**
A: No, requires internet to fetch data. But you can copy values for offline use.

**Q: How many symbols can I track?**
A: Depends on your API tier. Free: 10 symbols, Pro: Unlimited

**Q: Can I automate updates?**
A: Yes, with VBA macros you can schedule automatic refresh

**Q: Is my data secure?**
A: Yes, all API calls use HTTPS encryption

## Next Steps

1. ✅ Install add-in
2. ✅ Test with basic functions
3. ⬜ Build your first portfolio tracker
4. ⬜ Explore advanced functions
5. ⬜ Check out template library
6. ⬜ Join the community

Happy tracking!
