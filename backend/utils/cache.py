import time
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Simple in-memory cache manager.
    Can be replaced with Redis later.
    """
    _cache = {}
    _expiry = {}

    @staticmethod
    def set(key, value, ttl=None):
        """
        Set a value in the cache with optional TTL (in seconds).
        """
        CacheManager._cache[key] = value
        if ttl:
            CacheManager._expiry[key] = time.time() + ttl
        elif key in CacheManager._expiry:
            del CacheManager._expiry[key]

    @staticmethod
    def get(key):
        """
        Get a value from the cache. Returns None if expired or not found.
        """
        if key in CacheManager._expiry:
            if time.time() > CacheManager._expiry[key]:
                CacheManager.delete(key)
                return None
        return CacheManager._cache.get(key)
        
    @staticmethod
    def delete(key):
        """
        Delete a key from the cache.
        """
        if key in CacheManager._cache:
            del CacheManager._cache[key]
        if key in CacheManager._expiry:
            del CacheManager._expiry[key]

    @staticmethod
    def clear():
        """
        Clear all cache entries.
        """
        CacheManager._cache.clear()
        CacheManager._expiry.clear()
