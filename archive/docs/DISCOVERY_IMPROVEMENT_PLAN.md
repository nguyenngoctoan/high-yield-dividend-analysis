# Symbol Discovery Improvement Plan

## Current Problems

### Hard-Coded Symbol Lists
1. **Alpha Vantage Fallback** (lines 447-461): Acceptable - only on API failure
2. **Yahoo Screener** (lines 471-536): **CRITICAL ISSUE** - Hard-coded "targets" defeat the purpose of discovery

### Why This Fails
- Static lists become stale immediately
- Misses new ETF launches (YieldMax releases new ones quarterly!)
- Misses newly dividend-paying stocks
- Maintenance nightmare
- Not data-driven

## Proposed Solution: Criteria-Based Dynamic Discovery

### Phase 1: Enhanced FMP Screener Utilization (You Have Ultimate Plan!)

#### A. Advanced Stock Screener Parameters
FMP supports multiple screener parameters we're not using:

```python
def discover_dividend_stocks_advanced():
    """Use FMP's advanced screener with multiple criteria."""

    # High dividend yield stocks
    screener_configs = [
        {
            'name': 'High Yield Stocks',
            'params': {
                'dividendYieldMoreThan': 0.03,  # 3%+
                'marketCapMoreThan': 100000000,  # $100M+ market cap
                'volumeMoreThan': 100000,  # Minimum liquidity
                'limit': 10000
            }
        },
        {
            'name': 'Dividend Aristocrats (Consistent Payers)',
            'params': {
                'dividendYieldMoreThan': 0.01,  # 1%+
                'marketCapMoreThan': 1000000000,  # $1B+ large caps
                'priceMoreThan': 5,  # Filter penny stocks
                'limit': 10000
            }
        },
        {
            'name': 'REITs and MLPs',
            'params': {
                'sector': 'Real Estate',
                'dividendYieldMoreThan': 0.04,  # 4%+ typical for REITs
                'limit': 10000
            }
        }
    ]

    for config in screener_configs:
        url = f"https://financialmodelingprep.com/api/v3/stock-screener?"
        url += '&'.join([f"{k}={v}" for k, v in config['params'].items()])
        url += f"&apikey={FMP_API_KEY}"
        # Fetch and process...
```

#### B. Sector-Specific High Dividend Searches
```python
HIGH_DIVIDEND_SECTORS = [
    'Real Estate',  # REITs
    'Utilities',  # Stable dividend payers
    'Energy',  # MLPs and energy infrastructure
    'Financial Services',  # BDCs and mortgage REITs
    'Telecommunications'  # High yield telecoms
]

for sector in HIGH_DIVIDEND_SECTORS:
    discover_by_sector(sector, min_yield=0.03)
```

#### C. ETF Discovery by Fund Family (API-Driven)
Instead of hard-coding YieldMax symbols, discover them dynamically:

```python
def discover_etfs_by_family_dynamic():
    """Discover ETFs by analyzing fund families from ALL ETFs."""

    # Get ALL ETFs from FMP
    all_etfs = discover_all_etfs_from_fmp()

    # Analyze issuer patterns
    family_keywords = {
        'yieldmax': ['YMAX', 'yield', 'max'],
        'roundhill': ['roundhill'],
        'global_x': ['global x'],
        'defiance': ['defiance'],
        'first_trust': ['first trust']
    }

    high_yield_etfs = []
    for etf in all_etfs:
        name_lower = etf['name'].lower()
        symbol = etf['symbol']

        # Check if matches known high-yield families
        for family, keywords in family_keywords.items():
            if any(kw in name_lower for kw in keywords):
                high_yield_etfs.append(etf)
                break

        # Pattern matching for YieldMax naming convention
        if symbol.startswith('Y') and len(symbol) <= 5:
            # Likely YieldMax - validate with API
            high_yield_etfs.append(etf)

    # Now validate each ETF for actual dividend data
    return validate_etfs_with_dividend_data(high_yield_etfs)
```

### Phase 2: Multi-Exchange Discovery

FMP supports international exchanges - we should leverage this:

```python
INTERNATIONAL_HIGH_DIVIDEND_EXCHANGES = [
    'LSE',   # London - High dividend culture
    'TSX',   # Toronto - REITs and energy
    'ASX',   # Australia - High dividend culture
    'JSE',   # Johannesburg - Mining dividends
    'XETRA'  # Germany - Solid dividend payers
]
```

