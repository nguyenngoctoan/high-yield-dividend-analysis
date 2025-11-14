"""
Rate Limiting Middleware
Implements monthly + per-minute rate limiting with burst support
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import time
import logging

from supabase_helpers import get_supabase_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded"""
    def __init__(self, limit_type: str, reset_time: int, detail: str = None):
        self.limit_type = limit_type
        self.reset_time = reset_time
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail or f"{limit_type} rate limit exceeded. Try again after {reset_time} seconds.",
            headers={
                "Retry-After": str(reset_time),
                "X-RateLimit-Type": limit_type
            }
        )


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with dual protection:
    - Monthly call limits
    - Per-minute call limits with burst support
    """

    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/callback",
            "/auth/logout",
            "/auth/status"
        ]

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Extract API key
        api_key = self._extract_api_key(request)

        if not api_key:
            # No API key - allow through (will be caught by auth middleware)
            return await call_next(request)

        try:
            # Check rate limits
            rate_limit_info = await self._check_rate_limits(api_key)

            # Add rate limit headers to request state
            request.state.rate_limit_info = rate_limit_info

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            self._add_rate_limit_headers(response, rate_limit_info)

            return response

        except RateLimitExceeded as e:
            # Return 429 with rate limit info
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": e.detail,
                    "limit_type": e.limit_type,
                    "retry_after": e.reset_time
                },
                headers=e.headers
            )
        except Exception as e:
            logger.error(f"Rate limiter error: {e}", exc_info=True)
            # On error, allow the request through
            return await call_next(request)

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request headers or query params"""
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]

        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key

        # Check query parameter
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key

        return None

    async def _check_rate_limits(self, api_key_hash: str) -> Dict:
        """
        Check both monthly and per-minute rate limits
        Returns rate limit info or raises RateLimitExceeded
        """
        # Get API key info from database
        key_info = await self._get_key_info(api_key_hash)

        if not key_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        # Check if key is active
        if not key_info['is_active']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key is inactive"
            )

        # Get tier limits
        tier = key_info['tier']
        limits = await self._get_tier_limits(tier)

        # Check monthly limit
        await self._check_monthly_limit(key_info, limits)

        # Check per-minute limit
        await self._check_minute_limit(key_info, limits)

        # Increment usage counters
        await self._increment_usage(key_info['id'])

        # Return rate limit info
        return {
            "tier": tier,
            "monthly_limit": limits['monthly_call_limit'],
            "monthly_remaining": limits['monthly_call_limit'] - key_info['monthly_usage'] - 1,
            "monthly_reset": int(key_info['monthly_usage_reset_at'].timestamp()),
            "minute_limit": limits['calls_per_minute'],
            "minute_remaining": limits['calls_per_minute'] - key_info['minute_usage'] - 1,
            "minute_reset": int((key_info['minute_window_start'] + timedelta(minutes=1)).timestamp())
        }

    async def _get_key_info(self, api_key_hash: str) -> Optional[Dict]:
        """Get API key info from database"""
        try:
            # In production, you'd hash the API key first
            # For now, assuming key_hash column stores the prefix for lookup
            result = supabase.table('divv_api_keys').select(
                'id, tier, is_active, monthly_usage, monthly_usage_reset_at, '
                'minute_usage, minute_window_start'
            ).eq('key_hash', api_key_hash).eq('is_active', True).single().execute()

            if result.data:
                return result.data

            return None
        except Exception as e:
            logger.error(f"Error fetching API key info: {e}")
            return None

    async def _get_tier_limits(self, tier: str) -> Dict:
        """Get tier limits from database"""
        try:
            result = supabase.table('tier_limits').select(
                'monthly_call_limit, calls_per_minute, burst_limit'
            ).eq('tier', tier).single().execute()

            return result.data
        except Exception as e:
            logger.error(f"Error fetching tier limits: {e}")
            # Return default free tier limits as fallback
            return {
                'monthly_call_limit': 10000,
                'calls_per_minute': 10,
                'burst_limit': 20
            }

    async def _check_monthly_limit(self, key_info: Dict, limits: Dict):
        """Check if monthly limit is exceeded"""
        # Reset monthly counter if needed
        reset_time = key_info.get('monthly_usage_reset_at')
        if reset_time and datetime.now().timestamp() >= reset_time.timestamp():
            await self._reset_monthly_usage(key_info['id'])
            key_info['monthly_usage'] = 0

        # Check limit
        if key_info['monthly_usage'] >= limits['monthly_call_limit']:
            reset_at = key_info['monthly_usage_reset_at']
            reset_seconds = int((reset_at - datetime.now()).total_seconds())

            raise RateLimitExceeded(
                limit_type="monthly",
                reset_time=reset_seconds,
                detail=f"Monthly limit of {limits['monthly_call_limit']} calls exceeded. "
                       f"Limit resets in {reset_seconds} seconds."
            )

    async def _check_minute_limit(self, key_info: Dict, limits: Dict):
        """Check if per-minute limit is exceeded (with burst support)"""
        now = datetime.now()
        window_start = key_info.get('minute_window_start')

        # Reset minute counter if window expired
        if not window_start or (now - window_start).total_seconds() >= 60:
            await self._reset_minute_usage(key_info['id'])
            key_info['minute_usage'] = 0
            key_info['minute_window_start'] = now

        # Check limit (with burst allowance)
        burst_limit = limits['burst_limit']
        current_usage = key_info['minute_usage']

        if current_usage >= burst_limit:
            # Calculate time until next minute window
            reset_at = window_start + timedelta(minutes=1)
            reset_seconds = int((reset_at - now).total_seconds())

            raise RateLimitExceeded(
                limit_type="minute",
                reset_time=reset_seconds,
                detail=f"Per-minute limit of {limits['calls_per_minute']} calls "
                       f"(burst: {burst_limit}) exceeded. Try again in {reset_seconds} seconds."
            )

    async def _increment_usage(self, api_key_id: str):
        """Increment usage counters"""
        try:
            # Increment both monthly and minute usage
            supabase.rpc('increment_key_usage', {
                'key_id': api_key_id
            }).execute()
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")

    async def _reset_monthly_usage(self, api_key_id: str):
        """Reset monthly usage counter"""
        try:
            supabase.table('divv_api_keys').update({
                'monthly_usage': 0,
                'monthly_usage_reset_at': datetime.now() + timedelta(days=30)
            }).eq('id', api_key_id).execute()
        except Exception as e:
            logger.error(f"Error resetting monthly usage: {e}")

    async def _reset_minute_usage(self, api_key_id: str):
        """Reset minute usage counter"""
        try:
            supabase.table('divv_api_keys').update({
                'minute_usage': 0,
                'minute_window_start': datetime.now()
            }).eq('id', api_key_id).execute()
        except Exception as e:
            logger.error(f"Error resetting minute usage: {e}")

    def _add_rate_limit_headers(self, response, rate_limit_info: Dict):
        """Add rate limit headers to response"""
        if not rate_limit_info:
            return

        response.headers["X-RateLimit-Tier"] = rate_limit_info['tier']

        # Monthly headers
        response.headers["X-RateLimit-Limit-Month"] = str(rate_limit_info['monthly_limit'])
        response.headers["X-RateLimit-Remaining-Month"] = str(rate_limit_info['monthly_remaining'])
        response.headers["X-RateLimit-Reset-Month"] = str(rate_limit_info['monthly_reset'])

        # Per-minute headers
        response.headers["X-RateLimit-Limit-Minute"] = str(rate_limit_info['minute_limit'])
        response.headers["X-RateLimit-Remaining-Minute"] = str(rate_limit_info['minute_remaining'])
        response.headers["X-RateLimit-Reset-Minute"] = str(rate_limit_info['minute_reset'])


# Helper function to create SQL function for incrementing usage
INCREMENT_USAGE_SQL = """
CREATE OR REPLACE FUNCTION increment_key_usage(key_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE divv_api_keys
    SET
        monthly_usage = monthly_usage + 1,
        minute_usage = minute_usage + 1,
        request_count = request_count + 1,
        last_used_at = NOW(),
        updated_at = NOW()
    WHERE id = key_id;
END;
$$ LANGUAGE plpgsql;
"""
