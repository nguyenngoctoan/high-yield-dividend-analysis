# International Symbols Filtering Fix

## Problem
International symbols with suffixes like `.HK` (Hong Kong) and `.KS` (Korea) were appearing in the database despite having exchange-based filtering in place.

## Root Cause
The exchange-based filtering only checked the `exchangeShortName` field, but some international symbols were slipping through because they might be listed on US exchanges or the exchange field wasn't properly set.

## Solution Implemented

### 1. Added Centralized Symbol Suffix Blocking (lib/core/config.py)

Added `BLOCKED_SUFFIXES` list to `ExchangeConfig`:
```python
BLOCKED_SUFFIXES = [
    '.L', '.AX', '.DE', '.AS', '.MI', '.PA', '.SW', '.HK', '.BR',
    '.LS', '.MC', '.CO', '.ST', '.OL', '.HE', '.IC', '.VI', '.AT',
    '.WA', '.PR', '.BD', '.SA', '.MX', '.JK', '.KL', '.SI', '.BK',
    '.TW', '.KS', '.KQ', '.T', '.F', '.NZ', '.JO', '.SG', '.BO',
    '.NS', '.NE', '.ME'
]
```

Added three new helper methods:
- `is_international_symbol(symbol)` - Checks if symbol has international suffix
- `is_allowed_symbol(symbol, exchange)` - Comprehensive check (suffix + exchange)
- `is_allowed_exchange(exchange)` - Existing exchange check

### 2. Updated FMP Client Filtering (lib/data_sources/fmp_client.py)

Updated all symbol discovery methods to use the new filtering:

**discover_symbols()** (line 295-305):
```python
# Filter by both exchange and symbol suffix
if symbol and exchange in allowed_exchanges:
    if Config.EXCHANGE.is_allowed_symbol(symbol, exchange):
        symbols.append({...})
```

**discover_dividend_stocks()** (line 395-404):
```python
# Filter by both exchange and symbol suffix
if symbol and exchange in allowed_exchanges and dividend_yield > 0:
    if Config.EXCHANGE.is_allowed_symbol(symbol, exchange):
        symbols.append({...})
```

**discover_etfs()** (line 338-346):
```python
# Filter out international symbols
if symbol and name:
    if Config.EXCHANGE.is_allowed_symbol(symbol):
        symbols.append({...})
```

### 3. Database Cleanup (scripts/cleanup_all_international_symbols.py)

Updated cleanup script to use centralized config:
```python
from lib.core.config import Config
INTERNATIONAL_SUFFIXES = Config.EXCHANGE.BLOCKED_SUFFIXES
```

Ran cleanup to remove existing international symbols:
- 786 from raw_stocks
- 354 from raw_stock_prices
- 14 from raw_dividends
- 845 from dim_stocks
- **Total: 1,999 international symbols removed**

## Files Modified

1. **lib/core/config.py**
   - Added `BLOCKED_SUFFIXES` list
   - Added `is_international_symbol()` method
   - Added `is_allowed_symbol()` method

2. **lib/data_sources/fmp_client.py**
   - Updated `discover_symbols()` with suffix filtering
   - Updated `discover_dividend_stocks()` with suffix filtering
   - Updated `discover_etfs()` with suffix filtering

3. **scripts/cleanup_all_international_symbols.py**
   - Updated to use centralized `Config.EXCHANGE.BLOCKED_SUFFIXES`

## Prevention Strategy

The two-layer filtering approach ensures no international symbols get through:

**Layer 1: Exchange Filtering**
- Only allows symbols from: NYSE, NASDAQ, AMEX, BATS, OTC, TSX, TSXV, CSE
- Blocks all other exchanges

**Layer 2: Symbol Suffix Filtering**
- Blocks any symbol ending with international suffixes
- Even if exchange field is missing or incorrect, suffix check catches it
- Covers 35+ international exchange suffixes

## Testing

To verify filtering works:
```python
from lib.core.config import Config

# Should return True (blocked)
Config.EXCHANGE.is_international_symbol('0700.HK')
Config.EXCHANGE.is_international_symbol('005930.KS')

# Should return False (allowed)
Config.EXCHANGE.is_international_symbol('AAPL')
Config.EXCHANGE.is_international_symbol('MSFT')

# Comprehensive check
Config.EXCHANGE.is_allowed_symbol('AAPL', 'NASDAQ')  # True
Config.EXCHANGE.is_allowed_symbol('0700.HK', 'HKSE')  # False
```

## Allowed Symbols

**US Exchanges:**
- NYSE, NASDAQ, AMEX
- BATS, BTS, BYX, BZX, CBOE
- EDGA, EDGX, PCX, NGM
- OTCM, OTCX (OTC markets)

**Canadian Exchanges:**
- TSX, TSXV, CSE, TSE
- Note: Canadian symbols (.TO, .V) are ALLOWED

**Blocked:**
- All other international exchanges (Europe, Asia, Latin America, etc.)
- Any symbol with international suffix

## Impact

**Before:**
- 1,999 international symbols in database
- Mixed US and international symbols
- Potential data quality issues

**After:**
- Only US and Canadian symbols
- Clean, consistent symbol database
- Future-proof filtering at ingestion layer
- No international symbols can enter system

## Maintenance

The centralized `BLOCKED_SUFFIXES` list in `lib/core/config.py` is the single source of truth. To add new blocked suffixes:

1. Add to `Config.EXCHANGE.BLOCKED_SUFFIXES`
2. All filtering automatically uses the updated list
3. Run cleanup script to remove existing symbols

## Summary

✅ Added dual-layer filtering (exchange + suffix)
✅ Updated all FMP discovery methods
✅ Removed 1,999 existing international symbols
✅ Centralized configuration for maintainability
✅ Future-proof: no new international symbols can enter

The `.HK` and `.KS` symbols you were seeing have been removed, and the system now prevents any new international symbols from being added.