### Phase 3: Behavioral Discovery (Smart!)

Instead of hard-coding, discover based on actual dividend behavior:

```python
def discover_consistent_dividend_payers():
    """Find symbols with consistent dividend history (FMP has this data!)."""

    # FMP provides dividend calendar and history
    url = f"https://financialmodelingprep.com/api/v3/stock_dividend_calendar?from=2020-01-01&to=2025-01-01&apikey={FMP_API_KEY}"

    dividend_data = fetch(url)

    # Analyze frequency
    symbols_with_counts = {}
    for div in dividend_data:
        symbol = div['symbol']
        symbols_with_counts[symbol] = symbols_with_counts.get(symbol, 0) + 1

    # Find symbols with 4+ dividends per year (quarterly or better)
    consistent_payers = [
        symbol for symbol, count in symbols_with_counts.items()
        if count >= 16  # 4/year * 4 years = minimum 16 dividends
    ]

    return consistent_payers
```

### Phase 4: New ETF Launch Monitoring

YieldMax and others launch new ETFs regularly. Monitor for these:

```python
def discover_recently_launched_etfs(days_back=180):
    """Find ETFs launched in last N days."""

    all_etfs = discover_all_etfs_from_fmp()

    # FMP provides IPO date in company profile
    recent_etfs = []
    for etf in all_etfs:
        profile_url = f"https://financialmodelingprep.com/api/v3/profile/{etf['symbol']}?apikey={FMP_API_KEY}"
        profile = fetch(profile_url)

        if profile:
            ipo_date = profile[0].get('ipoDate')
            if ipo_date:
                ipo_datetime = datetime.strptime(ipo_date, '%Y-%m-%d')
                if (datetime.now() - ipo_datetime).days <= days_back:
                    recent_etfs.append(etf)

    return recent_etfs
```

### Phase 5: Peer Discovery

If we know JEPI is good, find similar ETFs:

```python
def discover_similar_symbols(reference_symbol, min_correlation=0.7):
    """Find symbols with similar price patterns and dividend behavior."""

    # FMP provides correlation data
    url = f"https://financialmodelingprep.com/api/v3/correlation?symbol={reference_symbol}&apikey={FMP_API_KEY}"

    # This gives you statistically similar instruments
    # Filter for high dividend payers among correlates
```

## Implementation Priority

### Week 1: Quick Wins
1. ✅ Enable FMP advanced screener with multiple criteria
2. ✅ Add sector-specific searches for high-dividend sectors
3. ✅ Replace Yahoo hard-coded lists with FMP ETF list filtering

### Week 2: Smart Discovery
1. ✅ Implement behavioral discovery (consistent dividend history)
2. ✅ Add recently launched ETF monitoring
3. ✅ Enhance validation with actual dividend data checks

### Week 3: International & Advanced
1. ✅ Add international exchange support
2. ✅ Implement peer/correlation discovery
3. ✅ Add fund family pattern analysis

## Success Metrics

**Before:**
- Hard-coded list: ~100 symbols
- Update frequency: Manual
- New symbol discovery: Weeks to months
- Coverage: Limited to what someone remembered to add

**After:**
- Dynamic discovery: 1,000+ symbols meeting criteria
- Update frequency: Every run (daily)
- New symbol discovery: Within 24 hours of launch
- Coverage: Complete market coverage based on objective criteria

## Example: YieldMax Auto-Discovery

Instead of:
```python
high_yield_targets = ['YMAX', 'YMAG', 'YBIT', ...]  # Static, stale
```

Use:
```python
# Get ALL ETFs
all_etfs = discover_all_etfs_from_fmp()

# Filter for YieldMax family dynamically
yieldmax_etfs = [
    etf for etf in all_etfs
    if 'yieldmax' in etf['name'].lower() or
    (etf['symbol'].startswith('Y') and len(etf['symbol']) <= 5 and
     validate_has_dividend_data(etf['symbol']))
]

# Result: Automatically discovers new YieldMax ETFs on launch day!
```

## Cost Benefit Analysis

**Your FMP Ultimate Plan includes:**
- 3,000 requests/minute
- Stock screener (unlimited parameters)
- ETF list endpoint
- Dividend calendar
- Historical dividends
- Company profiles
- Correlation data

**You're currently using:** <20% of available capacity

**Recommendation:** Maximize your Ultimate plan investment by using ALL available discovery endpoints!
