#!/usr/bin/env python3
"""
Delete all non-US/Canadian symbols from the database.

This script will remove international symbols from:
- stocks table
- stock_prices table
- dividend_history table
- dividend_calendar table
"""

import sys
from supabase_helpers import get_supabase_client, supabase_delete

# US and Canadian exchanges to KEEP
ALLOWED_EXCHANGES = [
    "NYSE", "NASDAQ", "AMEX", "BATS", "BTS", "BYX", "BZX", "CBOE",
    "EDGA", "EDGX", "PCX", "NGM",
    "OTCM", "OTCX", "OTC",  # OTC markets
    "TSX", "TSXV", "CSE", "TSE", "NEO"  # Canadian exchanges
]

def get_international_symbols():
    """Get list of all symbols with non-US/Canadian exchanges."""
    print("🔍 Finding international symbols to delete...")

    supabase = get_supabase_client()

    # Get all stocks with exchange data
    result = supabase.table('stocks').select('symbol, exchange').execute()

    international_symbols = []
    by_exchange = {}

    for stock in result.data:
        exchange = stock.get('exchange')
        symbol = stock.get('symbol')

        if exchange and exchange not in ALLOWED_EXCHANGES:
            international_symbols.append(symbol)
            by_exchange[exchange] = by_exchange.get(exchange, 0) + 1

    print(f"\n📊 Found {len(international_symbols)} international symbols to delete:")
    print("=" * 60)
    for exchange, count in sorted(by_exchange.items(), key=lambda x: -x[1]):
        print(f"  {exchange:15} {count:,} symbols")
    print("=" * 60)

    return international_symbols, by_exchange

def delete_from_table(table_name, symbols, batch_size=100):
    """Delete symbols from a table in batches."""
    print(f"\n🗑️  Deleting from {table_name}...")

    supabase = get_supabase_client()
    total_deleted = 0

    # Process in batches
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]

        try:
            # Delete using direct Supabase client
            result = supabase.table(table_name).delete().in_('symbol', batch).execute()
            deleted_count = len(result.data) if result.data else 0
            total_deleted += deleted_count

            if (i // batch_size + 1) % 10 == 0:
                print(f"  Processed {i + len(batch):,} / {len(symbols):,} symbols...")
        except Exception as e:
            print(f"  ⚠️  Error deleting batch {i // batch_size + 1}: {e}")

    print(f"  ✅ Deleted {total_deleted:,} records from {table_name}")
    return total_deleted

def main():
    print("=" * 80)
    print("🌍 INTERNATIONAL SYMBOL CLEANUP")
    print("=" * 80)
    print("\nThis will DELETE all non-US/Canadian symbols from the database.")
    print(f"Keeping only: {', '.join(ALLOWED_EXCHANGES[:8])}...")
    print("\n⚠️  WARNING: This action cannot be undone!")

    # Get symbols to delete
    symbols_to_delete, exchange_breakdown = get_international_symbols()

    if not symbols_to_delete:
        print("\n✅ No international symbols found. Database is already clean!")
        return

    print(f"\n📝 Total symbols to delete: {len(symbols_to_delete):,}")

    # Confirm
    response = input("\n❓ Proceed with deletion? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("❌ Deletion cancelled.")
        return

    print("\n🚀 Starting deletion process...")
    print("=" * 80)

    # Delete from each table
    tables = ['dividend_calendar', 'dividend_history', 'stock_prices', 'stocks']

    results = {}
    for table in tables:
        results[table] = delete_from_table(table, symbols_to_delete)

    print("\n" + "=" * 80)
    print("✅ CLEANUP COMPLETE")
    print("=" * 80)
    print("\nDeletion Summary:")
    for table, count in results.items():
        print(f"  {table:20} {count:,} records deleted")

    # Show final stats
    print("\n📊 Verifying final database state...")
    supabase = get_supabase_client()

    result = supabase.table('stocks').select('exchange', count='exact').execute()
    exchanges = {}
    for stock in result.data:
        ex = stock.get('exchange') or 'NULL'
        exchanges[ex] = exchanges.get(ex, 0) + 1

    print("\n📈 Final Exchange Distribution:")
    print("=" * 60)
    for exchange, count in sorted(exchanges.items(), key=lambda x: -x[1]):
        marker = "✅" if exchange == 'NULL' or exchange in ALLOWED_EXCHANGES else "❌"
        print(f"{marker} {exchange:15} {count:,} stocks")
    print("=" * 60)
    print(f"Total remaining: {sum(exchanges.values()):,} stocks")

    # Check for any remaining international symbols
    remaining_international = sum(
        count for ex, count in exchanges.items()
        if ex != 'NULL' and ex not in ALLOWED_EXCHANGES
    )

    if remaining_international > 0:
        print(f"\n⚠️  WARNING: {remaining_international} international symbols still remain!")
    else:
        print("\n✅ All international symbols successfully removed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
