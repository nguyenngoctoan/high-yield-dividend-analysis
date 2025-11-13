# Data Source Tracking System

## Overview

The Data Source Tracking System is a comprehensive solution for discovering and tracking which data sources (FMP, AlphaVantage, Yahoo Finance) have specific data types (AUM, dividends, volume, IV) for each symbol. This system avoids redundant API calls and optimizes data fetching by recording which sources successfully provide data.

## Key Features

- **Smart Source Selection**: Automatically uses the best available source based on historical success
- **Redundancy Avoidance**: Tracks which sources have been checked to prevent duplicate API calls
- **Multi-Source Discovery**: Tries multiple sources in priority order until data is found
- **Persistent Tracking**: Records results in database for future reference
- **Performance Optimization**: In-memory caching with configurable TTL

## Architecture

### Database Schema

#### `raw_data_source_tracking` Table

Tracks which sources have which data types for each symbol:

```sql
CREATE TABLE raw_data_source_tracking (
    symbol VARCHAR(20) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    has_data BOOLEAN DEFAULT false,
    last_checked_at TIMESTAMP WITH TIME ZONE,
    last_successful_fetch_at TIMESTAMP WITH TIME ZONE,
    fetch_attempts INT DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (symbol, data_type, source)
);
```

**Supported Data Types:**
- `aum` - Assets Under Management (for ETFs)
- `dividends` - Dividend payment history
- `volume` - Trading volume data
- `iv` - Implied Volatility (future support)
- `prices` - Historical price data
- `company_info` - Company/ETF metadata

**Supported Sources:**
- `FMP` - Financial Modeling Prep
- `AlphaVantage` - Alpha Vantage API
- `Yahoo` - Yahoo Finance

#### Helper View: `v_data_source_preferences`

Provides quick lookup of preferred sources:

```sql
CREATE VIEW v_data_source_preferences AS
SELECT
    symbol,
    data_type,
    preferred_source,  -- Best source based on priority and success
    available_sources, -- Array of all sources with data
    last_successful_fetch
FROM ...
```

### Helper Functions

#### `get_preferred_source(symbol, data_type)`
Returns the preferred data source for a symbol and data type.

#### `record_data_source_check(symbol, data_type, source, has_data, notes)`
Records the result of checking a data source.

## Data Availability by Source

### AUM (Assets Under Management)

| Source | Available | Notes |
|--------|-----------|-------|
| FMP | ✅ Yes | Via `/stable/etf/info` and metadata endpoints |
| AlphaVantage | ❌ No | Not available in any endpoint |
| Yahoo | ✅ Yes | Via `info.totalAssets` or `info.netAssets` |

**Priority Order**: FMP → Yahoo

### Dividends

| Source | Available | Notes |
|--------|-----------|-------|
| FMP | ✅ Yes | Via `/historical-price-full/stock_dividend/{symbol}` |
| AlphaVantage | ✅ Yes | Via field `7. dividend amount` in TIME_SERIES_DAILY_ADJUSTED |
| Yahoo | ✅ Yes | Via `ticker.dividends` |

**Priority Order**: FMP → Yahoo → AlphaVantage

### Volume

| Source | Available | Notes |
|--------|-----------|-------|
| FMP | ✅ Yes | Included in historical price data |
| AlphaVantage | ✅ Yes | Field `6. volume` in TIME_SERIES_DAILY_ADJUSTED |
| Yahoo | ✅ Yes | Included in historical data |

**Priority Order**: FMP → Yahoo → AlphaVantage

### Implied Volatility (IV)

| Source | Available | Notes |
|--------|-----------|-------|
| FMP | ❌ No | Not currently available |
| AlphaVantage | ❌ No | Not available |
| Yahoo | ⚠️ Partial | Requires options data (future implementation) |

**Priority Order**: Not yet implemented

## Usage

### 1. Running the Migration

First, apply the database migration:

```bash
# If using Supabase CLI
npx supabase migration up create_data_source_tracking

# Or run the SQL file directly
psql -h your-host -d your-db -f migrations/create_data_source_tracking.sql
```

### 2. Using the Data Source Tracker

#### Basic Usage

```python
from lib.utils.data_source_tracker import (
    DataSourceTracker, DataType, DataSource
)

# Initialize tracker
tracker = DataSourceTracker()

# Get preferred source for a symbol
preferred = tracker.get_preferred_source('SPY', DataType.AUM)
if preferred:
    print(f"Use {preferred.value} for SPY AUM")

# Record a check result
tracker.record_check(
    symbol='SPY',
    data_type=DataType.AUM,
    source=DataSource.FMP,
    has_data=True,
    notes='Successfully fetched AUM: $450B'
)

# Get all available sources
sources = tracker.get_available_sources('SPY', DataType.DIVIDENDS)
print(f"Dividend sources: {[s.value for s in sources]}")
```

