"""
Base classes for authorization service
Version: 2024-12-19_23-50
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List, ClassVar
from enum import Enum
from pydantic import BaseModel

class AuthorizationStatus(str, Enum):
    """Authorization status enumeration"""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    PENDING_INFO = "PENDING_INFO"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"

class BaseAuthorizationService:
    """Base class for authorization service implementations"""
    
    # Cache configuration
    CACHE_TTL: ClassVar[int] = 3600  # 1 hour
    CACHE_PREFIX: ClassVar[str] = "auth:"
    
    # Batch processing configuration
    MAX_BATCH_SIZE: ClassVar[int] = 100
    BATCH_TIMEOUT: ClassVar[int] = 30
    PARALLEL_WORKERS: ClassVar[int] = 5
    
    # Retry configuration
    RETRY_CONFIG: ClassVar[Dict[str, int]] = {
        "max_retries": 3,
        "backoff_factor": 2
    }
    
    # Status transition rules
    ALLOWED_STATUS_TRANSITIONS: ClassVar[Dict[str, List[str]]] = {
        AuthorizationStatus.DRAFT: [AuthorizationStatus.SUBMITTED],
        AuthorizationStatus.SUBMITTED: [AuthorizationStatus.IN_REVIEW, AuthorizationStatus.DENIED],
        AuthorizationStatus.IN_REVIEW: [AuthorizationStatus.APPROVED, AuthorizationStatus.DENIED, AuthorizationStatus.PENDING_INFO],
        AuthorizationStatus.PENDING_INFO: [AuthorizationStatus.IN_REVIEW, AuthorizationStatus.DENIED],
        AuthorizationStatus.APPROVED: [AuthorizationStatus.EXPIRED, AuthorizationStatus.REVOKED],
        AuthorizationStatus.DENIED: [],
        AuthorizationStatus.EXPIRED: [],
        AuthorizationStatus.REVOKED: []
    }

    @classmethod
    def validate_status_transition(cls, current_status: str, new_status: str) -> bool:
        """
        Validate if the status transition is allowed.
        
        Args:
            current_status: Current authorization status
            new_status: Proposed new status
            
        Returns:
            True if transition is allowed, False otherwise
        """
        try:
            allowed_transitions = cls.ALLOWED_STATUS_TRANSITIONS[current_status]
            return new_status in allowed_transitions
        except KeyError:
            return False

    @classmethod
    def cache_key(cls, authorization_id: int, prefix: Optional[str] = None) -> str:
        """
        Generate cache key for an authorization.
        
        Args:
            authorization_id: ID of the authorization
            prefix: Optional prefix override
            
        Returns:
            Cache key string
        """
        prefix = prefix or cls.CACHE_PREFIX
        return f"{prefix}{authorization_id}"

    @classmethod
    def batch_cache_key(cls, batch_id: str) -> str:
        """
        Generate cache key for a batch operation.
        
        Args:
            batch_id: ID of the batch operation
            
        Returns:
            Cache key string
        """
        return f"{cls.CACHE_PREFIX}batch:{batch_id}"

class AuthorizationError(Exception):
    """Base class for authorization errors"""
    pass

class InvalidStatusTransitionError(AuthorizationError):
    """Error raised when attempting an invalid status transition"""
    def __init__(self, current_status: str, new_status: str):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"Invalid status transition from {current_status} to {new_status}"
        )

class BatchSizeExceededError(AuthorizationError):
    """Error raised when batch size exceeds maximum"""
    def __init__(self, size: int, max_size: int):
        self.size = size
        self.max_size = max_size
        super().__init__(
            f"Batch size {size} exceeds maximum allowed size of {max_size}"
        )

class RetryableAuthorizationError(AuthorizationError):
    """Base class for errors that should trigger a retry"""
    pass

class NonRetryableAuthorizationError(AuthorizationError):
    """Base class for errors that should not trigger a retry"""
    pass

class AuthorizationMetrics:
    """Metrics collector for authorization operations"""
    
    def __init__(self):
        """Initialize metrics collectors"""
        # TODO: Initialize Prometheus metrics
        pass

    async def increment_counter(self, metric: str, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        # TODO: Implement counter increment
        pass

    async def observe_histogram(self, metric: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram observation"""
        # TODO: Implement histogram observation
        pass

    async def record_operation_time(self, operation: str, start_time: datetime):
        """Record operation duration"""
        duration = (datetime.utcnow() - start_time).total_seconds()
        await self.observe_histogram(
            "authorization_operation_duration",
            duration,
            {"operation": operation}
        )
