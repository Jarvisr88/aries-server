"""
Base Stored Procedure Module

This module provides the base class for all stored procedures implementations.
"""
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.logging import logger


class BaseProcedure:
    """Base class for all stored procedures"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._transaction = None
        self._results: Dict[str, Any] = {}

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the stored procedure with given parameters"""
        try:
            async with self.db.begin() as transaction:
                self._transaction = transaction
                await self._pre_execute(*args, **kwargs)
                await self._execute(*args, **kwargs)
                await self._post_execute(*args, **kwargs)
                return self._results
        except Exception as e:
            logger.error(f"Error executing procedure {self.__class__.__name__}: {str(e)}")
            raise
        finally:
            self._transaction = None
            self._results = {}

    async def _pre_execute(self, *args, **kwargs) -> None:
        """Pre-execution hook for setup and validation"""
        pass

    async def _execute(self, *args, **kwargs) -> None:
        """Main execution logic - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _execute method")

    async def _post_execute(self, *args, **kwargs) -> None:
        """Post-execution hook for cleanup and final processing"""
        pass

    async def _execute_raw_sql(self, sql: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL with parameters"""
        try:
            result = await self.db.execute(text(sql), params or {})
            return result
        except Exception as e:
            logger.error(f"Error executing SQL in {self.__class__.__name__}: {str(e)}")
            raise
