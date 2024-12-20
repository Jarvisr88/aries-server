"""
Inventory Management Services Tests
Version: 2024-12-14_19-18
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.inventory import (
    InventoryCategoryService,
    InventoryItemService,
    StockItemService,
    MaintenanceScheduleService,
    MaintenanceLogService
)
from app.schemas.inventory import (
    InventoryCategoryCreate,
    InventoryItemCreate,
    StockItemCreate,
    MaintenanceScheduleCreate,
    MaintenanceLogCreate
)
from app.models.inventory import ItemType, ItemStatus

@pytest.mark.asyncio
class TestInventoryCategoryService:
    async def test_create_category(self, db: AsyncSession):
        # Arrange
        service = InventoryCategoryService(db)
        category_data = InventoryCategoryCreate(
            name="Test Category",
            description="Test Description"
        )

        # Act
        category = await service.create(category_data, current_user_id=1)

        # Assert
        assert category.id is not None
        assert category.name == "Test Category"
        assert category.description == "Test Description"
        assert category.is_active == True

    async def test_create_subcategory(self, db: AsyncSession):
        # Arrange
        service = InventoryCategoryService(db)
        parent_data = InventoryCategoryCreate(name="Parent Category")
        parent = await service.create(parent_data, current_user_id=1)

        child_data = InventoryCategoryCreate(
            name="Child Category",
            parent_id=parent.id
        )

        # Act
        child = await service.create(child_data, current_user_id=1)

        # Assert
        assert child.id is not None
        assert child.parent_id == parent.id

    async def test_get_category_tree(self, db: AsyncSession):
        # Arrange
        service = InventoryCategoryService(db)
        
        # Create parent and children
        parent_data = InventoryCategoryCreate(name="Parent Category")
        parent = await service.create(parent_data, current_user_id=1)
        
        for i in range(3):
            child_data = InventoryCategoryCreate(
                name=f"Child Category {i}",
                parent_id=parent.id
            )
            await service.create(child_data, current_user_id=1)

        # Act
        children = await service.get_category_tree(parent.id)

        # Assert
        assert len(children) == 3
        assert all(c.parent_id == parent.id for c in children)

@pytest.mark.asyncio
class TestInventoryItemService:
    async def test_create_item(self, db: AsyncSession):
        # Arrange
        service = InventoryItemService(db)
        item_data = InventoryItemCreate(
            category_id=1,
            manufacturer_id=1,
            name="Test Item",
            model_number="TEST-001",
            item_type=ItemType.EQUIPMENT,
            purchase_price=Decimal("100.00"),
            reorder_point=5,
            is_serialized=True
        )

        # Act
        item = await service.create(item_data, current_user_id=1)

        # Assert
        assert item.id is not None
        assert item.name == "Test Item"
        assert item.model_number == "TEST-001"
        assert item.is_serialized == True

    async def test_create_duplicate_item(self, db: AsyncSession):
        # Arrange
        service = InventoryItemService(db)
        item_data = InventoryItemCreate(
            category_id=1,
            manufacturer_id=1,
            name="Test Item",
            model_number="TEST-001",
            item_type=ItemType.EQUIPMENT
        )

        # Act & Assert
        await service.create(item_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(item_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Item with this model number already exists" in exc.value.detail

    async def test_search_items(self, db: AsyncSession):
        # Arrange
        service = InventoryItemService(db)
        
        # Create test items
        items = [
            InventoryItemCreate(
                category_id=1,
                manufacturer_id=1,
                name=f"Test Item {i}",
                model_number=f"TEST-00{i}",
                item_type=ItemType.EQUIPMENT
            ) for i in range(3)
        ]
        
        for item in items:
            await service.create(item, current_user_id=1)

        # Act
        search_results = await service.search_items(query="Test Item", limit=2)

        # Assert
        assert len(search_results) == 2
        assert all("Test Item" in item.name for item in search_results)

@pytest.mark.asyncio
class TestStockItemService:
    async def test_create_stock_item(self, db: AsyncSession):
        # Arrange
        service = StockItemService(db)
        stock_data = StockItemCreate(
            inventory_item_id=1,
            serial_number="SN12345",
            warehouse_id=1,
            location_code="A1-B2-C3",
            purchase_date=datetime.utcnow(),
            purchase_cost=Decimal("100.00")
        )

        # Act
        stock = await service.create(stock_data, current_user_id=1)

        # Assert
        assert stock.id is not None
        assert stock.serial_number == "SN12345"
        assert stock.status == ItemStatus.AVAILABLE

    async def test_update_stock_status(self, db: AsyncSession):
        # Arrange
        service = StockItemService(db)
        stock_data = StockItemCreate(
            inventory_item_id=1,
            serial_number="SN12345",
            warehouse_id=1
        )
        stock = await service.create(stock_data, current_user_id=1)

        # Act
        updated_stock = await service.update_status(
            stock.id,
            ItemStatus.IN_USE,
            notes="Item is now in use"
        )

        # Assert
        assert updated_stock.status == ItemStatus.IN_USE
        assert updated_stock.notes == "Item is now in use"

@pytest.mark.asyncio
class TestMaintenanceScheduleService:
    async def test_create_maintenance_schedule(self, db: AsyncSession):
        # Arrange
        service = MaintenanceScheduleService(db)
        schedule_data = MaintenanceScheduleCreate(
            inventory_item_id=1,
            name="Monthly Check",
            interval_days=30,
            checklist="1. Check A\n2. Check B",
            estimated_duration_minutes=45
        )

        # Act
        schedule = await service.create(schedule_data, current_user_id=1)

        # Assert
        assert schedule.id is not None
        assert schedule.name == "Monthly Check"
        assert schedule.interval_days == 30
        assert schedule.is_active == True

    async def test_get_due_maintenance(self, db: AsyncSession):
        # Arrange
        stock_service = StockItemService(db)
        maintenance_service = MaintenanceScheduleService(db)
        
        # Create stock items with different maintenance dates
        now = datetime.utcnow()
        stock_items = [
            StockItemCreate(
                inventory_item_id=1,
                serial_number=f"SN{i}",
                warehouse_id=1,
                next_maintenance_date=now + timedelta(days=i)
            ) for i in range(10)
        ]
        
        for item in stock_items:
            await stock_service.create(item, current_user_id=1)

        # Act
        due_items = await maintenance_service.get_due_maintenance(days_ahead=5)

        # Assert
        assert len(due_items) == 6  # Items due within next 5 days

@pytest.mark.asyncio
class TestMaintenanceLogService:
    async def test_create_maintenance_log(self, db: AsyncSession):
        # Arrange
        service = MaintenanceLogService(db)
        log_data = MaintenanceLogCreate(
            stock_item_id=1,
            maintenance_schedule_id=1,
            maintenance_date=datetime.utcnow(),
            completed_by="John Doe",
            duration_minutes=30,
            status="COMPLETED",
            notes="Regular maintenance performed",
            labor_cost=Decimal("50.00")
        )

        # Act
        log = await service.create(log_data, current_user_id=1)

        # Assert
        assert log.id is not None
        assert log.completed_by == "John Doe"
        assert log.status == "COMPLETED"

    async def test_get_maintenance_history(self, db: AsyncSession):
        # Arrange
        service = MaintenanceLogService(db)
        
        # Create multiple maintenance logs
        logs = [
            MaintenanceLogCreate(
                stock_item_id=1,
                maintenance_date=datetime.utcnow() - timedelta(days=i),
                completed_by="John Doe",
                duration_minutes=30,
                status="COMPLETED"
            ) for i in range(3)
        ]
        
        for log in logs:
            await service.create(log, current_user_id=1)

        # Act
        history = await service.get_maintenance_history(stock_item_id=1, limit=2)

        # Assert
        assert len(history) == 2
        assert history[0].maintenance_date > history[1].maintenance_date  # Most recent first