#### Discovery Pattern

```python
# Discover data across multiple sources automatically
result = tracker.discover_and_record(
    symbol='AAPL',
    data_type=DataType.DIVIDENDS,
    sources_to_try=[DataSource.FMP, DataSource.YAHOO, DataSource.ALPHA_VANTAGE],
    fetch_callbacks={
        DataSource.FMP: lambda s: fmp_client.fetch_dividends(s),
        DataSource.YAHOO: lambda s: yahoo_client.fetch_dividends(s),
        DataSource.ALPHA_VANTAGE: lambda s: av_client.fetch_dividends(s),
    }
)

if result:
    source, data = result
    print(f"Found dividends from {source.value}")
```

### 3. Using the AUM Discovery Processor

```python
from lib.processors.aum_discovery_processor import (
    AUMDiscoveryProcessor, discover_aum, discover_all_etf_aum
)

# Discover AUM for a single symbol
result = discover_aum('SPY')
if result['success']:
    print(f"AUM: ${result['aum']:,.0f} from {result['source']}")

# Discover AUM for all ETFs
summary = discover_all_etf_aum(limit=100)
print(f"Found AUM for {summary['successful']} ETFs")

# Using the processor directly
processor = AUMDiscoveryProcessor()
processor.process_and_store('QQQ', force_rediscover=False, update_prices=True)
```

### 4. Using the Data Discovery Processor

```python
from lib.processors.data_discovery_processor import (
    DataDiscoveryProcessor, discover_dividends, discover_volume, discover_all_data
)

# Discover dividends
result = discover_dividends('AAPL')
if result['success']:
    print(f"Found {result['count']} dividends from {result['source']}")

# Discover volume
result = discover_volume('AAPL')
if result['success']:
    print(f"Volume data available from {result['source']}")

# Discover all data types
results = discover_all_data('AAPL')
for data_type, result in results.items():
    if result['success']:
        print(f"{data_type}: {result['source']}")

# Batch discovery
processor = DataDiscoveryProcessor()
from lib.utils.data_source_tracker import DataType
summary = processor.discover_batch(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    data_types=[DataType.DIVIDENDS, DataType.VOLUME],
    force_rediscover=False
)
```

### 5. Integration with Existing Processors

The existing processors (PriceProcessor, DividendProcessor, CompanyProcessor) can continue to work as before. The new discovery processors complement them by:

1. **Pre-discovery**: Run discovery processors first to identify best sources
2. **Source selection**: Existing processors can query preferred sources before fetching
3. **Result tracking**: Record which sources succeed/fail for future optimization

Example integration:

```python
from lib.processors.price_processor import PriceProcessor
from lib.utils.data_source_tracker import get_tracker, DataType

# Initialize
price_processor = PriceProcessor()
tracker = get_tracker()

# Check preferred source before fetching
symbol = 'AAPL'
preferred = tracker.get_preferred_source(symbol, DataType.PRICES)

if preferred:
    logger.info(f"Using preferred source {preferred.value} for {symbol}")
    # Fetch directly from preferred source
else:
    # Fall back to hybrid fetching
    logger.info(f"No preference found, using hybrid fetch for {symbol}")

# Existing hybrid fetch logic continues to work
prices = price_processor.fetch_prices(symbol, use_hybrid=True)

# Record the result
if prices:
    tracker.record_check(symbol, DataType.PRICES,
                        DataSource(prices['source']), True)
```

## Optimization Strategies

### 1. Periodic Discovery

Run discovery processors periodically to update source preferences:

```bash
# Daily discovery for new symbols
python -c "
from lib.processors.aum_discovery_processor import discover_all_etf_aum
from lib.processors.data_discovery_processor import DataDiscoveryProcessor
from lib.utils.data_source_tracker import DataType

# Discover AUM for ETFs without AUM data
discover_all_etf_aum(limit=None, force_rediscover=False)

# Discover dividends and volume for all symbols
processor = DataDiscoveryProcessor()
processor.discover_all_symbols(
    data_types=[DataType.DIVIDENDS, DataType.VOLUME],
    limit=1000,
    force_rediscover=False
)
"
```

### 2. Selective Re-discovery

Re-discover data for symbols where sources have failed recently:

