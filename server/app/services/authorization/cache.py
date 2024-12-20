"""
Cache utilities for authorization service
Version: 2024-12-19_23-50
"""
from typing import Optional, Any, TypeVar, Generic
from datetime import datetime
import json
from redis import Redis
from pydantic import BaseModel

from app.core.cache import get_redis_client
from app.core.logging import logger
from .base import BaseAuthorizationService

T = TypeVar('T', bound=BaseModel)

class AuthorizationCache(Generic[T]):
    """Cache manager for authorization data"""

    def __init__(self, model_class: type[T]):
        """
        Initialize cache manager.
        
        Args:
            model_class: Pydantic model class for serialization
        """
        self.redis: Redis = get_redis_client()
        self.model_class = model_class
        self.ttl = BaseAuthorizationService.CACHE_TTL

    async def get(self, cache_key: str) -> Optional[T]:
        """
        Get item from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached item if found, None otherwise
        """
        try:
            data = await self.redis.get(cache_key)
            if data:
                return self.model_class.model_validate(json.loads(data))
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None

    async def set(self, cache_key: str, value: T, ttl: Optional[int] = None) -> bool:
        """
        Set item in cache.
        
        Args:
            cache_key: Cache key
            value: Value to cache
            ttl: Optional TTL override
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ttl = ttl or self.ttl
            data = value.model_dump_json()
            return await self.redis.setex(cache_key, ttl, data)
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False

    async def delete(self, cache_key: str) -> bool:
        """
        Delete item from cache.
        
        Args:
            cache_key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return bool(await self.redis.delete(cache_key))
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False

    async def invalidate_pattern(self, pattern: str) -> bool:
        """
        Invalidate all keys matching pattern.
        
        Args:
            pattern: Pattern to match
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                return bool(await self.redis.delete(*keys))
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache pattern: {str(e)}")
            return False

class BatchOperationCache:
    """Cache manager for batch operations"""

    def __init__(self):
        """Initialize batch operation cache"""
        self.redis = get_redis_client()
        self.ttl = 300  # 5 minutes

    async def set_batch_status(
        self,
        batch_id: str,
        total: int,
        completed: int = 0,
        failed: int = 0,
        errors: Optional[dict] = None
    ) -> bool:
        """
        Set batch operation status.
        
        Args:
            batch_id: Batch operation ID
            total: Total number of items
            completed: Number of completed items
            failed: Number of failed items
            errors: Optional error details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            status = {
                "total": total,
                "completed": completed,
                "failed": failed,
                "errors": errors or {},
                "updated_at": datetime.utcnow().isoformat()
            }
            cache_key = BaseAuthorizationService.batch_cache_key(batch_id)
            return await self.redis.setex(
                cache_key,
                self.ttl,
                json.dumps(status)
            )
        except Exception as e:
            logger.error(f"Error setting batch status: {str(e)}")
            return False

    async def get_batch_status(self, batch_id: str) -> Optional[dict]:
        """
        Get batch operation status.
        
        Args:
            batch_id: Batch operation ID
            
        Returns:
            Batch status if found, None otherwise
        """
        try:
            cache_key = BaseAuthorizationService.batch_cache_key(batch_id)
            data = await self.redis.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Error getting batch status: {str(e)}")
            return None

    async def update_batch_progress(
        self,
        batch_id: str,
        completed: int = 0,
        failed: int = 0,
        errors: Optional[dict] = None
    ) -> bool:
        """
        Update batch operation progress.
        
        Args:
            batch_id: Batch operation ID
            completed: Additional completed items
            failed: Additional failed items
            errors: Optional error details to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = BaseAuthorizationService.batch_cache_key(batch_id)
            current = await self.get_batch_status(batch_id)
            if not current:
                return False

            current["completed"] += completed
            current["failed"] += failed
            if errors:
                current["errors"].update(errors)
            current["updated_at"] = datetime.utcnow().isoformat()

            return await self.redis.setex(
                cache_key,
                self.ttl,
                json.dumps(current)
            )
        except Exception as e:
            logger.error(f"Error updating batch progress: {str(e)}")
            return False
