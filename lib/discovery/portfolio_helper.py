"""
Portfolio Helper Module

Provides functions to get symbols from user portfolios that should bypass validation.
"""

import logging
from typing import List, Set
from supabase_helpers import supabase_select

logger = logging.getLogger(__name__)


def get_portfolio_symbols() -> Set[str]:
    """
    Get all unique symbols from user portfolios.

    These symbols should bypass strict validation rules because they are
    actively held in user portfolios.

    Returns:
        Set of symbols that exist in user portfolios
    """
    try:
        import os
        import psycopg2
        import json

        # Get database connection details
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5434')
        db_name = os.environ.get('DB_NAME', 'postgres')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD', 'postgres')

        # Connect to database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )

        cursor = conn.cursor()

        # Query to extract symbols from positions JSONB
        # The structure is: positions -> array of position objects -> 'symbol' -> 'symbol' (nested) -> 'symbol' (ticker)
        query = """
        SELECT DISTINCT
            pos->'symbol'->'symbol'->>'symbol' AS symbol
        FROM raw_portfolio_holdings,
        LATERAL jsonb_array_elements(positions) AS pos
        WHERE positions IS NOT NULL
        AND pos->'symbol'->'symbol'->>'symbol' IS NOT NULL
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        symbols = set()
        for row in rows:
            if row and row[0]:
                symbol = row[0].strip()
                if symbol:
                    symbols.add(symbol)

        cursor.close()
        conn.close()

        logger.info(f"✅ Found {len(symbols)} unique symbols in user portfolios")
        if symbols:
            logger.debug(f"   Sample portfolio symbols: {', '.join(sorted(list(symbols)[:10]))}")

        return symbols

    except Exception as e:
        logger.error(f"❌ Error fetching portfolio symbols: {e}")
        # Return empty set on error - don't break validation
        return set()


def is_portfolio_symbol(symbol: str) -> bool:
    """
    Check if a symbol exists in any user portfolio.

    Args:
        symbol: Symbol to check

    Returns:
        True if symbol is in a portfolio, False otherwise
    """
    portfolio_symbols = get_portfolio_symbols()
    return symbol in portfolio_symbols


# Export main functions
__all__ = ['get_portfolio_symbols', 'is_portfolio_symbol']
