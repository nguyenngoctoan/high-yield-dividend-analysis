#!/usr/bin/env python3
"""
Dividend Calendar Scraper Functions (Requests-only version)
Extract dividend data from YieldMax press releases using requests + BeautifulSoup only.
No Selenium/Chrome required.
"""

import os
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase_helpers import (
    get_supabase_client,
    test_supabase_connection,
    supabase_select,
    supabase_insert,
    supabase_upsert
)
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reduce HTTP request logging noise
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def parse_date(date_str):
    """Parse date string from YieldMax press releases."""
    if not date_str or date_str.strip() in ['-', '', 'N/A']:
        return None

    # Clean the date string
    date_str = date_str.strip()

    # Handle various date formats used in YieldMax press releases
    # Check 4-digit years first to avoid 2025 being matched as 25 (2-digit)
    date_patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',     # M/D/YYYY or MM/DD/YYYY
        r'(\d{4})-(\d{1,2})-(\d{1,2})',     # YYYY-M-D or YYYY-MM-DD
        r'(\d{1,2})/(\d{1,2})/(\d{2})',      # M/D/YY or MM/DD/YY
    ]

    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                if len(match.group(3)) == 2:  # Two-digit year
                    month, day, year = match.groups()
                    year = int(year)
                    if year < 50:  # Assume 2000s for years < 50
                        year += 2000
                    else:  # Assume 1900s for years >= 50
                        year += 1900
                elif pattern.startswith(r'(\d{4})'):  # YYYY-MM-DD format
                    year, month, day = match.groups()
                    year = int(year)
                else:  # Four-digit year
                    month, day, year = match.groups()
                    year = int(year)

                month, day = int(month), int(day)
                return datetime(year, month, day).strftime('%Y-%m-%d')

            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse date '{date_str}': {e}")
                continue

    logger.warning(f"Could not parse date format: '{date_str}'")
    return None

def extract_table_data(url):
    """Extract dividend table data from YieldMax press release URL using requests + BeautifulSoup."""
    logger.info(f"Loading URL: {url}")

    try:
        # Fetch the page with requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find tables that contain dividend data
        tables = soup.find_all('table')

        dividend_data = []

        for table in tables:
            # Check if this table contains dividend data by looking for key headers
            headers = table.find_all('th')
            if not headers:
                # Some tables use td for headers in first row
                first_row = table.find_all('tr')
                if first_row:
                    headers = first_row[0].find_all('td')
            header_texts = [h.get_text().strip().lower() for h in headers]

            # Look for tables with dividend-related headers
            has_dividend_headers = any(
                keyword in ' '.join(header_texts)
                for keyword in ['ex-date', 'ex date', 'payment date', 'distribution', 'ticker', 'symbol']
            )

            if not has_dividend_headers:
                continue

            logger.info("Table with dividend headers found")

            # Get all rows
            rows = table.find_all('tr')

            if len(rows) < 2:  # Need at least header + 1 data row
                continue

            # Parse headers to identify columns
            header_row = rows[0]
            header_cells = header_row.find_all('th')
            if not header_cells:
                header_cells = header_row.find_all('td')

            header_mapping = {}
            for i, cell in enumerate(header_cells):
                # Clean header text by removing line breaks and normalizing whitespace
                header_text = cell.get_text().strip().replace('\n', ' ').replace('\r', ' ').replace('  ', ' ').lower()

                if any(word in header_text for word in ['ticker', 'symbol', 'fund']) and 'etf' in header_text:
                    header_mapping[i] = 'ticker'
                elif ('name' in header_text) and ('etf' in header_text):
                    header_mapping[i] = 'name'
                elif 'distribution per share' in header_text or ('distribution' in header_text and 'per share' in header_text):
                    header_mapping[i] = 'amount'
                elif ('ex-date' in header_text and 'record' in header_text) or 'ex-date & record date' in header_text:
                    # This matches "Ex-Date & Record Date" column for ex_date
                    header_mapping[i] = 'ex_date'
                elif 'payment date' in header_text and 'record' not in header_text:
                    # This matches standalone "Payment Date" column for payment_date
                    header_mapping[i] = 'payment_date'

            logger.info(f"Header mapping found: {header_mapping}")

            # Extract data rows
            for row in rows[1:]:  # Skip header row
                cells = row.find_all('td')

                if len(cells) < 3:  # Need at least ticker, amount, and date
                    continue

                # Extract data based on header mapping
                record = {}

                for i, cell in enumerate(cells):
                    cell_text = cell.get_text().strip()

                    if i in header_mapping:
                        field_name = header_mapping[i]

                        if field_name == 'ticker':
                            # Clean ticker symbol
                            ticker = cell_text.replace('®', '').replace('™', '').strip()
                            if ticker and ticker != '-':
                                record['ticker'] = ticker

                        elif field_name == 'name':
                            if cell_text and cell_text != '-':
                                record['name'] = cell_text

                        elif field_name == 'amount':
                            # Extract dollar amount
                            amount_match = re.search(r'\$?(\d+\.?\d*)', cell_text.replace(',', ''))
                            if amount_match:
                                try:
                                    amount = float(amount_match.group(1))
                                    if amount > 0:
                                        record['amount'] = amount
                                except ValueError:
                                    pass

                        elif field_name == 'ex_date':
                            parsed_date = parse_date(cell_text)
                            if parsed_date:
                                record['ex_date'] = parsed_date

                        elif field_name == 'payment_date':
                            parsed_date = parse_date(cell_text)
                            if parsed_date:
                                record['payment_date'] = parsed_date

                # Only include records with minimum required fields
                if ('ticker' in record and
                    'amount' in record and
                    'ex_date' in record and
                    'payment_date' in record):

                    dividend_data.append(record)

                elif 'ticker' in record:
                    # Log incomplete records for debugging
                    missing_fields = []
                    if 'amount' not in record: missing_fields.append('amount')
                    if 'ex_date' not in record: missing_fields.append('ex_date')
                    if 'payment_date' not in record: missing_fields.append('payment_date')
                    logger.debug(f"Skipping {record['ticker']}: missing {', '.join(missing_fields)}")

        logger.info(f"✅ Found {len(dividend_data)} dividend records in article")
        return dividend_data

    except Exception as e:
        logger.error(f"❌ Error extracting table data: {e}")
        return []

