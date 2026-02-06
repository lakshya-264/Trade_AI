"""
Centralized Caching Service
Provides in-memory caching with TTL support and automatic cleanup
Can be upgraded to Redis for distributed caching
"""

from typing import Dict, Tuple, Optional, Any, Callable
from datetime import datetime, timedelta
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CacheService:
    """Centralized caching service with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cleanup_interval = timedelta(minutes=5)  # Cleanup every 5 minutes
        self._last_cleanup = datetime.utcnow()
        self._max_cache_size = 10000  # Maximum cache entries
        
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self._cache:
            return default
            
        expires_at, value = self._cache[key]
        
        # Check if expired
        if datetime.utcnow() > expires_at:
            del self._cache[key]
            return default
            
        return value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 60) -> None:
        """Set value in cache with TTL"""
        # Enforce max cache size
        if len(self._cache) >= self._max_cache_size:
            self._cleanup_expired()
            # If still full, remove oldest 10% of entries
            if len(self._cache) >= self._max_cache_size:
                self._evict_oldest()
        
        expires_at = datetime.utcnow() + timedelta(seconds=max(1, min(ttl_seconds, 3600)))
        self._cache[key] = (expires_at, value)
        
        # Periodic cleanup
        if datetime.utcnow() - self._last_cleanup > self._cleanup_interval:
            self._cleanup_expired()
    
    def delete(self, key: str) -> None:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (expires_at, _) in self._cache.items()
            if now > expires_at
        ]
        for key in expired_keys:
            del self._cache[key]
        self._last_cleanup = now
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _evict_oldest(self) -> None:
        """Evict oldest 10% of entries"""
        if not self._cache:
            return
            
        # Sort by expiration time and remove oldest 10%
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1][0]  # Sort by expires_at
        )
        evict_count = max(1, len(sorted_entries) // 10)
        for key, _ in sorted_entries[:evict_count]:
            del self._cache[key]
        
        logger.debug(f"Evicted {evict_count} oldest cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.utcnow()
        expired_count = sum(
            1 for expires_at, _ in self._cache.values()
            if now > expires_at
        )
        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "max_size": self._max_cache_size,
        }


# Global cache instance
cache_service = CacheService()


def cached(ttl_seconds: int = 60, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl_seconds=120, key_prefix="quote")
        async def get_quote(symbol: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Check cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_service.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cache miss, stored: {cache_key}")
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Check cache
            cached_value = cache_service.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_service.set(cache_key, result, ttl_seconds)
            logger.debug(f"Cache miss, stored: {cache_key}")
            
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_cache_key(*parts: str) -> str:
    """Generate a cache key from parts"""
    return ":".join(str(part) for part in parts if part)
