"""
Tier Restriction Middleware
Enforces feature access and data restrictions based on user's pricing tier
"""

from fastapi import Request, HTTPException, status
from typing import Optional, List
from datetime import datetime
import logging

from api.middleware.tier_enforcer import TierEnforcer, get_tier_from_request
from api.config import settings

logger = logging.getLogger(__name__)


class TierRestrictions:
    """
    Centralized tier restrictions for all API endpoints
    """

    # Endpoints that require specific minimum tiers
    TIER_REQUIREMENTS = {
        # Bulk operations - Professional+ only
        '/v1/bulk/': 'professional',

        # Historical data endpoints - based on years requested
        # (will be enforced in the endpoint logic)
    }

    # Tier hierarchy for comparison
    TIER_HIERARCHY = {
        'free': 0,
        'starter': 1,
        'premium': 2,
        'professional': 3,
        'enterprise': 4
    }

    @classmethod
    def check_tier_access(cls, tier: str, required_tier: str) -> bool:
        """Check if user's tier meets the minimum required tier"""
        user_level = cls.TIER_HIERARCHY.get(tier, 0)
        required_level = cls.TIER_HIERARCHY.get(required_tier, 0)
        return user_level >= required_level

    @classmethod
    async def enforce_endpoint_tier(cls, request: Request, required_tier: str):
        """
        Dependency function to enforce tier requirement on endpoints

        Usage in router:
        @router.get("/endpoint", dependencies=[Depends(TierRestrictions.enforce_professional_tier)])
        """
        tier = await get_tier_from_request(request)

        if not cls.check_tier_access(tier, required_tier):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_tier",
                    "message": f"This endpoint requires {required_tier} tier or higher. Current tier: {tier}",
                    "required_tier": required_tier,
                    "current_tier": tier,
                    "upgrade_url": f"{settings.FRONTEND_URL}/pricing"
                }
            )

    @classmethod
    async def enforce_professional_tier(cls, request: Request):
        """Dependency: Require Professional tier or higher"""
        return await cls.enforce_endpoint_tier(request, 'professional')

    @classmethod
    async def enforce_premium_tier(cls, request: Request):
        """Dependency: Require Premium tier or higher"""
        return await cls.enforce_endpoint_tier(request, 'premium')

    @classmethod
    async def enforce_starter_tier(cls, request: Request):
        """Dependency: Require Starter tier or higher"""
        return await cls.enforce_endpoint_tier(request, 'starter')

    @classmethod
    async def check_historical_data_access(cls, tier: str, years_requested: int) -> bool:
        """
        Check if tier has access to requested years of historical data

        Returns True if allowed, False otherwise
        """
        limits = await TierEnforcer.get_tier_limits(tier)
        max_years = limits.get('historical_years', 1)
        return years_requested <= max_years

    @classmethod
    async def get_max_historical_years(cls, tier: str) -> int:
        """Get maximum years of historical data for tier"""
        limits = await TierEnforcer.get_tier_limits(tier)
        return limits.get('historical_years', 1)

    @classmethod
    async def check_price_frequency_access(cls, tier: str, frequency: str) -> bool:
        """
        Check if tier has access to requested price data frequency

        Frequency: 'eod' (only supported frequency)
        """
        limits = await TierEnforcer.get_tier_limits(tier)
        allowed_frequency = limits.get('price_data_frequency', 'eod')

        frequency_hierarchy = {
            'eod': 0,
        }

        allowed_level = frequency_hierarchy.get(allowed_frequency, 0)
        requested_level = frequency_hierarchy.get(frequency, 0)

        return requested_level <= allowed_level

    @classmethod
    async def enforce_historical_data_limit(cls, request: Request, years_requested: int):
        """Enforce historical data access based on tier"""
        tier = await get_tier_from_request(request)
        max_years = await cls.get_max_historical_years(tier)

        if years_requested > max_years:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "historical_data_limit_exceeded",
                    "message": f"Requested {years_requested} years of data, but {tier} tier allows maximum {max_years} years",
                    "max_years": max_years,
                    "requested_years": years_requested,
                    "current_tier": tier,
                    "upgrade_url": f"{settings.FRONTEND_URL}/pricing"
                }
            )

    @classmethod
    async def enforce_price_frequency(cls, request: Request, frequency: str):
        """Enforce price data frequency based on tier"""
        tier = await get_tier_from_request(request)

        if not await cls.check_price_frequency_access(tier, frequency):
            limits = await TierEnforcer.get_tier_limits(tier)
            allowed_frequency = limits.get('price_data_frequency', 'eod')

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "price_frequency_not_available",
                    "message": f"{frequency} data requires higher tier. {tier} tier has access to {allowed_frequency} data",
                    "allowed_frequency": allowed_frequency,
                    "requested_frequency": frequency,
                    "current_tier": tier,
                    "upgrade_url": f"{settings.FRONTEND_URL}/pricing"
                }
            )


# Convenience dependencies for common tier requirements
async def require_professional_tier(request: Request):
    """FastAPI dependency: Require Professional tier"""
    return await TierRestrictions.enforce_professional_tier(request)


async def require_premium_tier(request: Request):
    """FastAPI dependency: Require Premium tier"""
    return await TierRestrictions.enforce_premium_tier(request)


async def require_starter_tier(request: Request):
    """FastAPI dependency: Require Starter tier"""
    return await TierRestrictions.enforce_starter_tier(request)
