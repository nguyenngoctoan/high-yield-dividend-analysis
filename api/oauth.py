"""
Google OAuth authentication utilities.

Handles OAuth flow, token management, and user session creation.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets

from authlib.integrations.starlette_client import OAuth
from jose import JWTError, jwt
from fastapi import HTTPException, status

from api.config import settings
from supabase_helpers import get_supabase_client


# Configure OAuth
oauth = OAuth()

oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account',
    }
)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT access token.

    Args:
        token: JWT token to verify

    Returns:
        Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def create_session_token() -> str:
    """
    Create a secure random session token.

    Returns:
        Random session token
    """
    return secrets.token_urlsafe(32)


async def get_or_create_user(google_user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get or create a user from Google OAuth user info.

    Args:
        google_user_info: User information from Google OAuth

    Returns:
        User data from database
    """
    supabase = get_supabase_client()

    google_id = google_user_info.get('sub')
    email = google_user_info.get('email')
    name = google_user_info.get('name')
    picture_url = google_user_info.get('picture')

    if not google_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google user information"
        )

    # Use the upsert function from the database
    result = supabase.rpc('upsert_google_user', {
        'p_google_id': google_id,
        'p_email': email,
        'p_name': name,
        'p_picture_url': picture_url
    }).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create or update user"
        )

    user_id = result.data

    # Fetch the complete user record
    user_result = supabase.table('divv_users').select('*').eq('id', user_id).execute()

    if not user_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user data"
        )

    return user_result.data[0]


def create_user_session(user: Dict[str, Any]) -> Dict[str, str]:
    """
    Create a session for an authenticated user.

    Args:
        user: User data from database

    Returns:
        Dictionary with access token and session info
    """
    # Create JWT access token
    access_token = create_access_token(
        data={
            "sub": str(user['id']),
            "email": user['email'],
            "tier": user.get('tier', 'free'),
            "type": "access"
        }
    )

    # Create session token for cookie
    session_token = create_session_token()

    return {
        "access_token": access_token,
        "session_token": session_token,
        "token_type": "bearer",
        "user_id": str(user['id']),
        "email": user['email'],
        "name": user.get('name', ''),
        "picture_url": user.get('picture_url', ''),
        "tier": user.get('tier', 'free')
    }


async def get_current_user(token: str) -> Dict[str, Any]:
    """
    Get the current user from a JWT token.

    Args:
        token: JWT access token

    Returns:
        User data from database

    Raises:
        HTTPException: If token is invalid or user not found
    """
    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    supabase = get_supabase_client()
    result = supabase.table('divv_users').select('*').eq('id', user_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = result.data[0]

    # Check if user is active
    if not user.get('is_active', True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    return user
