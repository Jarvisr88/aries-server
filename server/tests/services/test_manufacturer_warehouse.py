"""
Manufacturer and Warehouse Services Tests
Version: 2024-12-14_19-21
"""
import pytest
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.inventory import (
    ManufacturerService,
    WarehouseService
)
from app.schemas.inventory import (
    ManufacturerCreate,
    WarehouseCreate
)

@pytest.mark.asyncio
class TestManufacturerService:
    async def test_create_manufacturer(self, db: AsyncSession):
        # Arrange
        service = ManufacturerService(db)
        manufacturer_data = ManufacturerCreate(
            name="Test Manufacturer",
            contact_name="John Doe",
            contact_email="john@example.com",
            contact_phone="123-456-7890",
            website="https://example.com",
            notes="Test manufacturer notes"
        )

        # Act
        manufacturer = await service.create(manufacturer_data, current_user_id=1)

        # Assert
        assert manufacturer.id is not None
        assert manufacturer.name == "Test Manufacturer"
        assert manufacturer.contact_email == "john@example.com"

    async def test_create_duplicate_manufacturer(self, db: AsyncSession):
        # Arrange
        service = ManufacturerService(db)
        manufacturer_data = ManufacturerCreate(
            name="Test Manufacturer",
            contact_email="john@example.com"
        )

        # Act & Assert
        await service.create(manufacturer_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(manufacturer_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Manufacturer with this name already exists" in exc.value.detail

    async def test_search_manufacturers(self, db: AsyncSession):
        # Arrange
        service = ManufacturerService(db)
        manufacturers = [
            ManufacturerCreate(
                name=f"Manufacturer {i}",
                contact_email=f"contact{i}@example.com"
            ) for i in range(3)
        ]
        
        for m in manufacturers:
            await service.create(m, current_user_id=1)

        # Act
        search_results = await service.search_manufacturers(query="Manufacturer", limit=2)

        # Assert
        assert len(search_results) == 2
        assert all("Manufacturer" in m.name for m in search_results)

@pytest.mark.asyncio
class TestWarehouseService:
    async def test_create_warehouse(self, db: AsyncSession):
        # Arrange
        service = WarehouseService(db)
        warehouse_data = WarehouseCreate(
            name="Main Warehouse",
            address_line1="123 Storage St",
            city="Warehouse City",
            state="WH",
            postal_code="12345",
            country="USA",
            contact_name="Jane Doe",
            contact_phone="123-456-7890",
            storage_capacity=1000
        )

        # Act
        warehouse = await service.create(warehouse_data, current_user_id=1)

        # Assert
        assert warehouse.id is not None
        assert warehouse.name == "Main Warehouse"
        assert warehouse.storage_capacity == 1000

    async def test_create_duplicate_warehouse(self, db: AsyncSession):
        # Arrange
        service = WarehouseService(db)
        warehouse_data = WarehouseCreate(
            name="Main Warehouse",
            address_line1="123 Storage St",
            city="Warehouse City",
            state="WH",
            postal_code="12345"
        )

        # Act & Assert
        await service.create(warehouse_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(warehouse_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Warehouse with this name already exists" in exc.value.detail

    async def test_get_warehouse_capacity(self, db: AsyncSession):
        # Arrange
        service = WarehouseService(db)
        warehouse_data = WarehouseCreate(
            name="Test Warehouse",
            storage_capacity=1000,
            address_line1="Test Address"
        )
        warehouse = await service.create(warehouse_data, current_user_id=1)

        # Act
        capacity_info = await service.get_capacity_info(warehouse.id)

        # Assert
        assert capacity_info["total_capacity"] == 1000
        assert "available_capacity" in capacity_info
        assert "utilization_percentage" in capacity_info

    async def test_get_warehouse_items(self, db: AsyncSession):
        # Arrange
        service = WarehouseService(db)
        warehouse_data = WarehouseCreate(
            name="Test Warehouse",
            address_line1="Test Address"
        )
        warehouse = await service.create(warehouse_data, current_user_id=1)

        # Act
        items = await service.get_warehouse_items(
            warehouse.id,
            status="AVAILABLE",
            category_id=None,
            limit=10,
            offset=0
        )

        # Assert
        assert isinstance(items, list)
