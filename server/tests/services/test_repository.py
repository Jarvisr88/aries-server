"""
Repository Management Services Tests
Version: 2024-12-14_20-03
"""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.repository import RegionService, VariableService
from app.schemas.repository import RegionCreate, VariableCreate

@pytest.mark.asyncio
class TestRegionService:
    async def test_create_region(self, db: AsyncSession):
        # Arrange
        service = RegionService(db)
        region_data = RegionCreate(
            name="TEST_REGION",
            receiver_id="RCV001",
            receiver_name="Test Receiver",
            submitter_id="SUB001",
            submitter_name="Test Submitter",
            production=False
        )

        # Act
        region = await service.create(region_data, current_user_id=1)

        # Assert
        assert region.name == "TEST_REGION"
        assert region.receiver_id == "RCV001"
        assert region.production == False

    async def test_create_duplicate_region(self, db: AsyncSession):
        # Arrange
        service = RegionService(db)
        region_data = RegionCreate(
            name="TEST_REGION",
            receiver_id="RCV001",
            receiver_name="Test Receiver"
        )

        # Act & Assert
        await service.create(region_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(region_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Region with this name already exists" in exc.value.detail

    async def test_get_production_regions(self, db: AsyncSession):
        # Arrange
        service = RegionService(db)
        
        # Create production and non-production regions
        prod_region = RegionCreate(
            name="PROD_REGION",
            receiver_id="RCV001",
            production=True
        )
        test_region = RegionCreate(
            name="TEST_REGION",
            receiver_id="RCV002",
            production=False
        )
        
        await service.create(prod_region, current_user_id=1)
        await service.create(test_region, current_user_id=1)

        # Act
        prod_regions = await service.get_production_regions()

        # Assert
        assert len(prod_regions) == 1
        assert prod_regions[0].name == "PROD_REGION"

@pytest.mark.asyncio
class TestVariableService:
    async def test_create_variable(self, db: AsyncSession):
        # Arrange
        service = VariableService(db)
        variable_data = VariableCreate(
            name="TEST_VAR",
            value="test_value"
        )

        # Act
        variable = await service.create(variable_data, current_user_id=1)

        # Assert
        assert variable.name == "TEST_VAR"
        assert variable.value == "test_value"

    async def test_create_duplicate_variable(self, db: AsyncSession):
        # Arrange
        service = VariableService(db)
        variable_data = VariableCreate(
            name="TEST_VAR",
            value="test_value"
        )

        # Act & Assert
        await service.create(variable_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(variable_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Variable with this name already exists" in exc.value.detail

    async def test_get_set_variable_value(self, db: AsyncSession):
        # Arrange
        service = VariableService(db)
        
        # Act
        # Set new variable
        variable = await service.set_value("TEST_VAR", "initial_value", current_user_id=1)
        
        # Get value
        value1 = await service.get_value("TEST_VAR")
        
        # Update value
        await service.set_value("TEST_VAR", "updated_value", current_user_id=1)
        value2 = await service.get_value("TEST_VAR")

        # Assert
        assert value1 == "initial_value"
        assert value2 == "updated_value"

    async def test_get_nonexistent_variable(self, db: AsyncSession):
        # Arrange
        service = VariableService(db)
        
        # Act
        value = await service.get_value("NONEXISTENT_VAR")

        # Assert
        assert value is None
