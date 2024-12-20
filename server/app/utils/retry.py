"""
Retry utility for handling transient failures
"""
from functools import wraps
import asyncio
from typing import TypeVar, Callable, Any
import logging

from app.core.logging import logger

T = TypeVar('T')

def retry_with_backoff(max_retries: int = 3, backoff_factor: int = 2):
    """
    Decorator that retries an async function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Factor to multiply the delay by after each failure
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}. "
                            f"Final error: {str(e)}"
                        )
                        raise
                    
                    delay = backoff_factor ** retries
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} "
                        f"after {delay}s delay. Error: {str(e)}"
                    )
                    await asyncio.sleep(delay)
        
        return wrapper
    return decorator
