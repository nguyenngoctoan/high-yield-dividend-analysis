# ETF Scrapers Package

Unified collection of ETF data scrapers with shared utilities for scraping high-yield, options income, and covered call ETF data.

## Overview

This package contains scrapers for **8 ETF providers** covering **200+ ETFs** focused on:
- Covered call strategies
- Options income generation
- High yield dividend distributions
- Enhanced income strategies

All data is stored in PostgreSQL tables following the `raw_etfs_{provider}` naming convention.

## Package Structure

```
scripts/scrapers/etfs/
├── __init__.py                 # Package exports
├── common.py                   # Shared utilities and base classes
├── README.md                   # This file
│
├── yieldmax/                   # YieldMax ETFs (57 funds)
│   ├── scrape_yieldmax_all.py
│   └── README.md
│
├── roundhill/                  # Roundhill Investments (15+ funds)
│   ├── scrape_roundhill_all.py
│   └── README.md
│
├── neos/                       # Neos Investments (10+ funds)
│   ├── scrape_neos_all.py
│   └── README.md
│
├── kurv/                       # Kurv Investment Management (12+ funds)
│   ├── scrape_kurv_all.py
│   └── README.md
│
├── graniteshares/              # GraniteShares (25+ funds)
│   ├── scrape_graniteshares_all.py
│   └── README.md
│
├── defiance/                   # Defiance ETFs (20+ funds)
│   ├── scrape_defiance_all.py
│   └── README.md
│
├── globalx/                    # Global X Canada (30+ funds)
│   ├── scrape_globalx_all.py
│   ├── __init__.py
│   └── README.md
│
└── purpose/                    # Purpose Investments (40+ funds)
    ├── scrape_purpose_all.py
    └── README.md
```

## Shared Utilities (`common.py`)

The `common.py` module provides reusable functionality for all scrapers:

### Logging

```python
from scripts.scrapers.etfs.common import setup_logging

logger = setup_logging(__name__)
```

### Chrome WebDriver Setup

```python
from scripts.scrapers.etfs.common import get_chrome_options, create_chrome_driver

# Get standardized Chrome options
chrome_options = get_chrome_options()

# Create WebDriver with options
driver = create_chrome_driver(chrome_options, logger)
```

### Safe Element Finding

```python
from selenium.webdriver.common.by import By
from scripts.scrapers.etfs.common import safe_find_element, safe_find_elements

# Find single element
element = safe_find_element(driver, By.CSS_SELECTOR, '.ticker', logger, timeout=10)

# Find multiple elements
elements = safe_find_elements(driver, By.CSS_SELECTOR, '.holdings', logger, timeout=10)
```

### Database Operations

```python
from scripts.scrapers.etfs.common import save_to_database

data = {
    'ticker': 'TSLY',
    'fund_name': 'YieldMax TSLA Option Income Strategy ETF',
    'url': 'https://yieldmaxetfs.com/our-etfs/tsly/',
    'nav': '15.23',
    'distributions': {...}
}

success = save_to_database('raw_etfs_yieldmax', data, logger)
```

### Retry Logic

```python
from scripts.scrapers.etfs.common import scrape_with_retry

def scrape_page():
    # Your scraping logic
    return data

result = scrape_with_retry(scrape_page, max_retries=3, retry_delay=5, logger=logger)
```

### Base Scraper Class

```python
from scripts.scrapers.etfs.common import BaseETFScraper

class MyETFScraper(BaseETFScraper):
    def __init__(self, ticker, fund_name, url, logger=None):
        super().__init__(ticker, fund_name, url, 'raw_etfs_provider', logger)

    def scrape_data(self):
        # Implement your scraping logic
        return {'ticker': self.ticker, 'fund_name': self.fund_name, ...}

# Usage
scraper = MyETFScraper('TICKER', 'Fund Name', 'https://...', logger)
success = scraper.run()
```

### Batch Scraping

```python
from scripts.scrapers.etfs.common import batch_scrape_etfs

etf_configs = {
    'TICKER1': {'name': 'Fund 1', 'url': 'https://...'},
    'TICKER2': {'name': 'Fund 2', 'url': 'https://...'},
}

stats = batch_scrape_etfs(
    etf_configs=etf_configs,
    scraper_class=MyETFScraper,
    table_name='raw_etfs_provider',
    tickers=['TICKER1'],  # Optional: specific tickers
    delay_between_requests=2,
    logger=logger
)

print(f"Success: {stats['success']}/{stats['total']}")
```

## Database Tables

All ETF data is stored in PostgreSQL with the following schema:

### Table Naming Convention

```
raw_etfs_{provider}
```

Examples:
- `raw_etfs_yieldmax`
- `raw_etfs_roundhill`
- `raw_etfs_neos`
- `raw_etfs_kurv`
- `raw_etfs_graniteshares`
- `raw_etfs_defiance`
- `raw_etfs_globalx`
- `raw_etfs_purpose`

### Latest Data Views

Each table has a corresponding view for latest data:

```
v_{provider}_latest
```

Examples:
- `v_yieldmax_latest`
- `v_roundhill_latest`

### Common Columns

All tables include:
- `id` (bigserial, primary key)
- `ticker` (varchar, ETF ticker symbol)
- `fund_name` (text, full fund name)
- `url` (text, source URL)
- `scraped_at` (timestamptz, when data was scraped)
- `created_at` (timestamptz, record creation time)
- `updated_at` (timestamptz, last update time)
- Provider-specific JSON columns for flexible data storage

