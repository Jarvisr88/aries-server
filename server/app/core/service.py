"""
Base Service Layer Implementation
Version: 2024-12-14_19-07

This module provides the base service layer implementation following our guiding principles:
- Separation of concerns
- Single responsibility
- Interface segregation
- Dependency injection
- Error handling and logging
"""
from typing import Generic, TypeVar, Type, Optional, List, Any
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from pydantic import BaseModel

from app.core.database import Base
from app.core.logging import logger

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for all services implementing common CRUD operations
    """
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
        self._name = model.__name__

    async def create(self, schema: CreateSchemaType, **kwargs) -> ModelType:
        """Create a new record"""
        try:
            data = schema.model_dump(exclude_unset=True)
            data.update(kwargs)
            
            db_obj = self.model(**data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            
            logger.info(f"Created new {self._name}: {db_obj.id}")
            return db_obj
        except Exception as e:
            logger.error(f"Error creating {self._name}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not create {self._name}"
            ) from e

    async def get(self, id: Any) -> Optional[ModelType]:
        """Get a record by id"""
        try:
            query = select(self.model).where(self.model.id == id)
            result = await self.db.execute(query)
            obj = result.scalar_one_or_none()
            
            if not obj:
                logger.warning(f"{self._name} with id {id} not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self._name} not found"
                )
            
            return obj
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving {self._name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving {self._name}"
            ) from e

    async def get_multi(
        self, 
        *,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get multiple records with optional filtering"""
        try:
            query = select(self.model)
            
            # Apply filters
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)
            
            query = query.offset(skip).limit(limit)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving multiple {self._name}s: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving {self._name}s"
            ) from e

    async def update(
        self,
        id: Any,
        schema: UpdateSchemaType,
        **kwargs
    ) -> Optional[ModelType]:
        """Update a record"""
        try:
            obj = await self.get(id)
            data = schema.model_dump(exclude_unset=True)
            data.update(kwargs)
            data["updated_at"] = datetime.utcnow()
            
            for field, value in data.items():
                setattr(obj, field, value)
            
            await self.db.commit()
            await self.db.refresh(obj)
            
            logger.info(f"Updated {self._name}: {id}")
            return obj
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating {self._name}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update {self._name}"
            ) from e

    async def delete(self, id: Any) -> bool:
        """Delete a record"""
        try:
            obj = await self.get(id)
            await self.db.delete(obj)
            await self.db.commit()
            
            logger.info(f"Deleted {self._name}: {id}")
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting {self._name}: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not delete {self._name}"
            ) from e

    async def exists(self, id: Any) -> bool:
        """Check if a record exists"""
        try:
            await self.get(id)
            return True
        except HTTPException:
            return False
