#!/usr/bin/env python3
"""
Test script for Global X Canada scraper
Tests on sample ETFs to verify functionality
"""

from globalx_canada_scraper import GlobalXCanadaScraper
import json

def test_sample_etfs():
    """Test scraper on representative sample ETFs"""

    # Sample ETFs covering different categories
    test_tickers = [
        'ENCC',  # Covered Call - Commodities
        'CNDX',  # Core Equity
        'CASH',  # Money Market
    ]

    print("=" * 70)
    print("Global X Canada Scraper - Test Run")
    print("=" * 70)
    print(f"\nTesting {len(test_tickers)} sample ETFs:")
    for ticker in test_tickers:
        print(f"  - {ticker}")
    print()

    scraper = GlobalXCanadaScraper(delay=1.5)

    results = []
    for ticker in test_tickers:
        print(f"\n{'=' * 70}")
        print(f"Testing: {ticker}")
        print('=' * 70)

        data = scraper.scrape_etf(ticker)

        # Display summary
        print(f"\n✓ Successfully scraped {ticker}")

        if 'error' in data:
            print(f"❌ Error: {data['error']}")
            results.append(data)
            continue

        # Show extracted data
        print("\nExtracted Data Summary:")
        print("-" * 50)

        if data['basic_info'].get('name'):
            print(f"Name: {data['basic_info']['name']}")

        if data['pricing']:
            print(f"\nPricing:")
            for key, value in data['pricing'].items():
                print(f"  {key}: {value}")

        if data['metrics']:
            print(f"\nMetrics:")
            for key, value in data['metrics'].items():
                print(f"  {key}: {value}")

        if data['distributions']:
            print(f"\nDistributions:")
            for key, value in data['distributions'].items():
                print(f"  {key}: {value}")

        if data['holdings']:
            print(f"\nTop Holdings: ({len(data['holdings'])} total)")
            for i, holding in enumerate(data['holdings'][:3], 1):
                print(f"  {i}. {holding.get('security', 'N/A')} - {holding.get('weight', 'N/A')}")
            if len(data['holdings']) > 3:
                print(f"  ... and {len(data['holdings']) - 3} more")

        if data['performance']:
            print(f"\nPerformance:")
            for period, value in data['performance'].items():
                print(f"  {period}: {value}%")

        if data['calendar_returns']:
            print(f"\nCalendar Returns: ({len(data['calendar_returns'])} years)")
            recent_years = sorted(data['calendar_returns'].keys(), reverse=True)[:3]
            for year in recent_years:
                print(f"  {year}: {data['calendar_returns'][year]}%")

        if data['distribution_history']:
            print(f"\nDistribution History: {len(data['distribution_history'])} payments")

        results.append(data)

    # Save results
    output_file = 'globalx_test_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print(f"\nResults saved to: {output_file}")
    print(f"Total ETFs tested: {len(results)}")
    print(f"Successful: {sum(1 for r in results if 'error' not in r)}")
    print(f"Errors: {sum(1 for r in results if 'error' in r)}")

if __name__ == "__main__":
    test_sample_etfs()
