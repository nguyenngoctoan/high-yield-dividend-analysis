#!/usr/bin/env python3
"""
Snowball Analytics Dividend Calendar Scraper
Fetches dividend data from Snowball Analytics dividend calendar using Selenium.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import time

# Add paths to import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SnowballDividendScraper:
    # Map category names to URL slugs
    CATEGORIES = {
        'us-popular-div': 'us Popular dividend stocks',
        'us-popular-div-funds': 'us Popular dividend funds',
        'sp500': 'us S&P 500 stocks',
        'nyse': 'us NYSE popular stocks',
        'nasdaq': 'us NASDAQ popular stocks',
        'lse': 'LSE stocks',
        'tsx': 'TSE/TSX stocks',
        'asx': 'ASX All Ordinaries'
    }

    def __init__(self, year=None, month=None, category='us-popular-div', scrape_all=False):
        """
        Initialize the Snowball dividend scraper

        Args:
            year: Year to fetch (default: current year)
            month: Month to fetch (1-12, default: all months)
            category: Category to scrape (default: us-popular-div)
            scrape_all: If True, scrape all categories
        """
        self.base_url = "https://snowball-analytics.com/calendars/dividend-calendar"
        self.category = category
        self.scrape_all = scrape_all
        self.year = year or datetime.now().year
        self.month = month  # None means all months

        if not scrape_all:
            self.url = f"{self.base_url}/{category}"
        else:
            self.url = None  # Will iterate through all categories

    def scrape_dividends(self):
        """Scrape dividend data from Snowball Analytics using Selenium"""
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        # Set binary location (for Docker container with Chromium)
        chrome_binary = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
        if os.path.exists(chrome_binary):
            chrome_options.binary_location = chrome_binary

        driver = None
        try:
            logger.info("🌐 Starting browser...")
            print("🌐 Starting browser...")

            # Use ChromeDriver path from environment if available
            chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
            if os.path.exists(chromedriver_path):
                from selenium.webdriver.chrome.service import Service
                service = Service(executable_path=chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.url)

            # Wait for page to load
            logger.info("⏳ Waiting for page to load...")
            print("⏳ Waiting for page to load...")
            time.sleep(8)  # Longer wait for React to hydrate

            logger.info(f"📅 Scraping dividend calendar for year {self.year}")
            print(f"📅 Scraping dividend calendar for year {self.year}")

            # Parse the dividend table
            logger.info("📊 Parsing dividend table...")
            print("📊 Parsing dividend table...")

            records = self.parse_dividend_table(driver, category_name=self.CATEGORIES.get(self.category, self.category))

            return records

        except Exception as e:
            logger.error(f"❌ Error scraping Snowball Analytics: {e}")
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if driver:
                driver.quit()
                logger.info("🔚 Browser closed")

    def parse_dividend_table(self, driver, category_name='Snowball Analytics'):
        """Parse the dividend calendar table"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # Wait for table to load - Snowball uses various table structures
            wait = WebDriverWait(driver, 20)

            # Try to find table rows
            time.sleep(3)  # Additional wait for dynamic content

            # Find all table rows (try different selectors)
            table_selectors = [
                "table tbody tr",
                "div[role='table'] div[role='row']",
                ".dividend-row",
                "[data-testid='dividend-row']"
            ]

            table_rows = []
            for selector in table_selectors:
                try:
                    rows = driver.find_elements(By.CSS_SELECTOR, selector)
                    if rows and len(rows) > 0:
                        table_rows = rows
                        logger.info(f"✅ Found {len(rows)} rows using selector: {selector}")
                        break
                except:
                    continue

            if not table_rows:
                logger.warning("⚠️  Could not find dividend table rows")
                print("⚠️  Could not find dividend table rows")

                # Debug: save page source
                with open('/tmp/snowball_page.html', 'w') as f:
                    f.write(driver.page_source)
                logger.info("📄 Saved page source to /tmp/snowball_page.html for debugging")

                return []

            logger.info(f"📋 Found {len(table_rows)} dividend records")
            print(f"📋 Found {len(table_rows)} dividend records")

            records = []
            for idx, row in enumerate(table_rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")

                    # Debug first few rows
                    if idx < 2:
                        cell_texts = [cell.text.strip() for cell in cells]
                        logger.info(f"  Sample row {idx}: {len(cells)} cells - {cell_texts[:5]}")

                    if len(cells) >= 5:  # Minimum expected columns
                        # Snowball columns: Symbol+Company, Ex-Date, Payment Date, Amount, Yield
                        # Extract symbol from first cell (format: "Company Name\nSYMBOL")
                        cell0_text = cells[0].text.strip()
                        symbol = ''
                        company_name = ''
                        if '\n' in cell0_text:
                            parts = cell0_text.split('\n')
                            company_name = parts[0].strip()
                            symbol = parts[1].strip() if len(parts) > 1 else ''
                        else:
                            symbol = cell0_text

                        # Parse dates (format: "Nov 3, 25\n8 days ago")
                        def parse_snowball_date(date_text):
                            if not date_text:
                                return None
                            # Extract just the date part before newline
                            date_part = date_text.split('\n')[0].strip()
                            try:
                                # Parse "Nov 3, 25" format to YYYY-MM-DD
                                from datetime import datetime
                                parsed_date = datetime.strptime(date_part, '%b %d, %y')
                                return parsed_date.strftime('%Y-%m-%d')
                            except:
                                return None

                        ex_date_text = cells[1].text.strip() if len(cells) > 1 else ''
                        payment_date_text = cells[2].text.strip() if len(cells) > 2 else ''

                        record = {
                            'symbol': symbol,
                            'company_name': company_name,
                            'ex_date': parse_snowball_date(ex_date_text),
                            'payment_date': parse_snowball_date(payment_date_text),
                            'amount': cells[3].text.strip().replace('$', '').replace(',', '') if len(cells) > 3 else None,
                            'dividend_yield': cells[4].text.strip().replace('%', '') if len(cells) > 4 else None,
                            'frequency': cells[5].text.strip() if len(cells) > 5 else None,
                            'source': category_name
                        }

                        # Only add records with valid symbol and ex_date
                        if record['symbol'] and record['ex_date']:
                            records.append(record)

                except Exception as e:
                    logger.warning(f"⚠️  Error parsing row {idx}: {e}")
                    continue

            logger.info(f"✅ Successfully parsed {len(records)} valid dividend records")
            print(f"✅ Successfully parsed {len(records)} valid dividend records")
            return records

        except Exception as e:
            logger.error(f"❌ Error parsing table: {e}")
            print(f"❌ Error parsing table: {e}")
            import traceback
            traceback.print_exc()
            return []

    def save_to_database(self, records):
        """
        Save dividend records to raw_dividends_snowball table
        """
        if not records:
            return 0

        logger.info(f"💾 Saving {len(records)} dividend records to database...")
        print(f"💾 Saving {len(records)} dividend records to database...")

        try:
            from dotenv import load_dotenv
            from supabase import create_client

            load_dotenv()
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            supabase = create_client(url, key)

            # Prepare records for database
            db_records = []
            for record in records:
                if record:  # Skip None records
                    # Parse amount
                    amount = record.get('amount')
                    if amount and amount.replace('.', '').replace('-', '').isdigit():
                        amount = float(amount)
                    else:
                        amount = None

                    # Parse yield
                    dividend_yield = record.get('dividend_yield')
                    if dividend_yield and dividend_yield.replace('.', '').replace('-', '').isdigit():
                        dividend_yield = float(dividend_yield)
                    else:
                        dividend_yield = None

                    # Truncate symbol if too long
                    symbol = record['symbol'][:20] if record['symbol'] else ''

                    # Skip if symbol is too long (likely parsing error)
                    if len(record['symbol']) > 20:
                        logger.warning(f"⚠️  Skipping record with long symbol: {record['symbol']}")
                        continue

                    db_record = {
                        'symbol': symbol,
                        'company_name': record.get('company_name'),
                        'ex_date': record.get('ex_date') if record.get('ex_date') else None,
                        'payment_date': record.get('payment_date') if record.get('payment_date') else None,
                        'amount': amount,
                        'dividend_yield': dividend_yield,
                        'frequency': record.get('frequency'),
                        'source': record.get('source')
                    }
                    db_records.append(db_record)

            # Batch upsert with conflict resolution on symbol + ex_date
            batch_size = 1000
            saved_count = 0

            for i in range(0, len(db_records), batch_size):
                batch = db_records[i:i + batch_size]
                result = supabase.table('raw_dividends_snowball').upsert(
                    batch,
                    on_conflict='symbol,ex_date'
                ).execute()

                batch_saved = len(result.data) if result.data else 0
                saved_count += batch_saved

            logger.info(f"✅ Saved {saved_count} records to raw_dividends_snowball")
            print(f"✅ Saved {saved_count} records to database")

            return saved_count

        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            print(f"❌ Database error: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def run(self):
        """Main scraping workflow"""
        try:
            print(f"🎯 Snowball Analytics Dividend Scraper")
            print("=" * 80)
            print(f"📅 Year: {self.year}")
            if self.month:
                print(f"📆 Month: {self.month}")

            if self.scrape_all:
                print(f"📊 Scraping ALL categories (excluding us-popular-div, us-popular-div-funds)")
                # Exclude 'us-popular-div' and 'us-popular-div-funds' when scraping all to avoid overwriting other sources
                exclude_categories = ['us-popular-div', 'us-popular-div-funds']
                categories_to_scrape = [k for k in self.CATEGORIES.keys() if k not in exclude_categories]
            else:
                print(f"📊 Category: {self.CATEGORIES.get(self.category, self.category)}")
                categories_to_scrape = [self.category]

            print("=" * 80)

            total_saved = 0
            all_records = []

            for cat in categories_to_scrape:
                self.url = f"{self.base_url}/{cat}"
                logger.info(f"\n📂 Scraping category: {self.CATEGORIES.get(cat, cat)}")
                print(f"\n📂 Scraping category: {self.CATEGORIES.get(cat, cat)}")

                # Scrape dividends for this category
                records = self.scrape_dividends()

                if records:
                    # Save to database
                    saved_count = self.save_to_database(records)
                    total_saved += saved_count
                    all_records.extend(records)

                    print(f"  ✅ {len(records)} records scraped, {saved_count} saved")

                # Brief pause between categories
                if len(categories_to_scrape) > 1:
                    time.sleep(2)

            # Summary
            print(f"\n" + "=" * 80)
            print(f"🎉 Snowball Analytics Scraping Complete!")
            print(f"📊 Results Summary:")
            print(f"  • Categories scraped: {len(categories_to_scrape)}")
            print(f"  • Total dividend records: {len(all_records)}")
            print(f"  • Records saved to database: {total_saved}")
            print(f"  • Unique symbols: {len(set(r['symbol'] for r in all_records if r))}")
            print(f"  • Year: {self.year}")
            print("=" * 80)

            return total_saved

        except KeyboardInterrupt:
            logger.info("⏹️  Operation cancelled by user")
            print("\n⏹️  Operation cancelled")
            return 0
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return 0

def main():
    """Main entry point with configurable options"""
    import argparse

    parser = argparse.ArgumentParser(description='Snowball Analytics Dividend Scraper')
    parser.add_argument('--year', type=int, default=datetime.now().year,
                       help='Year to scrape (default: current year)')
    parser.add_argument('--month', type=int,
                       help='Month to scrape (1-12, default: all months)')
    parser.add_argument('--category', type=str, default='us-popular-div',
                       choices=list(SnowballDividendScraper.CATEGORIES.keys()),
                       help='Category to scrape (default: us-popular-div)')
    parser.add_argument('--all', action='store_true',
                       help='Scrape all categories')

    args = parser.parse_args()

    logger.info("🎯 Snowball Analytics Dividend Scraper Starting")
    print(f"🎯 Snowball Analytics Dividend Scraper")
    print(f"📅 Year: {args.year}")
    if args.month:
        print(f"📆 Month: {args.month}")
    if args.all:
        print(f"📊 Mode: Scraping ALL categories")
    else:
        print(f"📊 Category: {args.category}")
    print("")

    scraper = SnowballDividendScraper(
        year=args.year,
        month=args.month,
        category=args.category,
        scrape_all=args.all
    )
    total_records = scraper.run()

    if total_records > 0:
        print(f"\n✅ Successfully scraped {total_records} dividend records")
    else:
        print(f"\n📝 No dividend records found")

if __name__ == "__main__":
    main()
