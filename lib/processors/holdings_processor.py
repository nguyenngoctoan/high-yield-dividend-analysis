"""
Holdings Processor Module

Processes and stores ETF holdings data from FMP API.
Handles fetching, validation, and storage of portfolio compositions.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from lib.core.config import Config
from lib.core.models import ProcessingStats
from lib.data_sources.fmp_client import FMPClient
from supabase_helpers import supabase_update, supabase_select, supabase_insert

logger = logging.getLogger(__name__)


class HoldingsProcessor:
    """
    Processes ETF holdings data from FMP API.

    Features:
    - Fetch holdings for ETFs
    - Store holdings as JSON in stocks table
    - Track update timestamps
    - Statistics tracking
    - Batch operations
    """

    def __init__(self, fmp_client: Optional[FMPClient] = None):
        """
        Initialize holdings processor.

        Args:
            fmp_client: Optional FMP client
        """
        self.fmp_client = fmp_client or FMPClient()
        self.stats = ProcessingStats()

    def fetch_and_store_holdings(self, symbol: str) -> bool:
        """
        Fetch and store holdings for a single ETF.

        Args:
            symbol: ETF symbol

        Returns:
            True if successful
        """
        self.stats.total_processed += 1

        try:
            # Fetch holdings from FMP
            holdings_data = self.fmp_client.fetch_etf_holdings(symbol)

            if not holdings_data or not holdings_data.get('holdings'):
                logger.debug(f"⚠️  {symbol}: No holdings data available")
                self.stats.skipped += 1
                return False

            # Prepare database update
            holdings_list = holdings_data['holdings']
            holdings_count = len(holdings_list)
            updated_at = holdings_data.get('updated_at')

            # Store holdings list directly (supabase will handle JSON conversion)
            update_data = {
                'holdings': holdings_list,  # Don't json.dumps() - supabase handles JSONB conversion
                'holdings_updated_at': updated_at or datetime.now().isoformat()
            }

            result = supabase_update(
                'raw_stocks',
                {'symbol': symbol},
                update_data
            )

            if result:
                # Also save to holdings_history table for tracking changes over time
                today = datetime.now().date().isoformat()
                history_record = {
                    'symbol': symbol,
                    'date': today,
                    'holdings': holdings_list,
                    'holdings_count': holdings_count,
                    'data_source': 'FMP'
                }

                try:
                    # Insert/update history record (upsert on conflict)
                    from supabase_helpers import get_supabase_client
                    supabase = get_supabase_client()
                    supabase.table('raw_holdings_history').upsert(history_record).execute()
                    logger.debug(f"  💾 {symbol}: Saved to holdings_history")
                except Exception as e:
                    logger.warning(f"  ⚠️  {symbol}: Failed to save history - {e}")
                    # Don't fail the whole operation if history save fails

                logger.info(
                    f"✅ {symbol}: Stored {holdings_count} holdings "
                    f"(updated: {updated_at or 'now'})"
                )
                self.stats.successful += 1
                return True
            else:
                logger.error(f"❌ {symbol}: Failed to store holdings")
                self.stats.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {symbol}: Holdings processing error - {e}")
            self.stats.failed += 1
            self.stats.add_error(f"{symbol}: {str(e)}")
            return False

    def process_batch(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Process holdings for multiple ETFs.

        Args:
            symbols: List of ETF symbols

        Returns:
            Dictionary mapping symbol -> success status
        """
        self.stats.start()
        logger.info(f"📊 Processing holdings for {len(symbols)} ETFs")

        results = {}

        for symbol in symbols:
            success = self.fetch_and_store_holdings(symbol)
            results[symbol] = success

        self.stats.complete()

        logger.info(
            f"🎉 Batch complete: {self.stats.successful} successful, "
            f"{self.stats.skipped} skipped (no holdings), "
            f"{self.stats.failed} failed, {len(symbols)} total "
            f"in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def update_all_etfs(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Update holdings for all ETFs in the database.

        Args:
            limit: Optional limit on number of ETFs to process

        Returns:
            Dictionary with processing results
        """
        logger.info(f"🔄 Updating holdings for all ETFs (limit: {limit or 'None'})")

        # Get all ETF symbols from database
        # We'll identify ETFs by investment_strategy field or by checking if they have holdings
        etf_records = supabase_select(
            'raw_stocks',
            'symbol,name,investment_strategy',
            limit=limit
        )

        if not etf_records:
            logger.warning("⚠️  No ETFs found in database")
            return {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}

        # Filter for likely ETFs (those with investment_strategy or ending in common ETF patterns)
        etf_symbols = []
        for record in etf_records:
            symbol = record['symbol']
            name = record.get('name', '')
            strategy = record.get('investment_strategy')

            # Consider it an ETF if:
            # 1. Has an investment_strategy (from our classification)
            # 2. Name contains 'ETF'
            # 3. Common ETF patterns (e.g., ends with Y, X for leveraged, etc.)
            is_likely_etf = (
                strategy is not None or
                'ETF' in name.upper() or
                'FUND' in name.upper()
            )

            if is_likely_etf:
                etf_symbols.append(symbol)

        logger.info(f"📊 Found {len(etf_symbols)} potential ETFs to process")

        if not etf_symbols:
            logger.warning("⚠️  No ETFs identified for holdings update")
            return {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0, 'success_rate': 'N/A'}

        # Process them
        results = self.process_batch(etf_symbols)

        # Summary
        successful = sum(1 for success in results.values() if success)
        failed = self.stats.failed
        skipped = self.stats.skipped

        summary = {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'skipped': skipped,
            'success_rate': f"{(successful / len(results) * 100):.2f}%" if results else "N/A"
        }

        logger.info(
            f"🎉 Holdings update complete: {successful} successful, "
            f"{skipped} skipped, {failed} failed, {len(results)} total"
        )

        return summary

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.to_dict()


# Convenience functions
def fetch_etf_holdings(symbol: str) -> bool:
    """
    Quick function to fetch and store holdings for an ETF.

    Args:
        symbol: ETF symbol

    Returns:
        True if successful

    Example:
        success = fetch_etf_holdings('SPY')
    """
    processor = HoldingsProcessor()
    return processor.fetch_and_store_holdings(symbol)


def update_all_etf_holdings(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Quick function to update holdings for all ETFs.

    Args:
        limit: Optional limit on ETFs to process

    Returns:
        Summary dictionary

    Example:
        summary = update_all_etf_holdings(limit=100)
        print(f"Updated {summary['successful']} ETFs")
    """
    processor = HoldingsProcessor()
    return processor.update_all_etfs(limit=limit)


# Export main classes and functions
__all__ = [
    'HoldingsProcessor',
    'fetch_etf_holdings',
    'update_all_etf_holdings'
]
