"""
Symbol Prioritizer Module

Provides utilities for prioritizing symbols during batch processing.
Ensures high-priority symbols (portfolio holdings, high volume, large cap) are processed first.
"""

import logging
from typing import List, Dict, Any, Optional
from supabase_helpers import supabase_select

logger = logging.getLogger(__name__)


class SymbolPrioritizer:
    """
    Prioritize symbols for batch processing.

    Priority order:
    1. Portfolio holdings (user's actual investments)
    2. High trading volume (most active stocks)
    3. Large market cap (major companies)
    4. Everything else alphabetically
    """

    @staticmethod
    def get_priority_symbols(
        symbols: List[str],
        include_volume: bool = True,
        include_market_cap: bool = True
    ) -> Dict[str, int]:
        """
        Get priority scores for symbols.

        Args:
            symbols: List of symbols to prioritize
            include_volume: Include volume-based priority
            include_market_cap: Include market cap-based priority

        Returns:
            Dictionary mapping symbol -> priority score (higher = more important)
        """
        priority_scores = {symbol: 0 for symbol in symbols}

        try:
            # Fetch symbol data from database
            symbol_data = supabase_select(
                'raw_stocks',
                'symbol,volume,market_cap,exchange',
                where_clause={'symbol': f'in.({",".join(symbols)})'},
                limit=None
            )

            if not symbol_data:
                logger.debug("No symbol data found for prioritization")
                return priority_scores

            # Calculate priority scores
            for data in symbol_data:
                symbol = data.get('symbol')
                if symbol not in priority_scores:
                    continue

                score = 0

                # Volume priority (0-100 points)
                if include_volume and data.get('volume'):
                    volume = data['volume']
                    if volume > 100_000_000:  # Ultra high volume
                        score += 100
                    elif volume > 10_000_000:  # High volume
                        score += 75
                    elif volume > 1_000_000:  # Medium volume
                        score += 50
                    elif volume > 100_000:  # Low volume
                        score += 25

                # Market cap priority (0-100 points)
                if include_market_cap and data.get('market_cap'):
                    market_cap = data['market_cap']
                    if market_cap > 200_000_000_000:  # Mega cap ($200B+)
                        score += 100
                    elif market_cap > 10_000_000_000:  # Large cap ($10B+)
                        score += 75
                    elif market_cap > 2_000_000_000:  # Mid cap ($2B+)
                        score += 50
                    elif market_cap > 300_000_000:  # Small cap ($300M+)
                        score += 25

                # Exchange priority (0-50 points)
                # Prefer major exchanges (NYSE, NASDAQ) over OTC
                exchange = data.get('exchange', '').upper()
                if exchange in ('NYSE', 'NASDAQ'):
                    score += 50
                elif exchange in ('AMEX', 'TSX'):
                    score += 30
                elif exchange.startswith('OTC'):
                    score += 10

                priority_scores[symbol] = score

            logger.info(f"📊 Calculated priority scores for {len(priority_scores):,} symbols")

        except Exception as e:
            logger.warning(f"⚠️  Priority calculation failed: {e}")

        return priority_scores

    @staticmethod
    def prioritize_symbols(
        symbols: List[str],
        portfolio_symbols: Optional[List[str]] = None,
        include_volume: bool = True,
        include_market_cap: bool = True
    ) -> List[str]:
        """
        Sort symbols by priority (highest priority first).

        Args:
            symbols: List of symbols to prioritize
            portfolio_symbols: Optional list of portfolio holdings (highest priority)
            include_volume: Include volume-based priority
            include_market_cap: Include market cap-based priority

        Returns:
            Sorted list of symbols (highest priority first)
        """
        if not symbols:
            return []

        # Get base priority scores
        priority_scores = SymbolPrioritizer.get_priority_symbols(
            symbols,
            include_volume=include_volume,
            include_market_cap=include_market_cap
        )

        # Boost portfolio holdings to highest priority
        if portfolio_symbols:
            for symbol in portfolio_symbols:
                if symbol in priority_scores:
                    priority_scores[symbol] += 1000  # Ensure portfolio symbols come first

        # Sort by priority (descending), then alphabetically for ties
        sorted_symbols = sorted(
            symbols,
            key=lambda s: (-priority_scores.get(s, 0), s)
        )

        # Log top priorities
        if len(sorted_symbols) >= 10:
            top_10 = sorted_symbols[:10]
            logger.info(f"🎯 Top 10 priority symbols: {', '.join(top_10)}")

        return sorted_symbols

    @staticmethod
    def get_major_symbols(limit: int = 100) -> List[str]:
        """
        Get list of major symbols (high volume, large cap).

        Args:
            limit: Number of symbols to return

        Returns:
            List of major symbols
        """
        try:
            # Get high-volume, large-cap symbols
            result = supabase_select(
                'raw_stocks',
                'symbol',
                order_by='volume.desc,market_cap.desc',
                limit=limit
            )

            if result:
                symbols = [r['symbol'] for r in result]
                logger.info(f"📊 Found {len(symbols)} major symbols")
                return symbols

        except Exception as e:
            logger.warning(f"⚠️  Could not fetch major symbols: {e}")

        return []

    @staticmethod
    def split_priority_groups(
        symbols: List[str],
        portfolio_symbols: Optional[List[str]] = None,
        priority_limit: int = 1000
    ) -> tuple:
        """
        Split symbols into priority and standard groups.

        Args:
            symbols: List of symbols
            portfolio_symbols: Optional portfolio holdings
            priority_limit: Max number of priority symbols

        Returns:
            Tuple of (priority_symbols, standard_symbols)
        """
        # Prioritize all symbols
        sorted_symbols = SymbolPrioritizer.prioritize_symbols(
            symbols,
            portfolio_symbols=portfolio_symbols
        )

        # Split into priority and standard groups
        priority_symbols = sorted_symbols[:priority_limit]
        standard_symbols = sorted_symbols[priority_limit:]

        logger.info(
            f"🎯 Split into {len(priority_symbols):,} priority "
            f"and {len(standard_symbols):,} standard symbols"
        )

        return priority_symbols, standard_symbols


# Export main class
__all__ = ['SymbolPrioritizer']
