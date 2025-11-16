"""
Authentication Dependencies

Provides authentication and authorization checks for API endpoints.
All public endpoints must use these dependencies to ensure requests
are tied to authenticated user accounts.
"""

from fastapi import Depends, HTTPException, Request, status
from typing import Optional, Dict, Any
import hashlib
import logging
from datetime import datetime, timezone

from supabase_helpers import get_supabase_client

logger = logging.getLogger(__name__)


def _extract_api_key(request: Request) -> Optional[str]:
    """Extract API key from request headers or query parameters."""
    # Check Authorization header (Bearer token format)
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


def _hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256 (matches database storage)."""
    return hashlib.sha256(api_key.encode()).hexdigest()


async def require_api_key(request: Request) -> Dict[str, Any]:
    """
    Dependency: Require valid API key for all public endpoints.

    Returns authenticated user information including:
    - user_id: Supabase user ID
    - tier: API tier (free, starter, premium, professional, enterprise)
    - key_id: The API key ID
    - key_name: Name of the API key

    Raises:
    - 401: No API key provided
    - 403: Invalid or revoked API key
    """
    api_key = _extract_api_key(request)

    if not api_key:
        logger.warning(f"Unauthorized access attempt to {request.url.path} - no API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Pass as 'X-API-Key' header or '?api_key=...' query parameter.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Hash the API key (matches what's stored in database)
    api_key_hash = _hash_api_key(api_key)

    try:
        supabase = get_supabase_client()

        # Look up API key in database
        result = supabase.table('divv_api_keys').select(
            'id, user_id, tier, key_name, is_active, expires_at'
        ).eq('key_hash', api_key_hash).execute()

        if not result.data or len(result.data) == 0:
            logger.warning(f"Invalid API key attempt on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or revoked API key"
            )

        key_record = result.data[0]

        # Check if key is active
        if not key_record.get('is_active', False):
            logger.warning(f"Inactive API key used: user_id={key_record['user_id']}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key has been revoked"
            )

        # Check if key is expired
        if key_record.get('expires_at'):
            expires_at = datetime.fromisoformat(key_record['expires_at'].replace('Z', '+00:00'))
            if expires_at < datetime.now(timezone.utc):
                logger.warning(f"Expired API key used: user_id={key_record['user_id']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="API key has expired"
                )

        # Return authenticated user info
        auth_info = {
            'user_id': key_record['user_id'],
            'key_id': key_record['id'],
            'key_name': key_record.get('key_name', 'Unnamed Key'),
            'tier': key_record.get('tier', 'free'),
            'api_key_hash': api_key_hash  # For tracking in logs
        }

        # Store in request state for access in handlers
        request.state.user_id = auth_info['user_id']
        request.state.tier = auth_info['tier']
        request.state.key_id = auth_info['key_id']

        logger.info(f"Authenticated request: user_id={auth_info['user_id']}, tier={auth_info['tier']}, path={request.url.path}")

        return auth_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating API key: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating API key"
        )


async def get_user_id(request: Request) -> str:
    """
    Dependency: Extract user_id from authenticated request.

    Assumes require_api_key has already validated authentication.
    """
    user_id = getattr(request.state, 'user_id', None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user_id


async def get_user_tier(request: Request) -> str:
    """
    Dependency: Extract user tier from authenticated request.

    Assumes require_api_key has already validated authentication.
    """
    tier = getattr(request.state, 'tier', None)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return tier
