#!/usr/bin/env python3
"""
NYSE Ex-Date Dividend Scraper
Fetches dividend data from NYSE's ex-date dividends page using Selenium for specified date ranges.
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

class NYSEDividendScraper:
    def __init__(self, start_date=None, end_date=None, auto_continue=False):
        """
        Initialize the NYSE dividend scraper

        Args:
            start_date: Start date (YYYY-MM-DD format or datetime object)
            end_date: End date (YYYY-MM-DD format or datetime object)
            auto_continue: If True, automatically fetch from latest ex_date + 30 days
        """
        self.url = "https://www.nyse.com/ex-date-dividends"
        self.auto_continue = auto_continue

        # If auto_continue is enabled, fetch latest ex_date from database
        if auto_continue and start_date is None:
            latest_date = self.get_latest_ex_date()
            if latest_date:
                self.start_date = latest_date
                logger.info(f"🔍 Auto-continue mode: Starting from latest ex_date: {latest_date.strftime('%Y-%m-%d')}")
                print(f"🔍 Auto-continue mode: Starting from latest ex_date: {latest_date.strftime('%Y-%m-%d')}")
            else:
                logger.info("⚠️  No existing data found, starting from today")
                print("⚠️  No existing data found, starting from today")
                self.start_date = datetime.now()
        # Parse dates
        elif isinstance(start_date, str):
            self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        elif isinstance(start_date, datetime):
            self.start_date = start_date
        else:
            self.start_date = datetime.now()

        if isinstance(end_date, str):
            self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        elif isinstance(end_date, datetime):
            self.end_date = end_date
        else:
            self.end_date = self.start_date + timedelta(days=30)

    def get_latest_ex_date(self):
        """
        Get the latest ex_date from the raw_dividends_nyse table
        Returns None if table is empty or error occurs
        """
        try:
            from dotenv import load_dotenv
            from supabase import create_client

            load_dotenv()
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            supabase = create_client(url, key)

            # Query for the latest ex_date
            result = supabase.table('raw_dividends_nyse')\
                .select('ex_date')\
                .not_.is_('ex_date', 'null')\
                .order('ex_date', desc=True)\
                .limit(1)\
                .execute()

            if result.data and len(result.data) > 0:
                latest_date_str = result.data[0]['ex_date']
                latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
                logger.info(f"📊 Latest ex_date in database: {latest_date.strftime('%Y-%m-%d')}")
                print(f"📊 Latest ex_date in database: {latest_date.strftime('%Y-%m-%d')}")
                return latest_date

            return None

        except Exception as e:
            logger.warning(f"⚠️  Could not fetch latest ex_date: {e}")
            return None

    def scrape_dividends(self):
        """Scrape dividend data from NYSE using Selenium"""
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Run in background
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')

        driver = None
        try:
            logger.info("🌐 Starting browser...")
            print("🌐 Starting browser...")

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.url)

            # Wait for page to load
            logger.info("⏳ Waiting for page to load...")
            print("⏳ Waiting for page to load...")
            time.sleep(5)

            # Format dates for input
            start_date_str = self.start_date.strftime('%Y-%m-%d')
            end_date_str = self.end_date.strftime('%Y-%m-%d')

            logger.info(f"📅 Setting date range: {start_date_str} to {end_date_str}")
            print(f"📅 Setting date range: {start_date_str} to {end_date_str}")

            # Find and fill Ex-Date Range fields (using Ex-Date Range, not Record Date Range)
            wait = WebDriverWait(driver, 20)

            # Strategy: Find all date inputs and use the Ex-Date Range ones (indices 2 and 3)
            date_inputs = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='date']")))

            if len(date_inputs) >= 4:
                # Ex-Date Range: inputs[2] and inputs[3]
                ex_date_start = date_inputs[2]
                ex_date_end = date_inputs[3]

                logger.info("📝 Filling Ex-Date Range fields...")
                print("📝 Filling Ex-Date Range fields...")

                # Clear and fill start date
                ex_date_start.clear()
                ex_date_start.send_keys(start_date_str)
                time.sleep(1)

                # Clear and fill end date
                ex_date_end.clear()
                ex_date_end.send_keys(end_date_str)
                time.sleep(2)

                logger.info("⏳ Waiting for results to load...")
                print("⏳ Waiting for results to load...")
                time.sleep(5)

                # Parse the results table
                logger.info("📊 Parsing results table...")
                print("📊 Parsing results table...")

                records = self.parse_results_table(driver)

                return records
            else:
                logger.error(f"❌ Could not find date input fields (found {len(date_inputs)})")
                print(f"❌ Could not find date input fields (found {len(date_inputs)})")
                return []

        except Exception as e:
            logger.error(f"❌ Error scraping NYSE: {e}")
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if driver:
                driver.quit()
                logger.info("🔚 Browser closed")

    def parse_results_table(self, driver):
        """Parse the dividend results table"""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # Wait for table to load
            wait = WebDriverWait(driver, 20)

            # Find table rows (skip header)
            # The table structure: symbol, security_name, ex_date, record_date, cash_amount, declaration_date, frequency, type
            table_rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))

            logger.info(f"📋 Found {len(table_rows)} dividend records")
            print(f"📋 Found {len(table_rows)} dividend records")

            records = []
            for row in table_rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")

                    if len(cells) >= 4:  # Minimum expected columns
                        symbol = cells[0].text.strip() if len(cells) > 0 else ''
                        ex_date = cells[2].text.strip() if len(cells) > 2 else ''

                        # Debug: print first few records with all cell values
                        if len(records) < 2:
                            cell_values = [f"Cell{i}={cells[i].text.strip()}" for i in range(len(cells))]
                            logger.info(f"  Sample record: {', '.join(cell_values)}")

                        # NYSE table columns (5 columns): Symbol, Security Name, Ex-Date, Record Date, Declaration Date
                        # Note: NYSE ex-date dividends page does NOT include cash amounts
                        record = {
                            'symbol': symbol,
                            'security_name': cells[1].text.strip() if len(cells) > 1 else '',
                            'ex_date': ex_date,
                            'record_date': cells[3].text.strip() if len(cells) > 3 else '',
                            'cash_amount': None,  # Not available in NYSE ex-date dividends page
                            'declaration_date': cells[4].text.strip() if len(cells) > 4 else '',
                            'frequency': None,  # Not in NYSE table
                            'dividend_type': None,  # Not in NYSE table
                            'source': 'NYSE'
                        }

                        # Only add records with valid data
                        if record['symbol'] and record['ex_date']:
                            records.append(record)
                        else:
                            logger.warning(f"⚠️  Skipping row: symbol='{symbol}', ex_date='{ex_date}'")
                except Exception as e:
                    logger.warning(f"⚠️  Error parsing row: {e}")
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
        Save dividend records to raw_dividends_nyse table
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
                    cash_amount = record.get('cash_amount')
                    # Convert cash_amount to float if it exists and is not None
                    if cash_amount and cash_amount.replace('.', '').replace('-', '').isdigit():
                        cash_amount = float(cash_amount)
                    else:
                        cash_amount = None

                    db_record = {
                        'symbol': record['symbol'],
                        'security_name': record.get('security_name'),
                        'ex_date': record.get('ex_date') if record.get('ex_date') else None,
                        'record_date': record.get('record_date') if record.get('record_date') else None,
                        'cash_amount': cash_amount,
                        'declaration_date': record.get('declaration_date') if record.get('declaration_date') else None,
                        'frequency': record.get('frequency'),
                        'dividend_type': record.get('dividend_type'),
                        'source': record.get('source')
                    }
                    db_records.append(db_record)

            # Batch upsert with conflict resolution on symbol + ex_date
            batch_size = 1000
            saved_count = 0

            for i in range(0, len(db_records), batch_size):
                batch = db_records[i:i + batch_size]
                result = supabase.table('raw_dividends_nyse').upsert(
                    batch,
                    on_conflict='symbol,ex_date'
                ).execute()

                batch_saved = len(result.data) if result.data else 0
                saved_count += batch_saved

            logger.info(f"✅ Saved {saved_count} records to raw_dividends_nyse")
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
            print(f"🎯 NYSE Ex-Date Dividend Scraper")
            print("=" * 80)
            print(f"📅 Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
            print(f"📊 Fetching dividend data from NYSE")
            print("=" * 80)

            # Scrape dividends
            records = self.scrape_dividends()

            if records:
                # Save to database
                saved_count = self.save_to_database(records)

                # Summary
                print(f"\n" + "=" * 80)
                print(f"🎉 NYSE Dividend Scraping Complete!")
                print(f"📊 Results Summary:")
                print(f"  • Total dividend records: {len(records)}")
                print(f"  • Records saved to database: {saved_count}")
                print(f"  • Unique symbols: {len(set(r['symbol'] for r in records if r))}")
                print(f"  • Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
                print("=" * 80)

                return saved_count
            else:
                print(f"\n📝 No dividend records found for this date range")
                return 0

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

    parser = argparse.ArgumentParser(description='NYSE Ex-Date Dividend Scraper')
    parser.add_argument('--start-date', type=str,
                       help='Start date (YYYY-MM-DD, default: today or auto-continue)')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD, default: 30 days from start)')
    parser.add_argument('--days', type=int,
                       help='Number of days to scrape from start date (alternative to end-date)')
    parser.add_argument('--auto-continue', action='store_true',
                       help='Automatically start from latest ex_date in database and fetch next 30 days')

    args = parser.parse_args()

    # Handle auto-continue mode
    if args.auto_continue:
        logger.info("🎯 NYSE Dividend Scraper Starting (Auto-Continue Mode)")
        print(f"🎯 NYSE Dividend Scraper (Auto-Continue Mode)")
        print("")

        scraper = NYSEDividendScraper(auto_continue=True)
        total_records = scraper.run()

        if total_records > 0:
            print(f"\n✅ Successfully scraped {total_records} dividend records")
        else:
            print(f"\n📝 No dividend records found")
        return

    # Manual date mode
    if args.start_date:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    else:
        start_date = datetime.now()

    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    elif args.days:
        end_date = start_date + timedelta(days=args.days - 1)
    else:
        end_date = start_date + timedelta(days=30)

    logger.info("🎯 NYSE Dividend Scraper Starting")
    print(f"🎯 NYSE Dividend Scraper")
    print(f"📅 Start: {start_date.strftime('%Y-%m-%d')}")
    print(f"📅 End: {end_date.strftime('%Y-%m-%d')}")
    print("")

    scraper = NYSEDividendScraper(start_date=start_date, end_date=end_date)
    total_records = scraper.run()

    if total_records > 0:
        print(f"\n✅ Successfully scraped {total_records} dividend records")
    else:
        print(f"\n📝 No dividend records found")

if __name__ == "__main__":
    main()
