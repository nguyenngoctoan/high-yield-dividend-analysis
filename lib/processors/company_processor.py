"""
Company Processor Module

Processes and stores company/ETF information from multiple sources.
Handles both stock company data and ETF-specific metadata.
"""

import logging
from typing import List, Dict, Any, Optional

from lib.core.config import Config
from lib.core.models import CompanyInfo, ProcessingStats
from lib.data_sources.fmp_client import FMPClient
from lib.data_sources.yahoo_client import YahooClient
from supabase_helpers import supabase_batch_upsert, supabase_update

logger = logging.getLogger(__name__)


class CompanyProcessor:
    """
    Processes company and ETF information from multiple sources.

    Features:
    - Stock company profiles
    - ETF-specific metadata (fund family, expense ratio, etc.)
    - Hybrid fetching with fallback
    - Batch and single-record operations
    - Statistics tracking
    """

    def __init__(self,
                 fmp_client: Optional[FMPClient] = None,
                 yahoo_client: Optional[YahooClient] = None):
        """
        Initialize company processor.

        Args:
            fmp_client: Optional FMP client
            yahoo_client: Optional Yahoo client
        """
        self.fmp_client = fmp_client or FMPClient()
        self.yahoo_client = yahoo_client or YahooClient()

        self.stats = ProcessingStats()

    def fetch_company_info(self, symbol: str,
                          use_hybrid: bool = True) -> Optional[CompanyInfo]:
        """
        Fetch company/ETF information with hybrid fallback.

        Strategy:
        1. Try FMP for company profile
        2. For ETFs, try FMP ETF-specific endpoint
        3. Fallback to Yahoo Finance for enhanced data

        Args:
            symbol: Stock/ETF symbol
            use_hybrid: Enable hybrid fallback

        Returns:
            CompanyInfo model or None
        """
        logger.debug(f"🏢 Fetching company info for {symbol}")

        company_data = {}

        # Try FMP company profile
        try:
            fmp_profile = self.fmp_client.fetch_company_info(symbol)
            if fmp_profile:
                company_data.update(fmp_profile)
                logger.debug(f"✅ {symbol}: Got company profile from FMP")

                # If it's an ETF, get ETF-specific data
                if fmp_profile.get('is_etf'):
                    etf_info = self.fmp_client.fetch_etf_info(symbol)
                    if etf_info:
                        company_data.update(etf_info)
                        logger.debug(f"✅ {symbol}: Got ETF info from FMP")
        except Exception as e:
            logger.debug(f"⚠️  {symbol}: FMP company info failed - {e}")

        # Fallback/supplement with Yahoo Finance
        if use_hybrid and Config.DATA_FETCH.FALLBACK_TO_YAHOO:
            try:
                yahoo_info = self.yahoo_client.fetch_company_info(symbol)
                if yahoo_info:
                    # Merge data, preferring existing FMP data
                    for key, value in yahoo_info.items():
                        if key not in company_data or company_data[key] is None:
                            company_data[key] = value

                    logger.debug(f"✅ {symbol}: Enhanced with Yahoo data")
            except Exception as e:
                logger.debug(f"⚠️  {symbol}: Yahoo company info failed - {e}")

        if not company_data:
            logger.warning(f"❌ {symbol}: No company info available")
            return None

        # Create CompanyInfo model
        try:
            company_info = CompanyInfo(
                symbol=symbol,
                company_name=company_data.get('company_name'),
                description=company_data.get('description'),
                sector=company_data.get('sector'),
                industry=company_data.get('industry'),
                website=company_data.get('website'),
                ceo=company_data.get('ceo'),
                employees=company_data.get('employees'),
                market_cap=company_data.get('market_cap'),
                fund_family=company_data.get('fund_family'),
                expense_ratio=company_data.get('expense_ratio'),
                aum=company_data.get('aum'),
                inception_date=company_data.get('inception_date'),
                is_etf=company_data.get('is_etf', False),
                exchange=company_data.get('exchange'),
                currency=company_data.get('currency'),
                country=company_data.get('country')
            )

            logger.debug(
                f"✅ {symbol}: Created CompanyInfo "
                f"(type: {'ETF' if company_info.is_etf else 'Stock'})"
            )
            return company_info

        except Exception as e:
            logger.error(f"❌ {symbol}: Failed to create CompanyInfo model - {e}")
            return None

    def process_and_store(self, symbol: str,
                         use_hybrid: bool = True,
                         update_existing: bool = True) -> bool:
        """
        Fetch and store company information for a symbol.

        Args:
            symbol: Stock/ETF symbol
            use_hybrid: Enable hybrid fallback
            update_existing: Update existing records (vs insert only)

        Returns:
            True if successful
        """
        self.stats.total_processed += 1

        try:
            # Fetch company info
            company_info = self.fetch_company_info(symbol, use_hybrid)

            if not company_info:
                logger.debug(f"❌ {symbol}: No company info to store")
                self.stats.failed += 1
                return False

            # Prepare database record
            db_record = company_info.to_dict()

            # Update the stocks table
            if update_existing:
                result = supabase_update(
                    'raw_stocks',
                    {'symbol': symbol},
                    db_record
                )
            else:
                # Insert/upsert
                result = supabase_batch_upsert(
                    'raw_stocks',
                    [db_record],
                    batch_size=1
                )

            if result:
                logger.info(
                    f"✅ {symbol}: Stored company info "
                    f"(type: {'ETF' if company_info.is_etf else 'Stock'}, "
                    f"name: {company_info.display_name})"
                )
                self.stats.successful += 1
                return True
            else:
                logger.error(f"❌ {symbol}: Failed to store company info")
                self.stats.failed += 1
                return False

        except Exception as e:
            logger.error(f"❌ {symbol}: Company processing error - {e}")
            self.stats.failed += 1
            self.stats.add_error(f"{symbol}: {str(e)}")
            return False

    def process_batch(self, symbols: List[str],
                     use_hybrid: bool = True,
                     update_existing: bool = True) -> Dict[str, bool]:
        """
        Process company information for multiple symbols.

        Args:
            symbols: List of symbols
            use_hybrid: Enable hybrid fallback
            update_existing: Update existing records

        Returns:
            Dictionary mapping symbol -> success status
        """
        # Company data caching: Only refresh stale company data
        original_count = len(symbols)
        if Config.DATA_FETCH.CACHE_COMPANY_DATA:
            from datetime import datetime, timedelta
            from supabase_helpers import get_supabase_client

            try:
                cache_days = Config.DATA_FETCH.COMPANY_CACHE_DAYS
                cutoff_date = datetime.now() - timedelta(days=cache_days)

                logger.info(f"⚡ Checking company data cache ({cache_days} day threshold)...")

                # Get symbols with recent company updates (within cache period)
                # We want symbols where:
                # 1. company IS NOT NULL (has company data)
                # 2. updated_at is recent (within cache period)
                supabase = get_supabase_client()

                # Query for symbols with recent company data
                result = supabase.table('raw_stocks') \
                    .select('symbol, updated_at') \
                    .not_.is_('company', 'null') \
                    .gte('updated_at', cutoff_date.isoformat()) \
                    .in_('symbol', symbols) \
                    .execute()

                if result.data:
                    # These symbols have recent company data - skip them
                    recent_symbols = {r['symbol'] for r in result.data}
                    symbols = [s for s in symbols if s not in recent_symbols]

                    skipped = original_count - len(symbols)
                    if skipped > 0:
                        logger.info(
                            f"⚡ COMPANY CACHE: Skipping {skipped:,} symbols with recent data "
                            f"(processing {len(symbols):,} stale/new symbols)"
                        )
                        logger.info(f"   Time saved: ~{skipped * 0.5:.0f}s (estimated)")
                else:
                    logger.info(f"⚡ No cached company data found, processing all {len(symbols):,} symbols")

            except Exception as e:
                logger.warning(f"⚠️  Company cache check failed: {e}, processing all symbols")

        self.stats.start()
        logger.info(f"🏢 Processing company info for {len(symbols)} symbols")

        results = {}

        for symbol in symbols:
            success = self.process_and_store(
                symbol,
                use_hybrid=use_hybrid,
                update_existing=update_existing
            )
            results[symbol] = success

        self.stats.complete()

        logger.info(
            f"🎉 Batch complete: {self.stats.successful} successful, "
            f"{self.stats.failed} failed, {len(symbols)} total "
            f"in {self.stats.duration_seconds:.2f}s"
        )

        return results

    def refresh_null_company_names(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Refresh company names for stocks with NULL company fields.

        Useful for filling in missing data from previous incomplete runs.

        Args:
            limit: Optional limit on number of symbols to process

        Returns:
            Dictionary with processing results
        """
        logger.info(f"🔄 Refreshing NULL company names (limit: {limit or 'None'})")

        from supabase_helpers import supabase_select

        # Find symbols with NULL company (not company_name - that's the field in CompanyInfo model)
        query_conditions = {'company': None}  # Fixed: raw_stocks table has 'company' column, not 'company_name'
        null_symbols = supabase_select(
            'raw_stocks',
            'symbol',  # Just fetch symbol, we don't use is_etf
            where_clause=query_conditions,  # Fixed: was 'conditions', should be 'where_clause'
            limit=limit
        )

        if not null_symbols:
            logger.info("✅ No symbols with NULL company names found")
            return {'processed': 0, 'successful': 0, 'failed': 0, 'success_rate': 'N/A'}

        symbols = [s['symbol'] for s in null_symbols]
        logger.info(f"📊 Found {len(symbols)} symbols with NULL company names")

        # Process them
        results = self.process_batch(symbols, use_hybrid=True, update_existing=True)

        # Summary
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful

        summary = {
            'processed': len(results),
            'successful': successful,
            'failed': failed,
            'success_rate': f"{(successful / len(results) * 100):.2f}%" if results else "N/A"
        }

        logger.info(
            f"🎉 Refresh complete: {successful} successful, "
            f"{failed} failed, {len(results)} total"
        )

        return summary

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return self.stats.to_dict()


# Convenience functions
def process_company_info(symbol: str) -> bool:
    """
    Quick function to process company info for a symbol.

    Args:
        symbol: Stock/ETF symbol

    Returns:
        True if successful

    Example:
        success = process_company_info('AAPL')
    """
    processor = CompanyProcessor()
    return processor.process_and_store(symbol)


def process_company_info_batch(symbols: List[str]) -> Dict[str, bool]:
    """
    Quick function to process company info for multiple symbols.

    Args:
        symbols: List of symbols

    Returns:
        Dictionary of results

    Example:
        results = process_company_info_batch(['AAPL', 'MSFT', 'GOOGL'])
    """
    processor = CompanyProcessor()
    return processor.process_batch(symbols)


def refresh_null_companies(limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Quick function to refresh NULL company names.

    Args:
        limit: Optional limit on symbols to process

    Returns:
        Summary dictionary

    Example:
        summary = refresh_null_companies(limit=1000)
        print(f"Fixed {summary['successful']} companies")
    """
    processor = CompanyProcessor()
    return processor.refresh_null_company_names(limit=limit)


# Export main classes and functions
__all__ = [
    'CompanyProcessor',
    'process_company_info',
    'process_company_info_batch',
    'refresh_null_companies'
]
