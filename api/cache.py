"""
Redis Caching Utility

Provides decorators and functions for caching expensive database queries and API calls.
Uses Redis for distributed caching with automatic TTL management.
"""

import redis
import os
import json
from functools import wraps
from typing import Optional, Callable, Any
import logging
import hashlib

logger = logging.getLogger(__name__)

# Redis client configuration
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis connected successfully")
    REDIS_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️  Redis connection failed: {e}. Caching disabled.")
    redis_client = None
    REDIS_AVAILABLE = False


def _generate_cache_key(prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a unique cache key from function name and arguments.

    Args:
        prefix: Cache key prefix
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments

    Returns:
        Unique cache key string
    """
    # Create a stable representation of arguments
    key_parts = [prefix, func_name]

    # Add positional args
    if args:
        key_parts.extend(str(arg) for arg in args)

    # Add keyword args (sorted for consistency)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        key_parts.append(json.dumps(sorted_kwargs, sort_keys=True))

    # Hash if key is too long
    key_string = ":".join(key_parts)
    if len(key_string) > 200:
        hash_suffix = hashlib.md5(key_string.encode()).hexdigest()
        key_string = f"{prefix}:{func_name}:{hash_suffix}"

    return key_string


def cache_response(ttl: int = 300, key_prefix: str = "api"):
    """
    Decorator to cache function responses in Redis.

    Caches the return value of async functions for the specified TTL.
    Automatically skips caching if Redis is unavailable.

    Args:
        ttl: Time to live in seconds (default: 300 = 5 minutes)
        key_prefix: Prefix for cache key (default: "api")

    Usage:
        @cache_response(ttl=600, key_prefix="stock_quote")
        async def get_stock_quote(symbol: str):
            # Expensive database call
            return data

    Example:
        First call: Cache MISS - fetches from database (200ms)
        Second call: Cache HIT - returns from Redis (<5ms)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Skip caching if Redis unavailable
            if not REDIS_AVAILABLE or not redis_client:
                logger.debug(f"Redis unavailable, skipping cache for {func.__name__}")
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = _generate_cache_key(key_prefix, func.__name__, args, kwargs)

            try:
                # Try to get from cache
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache HIT: {cache_key}")
                    try:
                        return json.loads(cached)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in cache for {cache_key}, fetching fresh data")

                # Cache miss - call function
                logger.debug(f"Cache MISS: {cache_key}")
                result = await func(*args, **kwargs)

                # Store in cache (only if result is JSON-serializable)
                try:
                    redis_client.setex(cache_key, ttl, json.dumps(result))
                    logger.debug(f"Cached result for {cache_key} (TTL: {ttl}s)")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not cache result for {cache_key}: {e}")

                return result

            except redis.RedisError as e:
                logger.error(f"Redis error for {cache_key}: {e}, falling back to function call")
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def invalidate_cache(pattern: str) -> int:
    """
    Invalidate cache entries matching pattern.

    Args:
        pattern: Redis key pattern (e.g., "stock_quote:*", "api:get_dividends:*")

    Returns:
        Number of keys deleted

    Usage:
        # Invalidate all stock quotes
        invalidate_cache("stock_quote:*")

        # Invalidate specific symbol
        invalidate_cache("stock_quote:get_stock_quote:AAPL")
    """
    if not REDIS_AVAILABLE or not redis_client:
        logger.warning("Redis unavailable, cannot invalidate cache")
        return 0

    try:
        keys = redis_client.keys(pattern)
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache entries matching: {pattern}")
            return deleted
        return 0
    except redis.RedisError as e:
        logger.error(f"Failed to invalidate cache for pattern {pattern}: {e}")
        return 0


def get_cache_stats() -> dict:
    """
    Get Redis cache statistics.

    Returns:
        Dictionary with cache stats (hits, misses, memory usage, etc.)
    """
    if not REDIS_AVAILABLE or not redis_client:
        return {
            "available": False,
            "error": "Redis not connected"
        }

    try:
        info = redis_client.info("stats")
        memory = redis_client.info("memory")

        return {
            "available": True,
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": (
                info.get("keyspace_hits", 0) /
                max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
            ) * 100,
            "memory_used_mb": memory.get("used_memory", 0) / (1024 * 1024),
            "memory_peak_mb": memory.get("used_memory_peak", 0) / (1024 * 1024),
            "connected_clients": info.get("connected_clients", 0),
            "total_commands": info.get("total_commands_processed", 0)
        }
    except redis.RedisError as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "available": False,
            "error": str(e)
        }


def set_cache(key: str, value: Any, ttl: int = 300) -> bool:
    """
    Manually set a cache value.

    Args:
        key: Cache key
        value: Value to cache (must be JSON-serializable)
        ttl: Time to live in seconds

    Returns:
        True if successful, False otherwise
    """
    if not REDIS_AVAILABLE or not redis_client:
        return False

    try:
        redis_client.setex(key, ttl, json.dumps(value))
        return True
    except (redis.RedisError, TypeError, ValueError) as e:
        logger.error(f"Failed to set cache for {key}: {e}")
        return False


def get_cache(key: str) -> Optional[Any]:
    """
    Manually get a cache value.

    Args:
        key: Cache key

    Returns:
        Cached value if found, None otherwise
    """
    if not REDIS_AVAILABLE or not redis_client:
        return None

    try:
        cached = redis_client.get(key)
        if cached:
            return json.loads(cached)
        return None
    except (redis.RedisError, json.JSONDecodeError) as e:
        logger.error(f"Failed to get cache for {key}: {e}")
        return None
