"""
Cache utility for storing frequently accessed data
"""
from typing import Optional, Any
import aioredis
from app.core.config import settings
from app.core.logging import logger

class Cache:
    """Redis-based cache implementation"""
    
    def __init__(self):
        """Initialize the cache connection"""
        self._redis = None
        self._connected = False

    async def connect(self) -> None:
        """Establish connection to Redis"""
        if not self._connected:
            try:
                self._redis = await aioredis.create_redis_pool(
                    settings.REDIS_URL,
                    minsize=5,
                    maxsize=10
                )
                self._connected = True
                logger.info("Successfully connected to Redis cache")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {str(e)}")
                self._connected = False

    async def disconnect(self) -> None:
        """Close Redis connection"""
        if self._connected and self._redis is not None:
            self._redis.close()
            await self._redis.wait_closed()
            self._connected = False
            logger.info("Disconnected from Redis cache")

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists, None otherwise
        """
        if not self._connected:
            await self.connect()
        
        try:
            value = await self._redis.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            await self.connect()
            
        try:
            await self._redis.set(key, value)
            if expire:
                await self._redis.expire(key, expire)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if not self._connected:
            await self.connect()
            
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

# Global cache instance
cache = Cache()
