# update_stock.py Refactoring Plan

## Overview

**Current State**: 3,821 lines in one file
**Target State**: Modular architecture with ~10-12 focused modules

## Problems with Current Architecture

1. **Monolithic Design**: Everything in one 3,821-line file
2. **Mixed Concerns**: Discovery, validation, fetching, processing intertwined
3. **Hard to Test**: Can't unit test individual components
4. **Hard to Maintain**: Finding specific logic requires scrolling through thousands of lines
5. **Code Duplication**: Similar patterns repeated across data sources
6. **Poor Separation**: Data sources (FMP, Yahoo, AV) mixed with business logic

## Proposed Architecture

```
/lib                                 # New library directory
  /data_sources                      # Data source clients
    - __init__.py
    - base_client.py                 # Base class with retry, rate limiting
    - fmp_client.py                  # FMP API interactions (~300 lines)
    - yahoo_client.py                # Yahoo Finance (yfinance) (~200 lines)
    - alpha_vantage_client.py        # Alpha Vantage API (~200 lines)

  /discovery                         # Symbol discovery & validation
    - __init__.py
    - symbol_discovery.py            # Find symbols from all sources (~400 lines)
    - symbol_validator.py            # Validate symbols (~300 lines)

  /processors                        # Data processing logic
    - __init__.py
    - price_processor.py             # Price fetching/processing (~400 lines)
    - dividend_processor.py          # Dividend fetching/processing (~400 lines)
    - company_processor.py           # Company info, AUM, metadata (~200 lines)

  /core                              # Core utilities
    - __init__.py
    - config.py                      # Configuration, env vars, constants (~100 lines)
    - models.py                      # Data models/schemas (~100 lines)
    - rate_limiters.py               # Rate limiting (Semaphore) (~50 lines)
    - database.py                    # Alias to supabase_helpers.py

update_stock.py                      # Main orchestrator (~200-300 lines)
```

## Module Responsibilities

### 1. lib/core/config.py
**Purpose**: Centralized configuration
**Content**:
- Environment variable loading
- API keys
- Constants (ALLOWED_EXCHANGES, batch sizes, etc.)
- Feature flags (USE_HYBRID_DIVIDENDS, FALLBACK_TO_YAHOO, etc.)
- Logging configuration

**Benefits**:
- Single source of truth for configuration
- Easy to modify settings without touching logic
- Cleaner env var management

### 2. lib/core/rate_limiters.py
**Purpose**: Rate limiting utilities
**Content**:
- Semaphore classes for FMP, Yahoo, Alpha Vantage
- Rate limiter initialization
- Shared rate limiting logic

**Benefits**:
- Centralized rate limiting
- Easy to adjust rate limits
- Prevents API throttling

### 3. lib/core/models.py
**Purpose**: Data models and schemas
**Content**:
- StockPrice dataclass
- Dividend dataclass
- CompanyInfo dataclass
- ValidationResult dataclass

**Benefits**:
- Type safety
- Clear data structures
- Easy serialization/deserialization

### 4. lib/data_sources/base_client.py
**Purpose**: Base class for all data source clients
**Content**:
- Retry logic (fetch_with_adaptive_retry)
- Error handling patterns
- Response parsing utilities
- Common HTTP utilities

