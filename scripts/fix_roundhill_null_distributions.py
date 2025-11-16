#!/usr/bin/env python3
"""
Fix NULL distribution data for Roundhill ETFs: NVDW and XDIV
Scrape from roundhillinvestments.com
"""

import os
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from bs4 import BeautifulSoup
import json

def scrape_roundhill_distributions(ticker):
    """
    Scrape distribution data from Roundhill website
    """
    try:
        # Try the fund page
        url = f"https://www.roundhillinvestments.com/etf/{ticker.lower()}/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for distribution/dividend tables
            tables = soup.find_all('table')

            for table in tables:
                # Check if this is a distribution table
                headers_text = ' '.join([th.get_text().strip().lower() for th in table.find_all('th')])

                if any(keyword in headers_text for keyword in ['distribution', 'dividend', 'ex date', 'record date']):
                    # Found distribution table!
                    distributions = []

                    # Get headers
                    header_row = table.find('thead') or table.find('tr')
                    if header_row:
                        headers = [th.get_text().strip() for th in header_row.find_all('th')]

                        # Get rows
                        rows = table.find_all('tr')[1:]  # Skip header

                        for row in rows:
                            cells = row.find_all('td')
                            if len(cells) >= len(headers):
                                dist_record = {}
                                for i, header in enumerate(headers):
                                    if i < len(cells):
                                        dist_record[header] = cells[i].get_text().strip()
                                distributions.append(dist_record)

                    if distributions:
                        return distributions

            # If no table found, look for distribution info in text
            dist_section = soup.find(string=lambda text: text and 'distribution' in text.lower())
            if dist_section:
                print(f"      Found distribution info in text, but no structured table")
                return []  # Return empty for now, manual inspection needed

        return None

    except Exception as e:
        print(f"      Error scraping {ticker}: {e}")
        return None

def main():
    load_dotenv()

    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    if not db_password:
        print("❌ SUPABASE_DB_PASSWORD not found in .env")
        return 1

    # Database connection
    conn = psycopg2.connect(
        host="db.uykxgbrzpfswbdxtyzlv.supabase.co",
        port=6543,
        user="postgres",
        password=db_password,
        database="postgres"
    )

    print("=" * 80)
    print("🔧 FIXING ROUNDHILL NULL DISTRIBUTIONS")
    print("=" * 80)
    print()

    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get symbols with null distributions
    symbols_to_fix = ['NVDW', 'XDIV']

    for ticker in symbols_to_fix:
        print(f"📊 Processing {ticker}...")

        # Get current record
        cursor.execute("""
            SELECT ticker, fund_name, distributions
            FROM raw_roundhill_etf_data
            WHERE ticker = %s;
        """, (ticker,))

        record = cursor.fetchone()

        if record:
            print(f"   Fund: {record['fund_name']}")
            print(f"   Current distributions: {record['distributions']}")
            print()

            # Try to scrape distributions
            print(f"   Attempting to scrape from roundhillinvestments.com...")
            distributions = scrape_roundhill_distributions(ticker)

            if distributions is not None and len(distributions) > 0:
                # Update database
                try:
                    update_cursor = conn.cursor()
                    update_cursor.execute(
                        "UPDATE raw_roundhill_etf_data SET distributions = %s WHERE ticker = %s",
                        (json.dumps(distributions), ticker)
                    )
                    conn.commit()
                    update_cursor.close()

                    print(f"   ✅ Updated {ticker} with {len(distributions)} distribution records")
                    # Show first 2
                    for i, dist in enumerate(distributions[:2]):
                        print(f"      [{i}] {dist}")
                except Exception as e:
                    print(f"   ❌ Database update failed: {e}")
                    conn.rollback()

            elif distributions is not None and len(distributions) == 0:
                print(f"   ⚠️  No structured distribution data found on website")
                print(f"   📝 Manual check needed: https://www.roundhillinvestments.com/etf/{ticker.lower()}/")

            else:
                print(f"   ❌ Failed to scrape {ticker}")
                print(f"   📝 Manual check needed: https://www.roundhillinvestments.com/etf/{ticker.lower()}/")

        else:
            print(f"   ❌ {ticker} not found in database")

        print()
        time.sleep(2)  # Be nice to the server

    cursor.close()
    conn.close()

    print("=" * 80)
    print("✅ Processing complete")
    print("=" * 80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
