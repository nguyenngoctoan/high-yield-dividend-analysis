#!/usr/bin/env python3
"""
Supabase Helper Functions
This module provides Supabase client equivalents for all PostgreSQL operations
used in the dividend tracker project.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global Supabase client instance
_supabase_client = None

def get_supabase_client() -> Optional[Client]:
    """Get or create a Supabase client instance."""
    global _supabase_client

    if _supabase_client is None:
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')

            if not supabase_url or not supabase_key:
                logger.error("❌ Supabase credentials not found in environment")
                return None

            _supabase_client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Error creating Supabase client: {e}")
            return None

    return _supabase_client

def test_supabase_connection() -> bool:
    """Test Supabase connection and return success status."""
    try:
        supabase = get_supabase_client()
        if supabase:
            # Test with a simple query
            result = supabase.table('raw_stocks').select('symbol').limit(1).execute()
            logger.info("✅ Supabase connection successful")
            return True
        else:
            logger.error("❌ Supabase client initialization failed")
            return False
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        return False

def ensure_stocks_excluded_table() -> bool:
    """Ensure raw_stocks_excluded table exists. Create it if missing."""
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False

        # Try to query the table
        try:
            result = supabase.table('raw_stocks_excluded').select('symbol').limit(1).execute()
            logger.info("✅ raw_stocks_excluded table already exists")
            return True
        except Exception as e:
            if "relation" in str(e).lower() and "does not exist" in str(e).lower():
                logger.info("📦 raw_stocks_excluded table doesn't exist, attempting to create it...")

                # Since we can't execute raw SQL through Supabase client,
                # we'll create a placeholder by inserting and deleting
                try:
                    # Create a dummy record to trigger table creation
                    # Note: This won't work with the full schema, but will at least
                    # create the table structure
                    logger.warning("⚠️ Cannot create raw_stocks_excluded table programmatically.")
                    logger.warning("Please create the table manually using Supabase Studio.")
                    logger.warning("Navigate to: http://127.0.0.1:3004/")
                    logger.warning("Use the SQL Editor with the contents of: create_stocks_excluded_table.sql")
                    return False
                except Exception as create_error:
                    logger.error(f"❌ Failed to create raw_stocks_excluded table: {create_error}")
                    return False
            else:
                logger.error(f"❌ Error checking raw_stocks_excluded table: {e}")
                return False
    except Exception as e:
        logger.error(f"❌ Error in ensure_stocks_excluded_table: {e}")
        return False

def initialize_supabase_connection() -> bool:
    """Initialize and test Supabase connection."""
    try:
        if not test_supabase_connection():
            raise Exception("Supabase connection test failed")

        # Ensure required tables exist
        ensure_stocks_excluded_table()

        logger.info("✅ Supabase connection initialized and tested successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Error initializing Supabase connection: {e}")
        return False

def supabase_select(table: str, columns: str = "*",
                   where_clause: Optional[Dict] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None,
                   order_by: Optional[str] = None) -> List[Dict]:
    """
    Execute SELECT query on Supabase with automatic pagination for large datasets.

    Args:
        table: Table name
        columns: Columns to select (comma-separated string or "*")
        where_clause: Dictionary with 'condition' and optional 'params'
        limit: Maximum number of rows to return (None = all rows with pagination)
        offset: Number of rows to skip
        order_by: Column to order by (can include "DESC")

    Returns:
        List of dictionaries representing rows
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []

        # If no limit specified, paginate through all results
        if limit is None and offset is None:
            all_results = []
            page_size = 1000
            current_offset = 0

            while True:
                query = supabase.table(table)

                # Handle column selection
                if columns != "*":
                    columns_clean = columns.replace(" ", "")
                    query = query.select(columns_clean)
                else:
                    query = query.select("*")

                # Apply where clause
                query = _apply_where_clause(query, where_clause)

                # Apply order by
                query = _apply_order_by(query, order_by)

                # Apply pagination
                query = query.range(current_offset, current_offset + page_size - 1)

                result = query.execute()
                if not result.data:
                    break

                all_results.extend(result.data)

                # If we got less than page_size, we're done
                if len(result.data) < page_size:
                    break

                current_offset += page_size

            return all_results

        # Standard query with explicit limit/offset
        query = supabase.table(table)

        # Handle column selection
        if columns != "*":
            columns = columns.replace(" ", "")
            query = query.select(columns)
        else:
            query = query.select("*")

        # Apply where clause
        query = _apply_where_clause(query, where_clause)

        # Apply order by
        query = _apply_order_by(query, order_by)

        # Handle LIMIT and OFFSET
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.range(offset, offset + (limit or 1000) - 1)

        result = query.execute()
        return result.data if result.data else []

    except Exception as e:
        logger.error(f"❌ Supabase select error on {table}: {e}")
        return []