**Benefits**:
- DRY (Don't Repeat Yourself)
- Consistent error handling
- Easy to add new data sources

### 5. lib/data_sources/fmp_client.py
**Purpose**: FMP API client
**Content**:
- `fetch_prices(symbol, from_date=None)`
- `fetch_dividends(symbol, from_date=None)`
- `fetch_future_dividends(from_date, to_date)`
- `fetch_etf_metadata(symbol)`
- `fetch_company_profile(symbol)`
- `discover_all_symbols()`
- `discover_etfs()`

**Benefits**:
- All FMP logic in one place
- Easy to test FMP integration
- Clear API interface

### 6. lib/data_sources/yahoo_client.py
**Purpose**: Yahoo Finance client
**Content**:
- `fetch_prices(symbol)` (with AUM)
- `fetch_dividends(symbol)`
- `fetch_company_info(symbol)`
- Uses yfinance library

**Benefits**:
- Encapsulates yfinance usage
- Handles AUM extraction
- Fallback data source logic

### 7. lib/data_sources/alpha_vantage_client.py
**Purpose**: Alpha Vantage API client
**Content**:
- `fetch_prices(symbol)`
- `fetch_dividends(symbol)`
- Secondary data source implementation

**Benefits**:
- Alternative data source
- Redundancy for critical data

### 8. lib/discovery/symbol_discovery.py
**Purpose**: Symbol discovery from all sources
**Content**:
- `discover_from_fmp()`
- `discover_from_nasdaq()`
- `discover_etfs()`
- `discover_dividend_screeners()`
- `discover_all()` - orchestrates all sources
- Filtering by ALLOWED_EXCHANGES

**Benefits**:
- Centralized discovery logic
- Easy to add new sources
- Clear discovery workflow

### 9. lib/discovery/symbol_validator.py
**Purpose**: Symbol validation logic
**Content**:
- `validate_symbol(symbol)` - complete validation
- `check_price_activity(symbol)` - 7-day price check
- `check_dividend_history(symbol)` - 365-day dividend check
- `should_exclude(symbol)` - exclusion logic

**Benefits**:
- Reusable validation
- Clear validation criteria
- Easy to modify validation rules

### 10. lib/processors/price_processor.py
**Purpose**: Price data processing
**Content**:
- `update_prices_for_symbols(symbols)` - main entry point
- `process_symbol_prices(symbol)` - single symbol
- `fetch_hybrid_prices(symbol)` - multi-source fetch
- Database insertion logic

**Benefits**:
- Focused on price processing
- Hybrid approach (FMP → AV → Yahoo)
- Clean separation from fetching

### 11. lib/processors/dividend_processor.py
**Purpose**: Dividend data processing
**Content**:
- `update_dividends_for_symbols(symbols)`
- `process_symbol_dividends(symbol)`
- `fetch_hybrid_dividends(symbol)`
- Database insertion logic

**Benefits**:
- Focused on dividend processing
- Similar to price processor pattern
- Consistent architecture

### 12. lib/processors/company_processor.py
**Purpose**: Company information processing
**Content**:
- `fetch_company_info(symbol)`
- `fetch_etf_metadata(symbol)`
- `extract_aum(symbol)`
- Company name, exchange, sector extraction

**Benefits**:
- Centralized company data logic
- ETF-specific processing
- Metadata management

### 13. update_stock.py (Refactored)
**Purpose**: Orchestration and CLI
**Content**:
- Argument parsing
- Mode selection (discover, prices, dividends)
- High-level workflow coordination
- Logging setup
- Error handling
- Status reporting

**Example Structure**:
```python
#!/usr/bin/env python3
import argparse
import logging
from lib.core.config import setup_logging, get_config
from lib.discovery.symbol_discovery import discover_all
from lib.discovery.symbol_validator import validate_symbols
from lib.processors.price_processor import update_prices_for_symbols
from lib.processors.dividend_processor import update_dividends_for_symbols

def main():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['discover', 'prices', 'dividends'])
    args = parser.parse_args()

    # Setup
    setup_logging()
    logger = logging.getLogger(__name__)

    # Execute based on mode
    if args.mode == 'discover':
        symbols = discover_all()
        valid_symbols = validate_symbols(symbols)
        # ... save to database

    elif args.mode == 'prices':
        symbols = get_all_symbols_from_db()
        update_prices_for_symbols(symbols)

    elif args.mode == 'dividends':
        symbols = get_all_symbols_from_db()
        update_dividends_for_symbols(symbols)

if __name__ == '__main__':
    main()
```

## Migration Strategy

### Phase 1: Core Infrastructure (Week 1)
1. ✅ Create directory structure
2. Create `lib/core/config.py` - Move all constants, env vars
3. Create `lib/core/rate_limiters.py` - Move Semaphore classes
4. Create `lib/core/models.py` - Define data classes
5. Test core modules independently

### Phase 2: Data Source Clients (Week 2)
1. Create `lib/data_sources/base_client.py` - Base class with retry logic
2. Create `lib/data_sources/fmp_client.py` - Extract all FMP functions
3. Create `lib/data_sources/yahoo_client.py` - Extract Yahoo functions
4. Create `lib/data_sources/alpha_vantage_client.py` - Extract AV functions
5. Test each client with real API calls

### Phase 3: Discovery Module (Week 3)
1. Create `lib/discovery/symbol_discovery.py` - Move all discovery functions
2. Create `lib/discovery/symbol_validator.py` - Move validation logic
3. Update discovery to use data source clients
4. Test discovery workflow end-to-end

### Phase 4: Processors (Week 4)
1. Create `lib/processors/price_processor.py` - Move price processing
2. Create `lib/processors/dividend_processor.py` - Move dividend processing
3. Create `lib/processors/company_processor.py` - Move company processing
4. Test each processor independently

### Phase 5: Main Orchestrator (Week 5)
1. Refactor `update_stock.py` to use new modules
2. Maintain CLI interface (backward compatible)
3. Update imports throughout
4. Integration testing

### Phase 6: Cleanup & Documentation (Week 6)
1. Archive old `update_stock.py` as `update_stock_v1.py`
2. Update documentation
3. Update `daily_update.sh` if needed
4. Performance testing
5. Deploy to production

## Testing Strategy

### Unit Tests
- Test each module independently
- Mock external API calls
- Test error handling
- Test edge cases

### Integration Tests
- Test data source clients with real APIs (rate-limited)
- Test full workflow (discover → validate → update)
- Test database operations

### Regression Tests
- Ensure refactored version produces same results as original
- Compare outputs on sample data set
- Validate no functionality lost

## Benefits of Refactoring

### 1. Maintainability
- **Before**: Finding FMP price logic = scrolling through 3,821 lines
- **After**: Open `lib/data_sources/fmp_client.py` (~300 lines)

### 2. Testability
- **Before**: Can't unit test without running entire script
- **After**: Test each module independently with mocks

### 3. Reusability
- **Before**: Logic tied to update_stock.py
- **After**: Import clients in any script (e.g., `refresh_company_data.py`)

### 4. Extensibility
- **Before**: Adding new data source = editing 3,821-line file
- **After**: Create new file in `lib/data_sources/`, implement base class

### 5. Collaboration
- **Before**: Merge conflicts on single large file
- **After**: Work on separate modules without conflicts

### 6. Performance
- **Before**: Hard to optimize specific parts
- **After**: Profile and optimize individual modules

### 7. Documentation
- **Before**: One massive docstring
- **After**: Each module has focused documentation

## Example: Before vs After

### Before (Current)
```python
# In update_stock.py (line 1500-1600)
def fetch_fmp_prices(symbol, from_date=None):
    # 100 lines of FMP logic mixed with retry logic, error handling, etc.

# In update_stock.py (line 2500-2600)
def process_symbol_prices_hybrid(symbol, max_date=None):
    # 100 lines of processing logic that calls fetch_fmp_prices
```

### After (Refactored)
```python
# In lib/data_sources/fmp_client.py
class FMPClient:
    def fetch_prices(self, symbol, from_date=None):
        # 30 lines of clean FMP-specific logic
        return self._fetch_with_retry(url)

# In lib/processors/price_processor.py
class PriceProcessor:
    def __init__(self):
        self.fmp = FMPClient()
        self.yahoo = YahooClient()

    def process_symbol(self, symbol):
        # Try FMP first
        prices = self.fmp.fetch_prices(symbol)
        if not prices:
            prices = self.yahoo.fetch_prices(symbol)
        return self._save_to_database(prices)
```

## Risk Mitigation

### Risks
1. **Breaking Changes**: Refactoring might break existing functionality
2. **Time Investment**: Significant development time required
3. **Testing Overhead**: Need comprehensive tests
4. **Learning Curve**: Team needs to learn new structure

### Mitigation
1. **Keep Original**: Archive `update_stock.py` as `update_stock_v1.py`
2. **Gradual Migration**: Migrate one module at a time
3. **Backward Compatibility**: Keep CLI interface identical
4. **Parallel Running**: Run both versions, compare outputs
5. **Rollback Plan**: Easy to revert if issues arise

## Success Criteria

- ✅ All tests pass
- ✅ Same CLI interface (backward compatible)
- ✅ Same output as original script
- ✅ No performance degradation
- ✅ Each module < 500 lines
- ✅ 80%+ code coverage
- ✅ Documentation updated
- ✅ Team training completed

## Timeline

- **Week 1-2**: Core + Data Sources (Foundation)
- **Week 3-4**: Discovery + Processors (Business Logic)
- **Week 5**: Integration (Orchestration)
- **Week 6**: Testing + Documentation (Polish)

**Total**: ~6 weeks for complete refactoring

## Next Steps

1. Review this plan with team
2. Get approval for timeline
3. Start with Phase 1 (Core Infrastructure)
4. Create feature branch: `refactor/modular-architecture`
5. Regular code reviews after each phase
6. Update this document as we progress

---

**Status**: 📋 Planning Complete
**Next**: 🚀 Begin Implementation (Phase 1)
**Owner**: Development Team
**Target**: Q4 2025
