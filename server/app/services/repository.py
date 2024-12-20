"""
Repository Management Services
Version: 2024-12-14_20-03

This module implements services for the Repository schema.
"""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.service import BaseService
from app.models.repository import Region, Variable
from app.schemas.repository import (
    RegionCreate,
    RegionUpdate,
    VariableCreate,
    VariableUpdate
)
from app.core.logging import logger

class RegionService(BaseService[Region, RegionCreate, RegionUpdate]):
    """Service for managing regions"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Region, db)
    
    async def create(self, schema: RegionCreate, current_user_id: int, **kwargs) -> Region:
        """Create a new region"""
        try:
            # Check for existing region
            query = select(Region).where(Region.name == schema.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Region with this name already exists"
                )
            
            # Create region
            data = schema.model_dump()
            data.update(kwargs)
            db_region = Region(**data)
            self.db.add(db_region)
            
            await self.db.commit()
            await self.db.refresh(db_region)
            
            logger.info(f"Created new region: {db_region.name}")
            return db_region
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating region: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create region"
            ) from e

    async def get_production_regions(self) -> List[Region]:
        """Get all production regions"""
        try:
            query = select(Region).where(Region.production == True)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving production regions: {str(e)}")
            return []

class VariableService(BaseService[Variable, VariableCreate, VariableUpdate]):
    """Service for managing system variables"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Variable, db)
    
    async def create(self, schema: VariableCreate, current_user_id: int, **kwargs) -> Variable:
        """Create a new system variable"""
        try:
            # Check for existing variable
            query = select(Variable).where(Variable.name == schema.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Variable with this name already exists"
                )
            
            # Create variable
            data = schema.model_dump()
            data.update(kwargs)
            db_variable = Variable(**data)
            self.db.add(db_variable)
            
            await self.db.commit()
            await self.db.refresh(db_variable)
            
            logger.info(f"Created new system variable: {db_variable.name}")
            return db_variable
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating system variable: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create system variable"
            ) from e
    
    async def get_value(self, name: str) -> Optional[str]:
        """Get a variable's value by name"""
        try:
            query = select(Variable).where(Variable.name == name)
            result = await self.db.execute(query)
            variable = result.scalar_one_or_none()
            return variable.value if variable else None
        except Exception as e:
            logger.error(f"Error retrieving variable value: {str(e)}")
            return None

    async def set_value(self, name: str, value: str, current_user_id: int) -> Optional[Variable]:
        """Set a variable's value, creating it if it doesn't exist"""
        try:
            variable = await self.get_by_id(name)
            if variable:
                # Update existing variable
                variable.value = value
                await self.db.commit()
                await self.db.refresh(variable)
            else:
                # Create new variable
                schema = VariableCreate(name=name, value=value)
                variable = await self.create(schema, current_user_id)
            
            logger.info(f"Updated system variable {name} = {value}")
            return variable
            
        except Exception as e:
            logger.error(f"Error setting variable value: {str(e)}")
            await self.db.rollback()
            return None
