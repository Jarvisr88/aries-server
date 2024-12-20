"""
Retry utilities for authorization service
Version: 2024-12-19_23-50
"""
import asyncio
from functools import wraps
from typing import TypeVar, Callable, Any
from datetime import datetime

from app.core.logging import logger
from .base import (
    BaseAuthorizationService,
    RetryableAuthorizationError,
    NonRetryableAuthorizationError,
    AuthorizationMetrics
)

T = TypeVar('T')

def retry_with_backoff(
    max_retries: int = None,
    backoff_factor: int = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for retrying operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Base factor for exponential backoff
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            metrics = AuthorizationMetrics()
            retries = max_retries or BaseAuthorizationService.RETRY_CONFIG["max_retries"]
            factor = backoff_factor or BaseAuthorizationService.RETRY_CONFIG["backoff_factor"]
            
            last_exception = None
            start_time = datetime.utcnow()

            for attempt in range(retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record metrics
                    if attempt > 0:
                        await metrics.increment_counter(
                            "authorization_retry_success",
                            {"operation": func.__name__}
                        )
                    await metrics.record_operation_time(func.__name__, start_time)
                    
                    return result

                except RetryableAuthorizationError as e:
                    last_exception = e
                    if attempt < retries:
                        # Calculate backoff delay
                        delay = factor ** attempt
                        
                        # Record retry metrics
                        await metrics.increment_counter(
                            "authorization_retry_attempt",
                            {
                                "operation": func.__name__,
                                "attempt": str(attempt + 1)
                            }
                        )
                        
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{retries} for {func.__name__}: {str(e)}"
                            f" Waiting {delay} seconds..."
                        )
                        
                        await asyncio.sleep(delay)
                    else:
                        # Record final failure metrics
                        await metrics.increment_counter(
                            "authorization_retry_exhausted",
                            {"operation": func.__name__}
                        )
                        await metrics.record_operation_time(func.__name__, start_time)
                        
                        logger.error(
                            f"Max retries ({retries}) exceeded for {func.__name__}: {str(e)}"
                        )
                        raise

                except NonRetryableAuthorizationError as e:
                    # Record non-retryable error metrics
                    await metrics.increment_counter(
                        "authorization_non_retryable_error",
                        {"operation": func.__name__}
                    )
                    await metrics.record_operation_time(func.__name__, start_time)
                    
                    logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                    raise

                except Exception as e:
                    # Record unexpected error metrics
                    await metrics.increment_counter(
                        "authorization_unexpected_error",
                        {"operation": func.__name__}
                    )
                    await metrics.record_operation_time(func.__name__, start_time)
                    
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                    raise

            # If we get here, we've exhausted retries
            raise last_exception

        return wrapper
    return decorator

class RetryContext:
    """Context manager for retry operations"""

    def __init__(
        self,
        operation_name: str,
        max_retries: int = None,
        backoff_factor: int = None
    ):
        """
        Initialize retry context.
        
        Args:
            operation_name: Name of the operation
            max_retries: Maximum number of retry attempts
            backoff_factor: Base factor for exponential backoff
        """
        self.operation_name = operation_name
        self.max_retries = max_retries or BaseAuthorizationService.RETRY_CONFIG["max_retries"]
        self.backoff_factor = backoff_factor or BaseAuthorizationService.RETRY_CONFIG["backoff_factor"]
        self.metrics = AuthorizationMetrics()
        self.start_time = None
        self.attempt = 0

    async def __aenter__(self):
        """Enter the context manager"""
        self.start_time = datetime.utcnow()
        self.attempt += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager"""
        if exc_type is None:
            # Successful operation
            if self.attempt > 1:
                await self.metrics.increment_counter(
                    "authorization_retry_success",
                    {"operation": self.operation_name}
                )
        else:
            # Handle different error types
            if issubclass(exc_type, RetryableAuthorizationError):
                if self.attempt < self.max_retries:
                    delay = self.backoff_factor ** (self.attempt - 1)
                    await self.metrics.increment_counter(
                        "authorization_retry_attempt",
                        {
                            "operation": self.operation_name,
                            "attempt": str(self.attempt)
                        }
                    )
                    await asyncio.sleep(delay)
                    return True  # Retry the operation
                else:
                    await self.metrics.increment_counter(
                        "authorization_retry_exhausted",
                        {"operation": self.operation_name}
                    )
            elif issubclass(exc_type, NonRetryableAuthorizationError):
                await self.metrics.increment_counter(
                    "authorization_non_retryable_error",
                    {"operation": self.operation_name}
                )
            else:
                await self.metrics.increment_counter(
                    "authorization_unexpected_error",
                    {"operation": self.operation_name}
                )

        # Record operation time
        await self.metrics.record_operation_time(self.operation_name, self.start_time)
        return False  # Don't suppress the exception