## Running Scrapers

### Individual Scraper

```bash
# YieldMax - scrape all 57 ETFs
python3 scripts/scrapers/etfs/yieldmax/scrape_yieldmax_all.py

# YieldMax - scrape specific ticker
python3 scripts/scrapers/etfs/yieldmax/scrape_yieldmax_all.py --ticker TSLY

# Roundhill - scrape all ETFs
python3 scripts/scrapers/etfs/roundhill/scrape_roundhill_all.py

# Purpose - scrape all ETFs
python3 scripts/scrapers/etfs/purpose/scrape_purpose_all.py
```

### Common Command-Line Options

Most scrapers support:
- `--ticker SYMBOL` - Scrape specific ticker
- `--delay SECONDS` - Delay between requests (default: 2)
- `--help` - Show help message

## Data Coverage

| Provider | ETFs | Focus Area | Table |
|----------|------|------------|-------|
| **YieldMax** | 57 | Single-stock covered calls | `raw_etfs_yieldmax` |
| **Roundhill** | 15+ | Options income strategies | `raw_etfs_roundhill` |
| **Neos** | 10+ | Enhanced income ETFs | `raw_etfs_neos` |
| **Kurv** | 12+ | Yield enhancement | `raw_etfs_kurv` |
| **GraniteShares** | 25+ | Leveraged income | `raw_etfs_graniteshares` |
| **Defiance** | 20+ | Thematic income | `raw_etfs_defiance` |
| **Global X Canada** | 30+ | Canadian covered calls | `raw_etfs_globalx` |
| **Purpose** | 40+ | Monthly income, Yield Shares | `raw_etfs_purpose` |
| **TOTAL** | **200+** | High-yield ETFs | 8 tables |

## Requirements

### Python Dependencies

```bash
pip install selenium beautifulsoup4 supabase-py
```

### System Requirements

- **Chrome/Chromium**: For Selenium webdriver
- **ChromeDriver**: Matching Chrome version
- **PostgreSQL**: Via Supabase

### Environment Variables

```bash
# Supabase (required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Chrome/ChromeDriver paths (optional, has defaults)
CHROME_BIN=/usr/bin/chromium
CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

## Development Guidelines

### Creating a New Scraper

1. **Create provider directory**:
   ```bash
   mkdir scripts/scrapers/etfs/newprovider
   ```

2. **Extend BaseETFScraper**:
   ```python
   from scripts.scrapers.etfs.common import BaseETFScraper, setup_logging

   class NewProviderScraper(BaseETFScraper):
       def __init__(self, ticker, fund_name, url, logger=None):
           super().__init__(ticker, fund_name, url, 'raw_etfs_newprovider', logger)

       def scrape_data(self):
           # Implement scraping logic
           pass
   ```

3. **Use shared utilities**:
   - `create_chrome_driver()` for WebDriver
   - `safe_find_element()` for element finding
   - `scrape_with_retry()` for retry logic
   - `batch_scrape_etfs()` for batch processing

4. **Create database migration**:
   ```sql
   -- supabase/migrations/YYYYMMDD_add_newprovider_etf_data.sql
   CREATE TABLE raw_etfs_newprovider (...);
   CREATE VIEW v_newprovider_latest AS ...;
   ```

### Best Practices

- **Use shared utilities** - Don't duplicate code
- **Handle errors gracefully** - Use try/except and logging
- **Implement rate limiting** - Respect target websites
- **Log everything** - Use appropriate log levels (INFO, WARNING, ERROR)
- **Store raw JSON** - Use JSONB columns for flexible schema
- **Create views** - Make latest data easily accessible
- **Document your scraper** - Add README.md to provider folder

## Troubleshooting

### Chrome/ChromeDriver Issues

```bash
# Check Chrome version
google-chrome --version

# Check ChromeDriver version
chromedriver --version

# Install matching ChromeDriver
# Download from: https://chromedriver.chromium.org/
```

### Import Errors

If you get `ModuleNotFoundError`:

```python
# Scrapers should have this at the top:
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
```

### Database Connection

```python
from supabase_helpers import get_supabase_client

# Test connection
client = get_supabase_client()
result = client.table('raw_etfs_yieldmax').select('count').limit(1).execute()
print(f"Connection successful: {result}")
```

## Maintenance

### Update Schedules

- **Weekly**: Run all scrapers to get latest data
- **Monthly**: Review for new ETFs added by providers
- **Quarterly**: Update scraper logic if website changes

### Monitoring

Check data freshness:

```sql
-- Check latest scrape times
SELECT
    'yieldmax' as provider,
    MAX(scraped_at) as latest_scrape,
    COUNT(*) as total_records
FROM raw_etfs_yieldmax
UNION ALL
SELECT 'roundhill', MAX(scraped_at), COUNT(*) FROM raw_etfs_roundhill
-- ... repeat for all providers
ORDER BY provider;
```

## Contributing

When adding new scrapers or updating existing ones:

1. Use shared utilities from `common.py`
2. Follow existing naming conventions
3. Add comprehensive logging
4. Create database migrations
5. Update this README
6. Test thoroughly before committing

## License

Part of the high-yield-dividend-analysis project.

## Support

For issues or questions:
- Check provider-specific README in each subdirectory
- Review `common.py` for utility functions
- Check database migrations in `supabase/migrations/`
