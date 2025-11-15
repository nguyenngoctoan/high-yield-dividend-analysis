"""
Tier Enforcement Middleware
Restricts stock coverage and features based on user's pricing tier
"""

from fastapi import Request, HTTPException, status
from typing import Optional, Dict, List
import logging

from supabase_helpers import get_supabase_client
from api.config import settings

logger = logging.getLogger(__name__)
supabase = get_supabase_client()


class TierEnforcer:
    """
    Enforces tier-based restrictions on stock coverage and features
    """

    # Cache for tier limits
    _tier_limits_cache: Dict[str, Dict] = {}

    @classmethod
    async def get_tier_limits(cls, tier: str) -> Dict:
        """Get tier limits from cache or database"""
        if tier not in cls._tier_limits_cache:
            try:
                result = supabase.table('divv_tier_limits').select('*').eq('tier', tier).single().execute()
                cls._tier_limits_cache[tier] = result.data
            except Exception as e:
                logger.error(f"Error fetching tier limits for {tier}: {e}")
                # Return free tier as fallback
                return {
                    'tier': 'free',
                    'monthly_call_limit': 5000,
                    'calls_per_minute': 10,
                    'stock_coverage': {'type': 'sample', 'count': 150},
                    'features': {'bulk_export': False, 'webhooks': False},
                    'historical_years': 1,
                    'price_data_frequency': 'eod',
                    'support_level': 'community',
                    'portfolio_limit': 0
                }

        return cls._tier_limits_cache[tier]

    @classmethod
    async def check_symbol_access(cls, tier: str, symbol: str) -> bool:
        """
        Check if a symbol is accessible for the given tier

        Returns:
            True if symbol is accessible, False otherwise
        """
        limits = await cls.get_tier_limits(tier)
        stock_coverage = limits.get('stock_coverage', {})
        coverage_type = stock_coverage.get('type', 'sample')

        # Enterprise and Professional tiers have access to all symbols
        if tier in ['enterprise', 'professional']:
            return True

        # Premium tier: US + International stocks
        if tier == 'premium':
            return await cls._check_symbol_in_coverage(symbol, ['US', 'CA', 'UK', 'DE', 'FR', 'AU'])

        # Starter tier: US stocks only
        if tier == 'starter':
            return await cls._check_symbol_in_coverage(symbol, ['US'])

        # Free tier: Sample dataset only
        if tier == 'free':
            return await cls._check_symbol_in_free_tier(symbol)

        return False

    @classmethod
    async def check_symbols_access(cls, tier: str, symbols: List[str]) -> Dict[str, bool]:
        """
        Check access for multiple symbols

        Returns:
            Dictionary mapping symbol -> access boolean
        """
        results = {}
        for symbol in symbols:
            results[symbol] = await cls.check_symbol_access(tier, symbol)
        return results

    @classmethod
    async def filter_accessible_symbols(cls, tier: str, symbols: List[str]) -> List[str]:
        """
        Filter a list of symbols to only those accessible by the tier

        Returns:
            List of accessible symbols
        """
        access_map = await cls.check_symbols_access(tier, symbols)
        return [symbol for symbol, accessible in access_map.items() if accessible]

    @classmethod
    async def _check_symbol_in_coverage(cls, symbol: str, allowed_countries: List[str]) -> bool:
        """Check if symbol's exchange country is in allowed list"""
        try:
            # Get stock info from database
            result = supabase.table('raw_stocks').select('exchange').eq('symbol', symbol).single().execute()

            if not result.data:
                return False

            exchange = result.data.get('exchange', '')

            # Map exchanges to countries
            exchange_country_map = {
                'NYSE': 'US', 'NASDAQ': 'US', 'AMEX': 'US', 'BATS': 'US', 'CBOE': 'US',
                'TSX': 'CA', 'TSE': 'CA',
                'LSE': 'UK',
                'XETRA': 'DE',
                'EPA': 'FR', 'Euronext': 'FR',
                'ASX': 'AU'
            }

            country = exchange_country_map.get(exchange, 'US')
            return country in allowed_countries

        except Exception as e:
            logger.error(f"Error checking symbol coverage for {symbol}: {e}")
            return False

    @classmethod
    async def _check_symbol_in_free_tier(cls, symbol: str) -> bool:
        """Check if symbol is in the free tier sample dataset"""
        try:
            result = supabase.table('divv_free_tier_stocks').select('symbol').eq('symbol', symbol).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking free tier access for {symbol}: {e}")
            return False

    @classmethod
    async def check_feature_access(cls, tier: str, feature: str) -> bool:
        """
        Check if a feature is accessible for the given tier

        Features:
            - bulk_export: CSV/Excel downloads
            - webhooks: Webhook notifications
            - max_bulk_symbols: Maximum symbols per bulk request
            - custom_screeners: Save custom screeners
            - portfolio_tracking: Number of portfolios allowed
            - intraday_data: Access to hourly/minute data
            - real_time_dividends: Real-time dividend announcements
        """
        limits = await cls.get_tier_limits(tier)
        features = limits.get('features', {})

        # Check boolean features
        if feature in ['bulk_export', 'webhooks', 'custom_screeners', 'white_label']:
            return features.get(feature, False)

        # Check numeric features (return the value, not boolean)
        if feature == 'max_bulk_symbols':
            return features.get('max_bulk_symbols', 0) > 0

        if feature == 'portfolio_limit':
            return limits.get('portfolio_limit', 0)

        # Check data access features
        if feature == 'intraday_data':
            # Intraday data is not supported
            return False

        if feature == 'real_time_dividends':
            return tier in ['professional', 'enterprise']

        return False

    @classmethod
    async def get_max_bulk_symbols(cls, tier: str) -> int:
        """Get maximum number of symbols allowed in bulk requests"""
        limits = await cls.get_tier_limits(tier)
        features = limits.get('features', {})
        return features.get('max_bulk_symbols', 0)

    @classmethod
    async def get_historical_data_years(cls, tier: str) -> int:
        """Get number of years of historical data allowed"""
        limits = await cls.get_tier_limits(tier)
        return limits.get('historical_years', 1)

    @classmethod
    async def get_price_data_frequency(cls, tier: str) -> str:
        """Get allowed price data frequency (eod only)"""
        limits = await cls.get_tier_limits(tier)
        return limits.get('price_data_frequency', 'eod')

    @classmethod
    def enforce_symbol_access(cls, tier: str):
        """
        Dependency function for FastAPI routes
        Returns a function that checks symbol access
        """
        async def check_access(symbol: str):
            accessible = await cls.check_symbol_access(tier, symbol)
            if not accessible:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "access_denied",
                        "message": f"Symbol {symbol} is not accessible on the {tier} tier",
                        "upgrade_url": f"{settings.FRONTEND_URL}/pricing"
                    }
                )
            return True
        return check_access

    @classmethod
    def enforce_feature_access(cls, tier: str, feature: str):
        """
        Dependency function for FastAPI routes
        Returns a function that checks feature access
        """
        async def check_feature():
            accessible = await cls.check_feature_access(tier, feature)
            if not accessible:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "feature_not_available",
                        "message": f"Feature '{feature}' is not available on the {tier} tier",
                        "upgrade_url": f"{settings.FRONTEND_URL}/pricing"
                    }
                )
            return True
        return check_feature

    @classmethod
    def enforce_bulk_limit(cls, tier: str):
        """
        Dependency function for FastAPI routes
        Returns a function that checks bulk request limits
        """
        async def check_bulk_limit(symbols: List[str]):
            max_symbols = await cls.get_max_bulk_symbols(tier)

            if max_symbols == 0:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "bulk_requests_not_available",
                        "message": f"Bulk requests are not available on the {tier} tier",
                        "upgrade_url": f"{settings.FRONTEND_URL}/pricing"
                    }
                )

            if len(symbols) > max_symbols:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "bulk_limit_exceeded",
                        "message": f"Requested {len(symbols)} symbols, but {tier} tier allows maximum {max_symbols} symbols per request",
                        "max_symbols": max_symbols,
                        "requested_symbols": len(symbols),
                        "upgrade_url": f"{settings.FRONTEND_URL}/pricing"
                    }
                )

            return True
        return check_bulk_limit


# Helper function to get tier from request
async def get_tier_from_request(request: Request) -> str:
    """
    Extract tier from request state (set by rate limiter middleware)
    Falls back to 'free' if no API key present
    """
    if hasattr(request.state, 'rate_limit_info'):
        return request.state.rate_limit_info.get('tier', 'free')
    return 'free'
