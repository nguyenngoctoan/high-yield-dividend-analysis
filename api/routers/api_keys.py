"""
API Key Management Endpoints

Provides endpoints for creating, listing, and revoking API keys.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from api.auth import validate_api_key, generate_api_key, hash_api_key
from api.routers.auth import require_authentication
from supabase_helpers import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating a new API key."""

    name: str = Field(..., description="Friendly name for the API key", min_length=1, max_length=255)
    tier: str = Field(default="free", description="Subscription tier (free, pro, enterprise)")
    expires_in_days: Optional[int] = Field(
        default=None,
        description="Number of days until key expires (null for no expiration)",
        ge=1,
        le=3650
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="Additional metadata (email, company, etc.)"
    )


class APIKeyResponse(BaseModel):
    """Response model for API key information."""

    id: str
    user_id: str
    name: str
    key_prefix: str
    tier: str
    is_active: bool
    request_count: int
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    created_at: datetime


class CreateAPIKeyResponse(BaseModel):
    """Response model when creating a new API key (includes the full key)."""

    id: str
    api_key: str  # Only returned once on creation
    key_prefix: str
    name: str
    tier: str
    expires_at: Optional[datetime]
    created_at: datetime
    message: str


@router.post("/keys", response_model=CreateAPIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user: Dict = Depends(require_authentication)
) -> CreateAPIKeyResponse:
    """
    Create a new API key.

    This endpoint requires OAuth authentication (user must be logged in).
    The new API key is only shown once - save it securely!

    Args:
        request: API key creation parameters
        user: Authenticated user information from OAuth

    Returns:
        The newly created API key (shown only once)
    """
    # Validate tier
    if request.tier not in ['free', 'pro', 'enterprise']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "invalid_request_error",
                    "message": "Invalid tier. Must be one of: free, pro, enterprise",
                    "param": "tier",
                    "code": "invalid_tier"
                }
            }
        )

    # Generate new API key
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_prefix = api_key[:16]  # e.g., "sk_live_abc12345"

    # Calculate expiration
    expires_at = None
    if request.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

    try:
        supabase = get_supabase_client()

        # Insert the new API key
        result = supabase.table('divv_api_keys').insert({
            'user_id': str(user['id']),
            'name': request.name,
            'key_hash': key_hash,
            'key_prefix': key_prefix,
            'tier': user.get('tier', request.tier),  # Use user's tier, fallback to request tier
            'is_active': True,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'metadata': request.metadata
        }).execute()

        if not result.data:
            raise Exception("Failed to create API key")

        key_data = result.data[0]

        logger.info(f"Created new API key {key_data['id']} for user {user['id']} ({user['email']})")

        return CreateAPIKeyResponse(
            id=key_data['id'],
            api_key=api_key,  # Only returned once!
            key_prefix=key_prefix,
            name=request.name,
            tier=request.tier,
            expires_at=datetime.fromisoformat(key_data['expires_at'].replace('Z', '+00:00')) if key_data.get('expires_at') else None,
            created_at=datetime.fromisoformat(key_data['created_at'].replace('Z', '+00:00')),
            message="API key created successfully. Save this key securely - it won't be shown again!"
        )

    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "api_error",
                    "message": "Failed to create API key",
                    "code": "key_creation_failed"
                }
            }
        )