def _apply_where_clause(query, where_clause: Optional[Dict]):
    """Helper to apply where clause to query."""
    if not where_clause:
        return query

    # Check if it's the new simple dictionary format or old format
    if 'condition' in where_clause or 'params' in where_clause:
        # Old format with condition and params
        condition = where_clause.get('condition', '')
        params = where_clause.get('params', [])

        # Parse simple conditions
        if 'symbol = %s' in condition and params:
            query = query.eq('symbol', params[0])
        elif 'symbol IN %s' in condition and params:
            symbols_list = params[0] if isinstance(params[0], (list, tuple)) else [params[0]]
            query = query.in_('symbol', symbols_list)
        elif 'AND' in condition.upper():
            # Handle compound conditions
            parts = condition.split('AND')
            param_index = 0

            for part in parts:
                part = part.strip()
                if 'symbol = %s' in part and param_index < len(params):
                    query = query.eq('symbol', params[param_index])
                    param_index += 1
                elif 'date >= %s' in part and param_index < len(params):
                    query = query.gte('date', str(params[param_index]))
                    param_index += 1
                elif 'date <= %s' in part and param_index < len(params):
                    query = query.lte('date', str(params[param_index]))
                    param_index += 1
                elif 'ex_date >= %s' in part and param_index < len(params):
                    query = query.gte('ex_date', str(params[param_index]))
                    param_index += 1
                elif 'ex_date <= %s' in part and param_index < len(params):
                    query = query.lte('ex_date', str(params[param_index]))
                    param_index += 1
        elif 'date >= %s' in condition and params:
            query = query.gte('date', str(params[0]))
        elif 'date <= %s' in condition and params:
            query = query.lte('date', str(params[0]))
        elif '=' in condition:
            # Simple equality check
            parts = condition.split('=')
            if len(parts) == 2:
                col = parts[0].strip()
                if '%s' in parts[1] and params:
                    query = query.eq(col, params[0])
                else:
                    val = parts[1].strip().strip("'\"")
                    query = query.eq(col, val)
    else:
        # New simple format: {'column': 'value'}
        for key, value in where_clause.items():
            if value is None:
                query = query.is_(key, 'null')
            else:
                query = query.eq(key, value)

    return query


def _apply_order_by(query, order_by: Optional[str]):
    """Helper to apply order by to query."""
    if not order_by:
        return query

    # Handle .desc and .asc suffix notation
    if '.desc' in order_by.lower():
        column = order_by.replace('.desc', '').replace('.DESC', '').strip()
        query = query.order(column, desc=True)
    elif '.asc' in order_by.lower():
        column = order_by.replace('.asc', '').replace('.ASC', '').strip()
        query = query.order(column, desc=False)
    elif 'DESC' in order_by.upper():
        column = order_by.replace(' DESC', '').replace(' desc', '').strip()
        query = query.order(column, desc=True)
    elif 'ASC' in order_by.upper():
        column = order_by.replace(' ASC', '').replace(' asc', '').strip()
        query = query.order(column, desc=False)
    else:
        query = query.order(order_by)

    return query

