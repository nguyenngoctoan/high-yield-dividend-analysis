"""
Rate Limiting Middleware
Implements monthly + per-minute rate limiting with burst support
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Tuple
import time
import logging
import hashlib
from dateutil import parser

from supabase_helpers import get_supabase_client, get_supabase_admin_client

logger = logging.getLogger(__name__)
supabase = get_supabase_client()  # For reading data
supabase_admin = get_supabase_admin_client()  # For admin operations (rate limiting)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit exceeded"""
    def __init__(self, limit_type: str, reset_time: int, rate_limit_info: Dict = None, detail: str = None):
        self.limit_type = limit_type
        self.reset_time = reset_time
        self.rate_limit_info = rate_limit_info
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
        logger.info(f"RateLimiterMiddleware.dispatch called for path: {request.url.path}")

        # Skip rate limiting for excluded paths (exact match or prefix match, but not "/")
        for excluded_path in self.exclude_paths:
            if excluded_path == "/" and request.url.path == "/":
                logger.info(f"Skipping rate limiting for root path")
                return await call_next(request)
            elif excluded_path != "/" and request.url.path.startswith(excluded_path):
                logger.info(f"Skipping rate limiting for excluded path: {request.url.path} (matched: {excluded_path})")
                return await call_next(request)

        # Extract API key
        api_key = self._extract_api_key(request)

        if api_key:
            logger.info(f"Rate limiter: path={request.url.path}, api_key_prefix={api_key[:12] if len(api_key) >= 12 else api_key}")
        else:
            logger.info(f"Rate limiter: path={request.url.path}, has_api_key=False")

        if not api_key:
            # No API key - allow through (will be caught by auth middleware)
            logger.info("No API key found, allowing request through")
            return await call_next(request)

        rate_limit_info = None
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
            # Return 429 with rate limit info and headers
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": e.detail,
                    "limit_type": e.limit_type,
                    "retry_after": e.reset_time
                },
                headers=e.headers
            )
            # Add rate limit headers to 429 response if available
            if e.rate_limit_info:
                self._add_rate_limit_headers(response, e.rate_limit_info)
            return response
        except HTTPException as e:
            # Return proper response for HTTP exceptions (401, 403, etc.)
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers=dict(e.headers) if e.headers else {}
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

    async def _check_rate_limits(self, api_key: str) -> Dict:
        """
        Check both monthly and per-minute rate limits
        Returns rate limit info or raises RateLimitExceeded
        """
        # Hash the API key to look it up in the database
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Get API key info from database
        key_info = await self._get_key_info(key_hash)

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

        # Build rate limit info (before checking limits, so it's available even if we hit the limit)
        rate_limit_info = {
            "tier": tier,
            "monthly_limit": limits['monthly_call_limit'],
            "monthly_remaining": max(0, limits['monthly_call_limit'] - key_info['monthly_usage'] - 1),
            "monthly_reset": int(key_info['monthly_usage_reset_at'].timestamp()),
            "minute_limit": limits['calls_per_minute'],
            "minute_remaining": max(0, limits['calls_per_minute'] - key_info['minute_usage'] - 1),
            "minute_reset": int((key_info['minute_window_start'] + timedelta(minutes=1)).timestamp())
        }

        # Check monthly limit
        await self._check_monthly_limit(key_info, limits, rate_limit_info)

        # Check per-minute limit
        await self._check_minute_limit(key_info, limits, rate_limit_info)

        # Increment usage counters
        await self._increment_usage(key_info['id'])

        # Return rate limit info
        return rate_limit_info

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse ISO timestamp string to datetime object"""
        if isinstance(timestamp_str, datetime):
            return timestamp_str
        return parser.isoparse(timestamp_str)

    async def _get_key_info(self, api_key_hash: str) -> Optional[Dict]:
        """Get API key info from database"""
        try:
            logger.info(f"Looking up API key with hash: {api_key_hash[:10]}...")
            # Look up API key by hash
            result = supabase.table('divv_api_keys').select(
                'id, tier, is_active, monthly_usage, monthly_usage_reset_at, '
                'minute_usage, minute_window_start'
            ).eq('key_hash', api_key_hash).eq('is_active', True).execute()

            logger.info(f"Query result: {len(result.data) if result.data else 0} rows")

            if result.data and len(result.data) > 0:
                key_info = result.data[0]
                # Parse timestamp strings to datetime objects
                if key_info.get('monthly_usage_reset_at'):
                    key_info['monthly_usage_reset_at'] = self._parse_timestamp(key_info['monthly_usage_reset_at'])
                if key_info.get('minute_window_start'):
                    key_info['minute_window_start'] = self._parse_timestamp(key_info['minute_window_start'])

                logger.info(f"Found API key: {key_info['id']}")
                return key_info

            logger.warning(f"No API key found for hash: {api_key_hash[:10]}...")
            return None
        except Exception as e:
            logger.error(f"Error fetching API key info: {e}")
            return None

    async def _get_tier_limits(self, tier: str) -> Dict:
        """Get tier limits from database"""
        try:
            result = supabase.table('divv_tier_limits').select(
                'monthly_call_limit, calls_per_minute, burst_limit'
            ).eq('tier', tier).single().execute()

            return result.data
        except Exception as e:
            logger.error(f"Error fetching tier limits: {e}")
            # Return default free tier limits as fallback
            return {
                'monthly_call_limit': 5000,
                'calls_per_minute': 10,
                'burst_limit': 20
            }

    async def _check_monthly_limit(self, key_info: Dict, limits: Dict, rate_limit_info: Dict):
        """Check if monthly limit is exceeded"""
        # Reset monthly counter if needed
        reset_time = key_info.get('monthly_usage_reset_at')
        now = datetime.now(timezone.utc)
        if reset_time and now.timestamp() >= reset_time.timestamp():
            await self._reset_monthly_usage(key_info['id'])
            key_info['monthly_usage'] = 0

        # Check limit
        if key_info['monthly_usage'] >= limits['monthly_call_limit']:
            reset_at = key_info['monthly_usage_reset_at']
            reset_seconds = int((reset_at - now).total_seconds())

            raise RateLimitExceeded(
                limit_type="monthly",
                reset_time=reset_seconds,
                rate_limit_info=rate_limit_info,
                detail=f"Monthly limit of {limits['monthly_call_limit']} calls exceeded. "
                       f"Limit resets in {reset_seconds} seconds."
            )

    async def _check_minute_limit(self, key_info: Dict, limits: Dict, rate_limit_info: Dict):
        """Check if per-minute limit is exceeded (with burst support)"""
        now = datetime.now(timezone.utc)
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
                rate_limit_info=rate_limit_info,
                detail=f"Per-minute limit of {limits['calls_per_minute']} calls "
                       f"(burst: {burst_limit}) exceeded. Try again in {reset_seconds} seconds."
            )

    async def _increment_usage(self, api_key_id: str):
        """Increment usage counters"""
        try:
            # Use admin client for increment (requires service_role after security fix)
            if not supabase_admin:
                logger.error("❌ Admin client not initialized - cannot increment usage")
                logger.error("   Make sure SUPABASE_SERVICE_ROLE_KEY is set in .env file")
                return

            # Increment both monthly and minute usage
            supabase_admin.rpc('increment_key_usage', {
                'key_id': api_key_id
            }).execute()
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")

    async def _reset_monthly_usage(self, api_key_id: str):
        """Reset monthly usage counter"""
        try:
            supabase.table('divv_api_keys').update({
                'monthly_usage': 0,
                'monthly_usage_reset_at': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            }).eq('id', api_key_id).execute()
        except Exception as e:
            logger.error(f"Error resetting monthly usage: {e}")

    async def _reset_minute_usage(self, api_key_id: str):
        """Reset minute usage counter"""
        try:
            supabase.table('divv_api_keys').update({
                'minute_usage': 0,
                'minute_window_start': datetime.now(timezone.utc).isoformat()
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
