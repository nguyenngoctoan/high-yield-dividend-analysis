# Archived Dividend Scraper Scripts

This folder contains old/deprecated dividend scraping scripts that have been superseded by newer versions.

## Archived Files

### `scrape_dividend_calendar_supabase.py`
- **Status**: ❌ Deprecated (Selenium-based)
- **Reason**: Requires Chrome/Selenium which is not available on this system
- **Replaced by**: `scrape_dividend_calendar_requests.py` (uses requests + BeautifulSoup only)
- **Date Archived**: October 9, 2025

## Current Working Scripts

The following scripts are actively maintained in the project root:

1. **`scrape_yieldmax.py`** - Dynamic multi-article YieldMax scraper (RECOMMENDED)
   - Auto-discovers articles from Globe Newswire
   - Processes multiple articles in one run
   - No Chrome/browser dependencies

2. **`scrape_dividend_calendar_requests.py`** - Core scraping functions
   - Used by scrape_yieldmax.py
   - Requests + BeautifulSoup only (no Selenium)
   - Saves to `dividend_payments` table

## Migration Notes

If you need to reference the old Selenium-based scraper:
- The table parsing logic is similar
- Main difference: Selenium WebDriver vs requests.get()
- Database schema updated to use `dividend_payments` table instead of `dividend_calendar` view

## See Also

- `/archive_postgresql/scrape_dividend_calendar.py` - Original PostgreSQL version (pre-Supabase migration)