def supabase_insert(table: str, data: Union[Dict, List[Dict]],
                   on_conflict: Optional[str] = None, batch_size: int = 500) -> List[Dict]:
    """
    Execute INSERT query on Supabase.
    Automatically batches large datasets to prevent timeouts.

    Args:
        table: Table name
        data: Single dictionary or list of dictionaries to insert
        on_conflict: Conflict resolution strategy (not directly supported by Supabase client)
        batch_size: Number of records per batch (default: 500)

    Returns:
        List of inserted rows
    """
    if not data:
        return []

    try:
        supabase = get_supabase_client()
        if not supabase:
            return []

        # Convert single dict to list
        if isinstance(data, dict):
            data = [data]

        # Convert datetime objects to strings
        for row in data:
            for key, value in row.items():
                if isinstance(value, (datetime, date)):
                    row[key] = value.isoformat()

        # Process in batches to prevent timeouts
        all_results = []
        total_records = len(data)

        if total_records > batch_size:
            logger.info(f"📦 Batching {total_records} records into chunks of {batch_size}")

        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_records + batch_size - 1) // batch_size

            if total_records > batch_size:
                logger.info(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")

            try:
                result = supabase.table(table).insert(batch).execute()
                if result.data:
                    all_results.extend(result.data)
            except Exception as batch_error:
                logger.error(f"❌ Batch {batch_num} failed: {batch_error}")
                # If it's a duplicate key error and on_conflict is specified, try upsert for this batch
                if on_conflict and 'duplicate' in str(batch_error).lower():
                    upsert_result = supabase_upsert(table, batch, batch_size=batch_size)
                    if upsert_result:
                        all_results.extend(upsert_result)
                continue

        if total_records > batch_size:
            logger.info(f"✅ Completed batched insert: {len(all_results)}/{total_records} records processed")

        return all_results

    except Exception as e:
        logger.error(f"❌ Supabase insert error on {table}: {e}")
        # If it's a duplicate key error and on_conflict is specified, try upsert
        if on_conflict and 'duplicate' in str(e).lower():
            return supabase_upsert(table, data, batch_size=batch_size)
        return []

def supabase_upsert(table: str, data: Union[Dict, List[Dict]], batch_size: int = 500) -> List[Dict]:
    """
    Execute UPSERT (INSERT ... ON CONFLICT DO UPDATE) on Supabase.
    Automatically batches large datasets to prevent timeouts.

    Args:
        table: Table name
        data: Single dictionary or list of dictionaries to upsert
        batch_size: Number of records per batch (default: 500)

    Returns:
        List of upserted rows
    """
    if not data:
        return []

    try:
        supabase = get_supabase_client()
        if not supabase:
            return []

        # Convert single dict to list
        if isinstance(data, dict):
            data = [data]

        # Convert datetime objects to strings
        for row in data:
            for key, value in row.items():
                if isinstance(value, (datetime, date)):
                    row[key] = value.isoformat()

        # Process in batches to prevent timeouts
        all_results = []
        total_records = len(data)

        if total_records > batch_size:
            logger.info(f"📦 Batching {total_records} records into chunks of {batch_size}")

        for i in range(0, total_records, batch_size):
            batch = data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_records + batch_size - 1) // batch_size

            if total_records > batch_size:
                logger.info(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} records)...")

            try:
                # Specify conflict columns for proper upsert behavior
                # Different tables have different unique constraints
                if table == 'raw_stock_prices':
                    # raw_stock_prices has unique constraint on (symbol, date)
                    result = supabase.table(table).upsert(batch, on_conflict='symbol,date').execute()
                elif table == 'raw_stock_prices_hourly':
                    # raw_stock_prices_hourly has unique constraint on (symbol, timestamp)
                    # Use insert with upsert=True instead of explicit upsert
                    result = supabase.table(table).insert(batch, upsert=True).execute()
                elif table == 'raw_dividends':
                    # raw_dividends has unique constraint on (symbol, ex_date)
                    # Use proper upsert to update existing records
                    result = supabase.table(table).upsert(batch, on_conflict='symbol,ex_date').execute()
                elif table == 'raw_stocks':
                    # raw_stocks has unique constraint on symbol
                    result = supabase.table(table).upsert(batch, on_conflict='symbol').execute()
                elif table == 'raw_stocks_excluded':
                    # raw_stocks_excluded has unique constraint on symbol
                    result = supabase.table(table).upsert(batch, on_conflict='symbol').execute()
                else:
                    # Default upsert without explicit conflict handling
                    result = supabase.table(table).upsert(batch).execute()

                if result.data:
                    all_results.extend(result.data)

            except Exception as batch_error:
                logger.error(f"❌ Batch {batch_num} failed: {batch_error}")
                # Continue with next batch instead of failing completely
                continue

        if total_records > batch_size:
            logger.info(f"✅ Completed batched upsert: {len(all_results)}/{total_records} records processed")

        return all_results

    except Exception as e:
        logger.error(f"❌ Supabase upsert error on {table}: {e}")
        return []

