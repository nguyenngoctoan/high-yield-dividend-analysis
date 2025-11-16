"""
API Dependencies

Provides FastAPI dependency injection functions for authentication,
authorization, and rate limiting across all endpoints.
"""

from api.dependencies.auth import (
    require_api_key,
    get_user_id,
    get_user_tier,
)

__all__ = [
    'require_api_key',
    'get_user_id',
    'get_user_tier',
]
