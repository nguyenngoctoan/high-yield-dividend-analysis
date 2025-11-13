#!/usr/bin/env python3
"""
CBOE Dividend Detail Scraper
Fetches dividend notifications from CBOE's API and scrapes detailed dividend data
from individual detail pages including ex-dates, payment dates, amounts, etc.
"""

import sys
import os
import logging
import requests
from datetime import datetime
import json
import time
import glob
from bs4 import BeautifulSoup
from urllib.parse import urlencode

# Add paths to import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CBOEDividendScraper:
    def __init__(self, years=None, auto_discover_years=False):
        """
        Initialize the CBOE dividend detail scraper

        Args:
            years: List of years to fetch (default: current year)
            auto_discover_years: If True, automatically discover all available years from CBOE
        """
        self.base_url = "https://www.cboe.com/us/equities/notices/data/dividends/"
        self.detail_url = "https://www.cboe.com/us/equities/notices/dividends/details/"
        self.auto_discover_years = auto_discover_years
        self.years = years or [datetime.now().year]
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    def discover_available_years(self):
        """Discover all available years from CBOE API"""
        logger.info("🔍 Discovering available years from CBOE...")
        print("🔍 Discovering available years from CBOE...")

        try:
            # Fetch any year to get the year_list
            url = f"{self.base_url}?year={datetime.now().year}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            year_list = data.get('year_list', [])

            logger.info(f"✅ Found {len(year_list)} available years: {year_list}")
            print(f"✅ Found {len(year_list)} available years: {', '.join(map(str, year_list))}")

            return year_list

        except Exception as e:
            logger.error(f"❌ Error discovering years: {e}")
            print(f"❌ Error: {e}")
            return [datetime.now().year]

    def fetch_notifications(self, year):
        """Fetch dividend notifications for a given year"""
        logger.info(f"🔍 Fetching CBOE dividend notifications for {year}...")
        print(f"🔍 Fetching CBOE dividend notifications for {year}...")

        try:
            url = f"{self.base_url}?year={year}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            alerts = data.get('alerts', [])

            logger.info(f"✅ Found {len(alerts)} notifications for {year}")
            print(f"✅ Found {len(alerts)} notifications for {year}")

            return alerts

        except Exception as e:
            logger.error(f"❌ Error fetching notifications for {year}: {e}")
            print(f"❌ Error: {e}")
            return []

    def scrape_detail_page(self, alert):
        """Scrape detailed dividend information from a CBOE detail page"""
        try:
            # Build detail page URL
            params = {
                'symbols': alert.get('symbols', ''),
                'declaration_dt': alert.get('declaration_dt', ''),
                'firm_name': alert.get('firm_name', '')
            }
            url = f"{self.detail_url}?{urlencode(params)}"

            logger.info(f"  📄 Scraping detail page: {url}")

            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the dividend table
            table = soup.find('table')
            if not table:
                logger.warning(f"  ⚠️ No table found on detail page")
                return []

            records = []
            rows = table.find_all('tr')[1:]  # Skip header row

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 7:
                    try:
                        record = {
                            'symbol': cols[0].get_text().strip(),
                            'name': cols[1].get_text().strip(),
                            'ex_date': cols[2].get_text().strip(),
                            'record_date': cols[3].get_text().strip(),
                            'payment_date': cols[4].get_text().strip(),
                            'amount': cols[5].get_text().strip().replace('$', '').replace(',', ''),
                            'frequency': cols[6].get_text().strip() if len(cols) > 6 else None,
                            'distribution_type': cols[7].get_text().strip() if len(cols) > 7 else None,
                            'firm_name': alert.get('firm_name', ''),
                            'declaration_date': alert.get('declaration_dt', ''),
                            'notification': url  # Store the source URL
                        }
                        records.append(record)
                    except Exception as e:
                        logger.warning(f"  ⚠️ Error parsing row: {e}")
                        continue

            logger.info(f"  ✅ Scraped {len(records)} dividend records from detail page")
            return records

        except Exception as e:
            logger.error(f"  ❌ Error scraping detail page: {e}")
            return []

    def get_existing_notifications(self, supabase):
        """Get set of already-scraped notification URLs from database"""
        try:
            result = supabase.table('raw_dividends_cboe').select('notification').execute()
            existing_notifications = set()
            if result.data:
                for row in result.data:
                    if row.get('notification'):
                        existing_notifications.add(row['notification'])
            logger.info(f"📊 Found {len(existing_notifications)} existing notification URLs in database")
            return existing_notifications
        except Exception as e:
            logger.warning(f"⚠️  Could not fetch existing notifications: {e}")
            return set()

    def build_notification_url(self, alert):
        """Build the notification URL from alert data"""
        from urllib.parse import urlencode
        params = {
            'symbols': alert.get('symbols', ''),
            'declaration_dt': alert.get('declaration_dt', ''),
            'firm_name': alert.get('firm_name', '')
        }
        return f"{self.detail_url}?{urlencode(params)}"

    def scrape_all_details(self, alerts):
        """Scrape detail pages for all notifications and save immediately"""
        total_saved = 0
        skipped_count = 0

        # Initialize database connection once
        from dotenv import load_dotenv
        from supabase import create_client

        load_dotenv()
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        supabase = create_client(url, key)

        # Get existing notifications to skip
        existing_notifications = self.get_existing_notifications(supabase)

        for i, alert in enumerate(alerts, 1):
            # Check if this notification was already scraped
            notification_url = self.build_notification_url(alert)

            if notification_url in existing_notifications:
                logger.info(f"⏭️  Skipping notification {i}/{len(alerts)}: {alert.get('firm_name', 'Unknown')} (already scraped)")
                print(f"\r⏭️  Skipped {i}/{len(alerts)} notifications (already in DB)", end='', flush=True)
                skipped_count += 1
                continue

            logger.info(f"📰 Processing notification {i}/{len(alerts)}: {alert.get('firm_name', 'Unknown')}")
            print(f"\n📰 Notification {i}/{len(alerts)}: {alert.get('firm_name', 'Unknown')} ({alert.get('declaration_dt', '')})")

            # Scrape detail page
            records = self.scrape_detail_page(alert)

            if records:
                print(f"  ✅ Found {len(records)} dividend records")
                for record in records:
                    print(f"    • {record['symbol']}: ${record['amount']} (ex: {record['ex_date']}, pay: {record['payment_date']})")

                # Save immediately to database
                try:
                    db_records = []
                    for record in records:
                        db_record = {
                            'symbol': record['symbol'],
                            'name': record.get('name'),
                            'firm_name': record.get('firm_name'),
                            'declaration_date': record.get('declaration_date'),
                            'ex_date': record.get('ex_date'),
                            'record_date': record.get('record_date'),
                            'payment_date': record.get('payment_date'),
                            'amount': float(record['amount']) if record.get('amount') else None,
                            'frequency': record.get('frequency'),
                            'distribution_type': record.get('distribution_type'),
                            'notification': record.get('notification')  # Source URL
                        }
                        db_records.append(db_record)

                    result = supabase.table('raw_dividends_cboe').upsert(
                        db_records,
                        on_conflict='symbol,payment_date'
                    ).execute()

                    saved_count = len(result.data) if result.data else 0
                    total_saved += saved_count
                    print(f"  💾 Saved {saved_count} records to database (total: {total_saved})")

                except Exception as e:
                    logger.error(f"  ❌ Error saving records: {e}")
                    print(f"  ❌ Error saving: {e}")
            else:
                print(f"  ⚠️ No dividend data found")

            # Brief pause between requests
            if i < len(alerts):
                time.sleep(1)

        print(f"\n\n✅ Summary: Processed {len(alerts)} notifications")
        print(f"   • Skipped: {skipped_count} (already in DB)")
        print(f"   • Scraped: {len(alerts) - skipped_count}")
        print(f"   • Total saved: {total_saved}")

        return total_saved

    def save_to_database(self, records):
        """
        Save dividend detail records to raw_dividends_cboe table
        """
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
                db_record = {
                    'symbol': record['symbol'],
                    'name': record.get('name'),
                    'firm_name': record.get('firm_name'),
                    'declaration_date': record.get('declaration_date'),
                    'ex_date': record.get('ex_date'),
                    'record_date': record.get('record_date'),
                    'payment_date': record.get('payment_date'),
                    'amount': float(record['amount']) if record.get('amount') else None,
                    'frequency': record.get('frequency'),
                    'distribution_type': record.get('distribution_type')
                }
                db_records.append(db_record)

            # Batch upsert with conflict resolution on symbol + payment_date
            batch_size = 1000
            saved_count = 0

            for i in range(0, len(db_records), batch_size):
                batch = db_records[i:i + batch_size]
                result = supabase.table('raw_dividends_cboe').upsert(
                    batch,
                    on_conflict='symbol,payment_date'
                ).execute()

                batch_saved = len(result.data) if result.data else 0
                saved_count += batch_saved

                logger.info(f"  • Saved batch {i//batch_size + 1}: {batch_saved} records")

            logger.info(f"✅ Saved {saved_count} records to raw_dividends_cboe")
            print(f"✅ Saved {saved_count} records to database")

            return saved_count

        except Exception as e:
            logger.error(f"❌ Error saving to database: {e}")
            print(f"❌ Database error: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def export_to_json(self, records, filename=None):
        """Export records to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"cboe_dividend_notifications_{timestamp}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(records, f, indent=2, default=str)

            logger.info(f"📁 Exported to {filename}")
            print(f"📁 Exported to {filename}")
            return filename

        except Exception as e:
            logger.error(f"❌ Error exporting to JSON: {e}")
            return None

    def cleanup_cache_files(self):
        """Clean up any cboe_dividend_notifications JSON cache files"""
        try:
            # Get current working directory
            cwd = os.getcwd()

            # Find all CBOE cache files
            cache_files = glob.glob(os.path.join(cwd, "cboe_dividend_notifications_*.json"))

            if cache_files:
                logger.info(f"🧹 Cleaning up {len(cache_files)} cache file(s)...")
                print(f"\n🧹 Cleaning up cache files...")

                deleted_count = 0
                for cache_file in cache_files:
                    try:
                        os.remove(cache_file)
                        deleted_count += 1
                        logger.debug(f"  • Deleted: {os.path.basename(cache_file)}")
                    except Exception as e:
                        logger.warning(f"  ⚠️ Could not delete {cache_file}: {e}")

                print(f"✅ Cleaned up {deleted_count} cache file(s)")
                logger.info(f"✅ Cleaned up {deleted_count} cache file(s)")
            else:
                logger.debug("No cache files to clean up")

        except Exception as e:
            logger.warning(f"⚠️ Error during cleanup: {e}")
            # Don't fail the entire script due to cleanup errors

    def run(self):
        """Main scraping workflow"""
        try:
            all_records = []

            print(f"🎯 CBOE Dividend Detail Scraper")
            print("=" * 80)

            # Auto-discover years if enabled
            if self.auto_discover_years:
                self.years = self.discover_available_years()
                print(f"📅 Auto-discovered years: {', '.join(map(str, self.years))}")
            else:
                print(f"📅 Years: {', '.join(map(str, self.years))}")

            print(f"📊 Scraping detailed dividend data from CBOE detail pages")
            print("=" * 80)

            for year in self.years:
                # Fetch notifications
                alerts = self.fetch_notifications(year)

                if alerts:
                    # Scrape detail pages for each notification (saves immediately)
                    saved_count = self.scrape_all_details(alerts)
                    all_records.append(saved_count)  # Track total saved

                    print(f"\n  • Processed {len(alerts)} notifications, saved {saved_count} records")

            if all_records:
                # all_records now contains counts, not record objects
                total_saved = sum(all_records)

                # Display summary
                print(f"\n📊 Summary:")
                print(f"  • Total dividend records saved: {total_saved}")

                # Query database for summary
                try:
                    from dotenv import load_dotenv
                    from supabase import create_client

                    load_dotenv()
                    url = os.getenv('SUPABASE_URL')
                    key = os.getenv('SUPABASE_KEY')
                    supabase = create_client(url, key)

                    result = supabase.table('raw_dividends_cboe').select('*').execute()
                    print(f"  • Total records in database: {len(result.data)}")
                    print(f"  • Unique symbols: {len(set(r['symbol'] for r in result.data))}")

                except Exception as e:
                    logger.warning(f"Could not get database summary: {e}")

                print(f"\n✅ Scraping complete!")
                print(f"💾 Database: {total_saved} records saved to raw_dividends_cboe")
            else:
                print(f"\n⚠️  No dividend records found")

            # Clean up any cache files
            self.cleanup_cache_files()

            return sum(all_records) if all_records else 0

        except KeyboardInterrupt:
            logger.info("⏹️  Operation cancelled by user")
            print("\n⏹️  Operation cancelled")
            # Clean up cache files even if cancelled
            self.cleanup_cache_files()
            return 0
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
            # Clean up cache files even if there was an error
            self.cleanup_cache_files()
            return 0

def main():
    """Main entry point with configurable options"""
    import argparse

    parser = argparse.ArgumentParser(description='CBOE Dividend Detail Scraper')
    parser.add_argument('--years', type=int, nargs='+',
                       help='Specific years to fetch (e.g., --years 2024 2025)')
    parser.add_argument('--recent', action='store_true',
                       help='Fetch last 2 years only')
    parser.add_argument('--all-years', action='store_true',
                       help='Auto-discover and fetch all available years from CBOE (2012-present)')
    parser.add_argument('--force-weekend', action='store_true',
                       help='Force scraping even on weekends (default: skip on weekends)')

    args = parser.parse_args()

    # OPTIMIZATION: Skip CBOE scraping on weekends (CBOE doesn't update on weekends)
    # This saves ~15 minutes of wasted scraping time
    if not args.force_weekend:
        current_day = datetime.now().weekday()  # 0=Monday, 6=Sunday
        if current_day >= 5:  # Saturday (5) or Sunday (6)
            day_name = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][current_day]
            logger.info(f"⏭️  Skipping CBOE scraping (today is {day_name} - CBOE doesn't update on weekends)")
            print(f"⏭️  Skipping CBOE scraping on {day_name} (CBOE doesn't update on weekends)")
            print(f"💡 To force scraping on weekends, use --force-weekend flag")
            print(f"⏱️  Time saved: ~15 minutes")
            return

    # Determine which years to scrape
    auto_discover = args.all_years

    if args.all_years:
        years = None  # Will be discovered automatically
    elif args.recent:
        current_year = datetime.now().year
        years = [current_year, current_year - 1]
    elif args.years:
        years = args.years
    else:
        years = [datetime.now().year]

    logger.info("🎯 CBOE Dividend Detail Scraper Starting")
    print(f"🎯 CBOE Dividend Detail Scraper")
    if not auto_discover:
        print(f"📅 Years: {', '.join(map(str, years))}")
    print("")

    scraper = CBOEDividendScraper(years=years, auto_discover_years=auto_discover)
    total_records = scraper.run()

    if total_records > 0:
        print(f"\n✅ Successfully scraped {total_records} dividend records")
    else:
        print(f"\n📝 No dividend records found")

if __name__ == "__main__":
    main()
