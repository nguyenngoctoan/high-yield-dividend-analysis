#!/usr/bin/env python3
"""
Dynamic YieldMax Dividend Scraper
Automatically discovers and scrapes YieldMax dividend distribution articles from Globe Newswire.
Replaces all static URL-based YieldMax scrapers with dynamic article discovery.
"""

import sys
import os
import time
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

# Add paths to import helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))  # For supabase_helpers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'archive', 'old_scripts'))
from scrape_dividend_calendar_requests import extract_table_data, save_to_dividend_calendar

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YieldMaxDynamicScraper:
    def __init__(self, max_articles=20, days_back=365, include_product_launches=False):
        """
        Initialize the dynamic YieldMax scraper
        
        Args:
            max_articles: Maximum number of articles to process
            days_back: Only process articles from this many days back
            include_product_launches: Whether to process product launch articles (usually no dividend data)
        """
        self.max_articles = max_articles
        self.days_back = days_back
        self.include_product_launches = include_product_launches
        self.search_url = "https://www.globenewswire.com/en/search/keyword/yieldmax?pageSize=25"
        
    def discover_yieldmax_articles(self):
        """Discover YieldMax articles from Globe Newswire search"""
        logger.info(f"🔍 Discovering YieldMax articles from Globe Newswire...")
        print(f"🔍 Searching for YieldMax articles...")
        
        try:
            response = requests.get(self.search_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links
            article_links = []
            
            # Look for links in search results
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text().strip()
                
                if 'news-release' in href and 'YieldMax' in text:
                    if href.startswith('/'):
                        href = 'https://www.globenewswire.com' + href
                    
                    # Extract date from URL for filtering
                    date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', href)
                    if date_match:
                        year, month, day = map(int, date_match.groups())
                        article_date = datetime(year, month, day)
                        cutoff_date = datetime.now() - timedelta(days=self.days_back)
                        
                        if article_date >= cutoff_date:
                            article_links.append({
                                'url': href,
                                'title': text,
                                'date': article_date
                            })
            
            # Remove duplicates and sort by date (newest first)
            seen_urls = set()
            unique_articles = []
            for article in article_links:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            unique_articles.sort(key=lambda x: x['date'], reverse=True)
            
            logger.info(f"✅ Discovered {len(unique_articles)} YieldMax articles within {self.days_back} days")
            return unique_articles[:self.max_articles]
            
        except Exception as e:
            logger.error(f"❌ Error discovering articles: {e}")
            return []
    
    def filter_dividend_articles(self, articles):
        """Filter articles to focus on dividend distributions vs product launches"""
        dividend_articles = []
        other_articles = []
        
        for article in articles:
            title = article['title'].lower()
            url = article['url'].lower()
            
            # Keywords that indicate dividend distribution articles
            dividend_keywords = [
                'announces distributions',
                'distribution',
                'dividend',
                'monthly distributions',
                'quarterly distributions'
            ]
            
            # Keywords that indicate product launches (usually no dividend data)
            launch_keywords = [
                'introduces',
                'launches',
                'new etf',
                'option income strategy etf'
            ]
            
            is_dividend_article = any(keyword in title for keyword in dividend_keywords)
            is_launch_article = any(keyword in title for keyword in launch_keywords)
            
            if is_dividend_article or (is_launch_article and self.include_product_launches):
                if is_dividend_article:
                    dividend_articles.append(article)
                else:
                    other_articles.append(article)
        
        logger.info(f"📊 Filtered articles: {len(dividend_articles)} dividend, {len(other_articles)} other")
        
        return dividend_articles, other_articles
    
    def get_existing_source_urls(self):
        """Get set of already-scraped source URLs from database"""
        try:
            from dotenv import load_dotenv
            from supabase import create_client

            load_dotenv()
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            supabase = create_client(url, key)

            result = supabase.table('raw_dividends_yieldmax').select('source_url').execute()
            existing_urls = set()
            if result.data:
                for row in result.data:
                    if row.get('source_url'):
                        existing_urls.add(row['source_url'])
            logger.info(f"📊 Found {len(existing_urls)} existing source URLs in database")
            return existing_urls
        except Exception as e:
            logger.warning(f"⚠️  Could not fetch existing source URLs: {e}")
            return set()

    def scrape_articles(self, articles, article_type="dividend"):
        """Scrape dividend data from discovered articles"""
        total_saved = 0
        successful_articles = 0
        skipped_count = 0

        logger.info(f"🚀 Starting dynamic YieldMax scraping - {len(articles)} {article_type} articles")
        print(f"🎯 Dynamic YieldMax Scraper")
        print("=" * 80)
        print(f"📰 Total {article_type} articles to process: {len(articles)}")
        print(f"🗓️ Date range: Last {self.days_back} days")
        print(f"🔍 Auto-discovered from: {self.search_url}")
        print("=" * 80)

        # Get existing source URLs to skip
        existing_urls = self.get_existing_source_urls()

        for i, article in enumerate(articles, 1):
            # Check if this article was already scraped
            if article['url'] in existing_urls:
                logger.info(f"⏭️  Skipping article {i}/{len(articles)}: {article['title']} (already scraped)")
                print(f"\r⏭️  Skipped {i}/{len(articles)} articles (already in DB)", end='', flush=True)
                skipped_count += 1
                continue
            try:
                logger.info(f"📰 Processing article {i}/{len(articles)}: {article['url']}")
                print(f"\n📰 Article {i}/{len(articles)} - {article['date'].strftime('%B %d, %Y')}")
                print(f"📄 Title: {article['title']}")
                print(f"🔗 URL: {article['url']}")
                
                # Extract data from this article
                data = extract_table_data(article['url'])
                
                if data:
                    logger.info(f"✅ Found {len(data)} dividend records in article {i}")
                    print(f"✅ Found {len(data)} dividend records")
                    
                    # Display found records
                    for record in data:
                        print(f"  • {record['ticker']}: ${record['amount']} (ex: {record['ex_date']}, pay: {record['payment_date']})")
                    
                    # Save to database with source URL
                    saved_count = save_to_dividend_calendar(data, article['url'])
                    total_saved += saved_count
                    successful_articles += 1
                    
                    logger.info(f"💾 Saved {saved_count} records from article {i}")
                    print(f"💾 Saved {saved_count} records to database")
                    
                else:
                    logger.warning(f"⚠️ No dividend data found in article {i}")
                    print(f"⚠️ No dividend data found")
                    if "introduces" in article['title'].lower() or "launches" in article['title'].lower():
                        print("  (This appears to be a product launch announcement)")
                
                # Brief pause between articles
                if i < len(articles):
                    logger.info("⏳ Pausing 3 seconds before next article...")
                    time.sleep(3)
                    
            except KeyboardInterrupt:
                logger.info("⏹️ User cancelled operation")
                break
            except Exception as e:
                logger.error(f"❌ Error processing article {i}: {e}")
                print(f"❌ Error: {e}")
                continue

        print(f"\n\n✅ Summary: Processed {len(articles)} articles")
        print(f"   • Skipped: {skipped_count} (already in DB)")
        print(f"   • Scraped: {successful_articles}")
        print(f"   • Total saved: {total_saved}")

        return total_saved, successful_articles
    
    def run(self):
        """Main scraping workflow"""
        try:
            # Discover articles
            all_articles = self.discover_yieldmax_articles()
            
            if not all_articles:
                print("⚠️ No YieldMax articles found")
                return 0
            
            # Filter articles
            dividend_articles, other_articles = self.filter_dividend_articles(all_articles)
            
            # Process dividend articles first (priority)
            total_saved = 0
            total_successful = 0
            
            if dividend_articles:
                print(f"\n🎯 Processing {len(dividend_articles)} dividend distribution articles...")
                saved, successful = self.scrape_articles(dividend_articles, "dividend")
                total_saved += saved
                total_successful += successful
            
            # Process other articles if enabled
            if other_articles and self.include_product_launches:
                print(f"\n🚀 Processing {len(other_articles)} product launch articles...")
                saved, successful = self.scrape_articles(other_articles, "product launch")
                total_saved += saved
                total_successful += successful
            
            # Summary
            print("\n" + "=" * 80)
            print(f"🎉 Dynamic YieldMax Scraping Complete!")
            print(f"📊 Results Summary:")
            print(f"  • Articles discovered: {len(all_articles)}")
            print(f"  • Dividend articles: {len(dividend_articles)}")
            print(f"  • Other articles: {len(other_articles)}")
            print(f"  • Articles processed: {total_successful}")
            print(f"  • Total dividend records saved: {total_saved}")
            print(f"  • Date range: Last {self.days_back} days")
            print(f"  • Auto-discovery: ✅ Enabled")
            print("=" * 80)
            
            logger.info(f"🏁 Dynamic scraping complete: {total_successful} articles processed, {total_saved} total records saved")
            
            # Show database totals
            if total_saved > 0:
                try:
                    import os
                    from dotenv import load_dotenv
                    from supabase import create_client
                    
                    load_dotenv()
                    url = os.getenv('SUPABASE_URL')
                    key = os.getenv('SUPABASE_KEY')
                    supabase = create_client(url, key)
                    
                    total_result = supabase.table('dividend_calendar').select('*', count='exact').execute()
                    print(f"📈 Updated database total: {total_result.count} dividend records")
                    
                except Exception as e:
                    logger.warning(f"Could not get database total: {e}")
            
            return total_saved
            
        except KeyboardInterrupt:
            logger.info("⏹️ Operation cancelled by user")
            print("\n⏹️ Operation cancelled")
            return 0
        except Exception as e:
            logger.error(f"❌ Fatal error in dynamic scraper: {e}")
            print(f"\n❌ Fatal error: {e}")
            return 0

def main():
    """Main entry point with configurable options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic YieldMax Dividend Scraper')
    parser.add_argument('--max-articles', type=int, default=20, help='Maximum articles to process (default: 20)')
    parser.add_argument('--days-back', type=int, default=90, help='Days back to search (default: 90)')
    parser.add_argument('--include-launches', action='store_true', help='Include product launch articles')
    parser.add_argument('--recent-only', action='store_true', help='Only process last 7 days')
    
    args = parser.parse_args()
    
    # Adjust days back for recent-only mode
    days_back = 7 if args.recent_only else args.days_back
    
    logger.info("🎯 YieldMax Dynamic Scraper Starting")
    print(f"🎯 YieldMax Dynamic Dividend Scraper")
    print(f"⚙️ Max Articles: {args.max_articles}")
    print(f"📅 Days Back: {days_back}")
    print(f"🚀 Include Launches: {args.include_launches}")
    print("")
    
    scraper = YieldMaxDynamicScraper(
        max_articles=args.max_articles,
        days_back=days_back,
        include_product_launches=args.include_launches
    )
    
    total_saved = scraper.run()
    
    if total_saved > 0:
        print(f"\n✅ Successfully saved {total_saved} YieldMax dividend records")
    else:
        print(f"\n📝 No new dividend records found or saved")

if __name__ == "__main__":
    main()