#!/usr/bin/env python3
"""
Backfill exchange metadata for existing stocks in the database.
Infers exchange from symbol suffix (e.g., .TO = TSX, .L = LSE)
"""

import sys
from supabase_helpers import get_supabase_client, supabase_update

def infer_exchange_from_symbol(symbol):
    """Infer exchange from symbol suffix."""
    if '.' not in symbol:
        # US symbols without suffix - likely NASDAQ or NYSE
        # We'll default to NASDAQ for now
        if symbol.isalpha() and len(symbol) <= 5:
            return 'NASDAQ'
        return None

    suffix = symbol.split('.')[-1].upper()

    # US and Canadian exchanges only
    exchange_map = {
        'TO': 'TSX',    # Toronto Stock Exchange
        'V': 'TSXV',    # TSX Venture
        'CN': 'CSE',    # Canadian Securities Exchange
    }

    return exchange_map.get(suffix)

def backfill_exchanges(batch_size=1000):
    """Backfill exchange metadata for all stocks."""
    print("🔄 Starting exchange metadata backfill...")

    supabase = get_supabase_client()

    # Get all stocks without exchange data
    offset = 0
    total_updated = 0
    total_processed = 0

    while True:
        # Fetch batch of stocks
        result = supabase.table('raw_stocks').select('symbol, exchange').is_('exchange', 'null').range(offset, offset + batch_size - 1).execute()

        if not result.data:
            break

        batch = result.data
        print(f"\n📊 Processing batch: {offset} to {offset + len(batch)}")

        # Process each stock
        for stock in batch:
            symbol = stock['symbol']
            current_exchange = stock.get('exchange')

            # Skip if exchange already set
            if current_exchange:
                continue

            # Infer exchange
            inferred_exchange = infer_exchange_from_symbol(symbol)

            if inferred_exchange:
                # Update database
                try:
                    supabase_update('stocks',
                                  {'exchange': inferred_exchange},
                                  where_clause={'condition': 'symbol = %s', 'params': [symbol]})
                    total_updated += 1

                    # Log every 100 updates
                    if total_updated % 100 == 0:
                        print(f"  ✅ Updated {total_updated} stocks so far...")
                except Exception as e:
                    print(f"  ❌ Error updating {symbol}: {e}")

            total_processed += 1

        # Move to next batch
        offset += batch_size

        # If we got fewer results than batch_size, we're done
        if len(batch) < batch_size:
            break

    print(f"\n" + "="*80)
    print(f"✅ Backfill complete!")
    print(f"   Total processed: {total_processed:,}")
    print(f"   Total updated: {total_updated:,}")
    print(f"   Not updated: {total_processed - total_updated:,} (no suffix to infer exchange)")

    # Show exchange distribution
    print(f"\n📊 Exchange distribution after backfill:")
    result = supabase.table('raw_stocks').select('exchange', count='exact').execute()

    exchange_counts = {}
    for stock in result.data:
        ex = stock.get('exchange')
        if ex:
            exchange_counts[ex] = exchange_counts.get(ex, 0) + 1

    for exchange, count in sorted(exchange_counts.items(), key=lambda x: -x[1]):
        print(f"   {exchange}: {count:,} stocks")

    null_count = len([s for s in result.data if not s.get('exchange')])
    print(f"   (null): {null_count:,} stocks")

if __name__ == "__main__":
    try:
        backfill_exchanges()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
