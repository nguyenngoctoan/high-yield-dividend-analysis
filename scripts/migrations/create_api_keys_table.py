#!/usr/bin/env python3
"""
Create API Keys Table
Run this script to create the divv_api_keys table in the database.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_helpers import get_supabase_client

def create_api_keys_table():
    """Create the divv_api_keys table."""
    supabase = get_supabase_client()
    
    # Read the migration SQL
    migration_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations',
        'create_divv_api_keys.sql'
    )
    
    with open(migration_file, 'r') as f:
        sql = f.read()
    
    # Execute the SQL using Supabase's RPC
    try:
        # Split into individual statements and execute
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                print(f"Executing: {statement[:80]}...")
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print("✓ Success")
        
        print("\n✓ API Keys table created successfully!")
        
        # Verify table exists
        result = supabase.table('divv_api_keys').select('count').limit(0).execute()
        print(f"✓ Table verified: divv_api_keys")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTrying alternative approach with direct table creation...")
        
        # Try creating through Supabase directly (this might not work for DDL)
        print("Note: You may need to run this SQL directly in the Supabase SQL Editor:")
        print(sql)
        return False
    
    return True

if __name__ == '__main__':
    create_api_keys_table()
