"""
Order Processing Services Tests
Version: 2024-12-14_19-16
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.order import (
    OrderService,
    ShippingMethodService,
    DeliveryScheduleService
)
from app.schemas.order import (
    OrderCreate,
    OrderDetailCreate,
    DeliveryScheduleCreate,
    ShippingMethodCreate
)
from app.models.order import OrderStatus, SaleRentType

@pytest.mark.asyncio
class TestOrderService:
    async def test_create_order(self, db: AsyncSession):
        # Arrange
        service = OrderService(db)
        order_detail = OrderDetailCreate(
            inventory_item_id=1,
            sale_rent_type=SaleRentType.SALE,
            quantity=1,
            unit_price=Decimal("100.00")
        )
        order_data = OrderCreate(
            customer_id=1,
            order_details=[order_detail]
        )

        # Act
        order = await service.create(order_data, current_user_id=1)

        # Assert
        assert order.id is not None
        assert order.order_number.startswith("ORD-")
        assert order.status == OrderStatus.PENDING
        assert len(order.order_details) == 1
        assert order.order_details[0].inventory_item_id == 1

    async def test_update_order_status(self, db: AsyncSession):
        # Arrange
        service = OrderService(db)
        order_detail = OrderDetailCreate(
            inventory_item_id=1,
            sale_rent_type=SaleRentType.SALE,
            quantity=1,
            unit_price=Decimal("100.00")
        )
        order_data = OrderCreate(
            customer_id=1,
            order_details=[order_detail]
        )
        order = await service.create(order_data, current_user_id=1)

        # Act
        updated_order = await service.update_status(
            order.id,
            OrderStatus.PROCESSING,
            notes="Order is being processed"
        )

        # Assert
        assert updated_order.status == OrderStatus.PROCESSING
        history = await service.get_status_history(order.id)
        assert len(history) == 2  # Initial PENDING + PROCESSING
        assert history[-1].status == OrderStatus.PROCESSING
        assert history[-1].notes == "Order is being processed"

    async def test_search_orders(self, db: AsyncSession):
        # Arrange
        service = OrderService(db)
        
        # Create multiple orders
        for i in range(3):
            order_detail = OrderDetailCreate(
                inventory_item_id=1,
                sale_rent_type=SaleRentType.SALE,
                quantity=1,
                unit_price=Decimal("100.00")
            )
            order_data = OrderCreate(
                customer_id=1,
                order_details=[order_detail]
            )
            await service.create(order_data, current_user_id=1)

        # Act
        orders = await service.search_orders(
            customer_id=1,
            status=OrderStatus.PENDING,
            limit=2
        )

        # Assert
        assert len(orders) == 2
        assert all(o.customer_id == 1 for o in orders)
        assert all(o.status == OrderStatus.PENDING for o in orders)

@pytest.mark.asyncio
class TestShippingMethodService:
    async def test_create_shipping_method(self, db: AsyncSession):
        # Arrange
        service = ShippingMethodService(db)
        method_data = ShippingMethodCreate(
            name="Express Delivery",
            carrier="FastShip",
            description="Next day delivery",
            tracking_url_template="https://track.fastship.com/{tracking_number}"
        )

        # Act
        method = await service.create(method_data, current_user_id=1)

        # Assert
        assert method.id is not None
        assert method.name == "Express Delivery"
        assert method.carrier == "FastShip"
        assert method.is_active == True

    async def test_create_duplicate_shipping_method(self, db: AsyncSession):
        # Arrange
        service = ShippingMethodService(db)
        method_data = ShippingMethodCreate(
            name="Express Delivery",
            carrier="FastShip"
        )

        # Act & Assert
        await service.create(method_data, current_user_id=1)
        with pytest.raises(HTTPException) as exc:
            await service.create(method_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Shipping method with this name already exists" in exc.value.detail

    async def test_get_active_methods(self, db: AsyncSession):
        # Arrange
        service = ShippingMethodService(db)
        
        # Create active and inactive methods
        active_method = ShippingMethodCreate(
            name="Active Method",
            carrier="Carrier",
            is_active=True
        )
        inactive_method = ShippingMethodCreate(
            name="Inactive Method",
            carrier="Carrier",
            is_active=False
        )
        
        await service.create(active_method, current_user_id=1)
        await service.create(inactive_method, current_user_id=1)

        # Act
        active_methods = await service.get_active_methods()

        # Assert
        assert len(active_methods) == 1
        assert active_methods[0].name == "Active Method"

@pytest.mark.asyncio
class TestDeliveryScheduleService:
    async def test_create_delivery_schedule(self, db: AsyncSession):
        # Arrange
        service = DeliveryScheduleService(db)
        now = datetime.utcnow()
        schedule_data = DeliveryScheduleCreate(
            order_id=1,
            scheduled_date=now.date(),
            delivery_window_start=now.replace(hour=9),
            delivery_window_end=now.replace(hour=12),
            status="SCHEDULED",
            driver_notes="Ring doorbell"
        )

        # Act
        schedule = await service.create(schedule_data, current_user_id=1)

        # Assert
        assert schedule.id is not None
        assert schedule.order_id == 1
        assert schedule.status == "SCHEDULED"
        assert schedule.signature_required == True
        assert schedule.signature_obtained == False

    async def test_create_invalid_delivery_window(self, db: AsyncSession):
        # Arrange
        service = DeliveryScheduleService(db)
        now = datetime.utcnow()
        schedule_data = DeliveryScheduleCreate(
            order_id=1,
            scheduled_date=now.date(),
            delivery_window_start=now.replace(hour=12),
            delivery_window_end=now.replace(hour=9),  # End before start
            status="SCHEDULED"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await service.create(schedule_data, current_user_id=1)
        assert exc.value.status_code == 400
        assert "Delivery window end must be after start time" in exc.value.detail

    async def test_complete_delivery(self, db: AsyncSession):
        # Arrange
        service = DeliveryScheduleService(db)
        now = datetime.utcnow()
        schedule_data = DeliveryScheduleCreate(
            order_id=1,
            scheduled_date=now.date(),
            delivery_window_start=now.replace(hour=9),
            delivery_window_end=now.replace(hour=12),
            status="SCHEDULED"
        )
        schedule = await service.create(schedule_data, current_user_id=1)

        # Act
        completed_schedule = await service.complete_delivery(
            schedule.id,
            signature="John Doe",
            delivery_notes="Delivered to front door"
        )

        # Assert
        assert completed_schedule.status == "COMPLETED"
        assert completed_schedule.signature_obtained == True
        assert completed_schedule.driver_notes == "Delivered to front door"
        assert completed_schedule.actual_delivery_date is not None

    async def test_get_daily_schedule(self, db: AsyncSession):
        # Arrange
        service = DeliveryScheduleService(db)
        now = datetime.utcnow()
        
        # Create schedules for today and tomorrow
        today_schedule = DeliveryScheduleCreate(
            order_id=1,
            scheduled_date=now.date(),
            delivery_window_start=now.replace(hour=9),
            delivery_window_end=now.replace(hour=12),
            status="SCHEDULED"
        )
        tomorrow_schedule = DeliveryScheduleCreate(
            order_id=2,
            scheduled_date=(now + timedelta(days=1)).date(),
            delivery_window_start=(now + timedelta(days=1)).replace(hour=9),
            delivery_window_end=(now + timedelta(days=1)).replace(hour=12),
            status="SCHEDULED"
        )
        
        await service.create(today_schedule, current_user_id=1)
        await service.create(tomorrow_schedule, current_user_id=1)

        # Act
        today_deliveries = await service.get_daily_schedule(now)

        # Assert
        assert len(today_deliveries) == 1
        assert today_deliveries[0].order_id == 1
