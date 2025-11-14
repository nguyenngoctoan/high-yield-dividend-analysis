"""
Authentication Endpoints

Provides Google OAuth login, callback, logout, and session management.
"""

from fastapi import APIRouter, Request, Response, HTTPException, status, Depends, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from api.oauth import oauth, get_or_create_user, create_user_session, get_current_user
from api.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


@router.get("/login")
async def login(request: Request):
    """
    Initiate Google OAuth login flow.

    Redirects the user to Google's OAuth consent screen.
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI

    # Generate authorization URL
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def auth_callback(request: Request, response: Response):
    """
    Handle OAuth callback from Google.

    Exchanges authorization code for access token and creates user session.
    """
    try:
        # Get access token from Google
        token = await oauth.google.authorize_access_token(request)

        # Get user info from Google
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback: fetch user info explicitly
            resp = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
            user_info = resp.json()

        logger.info(f"User logged in: {user_info.get('email')}")

        # Get or create user in database
        user = await get_or_create_user(user_info)

        # Create session
        session_data = create_user_session(user)

        # Set secure HTTP-only cookie with session token
        # Redirect back to the docs site (port 3000) after successful login
        response = RedirectResponse(url=settings.FRONTEND_URL)
        response.set_cookie(
            key="session_token",
            value=session_data['session_token'],
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            domain=settings.COOKIE_DOMAIN if settings.is_production else None
        )

        # Also set access token in cookie for easy access
        response.set_cookie(
            key="access_token",
            value=session_data['access_token'],
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite=settings.COOKIE_SAMESITE,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            domain=settings.COOKIE_DOMAIN if settings.is_production else None
        )

        return response

    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        # Redirect back to the docs site home page on error
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/?error=authentication_failed"
        )


@router.post("/logout")
@router.get("/logout")
async def logout():
    """
    Logout the current user.

    Clears session cookies and redirects to login page.
    Supports both GET and POST methods.
    """
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(
        key="session_token",
        domain=settings.COOKIE_DOMAIN if settings.is_production else None
    )
    response.delete_cookie(
        key="access_token",
        domain=settings.COOKIE_DOMAIN if settings.is_production else None
    )
    return response


@router.get("/me")
async def get_user_profile(
    access_token: Optional[str] = Cookie(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Get the current authenticated user's profile.

    Supports both cookie-based and header-based authentication.
    """
    # Try to get token from Authorization header first, then from cookie
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user(token)

    return {
        "id": user['id'],
        "email": user['email'],
        "name": user.get('name'),
        "picture_url": user.get('picture_url'),
        "tier": user.get('tier', 'free'),
        "is_active": user.get('is_active', True),
        "created_at": user['created_at'],
        "last_login_at": user.get('last_login_at')
    }


@router.get("/status")
async def auth_status(
    access_token: Optional[str] = Cookie(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Check if the user is authenticated.

    Returns authentication status without throwing errors.
    """
    # Try to get token from Authorization header first, then from cookie
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        return {
            "authenticated": False,
            "user": None
        }

    try:
        user = await get_current_user(token)
        return {
            "authenticated": True,
            "user": {
                "id": user['id'],
                "email": user['email'],
                "name": user.get('name'),
                "picture_url": user.get('picture_url'),
                "tier": user.get('tier', 'free')
            }
        }
    except HTTPException:
        return {
            "authenticated": False,
            "user": None
        }


# Dependency to require authentication
async def require_authentication(
    access_token: Optional[str] = Cookie(None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency that requires user authentication.

    Can be used with FastAPI's Depends() to protect routes.

    Example:
        @app.get("/protected")
        async def protected_route(user: Dict = Depends(require_authentication)):
            return {"user_id": user['id']}
    """
    # Try to get token from Authorization header first, then from cookie
    token = None
    if credentials:
        token = credentials.credentials
    elif access_token:
        token = access_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await get_current_user(token)
