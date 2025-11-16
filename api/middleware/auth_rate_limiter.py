"""
Auth Endpoint Rate Limiter

Provides rate limiting specifically for authentication endpoints to prevent
brute force attacks on login, signup, and token refresh endpoints.

Rate limits:
- Per-IP: 5 login attempts per minute
- Per-IP: 10 general auth requests per minute
- Per-email: 3 failed login attempts per 5 minutes
"""

import logging
from fastapi import HTTPException, status
from typing import Dict, Tuple
from datetime import datetime, timedelta, timezone
from cachetools import TTLCache
import hashlib

logger = logging.getLogger(__name__)

# IP-based rate limiting: {ip_address: [timestamp1, timestamp2, ...]}
# Each entry expires after 60 seconds
_ip_rate_limits = TTLCache(maxsize=10000, ttl=60)

# Email-based failed login tracking: {email_hash: [timestamp1, timestamp2, ...]}
# Each entry expires after 300 seconds (5 minutes)
_email_failed_attempts = TTLCache(maxsize=5000, ttl=300)


class AuthRateLimiter:
    """Rate limiter for authentication endpoints"""

    # Rate limit configurations
    LOGIN_LIMIT_PER_IP = 5  # 5 login attempts per minute per IP
    GENERAL_AUTH_LIMIT_PER_IP = 10  # 10 general auth requests per minute per IP
    FAILED_LOGIN_LIMIT_PER_EMAIL = 3  # 3 failed attempts per 5 minutes per email
    WINDOW_SECONDS = 60  # Rate limit window

    @staticmethod
    def _hash_email(email: str) -> str:
        """Hash email for privacy"""
        return hashlib.sha256(email.lower().encode()).hexdigest()

    @staticmethod
    def check_login_rate_limit(ip_address: str) -> None:
        """
        Check if IP has exceeded login rate limit.

        Args:
            ip_address: Client IP address

        Raises:
            HTTPException: If rate limit exceeded (429)
        """
        if not ip_address:
            ip_address = "unknown"

        # Get current attempts for this IP
        current_time = datetime.now(timezone.utc)
        attempts = _ip_rate_limits.get(f"login_{ip_address}", [])

        # Remove old attempts (older than 60 seconds)
        recent_attempts = [
            ts for ts in attempts
            if (current_time - ts).total_seconds() < AuthRateLimiter.WINDOW_SECONDS
        ]

        # Check limit
        if len(recent_attempts) >= AuthRateLimiter.LOGIN_LIMIT_PER_IP:
            logger.warning(
                f"Login rate limit exceeded for IP: {ip_address}, "
                f"attempts: {len(recent_attempts)}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Type": "login"
                }
            )

        # Record this attempt
        recent_attempts.append(current_time)
        _ip_rate_limits[f"login_{ip_address}"] = recent_attempts

    @staticmethod
    def check_general_auth_rate_limit(ip_address: str) -> None:
        """
        Check if IP has exceeded general auth rate limit.

        Args:
            ip_address: Client IP address

        Raises:
            HTTPException: If rate limit exceeded (429)
        """
        if not ip_address:
            ip_address = "unknown"

        # Get current attempts for this IP
        current_time = datetime.now(timezone.utc)
        attempts = _ip_rate_limits.get(f"auth_{ip_address}", [])

        # Remove old attempts (older than 60 seconds)
        recent_attempts = [
            ts for ts in attempts
            if (current_time - ts).total_seconds() < AuthRateLimiter.WINDOW_SECONDS
        ]

        # Check limit
        if len(recent_attempts) >= AuthRateLimiter.GENERAL_AUTH_LIMIT_PER_IP:
            logger.warning(
                f"General auth rate limit exceeded for IP: {ip_address}, "
                f"attempts: {len(recent_attempts)}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many authentication requests. Please try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Type": "auth"
                }
            )

        # Record this attempt
        recent_attempts.append(current_time)
        _ip_rate_limits[f"auth_{ip_address}"] = recent_attempts

    @staticmethod
    def record_failed_login(email: str) -> None:
        """
        Record a failed login attempt for an email address.

        Args:
            email: Email address that failed login
        """
        email_hash = AuthRateLimiter._hash_email(email)
        current_time = datetime.now(timezone.utc)

        # Get current failed attempts
        attempts = _email_failed_attempts.get(email_hash, [])

        # Remove old attempts (older than 300 seconds / 5 minutes)
        recent_attempts = [
            ts for ts in attempts
            if (current_time - ts).total_seconds() < 300
        ]

        # Record this failed attempt
        recent_attempts.append(current_time)
        _email_failed_attempts[email_hash] = recent_attempts

        logger.warning(
            f"Failed login attempt for email: {email_hash[:8]}..., "
            f"attempts in last 5 min: {len(recent_attempts)}"
        )

    @staticmethod
    def check_email_failed_login_limit(email: str) -> None:
        """
        Check if email has exceeded failed login rate limit.

        Args:
            email: Email address to check

        Raises:
            HTTPException: If rate limit exceeded (429)
        """
        email_hash = AuthRateLimiter._hash_email(email)
        current_time = datetime.now(timezone.utc)

        # Get current failed attempts
        attempts = _email_failed_attempts.get(email_hash, [])

        # Remove old attempts (older than 300 seconds / 5 minutes)
        recent_attempts = [
            ts for ts in attempts
            if (current_time - ts).total_seconds() < 300
        ]

        # Check limit
        if len(recent_attempts) >= AuthRateLimiter.FAILED_LOGIN_LIMIT_PER_EMAIL:
            logger.warning(
                f"Email failed login limit exceeded: {email_hash[:8]}..., "
                f"attempts: {len(recent_attempts)}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Account temporarily locked. Please try again in 5 minutes.",
                headers={
                    "Retry-After": "300",
                    "X-RateLimit-Type": "failed_login"
                }
            )

    @staticmethod
    def get_attempts_remaining(ip_address: str, endpoint_type: str = "login") -> int:
        """
        Get number of remaining attempts for an IP.

        Args:
            ip_address: Client IP address
            endpoint_type: "login" or "auth"

        Returns:
            Number of attempts remaining
        """
        if not ip_address:
            ip_address = "unknown"

        current_time = datetime.now(timezone.utc)
        key = f"{endpoint_type}_{ip_address}"
        attempts = _ip_rate_limits.get(key, [])

        # Remove old attempts
        recent_attempts = [
            ts for ts in attempts
            if (current_time - ts).total_seconds() < AuthRateLimiter.WINDOW_SECONDS
        ]

        if endpoint_type == "login":
            limit = AuthRateLimiter.LOGIN_LIMIT_PER_IP
        else:
            limit = AuthRateLimiter.GENERAL_AUTH_LIMIT_PER_IP

        return max(0, limit - len(recent_attempts))

    @staticmethod
    def reset_ip_limit(ip_address: str, endpoint_type: str = "login") -> None:
        """
        Reset rate limit for an IP (for successful authentication).

        Args:
            ip_address: Client IP address
            endpoint_type: "login" or "auth"
        """
        if not ip_address:
            return

        key = f"{endpoint_type}_{ip_address}"
        _ip_rate_limits.pop(key, None)
        logger.info(f"Rate limit reset for IP: {ip_address}, type: {endpoint_type}")

    @staticmethod
    def reset_email_failed_attempts(email: str) -> None:
        """
        Reset failed login attempts for an email (on successful login).

        Args:
            email: Email address
        """
        email_hash = AuthRateLimiter._hash_email(email)
        _email_failed_attempts.pop(email_hash, None)
        logger.info(f"Failed login attempts reset for email: {email_hash[:8]}...")


# Create global instance
auth_rate_limiter = AuthRateLimiter()