def supabase_delete(table: str, where_clause: Dict) -> bool:
    """
    Execute DELETE query on Supabase.

    Args:
        table: Table name
        where_clause: Dictionary with 'condition' and optional 'params'

    Returns:
        True if successful, False otherwise
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return False

        query = supabase.table(table)

        # Parse where clause
        condition = where_clause.get('condition', '')
        params = where_clause.get('params', [])

        if 'symbol = %s' in condition and params:
            query = query.delete().eq('symbol', params[0])
        elif 'symbol IN %s' in condition and params:
            symbols_list = params[0] if isinstance(params[0], (list, tuple)) else [params[0]]
            query = query.delete().in_('symbol', symbols_list)
        elif '=' in condition:
            parts = condition.split('=')
            if len(parts) == 2:
                col = parts[0].strip()
                if '%s' in parts[1] and params:
                    query = query.delete().eq(col, params[0])
                else:
                    val = parts[1].strip().strip("'\"")
                    query = query.delete().eq(col, val)

        result = query.execute()
        return True

    except Exception as e:
        logger.error(f"❌ Supabase delete error on {table}: {e}")
        return False

def supabase_update(table: str, where_clause: Dict, data: Dict) -> List[Dict]:
    """
    Execute UPDATE query on Supabase.

    Args:
        table: Table name
        where_clause: Dictionary with conditions (either simple {'column': 'value'} or old format with 'condition' and 'params')
        data: Dictionary of columns to update

    Returns:
        List of updated rows
    """
    try:
        supabase = get_supabase_client()
        if not supabase:
            return []

        # Convert datetime objects to strings
        for key, value in data.items():
            if isinstance(value, (datetime, date)):
                data[key] = value.isoformat()

        query = supabase.table(table).update(data)

        # Parse where clause - support both old and new formats
        if 'condition' in where_clause or 'params' in where_clause:
            # Old format with condition and params
            condition = where_clause.get('condition', '')
            params = where_clause.get('params', [])

            if 'symbol = %s' in condition and params:
                query = query.eq('symbol', params[0])
            elif '=' in condition:
                parts = condition.split('=')
                if len(parts) == 2:
                    col = parts[0].strip()
                    if '%s' in parts[1] and params:
                        query = query.eq(col, params[0])
                    else:
                        val = parts[1].strip().strip("'\"")
                        query = query.eq(col, val)
        else:
            # New simple format: {'column': 'value'}
            for key, value in where_clause.items():
                query = query.eq(key, value)

        result = query.execute()
        return result.data if result.data else []

    except Exception as e:
        logger.error(f"❌ Supabase update error on {table}: {e}")
        return []

# Batch operation helpers
def supabase_batch_upsert(table: str, data: List[Dict], batch_size: int = 1000) -> int:
    """
    Execute batch upsert operations on Supabase.

    Args:
        table: Table name
        data: List of dictionaries to upsert
        batch_size: Number of records per batch

    Returns:
        Total number of records upserted
    """
    if not data:
        return 0

    total_upserted = 0

    try:
        # Process in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            result = supabase_upsert(table, batch)
            if result:
                total_upserted += len(result)
                logger.info(f"✅ Batch upserted {len(result)} records to {table}")

        return total_upserted

    except Exception as e:
        logger.error(f"❌ Batch upsert error on {table}: {e}")
        return total_upserted

# Compatibility aliases (drop-in replacements for pg_* functions)
pg_select = supabase_select
pg_insert = supabase_insert
pg_upsert = supabase_upsert
pg_delete = supabase_delete
pg_update = supabase_update

# Additional helper functions
def get_excluded_symbols() -> set:
    """Get all excluded symbols from the database."""
    try:
        excluded = supabase_select('raw_stocks_excluded', 'symbol')
        return set(row['symbol'] for row in excluded)
    except Exception as e:
        logger.error(f"❌ Error fetching excluded symbols: {e}")
        return set()

def get_existing_symbols() -> set:
    """Get all existing symbols from the raw_stocks table."""
    try:
        stocks = supabase_select('raw_stocks', 'symbol')
        return set(row['symbol'] for row in stocks)
    except Exception as e:
        logger.error(f"❌ Error fetching existing symbols: {e}")
        return set()

def check_symbol_exists(symbol: str, table: str = 'raw_stocks') -> bool:
    """Check if a symbol exists in the specified table."""
    try:
        result = supabase_select(
            table,
            'symbol',
            {'condition': 'symbol = %s', 'params': [symbol]},
            limit=1
        )
        return len(result) > 0
    except Exception as e:
        logger.error(f"❌ Error checking symbol {symbol}: {e}")
        return False