```sql
-- Find symbols with failed checks in last 7 days
SELECT symbol, data_type, source, notes
FROM raw_data_source_tracking
WHERE has_data = false
  AND last_checked_at > NOW() - INTERVAL '7 days'
ORDER BY last_checked_at DESC;
```

### 3. Cache Management

The tracker includes an in-memory cache with 1-hour TTL:

```python
# Clear cache if needed
tracker.clear_cache()

# Disable cache for a specific lookup
preferred = tracker.get_preferred_source(symbol, data_type, use_cache=False)
```

## Statistics and Monitoring

### Get Tracking Statistics

```python
# Get statistics for a specific data type
stats = tracker.get_statistics(DataType.AUM)
print(stats)

# Output:
# {
#     'stats': [
#         {
#             'source': 'FMP',
#             'total_checks': 1500,
#             'successful': 1200,
#             'unsuccessful': 300,
#             'unique_symbols': 1000
#         },
#         {
#             'source': 'Yahoo',
#             'total_checks': 500,
#             'successful': 450,
#             'unsuccessful': 50,
#             'unique_symbols': 400
#         }
#     ],
#     'count': 2
# }

# Get overall statistics
all_stats = tracker.get_statistics()
```

### SQL Queries for Monitoring

```sql
-- Success rate by source and data type
SELECT
    data_type,
    source,
    COUNT(*) as total_checks,
    COUNT(*) FILTER (WHERE has_data = true) as successful,
    ROUND(100.0 * COUNT(*) FILTER (WHERE has_data = true) / COUNT(*), 2) as success_rate
FROM raw_data_source_tracking
GROUP BY data_type, source
ORDER BY data_type, success_rate DESC;

-- Symbols with multiple sources for a data type
SELECT
    symbol,
    data_type,
    COUNT(*) as source_count,
    array_agg(source) FILTER (WHERE has_data = true) as available_sources
FROM raw_data_source_tracking
WHERE has_data = true
GROUP BY symbol, data_type
HAVING COUNT(*) > 1
ORDER BY source_count DESC;

-- Recent discoveries (last 24 hours)
SELECT
    symbol,
    data_type,
    source,
    last_successful_fetch_at
FROM raw_data_source_tracking
WHERE last_successful_fetch_at > NOW() - INTERVAL '24 hours'
ORDER BY last_successful_fetch_at DESC
LIMIT 100;
```

## Best Practices

1. **Run discovery before bulk operations**: Use discovery processors to identify best sources before running large batch jobs

2. **Respect rate limits**: The discovery process respects existing rate limiters for each source

3. **Monitor success rates**: Regularly check statistics to identify problematic sources or data types

4. **Update stale data**: Re-run discovery for symbols checked more than 30 days ago

5. **Handle edge cases**: Some symbols may not have certain data types (e.g., non-ETFs don't have AUM)

6. **Use force_rediscover sparingly**: Only force rediscovery when you suspect source availability has changed

7. **Batch operations**: Process symbols in batches for better performance

8. **Error handling**: The system gracefully handles API failures and records them for analysis

## Troubleshooting

### No preferred source found

If `get_preferred_source()` returns `None`:
1. Run discovery for that symbol and data type
2. Check if the data type is available for that symbol (e.g., AUM only for ETFs)
3. Verify API keys are configured correctly

### Discovery always returns None

1. Check API connectivity and rate limits
2. Verify the symbol exists in the respective APIs
3. Check logs for specific error messages
4. Try with `force_rediscover=True` to bypass cache

### Performance issues

1. Use batch operations instead of single symbol processing
2. Enable caching (default)
3. Limit discovery scope with `limit` parameter
4. Run discovery during off-peak hours

## Future Enhancements

1. **IV (Implied Volatility) Support**: Implement options data fetching for IV calculation
2. **Machine Learning**: Predict best source based on symbol characteristics
3. **Real-time Monitoring**: Dashboard for tracking source health and performance
4. **Automatic Failover**: Dynamically adjust source priority based on recent failures
5. **Cost Optimization**: Track API costs per source and optimize accordingly

## Related Files

- Migration: `migrations/create_data_source_tracking.sql`
- Tracker Module: `lib/utils/data_source_tracker.py`
- AUM Discovery: `lib/processors/aum_discovery_processor.py`
- Data Discovery: `lib/processors/data_discovery_processor.py`
- Data Sources: `lib/data_sources/fmp_client.py`, `yahoo_client.py`, `alpha_vantage_client.py`

## Support

For issues or questions about the Data Source Tracking System:
1. Check the logs for error messages
2. Review statistics to identify patterns
3. Consult the source code and inline documentation
4. Test with a small batch before large-scale operations
