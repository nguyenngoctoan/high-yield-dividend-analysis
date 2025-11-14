#!/usr/bin/env python3
"""
Nasdaq Dividend Calendar Scraper
Fetches dividend data from Nasdaq's API for specified date ranges.
"""

import sys
import os
import logging
import requests
from datetime import datetime, timedelta
import json

# Add paths to import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NasdaqDividendScraper:
    def __init__(self, start_date=None, end_date=None, auto_continue=False):
        """
        Initialize the Nasdaq dividend scraper

        Args:
            start_date: Start date (YYYY-MM-DD format or datetime object)
            end_date: End date (YYYY-MM-DD format or datetime object)
            auto_continue: If True, automatically fetch from latest announcement_date + 30 days
        """
        self.api_url = "https://api.nasdaq.com/api/calendar/dividends"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        self.auto_continue = auto_continue

        # If auto_continue is enabled, fetch latest announcement_date from database
        if auto_continue and start_date is None:
            latest_date = self.get_latest_announcement_date()
            if latest_date:
                self.start_date = latest_date
                logger.info(f"🔍 Auto-continue mode: Starting from latest announcement_date: {latest_date.strftime('%Y-%m-%d')}")
                print(f"🔍 Auto-continue mode: Starting from latest announcement_date: {latest_date.strftime('%Y-%m-%d')}")
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

    def get_latest_announcement_date(self):
        """
        Get the latest announcement_date from the raw_dividends_nasdaq table
        Returns None if table is empty or error occurs
        """
        try:
            from dotenv import load_dotenv
            from supabase import create_client

            load_dotenv()
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            supabase = create_client(url, key)

            # Query for the latest announcement_date
            result = supabase.table('raw_dividends_nasdaq')\
                .select('announcement_date')\
                .not_.is_('announcement_date', 'null')\
                .order('announcement_date', desc=True)\
                .limit(1)\
                .execute()

            if result.data and len(result.data) > 0:
                latest_date_str = result.data[0]['announcement_date']
                latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
                return latest_date

            return None

        except Exception as e:
            logger.warning(f"⚠️  Could not fetch latest announcement_date: {e}")
            return None

    def fetch_dividends_for_date(self, date):
        """Fetch dividend data for a specific date"""
        date_str = date.strftime('%Y-%m-%d')

        try:
            url = f"{self.api_url}?date={date_str}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get('status', {}).get('rCode') == 200:
                calendar = data.get('data', {}).get('calendar', {})
                rows = calendar.get('rows')

                if rows:
                    logger.info(f"✅ Found {len(rows)} dividends for {date_str}")
                    return rows
                else:
                    logger.info(f"📭 No dividends for {date_str}")
                    return []
            else:
                logger.warning(f"⚠️ API returned non-200 status for {date_str}")
                return []

        except Exception as e:
            logger.error(f"❌ Error fetching dividends for {date_str}: {e}")
            return []

    def parse_dividend_record(self, record, fetch_date):
        """Parse a dividend record into standardized format"""
        try:
            return {
                'symbol': record.get('symbol', '').strip(),
                'company_name': record.get('companyName', '').strip(),
                'ex_date': record.get('dividend_Ex_Date', ''),
                'payment_date': record.get('payment_Date', ''),
                'record_date': record.get('record_Date', ''),
                'dividend_rate': float(record.get('dividend_Rate', 0)) if record.get('dividend_Rate') else None,
                'annual_dividend': float(record.get('indicated_Annual_Dividend', 0)) if record.get('indicated_Annual_Dividend') else None,
                'announcement_date': record.get('announcement_Date', ''),
                'fetch_date': fetch_date.strftime('%Y-%m-%d'),
                'source': 'Nasdaq'
            }
        except Exception as e:
            logger.error(f"Error parsing record: {e}")
            return None

    def save_to_database(self, records):
        """
        Save dividend records to raw_dividends_nasdaq table
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
                    db_record = {
                        'symbol': record['symbol'],
                        'company_name': record.get('company_name'),
                        'ex_date': record.get('ex_date'),
                        'payment_date': record.get('payment_date'),
                        'record_date': record.get('record_date'),
                        'dividend_rate': record.get('dividend_rate'),
                        'annual_dividend': record.get('annual_dividend'),
                        'announcement_date': record.get('announcement_date'),
                        'source': record.get('source')
                    }
                    db_records.append(db_record)

            # Batch upsert with conflict resolution on symbol + ex_date
            batch_size = 1000
            saved_count = 0

            for i in range(0, len(db_records), batch_size):
                batch = db_records[i:i + batch_size]
                result = supabase.table('raw_dividends_nasdaq').upsert(
                    batch,
                    on_conflict='symbol,ex_date'
                ).execute()

                batch_saved = len(result.data) if result.data else 0
                saved_count += batch_saved

            logger.info(f"✅ Saved {saved_count} records to raw_dividends_nasdaq")
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
            all_records = []

            print(f"🎯 Nasdaq Dividend Calendar Scraper")
            print("=" * 80)
            print(f"📅 Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
            print(f"📊 Fetching dividend data from Nasdaq API")
            print("=" * 80)

            # Iterate through each date
            current_date = self.start_date
            dates_processed = 0

            while current_date <= self.end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                print(f"\n📆 Processing {date_str}...")

                # Fetch dividends for this date
                records = self.fetch_dividends_for_date(current_date)

                if records:
                    # Parse records
                    parsed_records = []
                    for record in records:
                        parsed = self.parse_dividend_record(record, current_date)
                        if parsed:
                            parsed_records.append(parsed)

                    print(f"  ✅ Found {len(parsed_records)} dividend records")

                    # Save immediately to database
                    if parsed_records:
                        saved = self.save_to_database(parsed_records)
                        all_records.extend(parsed_records)
                        print(f"  💾 Saved {saved} records (total so far: {len(all_records)})")
                else:
                    print(f"  📭 No dividends for this date")

                dates_processed += 1
                current_date += timedelta(days=1)

            # Summary
            print(f"\n" + "=" * 80)
            print(f"🎉 Nasdaq Dividend Scraping Complete!")
            print(f"📊 Results Summary:")
            print(f"  • Dates processed: {dates_processed}")
            print(f"  • Total dividend records: {len(all_records)}")
            print(f"  • Unique symbols: {len(set(r['symbol'] for r in all_records if r))}")
            print(f"  • Date range: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
            print("=" * 80)

            return len(all_records)

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

    parser = argparse.ArgumentParser(description='Nasdaq Dividend Calendar Scraper')
    parser.add_argument('--start-date', type=str,
                       help='Start date (YYYY-MM-DD, default: today or auto-continue)')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD, default: 30 days from start)')
    parser.add_argument('--days', type=int,
                       help='Number of days to scrape from start date (alternative to end-date)')
    parser.add_argument('--auto-continue', action='store_true',
                       help='Automatically start from latest announcement_date in database and fetch next 30 days')

    args = parser.parse_args()

    # Handle auto-continue mode
    if args.auto_continue:
        logger.info("🎯 Nasdaq Dividend Calendar Scraper Starting (Auto-Continue Mode)")
        print(f"🎯 Nasdaq Dividend Calendar Scraper (Auto-Continue Mode)")
        print("")

        scraper = NasdaqDividendScraper(auto_continue=True)
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

    logger.info("🎯 Nasdaq Dividend Calendar Scraper Starting")
    print(f"🎯 Nasdaq Dividend Calendar Scraper")
    print(f"📅 Start: {start_date.strftime('%Y-%m-%d')}")
    print(f"📅 End: {end_date.strftime('%Y-%m-%d')}")
    print("")

    scraper = NasdaqDividendScraper(start_date=start_date, end_date=end_date)
    total_records = scraper.run()

    if total_records > 0:
        print(f"\n✅ Successfully scraped {total_records} dividend records")
    else:
        print(f"\n📝 No dividend records found")

if __name__ == "__main__":
    main()