def save_to_dividend_calendar(dividend_data):
    """Save dividend data to the dividend_payments table using Supabase."""
    if not dividend_data:
        return 0

    saved_count = 0

    for record in dividend_data:
        try:
            # Prepare the data for upsert
            dividend_record = {
                'symbol': record['ticker'],
                'ex_date': str(record['ex_date']),
                'amount_per_share': float(record['amount']),
                'amount': float(record['amount']),  # Will be multiplied by shares_owned later
                'payment_date': str(record['payment_date']) if record.get('payment_date') else None,
                'frequency': 'monthly'  # Default for YieldMax, could be extracted from article
            }

            # Upsert will handle both insert and update cases
            result = supabase_upsert('dividend_payments', dividend_record)

            if result:
                logger.info(f"Saved dividend record for {record['ticker']} on {record['ex_date']}: ${record['amount']}")
                saved_count += 1
            else:
                logger.warning(f"Failed to save dividend record for {record['ticker']}")

        except Exception as e:
            logger.error(f"❌ Error saving record for {record['ticker']}: {e}")
            continue

    logger.info(f"Database operation complete: {saved_count} saved, {len(dividend_data) - saved_count} skipped")
    return saved_count

def main():
    """Main execution function to scrape dividend calendar data."""
    import sys

    # Default YieldMax press release URL (recent example)
    default_url = "https://www.globenewswire.com/news-release/2025/10/08/3163172/0/en/YieldMax-ETFs-Announces-Distributions-on-BABO-MARO-ULTY-MRNY-SLTY-and-Others.html"

    # Use URL from command line argument if provided, otherwise use default
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = default_url
        logger.info(f"No URL provided, using default: {url}")

    print(f"🔍 Scraping dividend data from: {url}")

    try:
        # Extract dividend data from the URL
        dividend_data = extract_table_data(url)

        if dividend_data:
            print(f"✅ Found {len(dividend_data)} dividend records:")
            for record in dividend_data:
                print(f"  📊 {record['ticker']}: ${record['amount']} (Ex: {record['ex_date']}, Pay: {record['payment_date']})")

            # Save to database
            print(f"💾 Saving to database...")
            saved_count = save_to_dividend_calendar(dividend_data)
            print(f"✅ Successfully saved {saved_count} records to dividend_payments table")

        else:
            print("❌ No dividend data found in the article")

    except Exception as e:
        logger.error(f"❌ Error during scraping: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