@router.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    user: Dict = Depends(require_authentication),
    include_inactive: bool = False
) -> List[APIKeyResponse]:
    """
    List all API keys for the authenticated user.

    Args:
        user: Authenticated user information from OAuth
        include_inactive: Whether to include revoked keys

    Returns:
        List of API keys (without the actual key values)
    """
    try:
        supabase = get_supabase_client()

        # Query API keys
        query = supabase.table('divv_api_keys').select('*').eq('user_id', str(user['id']))

        if not include_inactive:
            query = query.eq('is_active', True)

        result = query.order('created_at', desc=True).execute()

        keys = []
        for key_data in result.data:
            keys.append(APIKeyResponse(
                id=key_data['id'],
                user_id=key_data['user_id'],
                name=key_data.get('name', 'Unnamed Key'),
                key_prefix=key_data['key_prefix'],
                tier=key_data.get('tier', 'free'),
                is_active=key_data['is_active'],
                request_count=key_data.get('request_count', 0),
                last_used_at=datetime.fromisoformat(key_data['last_used_at'].replace('Z', '+00:00')) if key_data.get('last_used_at') else None,
                expires_at=datetime.fromisoformat(key_data['expires_at'].replace('Z', '+00:00')) if key_data.get('expires_at') else None,
                created_at=datetime.fromisoformat(key_data['created_at'].replace('Z', '+00:00'))
            ))

        return keys

    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "api_error",
                    "message": "Failed to retrieve API keys",
                    "code": "key_retrieval_failed"
                }
            }
        )


@router.delete("/keys/{key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    key_id: str,
    user: Dict = Depends(require_authentication)
) -> Dict[str, Any]:
    """
    Revoke an API key.

    This marks the key as inactive and prevents further use.
    The key data is retained for audit purposes.

    Args:
        key_id: The ID of the API key to revoke
        user: Authenticated user information from OAuth

    Returns:
        Confirmation message
    """
    try:
        supabase = get_supabase_client()

        # Verify the key belongs to the user
        result = supabase.table('divv_api_keys').select('*').eq('id', key_id).eq('user_id', str(user['id'])).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "type": "invalid_request_error",
                        "message": "API key not found or does not belong to you",
                        "param": "key_id",
                        "code": "key_not_found"
                    }
                }
            )

        # Revoke the key
        supabase.table('divv_api_keys').update({'is_active': False}).eq('id', key_id).execute()

        logger.info(f"Revoked API key {key_id} for user {user['id']} ({user['email']})")

        return {
            "id": key_id,
            "revoked": True,
            "message": "API key has been revoked successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "api_error",
                    "message": "Failed to revoke API key",
                    "code": "key_revocation_failed"
                }
            }
        )


@router.get("/keys/{key_id}/usage")
async def get_api_key_usage(
    key_id: str,
    user: Dict = Depends(require_authentication),
    days: int = 30
) -> Dict[str, Any]:
    """
    Get usage statistics for an API key.

    Args:
        key_id: The ID of the API key
        user: Authenticated user information from OAuth
        days: Number of days of history to retrieve (default: 30)

    Returns:
        Usage statistics and request history
    """
    try:
        supabase = get_supabase_client()

        # Verify the key belongs to the user
        key_result = supabase.table('divv_api_keys').select('*').eq('id', key_id).eq('user_id', str(user['id'])).execute()

        if not key_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "type": "invalid_request_error",
                        "message": "API key not found or does not belong to you",
                        "param": "key_id",
                        "code": "key_not_found"
                    }
                }
            )

        # Get daily usage statistics
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()

        usage_result = supabase.table('mv_api_usage_daily').select('*').eq('api_key_id', key_id).gte('request_date', cutoff_date.isoformat()).order('request_date', desc=True).execute()

        # Calculate totals
        total_requests = sum(day['total_requests'] for day in usage_result.data)
        total_errors = sum(day['error_requests'] for day in usage_result.data)
        avg_response_time = sum(day['avg_response_time_ms'] for day in usage_result.data) / len(usage_result.data) if usage_result.data else 0

        return {
            "api_key_id": key_id,
            "period_days": days,
            "total_requests": total_requests,
            "successful_requests": total_requests - total_errors,
            "error_requests": total_errors,
            "error_rate": (total_errors / total_requests * 100) if total_requests > 0 else 0,
            "avg_response_time_ms": round(avg_response_time, 2),
            "daily_usage": usage_result.data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve API key usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "api_error",
                    "message": "Failed to retrieve usage statistics",
                    "code": "usage_retrieval_failed"
                }
            }
        )
