"""
Redis caching utility for JIRA Sync Dashboard.
Provides caching layer for database queries to improve performance.
"""

import json
import logging
import os
from typing import Any, Optional, Callable
from functools import wraps
from datetime import timedelta
import redis
from redis.exceptions import RedisError
import hashlib

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager with connection pooling and error handling."""
    
    def __init__(self):
        """Initialize Redis connection with configuration from environment."""
        self.redis_client = None
        self.ttl = int(os.getenv('REDIS_TTL', '110'))  # Default 110 seconds
        self.enabled = os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
        
        if self.enabled:
            try:
                # Create connection pool for better performance
                pool = redis.ConnectionPool(
                    host=os.getenv('REDIS_HOST', 'localhost'),
                    port=int(os.getenv('REDIS_PORT', '6379')),
                    password=os.getenv('REDIS_PASSWORD', None),
                    max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                self.redis_client = redis.Redis(connection_pool=pool)
                
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connected successfully")
                
            except (RedisError, Exception) as e:
                logger.warning(f"Redis connection failed, caching disabled: {e}")
                self.enabled = False
                self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a unique cache key based on function arguments."""
        # Create a string representation of arguments
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))
        
        # Add keyword arguments
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}:{json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}:{v}")
        
        # Create hash for long keys
        key_string = ":".join(key_parts)
        if len(key_string) > 200:
            # Use hash for very long keys
            hash_suffix = hashlib.md5(key_string.encode()).hexdigest()[:8]
            return f"{prefix}:{hash_suffix}"
        
        return key_string
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                # Try to deserialize JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
            
        except RedisError as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            # Use provided TTL or default
            ttl = ttl or self.ttl
            
            return self.redis_client.setex(key, ttl, value)
            
        except RedisError as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.error(f"Redis delete pattern error for {pattern}: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear all cache entries (use with caution)."""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Redis cache cleared")
            return True
        except RedisError as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    def invalidate_sync_cache(self):
        """Invalidate all sync-related cache entries after sync completes."""
        patterns = [
            "issues:*",
            "project:*",
            "recent:*",
            "search:*",
            "stats:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = self.delete_pattern(pattern)
            total_deleted += deleted
        
        if total_deleted > 0:
            logger.info(f"Invalidated {total_deleted} cache entries after sync")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = self.redis_client.info("stats")
            memory = self.redis_client.info("memory")
            
            return {
                "enabled": True,
                "keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used": memory.get("used_memory_human", "0"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except RedisError as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache_instance = None

def get_cache() -> RedisCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def cache_result(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results in Redis.
    
    Args:
        prefix: Cache key prefix (e.g., "issues", "projects")
        ttl: Time to live in seconds (default from environment)
    
    Example:
        @cache_result("issues", ttl=120)
        def get_issue(issue_key: str):
            return db.query(...)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Generate cache key
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            
            # Only cache non-None results
            if result is not None:
                cache.set(cache_key, result, ttl)
            
            return result
        
        # Add method to invalidate this function's cache
        def invalidate(*args, **kwargs):
            cache = get_cache()
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            cache.delete(cache_key)
        
        wrapper.invalidate = invalidate
        return wrapper
    
    return decorator


def cache_aside(key: str, func: Callable, ttl: Optional[int] = None) -> Any:
    """
    Cache-aside pattern helper for manual caching.
    
    Args:
        key: Cache key
        func: Function to call if cache miss
        ttl: Time to live in seconds
    
    Returns:
        Cached or computed result
    """
    cache = get_cache()
    
    # Try cache first
    result = cache.get(key)
    if result is not None:
        return result
    
    # Compute and cache
    result = func()
    if result is not None:
        cache.set(key, result, ttl)
    
    return result