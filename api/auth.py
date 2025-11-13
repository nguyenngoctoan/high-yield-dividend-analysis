"""
Authentication middleware and utilities for the Dividend API.

Implements API key-based authentication with database storage and validation.
"""

from fastapi import Security, HTTPException, status, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from typing import Optional, Dict, Any
import hashlib
import secrets
import time
from datetime import datetime
from supabase_helpers import get_supabase_client

# API Key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using SHA-256.

    Args:
        api_key: The plaintext API key

    Returns:
        Hexadecimal hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """
    Generate a secure random API key.

    Returns:
        A 32-character random API key with prefix 'sk_live_'
    """
    random_part = secrets.token_urlsafe(32)
    return f"sk_live_{random_part}"


async def validate_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    request: Request = None
) -> Dict[str, Any]:
    """
    Validate an API key from the request header.

    Args:
        api_key: The API key from X-API-Key header
        request: The FastAPI request object

    Returns:
        Dictionary with user information and API key details

    Raises:
        HTTPException: If the API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "No API key provided. Include your API key in the X-API-Key header.",
                    "code": "api_key_missing"
                }
            }
        )

    # Validate API key format
    if not api_key.startswith("sk_live_") and not api_key.startswith("sk_test_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "type": "authentication_error",
                    "message": "Invalid API key format. API keys must start with 'sk_live_' or 'sk_test_'.",
                    "code": "invalid_api_key_format"
                }
            }
        )

    # Hash the API key for database lookup
    key_hash = hash_api_key(api_key)

    try:
        supabase = get_supabase_client()

        # Look up the API key in the database
        result = supabase.table('api_keys').select('*').eq('key_hash', key_hash).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "type": "authentication_error",
                        "message": "Invalid API key. Your API key may be revoked or incorrect.",
                        "code": "invalid_api_key"
                    }
                }
            )

        key_data = result.data[0]

        # Check if the key is active
        if not key_data.get('is_active', False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": {
                        "type": "authentication_error",
                        "message": "API key has been revoked. Please generate a new key.",
                        "code": "api_key_revoked"
                    }
                }
            )

        # Check if the key has expired
        expires_at = key_data.get('expires_at')
        if expires_at:
            expiry_time = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(expiry_time.tzinfo) > expiry_time:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "error": {
                            "type": "authentication_error",
                            "message": "API key has expired. Please generate a new key.",
                            "code": "api_key_expired"
                        }
                    }
                )

        # Update last used timestamp
        supabase.table('api_keys').update({
            'last_used_at': datetime.utcnow().isoformat(),
            'request_count': key_data.get('request_count', 0) + 1
        }).eq('id', key_data['id']).execute()

        # Return user information
        return {
            "user_id": key_data.get('user_id'),
            "api_key_id": key_data.get('id'),
            "tier": key_data.get('tier', 'free'),
            "rate_limit": get_rate_limit_for_tier(key_data.get('tier', 'free'))
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "api_error",
                    "message": "Failed to validate API key",
                    "code": "validation_error"
                }
            }
        )


def get_rate_limit_for_tier(tier: str) -> Dict[str, int]:
    """
    Get rate limit configuration for a tier.

    Args:
        tier: The subscription tier (free, pro, enterprise)

    Returns:
        Dictionary with rate limit settings
    """
    rate_limits = {
        "free": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        },
        "pro": {
            "requests_per_minute": 600,
            "requests_per_hour": 20000,
            "requests_per_day": 500000
        },
        "enterprise": {
            "requests_per_minute": 6000,
            "requests_per_hour": 200000,
            "requests_per_day": 10000000
        }
    }

    return rate_limits.get(tier, rate_limits["free"])


# Optional authentication (for public endpoints)
async def optional_api_key(
    api_key: Optional[str] = Security(API_KEY_HEADER)
) -> Optional[Dict[str, Any]]:
    """
    Optionally validate an API key if provided.

    This allows endpoints to be accessed without authentication,
    but provides user context if a valid API key is present.

    Args:
        api_key: The API key from X-API-Key header (optional)

    Returns:
        User information if API key is valid, None otherwise
    """
    if not api_key:
        return None

    try:
        return await validate_api_key(api_key)
    except HTTPException:
        return None
