"""
Symbol Discovery Module

Orchestrates symbol discovery from multiple data sources (FMP, Alpha Vantage, Yahoo).
Combines results and deduplicates symbols for processing.
"""

import logging
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.core.config import Config
from lib.core.models import ProcessingStats
from lib.data_sources.fmp_client import FMPClient
from lib.data_sources.alpha_vantage_client import AlphaVantageClient
from lib.data_sources.yahoo_client import YahooClient

logger = logging.getLogger(__name__)


class SymbolDiscovery:
    """
    Orchestrates symbol discovery from multiple data sources.

    Combines symbols from FMP, Alpha Vantage, and other sources,
    removes duplicates, and returns a unified list for processing.
    """

    def __init__(self):
        """Initialize symbol discovery with data source clients."""
        self.fmp_client = FMPClient() if Config.FEATURES.ENABLE_FMP else None
        self.av_client = AlphaVantageClient() if Config.FEATURES.ENABLE_ALPHA_VANTAGE else None
        self.yahoo_client = YahooClient() if Config.FEATURES.ENABLE_YAHOO else None

        self.stats = ProcessingStats()

    def discover_all_symbols(self, limit: Optional[int] = None,
                            sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Discover symbols from all available sources.

        Args:
            limit: Optional limit per source
            sources: Optional list of sources to use ['fmp', 'av', 'yahoo']
                    If None, uses all available sources

        Returns:
            List of unique symbol dictionaries
        """
        self.stats.start()
        logger.info(f"🔍 Starting symbol discovery (limit: {limit or 'None'})")

        # Determine which sources to use
        if sources is None:
            sources = []
            if self.fmp_client and self.fmp_client.is_available():
                sources.append('fmp')
            if self.av_client and self.av_client.is_available():
                sources.append('av')
            # Yahoo doesn't support symbol discovery

        logger.info(f"📊 Using sources: {', '.join(sources) if sources else 'None'}")

        all_symbols = []
        discovered_symbols = set()

        # Discover from FMP
        if 'fmp' in sources and self.fmp_client:
            fmp_symbols = self._discover_from_fmp(limit)
            all_symbols.extend(fmp_symbols)
            discovered_symbols.update(s['symbol'] for s in fmp_symbols)
            logger.info(f"✅ FMP: {len(fmp_symbols)} symbols")

        # Discover from Alpha Vantage
        if 'av' in sources and self.av_client:
            av_symbols = self._discover_from_alpha_vantage(limit)
            # Only add symbols not already discovered
            new_symbols = [s for s in av_symbols if s['symbol'] not in discovered_symbols]
            all_symbols.extend(new_symbols)
            discovered_symbols.update(s['symbol'] for s in new_symbols)
            logger.info(f"✅ Alpha Vantage: {len(av_symbols)} total, {len(new_symbols)} new")

        self.stats.total_processed = len(all_symbols)
        self.stats.successful = len(all_symbols)
        self.stats.complete()

        logger.info(
            f"🎉 Discovery complete: {len(all_symbols)} unique symbols "
            f"in {self.stats.duration_seconds:.2f}s"
        )

        return all_symbols

    def discover_etfs(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discover ETFs specifically.

        Args:
            limit: Optional limit on number of ETFs

        Returns:
            List of ETF dictionaries
        """
        logger.info(f"🔍 Discovering ETFs (limit: {limit or 'None'})")

        if not self.fmp_client or not self.fmp_client.is_available():
            logger.warning("⚠️  FMP client not available for ETF discovery")
            return []

        etfs = self.fmp_client.discover_etfs()

        if limit:
            etfs = etfs[:limit]

        logger.info(f"✅ Discovered {len(etfs)} ETFs")
        return etfs

    def discover_dividend_stocks(self, min_yield: float = 0.01,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Discover dividend-paying stocks.

        Args:
            min_yield: Minimum dividend yield (default: 1%)
            limit: Optional limit on results

        Returns:
            List of dividend stock dictionaries
        """
        logger.info(
            f"🔍 Discovering dividend stocks "
            f"(yield > {min_yield:.1%}, limit: {limit or 'None'})"
        )

        if not self.fmp_client or not self.fmp_client.is_available():
            logger.warning("⚠️  FMP client not available for dividend stock discovery")
            return []

        dividend_stocks = self.fmp_client.discover_dividend_stocks(
            min_yield=min_yield,
            limit=limit
        )

        logger.info(f"✅ Discovered {len(dividend_stocks)} dividend stocks")
        return dividend_stocks

    def discover_comprehensive(self, include_etfs: bool = True,
                              include_dividend_stocks: bool = True,
                              limit_per_source: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Comprehensive discovery from all sources and methods.

        Args:
            include_etfs: Include comprehensive ETF list
            include_dividend_stocks: Include dividend stock screener
            limit_per_source: Optional limit per discovery method

        Returns:
            Deduplicated list of all discovered symbols
        """
        self.stats.start()
        logger.info("🔍 Starting comprehensive symbol discovery")

        all_symbols = []
        discovered_symbols: Set[str] = set()

        def add_symbols(new_symbols: List[Dict[str, Any]], source_name: str):
            """Helper to add symbols and track duplicates."""
            unique_new = [s for s in new_symbols if s['symbol'] not in discovered_symbols]
            all_symbols.extend(unique_new)
            discovered_symbols.update(s['symbol'] for s in unique_new)
            logger.info(
                f"✅ {source_name}: {len(new_symbols)} total, "
                f"{len(unique_new)} new, {len(discovered_symbols)} cumulative"
            )

        # 1. Regular symbol discovery
        regular_symbols = self.discover_all_symbols(limit=limit_per_source)
        add_symbols(regular_symbols, "Regular Discovery")

        # 2. ETF-specific discovery
        if include_etfs and self.fmp_client and self.fmp_client.is_available():
            etf_symbols = self.discover_etfs(limit=limit_per_source)
            add_symbols(etf_symbols, "ETF Discovery")

        # 3. Dividend stock discovery
        if include_dividend_stocks and self.fmp_client and self.fmp_client.is_available():
            div_symbols = self.discover_dividend_stocks(
                min_yield=0.01,
                limit=limit_per_source
            )
            add_symbols(div_symbols, "Dividend Discovery")

        self.stats.total_processed = len(all_symbols)
        self.stats.successful = len(all_symbols)
        self.stats.complete()

        logger.info(
            f"🎉 Comprehensive discovery complete: "
            f"{len(all_symbols)} unique symbols in {self.stats.duration_seconds:.2f}s"
        )

        return all_symbols

    def _discover_from_fmp(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Discover symbols from FMP."""
        if not self.fmp_client:
            return []

        try:
            return self.fmp_client.discover_symbols(limit=limit)
        except Exception as e:
            logger.error(f"❌ FMP discovery failed: {e}")
            self.stats.add_error(f"FMP: {str(e)}")
            return []

    def _discover_from_alpha_vantage(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Discover symbols from Alpha Vantage."""
        if not self.av_client:
            return []

        try:
            return self.av_client.discover_symbols(limit=limit)
        except Exception as e:
            logger.error(f"❌ Alpha Vantage discovery failed: {e}")
            self.stats.add_error(f"Alpha Vantage: {str(e)}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        return self.stats.to_dict()


# Convenience function for quick discovery
def discover_symbols(limit: Optional[int] = None,
                    sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Quick symbol discovery function.

    Args:
        limit: Optional limit per source
        sources: Optional list of sources ['fmp', 'av']

    Returns:
        List of symbol dictionaries

    Example:
        symbols = discover_symbols(limit=100, sources=['fmp'])
    """
    discovery = SymbolDiscovery()
    return discovery.discover_all_symbols(limit=limit, sources=sources)


def discover_etfs(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Quick ETF discovery function.

    Args:
        limit: Optional limit on ETFs

    Returns:
        List of ETF dictionaries

    Example:
        etfs = discover_etfs(limit=1000)
    """
    discovery = SymbolDiscovery()
    return discovery.discover_etfs(limit=limit)


def discover_dividend_stocks(min_yield: float = 0.01,
                             limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Quick dividend stock discovery function.

    Args:
        min_yield: Minimum dividend yield
        limit: Optional limit on results

    Returns:
        List of dividend stock dictionaries

    Example:
        stocks = discover_dividend_stocks(min_yield=0.05, limit=500)
    """
    discovery = SymbolDiscovery()
    return discovery.discover_dividend_stocks(min_yield=min_yield, limit=limit)


# Export main classes and functions
__all__ = [
    'SymbolDiscovery',
    'discover_symbols',
    'discover_etfs',
    'discover_dividend_stocks'
]
