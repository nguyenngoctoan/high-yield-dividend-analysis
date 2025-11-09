#!/usr/bin/env python3
"""Create tables in Supabase database."""

import os
from dotenv import load_dotenv
from supabase import create_client
import psycopg2
from psycopg2 import sql

load_dotenv()

# Connect to the database directly
DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

print("Creating tables in Supabase database...")
print("-" * 50)

try:
    # Connect to database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create stocks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) UNIQUE NOT NULL,
            company_name VARCHAR(255),
            exchange VARCHAR(50),
            sector VARCHAR(100),
            industry VARCHAR(100),
            market_cap BIGINT,
            price DECIMAL(10, 2),
            volume BIGINT,
            pe_ratio DECIMAL(10, 2),
            dividend_yield DECIMAL(10, 6),
            dividend_amount DECIMAL(10, 4),
            ex_dividend_date DATE,
            payment_date DATE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Created stocks table")

    # Create excluded_symbols table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS excluded_symbols (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) UNIQUE NOT NULL,
            reason VARCHAR(255),
            excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✅ Created excluded_symbols table")

    # Create price_history table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            date DATE NOT NULL,
            open DECIMAL(10, 2),
            high DECIMAL(10, 2),
            low DECIMAL(10, 2),
            close DECIMAL(10, 2),
            volume BIGINT,
            UNIQUE(symbol, date)
        );
    """)
    print("✅ Created price_history table")

    # Create dividend_history table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dividend_history (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(20) NOT NULL,
            ex_dividend_date DATE,
            payment_date DATE,
            record_date DATE,
            declaration_date DATE,
            amount DECIMAL(10, 4),
            currency VARCHAR(10) DEFAULT 'USD',
            UNIQUE(symbol, ex_dividend_date)
        );
    """)
    print("✅ Created dividend_history table")

    # Create indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stocks_symbol ON stocks(symbol);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stocks_dividend_yield ON stocks(dividend_yield DESC);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_price_history_symbol_date ON price_history(symbol, date DESC);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_dividend_history_symbol_date ON dividend_history(symbol, ex_dividend_date DESC);")
    print("✅ Created indexes")

    # Commit changes
    conn.commit()
    cur.close()
    conn.close()

    print("\n✅ Database setup complete!")
    print("\nYou can now run: ./run_nasdaq_full_update.sh")

except Exception as e:
    print(f"❌ Error creating tables: {e}")