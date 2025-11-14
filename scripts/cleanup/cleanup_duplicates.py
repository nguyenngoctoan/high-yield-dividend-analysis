#!/usr/bin/env python3
"""
Cleanup Duplicates Script

Removes duplicate records from stock_prices and dividend_history tables.
Keeps the most recent record (highest created_at/id) for each unique key.
"""

import sys
from pathlib import Path
import psycopg2
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

def cleanup_duplicates():
    """Remove duplicates from stock_prices and dividend_history tables."""

    conn = psycopg2.connect(
        host='localhost',
        port=5434,
        database='postgres',
        user='postgres',
        password=os.getenv('PGPASSWORD', 'postgres')
    )
    cursor = conn.cursor()

    print("=" * 80)
    print("DUPLICATE CLEANUP SCRIPT")
    print("=" * 80)

    # =========================================================================
    # 1. Check and clean raw_stock_prices duplicates
    # =========================================================================
    print("\n📊 CHECKING raw_stock_prices TABLE...")
    print("-" * 80)

    # Find duplicates
    cursor.execute("""
        SELECT symbol, date, COUNT(*) as cnt
        FROM raw_stock_prices
        GROUP BY symbol, date
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 10;
    """)

    stock_price_dupes = cursor.fetchall()

    if stock_price_dupes:
        total_dupes = sum(row[2] - 1 for row in stock_price_dupes)
        print(f"⚠️  Found duplicates in raw_stock_prices:")
        for symbol, date, count in stock_price_dupes[:5]:
            print(f"   - {symbol} on {date}: {count} records")

        if len(stock_price_dupes) > 5:
            print(f"   ... and {len(stock_price_dupes) - 5} more")

        print(f"\n🧹 Cleaning up {total_dupes} duplicate records...")

        # Delete duplicates, keeping the newest record (highest id)
        cursor.execute("""
            WITH duplicates AS (
                SELECT
                    id,
                    symbol,
                    date,
                    ROW_NUMBER() OVER (
                        PARTITION BY symbol, date
                        ORDER BY created_at DESC NULLS LAST, id DESC
                    ) as rn
                FROM raw_stock_prices
            )
            DELETE FROM raw_stock_prices
            WHERE id IN (
                SELECT id FROM duplicates WHERE rn > 1
            );
        """)

        deleted_count = cursor.rowcount
        print(f"✅ Deleted {deleted_count} duplicate records from raw_stock_prices")
    else:
        print("✅ No duplicates found in raw_stock_prices")

    # =========================================================================
    # 2. Check and clean raw_dividends duplicates
    # =========================================================================
    print("\n💰 CHECKING raw_dividends TABLE...")
    print("-" * 80)

    # Find duplicates
    cursor.execute("""
        SELECT symbol, ex_date, COUNT(*) as cnt
        FROM raw_dividends
        GROUP BY symbol, ex_date
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        LIMIT 10;
    """)

    dividend_dupes = cursor.fetchall()

    if dividend_dupes:
        total_dupes = sum(row[2] - 1 for row in dividend_dupes)
        print(f"⚠️  Found duplicates in raw_dividends:")
        for symbol, ex_date, count in dividend_dupes[:5]:
            print(f"   - {symbol} on {ex_date}: {count} records")

        if len(dividend_dupes) > 5:
            print(f"   ... and {len(dividend_dupes) - 5} more")

        print(f"\n🧹 Cleaning up {total_dupes} duplicate records...")

        # Delete duplicates, keeping the newest record (highest id)
        cursor.execute("""
            WITH duplicates AS (
                SELECT
                    id,
                    symbol,
                    ex_date,
                    ROW_NUMBER() OVER (
                        PARTITION BY symbol, ex_date
                        ORDER BY created_at DESC NULLS LAST, id DESC
                    ) as rn
                FROM raw_dividends
            )
            DELETE FROM raw_dividends
            WHERE id IN (
                SELECT id FROM duplicates WHERE rn > 1
            );
        """)

        deleted_count = cursor.rowcount
        print(f"✅ Deleted {deleted_count} duplicate records from raw_dividends")
    else:
        print("✅ No duplicates found in raw_dividends")

    # =========================================================================
    # 3. Verify unique constraints exist
    # =========================================================================
    print("\n🔒 VERIFYING UNIQUE CONSTRAINTS...")
    print("-" * 80)

    # Check raw_stock_prices constraint
    cursor.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'raw_stock_prices'
        AND constraint_type = 'UNIQUE';
    """)

    sp_constraints = cursor.fetchall()
    if sp_constraints:
        print(f"✅ raw_stock_prices has unique constraint(s):")
        for (constraint_name,) in sp_constraints:
            print(f"   - {constraint_name}")
    else:
        print("⚠️  raw_stock_prices missing unique constraint!")
        print("   Adding constraint on (symbol, date)...")
        cursor.execute("""
            ALTER TABLE raw_stock_prices
            ADD CONSTRAINT raw_stock_prices_symbol_date_key UNIQUE (symbol, date);
        """)
        print("✅ Added unique constraint to raw_stock_prices")

    # Check raw_dividends constraint
    cursor.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'raw_dividends'
        AND constraint_type = 'UNIQUE';
    """)

    dh_constraints = cursor.fetchall()
    if dh_constraints:
        print(f"✅ raw_dividends has unique constraint(s):")
        for (constraint_name,) in dh_constraints:
            print(f"   - {constraint_name}")
    else:
        print("⚠️  raw_dividends missing unique constraint!")
        print("   Adding constraint on (symbol, ex_date)...")
        cursor.execute("""
            ALTER TABLE raw_dividends
            ADD CONSTRAINT unique_symbol_ex_date UNIQUE (symbol, ex_date);
        """)
        print("✅ Added unique constraint to raw_dividends")

    # Commit changes
    conn.commit()

    # =========================================================================
    # 4. Final verification
    # =========================================================================
    print("\n✅ FINAL VERIFICATION...")
    print("-" * 80)

    # Verify no duplicates in raw_stock_prices
    cursor.execute("""
        SELECT COUNT(*) as total_dupes
        FROM (
            SELECT symbol, date, COUNT(*) as cnt
            FROM raw_stock_prices
            GROUP BY symbol, date
            HAVING COUNT(*) > 1
        ) dupes;
    """)

    sp_dupes = cursor.fetchone()[0]
    print(f"raw_stock_prices duplicates remaining: {sp_dupes}")

    # Verify no duplicates in raw_dividends
    cursor.execute("""
        SELECT COUNT(*) as total_dupes
        FROM (
            SELECT symbol, ex_date, COUNT(*) as cnt
            FROM raw_dividends
            GROUP BY symbol, ex_date
            HAVING COUNT(*) > 1
        ) dupes;
    """)

    dh_dupes = cursor.fetchone()[0]
    print(f"raw_dividends duplicates remaining: {dh_dupes}")

    # Get table counts
    cursor.execute("SELECT COUNT(*) FROM raw_stock_prices;")
    sp_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM raw_dividends;")
    dh_count = cursor.fetchone()[0]

    print(f"\nFinal record counts:")
    print(f"  raw_stock_prices: {sp_count:,} records")
    print(f"  raw_dividends: {dh_count:,} records")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    if sp_dupes == 0 and dh_dupes == 0:
        print("🎉 SUCCESS: All duplicates cleaned up!")
    else:
        print("⚠️  WARNING: Some duplicates may remain. Review manually.")
    print("=" * 80)


if __name__ == '__main__':
    try:
        cleanup_duplicates()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
