"""
Inventory Management Services
Version: 2024-12-14_19-18

This module implements services for the Inventory Management domain.
"""
from typing import List, Optional, Dict, Tuple, Decimal
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.core.service import BaseService
from app.models.inventory import (
    InventoryCategory,
    Manufacturer,
    InventoryItem,
    StockItem,
    Warehouse,
    MaintenanceSchedule,
    MaintenanceLog,
    ItemStatus,
    InventoryAdjustment,
    StockTransfer,
    InventoryReservation
)
from app.schemas.inventory import (
    InventoryCategoryCreate,
    InventoryCategoryUpdate,
    ManufacturerCreate,
    ManufacturerUpdate,
    InventoryItemCreate,
    InventoryItemUpdate,
    StockItemCreate,
    StockItemUpdate,
    WarehouseCreate,
    WarehouseUpdate,
    MaintenanceScheduleCreate,
    MaintenanceScheduleUpdate,
    MaintenanceLogCreate,
    MaintenanceLogUpdate
)
from app.core.logging import logger

class InventoryCategoryService(BaseService[InventoryCategory, InventoryCategoryCreate, InventoryCategoryUpdate]):
    """Service for managing inventory categories"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InventoryCategory, db)
    
    async def create(self, schema: InventoryCategoryCreate, current_user_id: int, **kwargs) -> InventoryCategory:
        """Create a new inventory category"""
        try:
            # Validate parent category if provided
            if schema.parent_id:
                parent = await self.get(schema.parent_id)
                if not parent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Parent category not found"
                    )
            
            # Create category
            data = schema.model_dump()
            data.update(kwargs)
            db_category = InventoryCategory(**data)
            self.db.add(db_category)
            
            await self.db.commit()
            await self.db.refresh(db_category)
            
            logger.info(f"Created new inventory category: {db_category.name}")
            return db_category
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating inventory category: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create inventory category"
            ) from e
    
    async def get_category_tree(self, parent_id: Optional[int] = None) -> List[InventoryCategory]:
        """Get category hierarchy tree"""
        try:
            query = select(InventoryCategory).where(
                InventoryCategory.parent_id == parent_id
            ).order_by(InventoryCategory.name)
            
            result = await self.db.execute(query)
            categories = result.scalars().all()
            return categories
            
        except Exception as e:
            logger.error(f"Error retrieving category tree: {str(e)}")
            return []

class InventoryItemService(BaseService[InventoryItem, InventoryItemCreate, InventoryItemUpdate]):
    """Service for managing inventory items"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(InventoryItem, db)
    
    async def create(self, schema: InventoryItemCreate, current_user_id: int, **kwargs) -> InventoryItem:
        """Create a new inventory item"""
        try:
            # Check for duplicate model number
            query = select(InventoryItem).where(
                and_(
                    InventoryItem.model_number == schema.model_number,
                    InventoryItem.manufacturer_id == schema.manufacturer_id
                )
            )
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Item with this model number already exists for this manufacturer"
                )
            
            # Create item
            data = schema.model_dump()
            data.update(kwargs)
            db_item = InventoryItem(**data)
            self.db.add(db_item)
            
            await self.db.commit()
            await self.db.refresh(db_item)
            
            logger.info(f"Created new inventory item: {db_item.name}")
            return db_item
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating inventory item: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create inventory item"
            ) from e
    
    async def search_items(
        self,
        query: str,
        category_id: Optional[int] = None,
        manufacturer_id: Optional[int] = None,
        item_type: Optional[str] = None,
        is_active: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[InventoryItem]:
        """Search inventory items with filters"""
        try:
            conditions = []
            if query:
                conditions.append(
                    or_(
                        InventoryItem.name.ilike(f"%{query}%"),
                        InventoryItem.model_number.ilike(f"%{query}%"),
                        InventoryItem.hcpcs_code.ilike(f"%{query}%")
                    )
                )
            if category_id:
                conditions.append(InventoryItem.category_id == category_id)
            if manufacturer_id:
                conditions.append(InventoryItem.manufacturer_id == manufacturer_id)
            if item_type:
                conditions.append(InventoryItem.item_type == item_type)
            if is_active is not None:
                conditions.append(InventoryItem.is_active == is_active)
            
            query = select(InventoryItem)
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching inventory items: {str(e)}")
            return []
    
    async def check_stock_levels(self) -> List[InventoryItem]:
        """Check items that need reordering"""
        try:
            query = select(InventoryItem).where(
                and_(
                    InventoryItem.is_active == True,
                    InventoryItem.total_stock <= InventoryItem.reorder_point
                )
            )
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error checking stock levels: {str(e)}")
            return []

class StockItemService(BaseService[StockItem, StockItemCreate, StockItemUpdate]):
    """Service for managing stock items"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(StockItem, db)
    
    async def create(self, schema: StockItemCreate, current_user_id: int, **kwargs) -> StockItem:
        """Create a new stock item"""
        try:
            # Check if serial number is required and unique
            inventory_item = await self.db.get(InventoryItem, schema.inventory_item_id)
            if inventory_item.is_serialized and not schema.serial_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Serial number is required for this item"
                )
            
            if schema.serial_number:
                query = select(StockItem).where(StockItem.serial_number == schema.serial_number)
                result = await self.db.execute(query)
                if result.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Stock item with this serial number already exists"
                    )
            
            # Create stock item
            data = schema.model_dump()
            data.update(kwargs)
            db_stock = StockItem(**data)
            self.db.add(db_stock)
            
            # Set next maintenance date if required
            if inventory_item.requires_maintenance and inventory_item.maintenance_interval_days:
                db_stock.next_maintenance_date = datetime.utcnow() + timedelta(
                    days=inventory_item.maintenance_interval_days
                )
            
            await self.db.commit()
            await self.db.refresh(db_stock)
            
            logger.info(f"Created new stock item: {db_stock.id}")
            return db_stock
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating stock item: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create stock item"
            ) from e
    
    async def update_status(
        self,
        stock_id: int,
        new_status: ItemStatus,
        notes: Optional[str] = None,
        current_user_id: int = None
    ) -> StockItem:
        """Update stock item status"""
        try:
            stock_item = await self.get(stock_id)
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            stock_item.status = new_status
            if notes:
                stock_item.notes = notes
            
            await self.db.commit()
            await self.db.refresh(stock_item)
            
            logger.info(f"Updated stock item status: {stock_item.id} -> {new_status}")
            return stock_item
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating stock item status: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update stock item status"
            ) from e

    async def adjust_inventory(
        self,
        item_id: int,
        adjustment_quantity: int,
        reason: str,
        location_id: int,
        current_user_id: int
    ) -> StockItem:
        """Adjust inventory quantity with audit trail"""
        try:
            stock_item = await self.get(item_id)
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            # Create adjustment record
            adjustment = InventoryAdjustment(
                stock_item_id=item_id,
                adjustment_quantity=adjustment_quantity,
                reason=reason,
                location_id=location_id,
                adjusted_by=current_user_id
            )
            self.db.add(adjustment)
            
            # Update stock quantity
            stock_item.quantity += adjustment_quantity
            if stock_item.quantity < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Adjustment would result in negative inventory"
                )
            
            await self.db.commit()
            await self.db.refresh(stock_item)
            
            logger.info(f"Adjusted inventory for item: {item_id}")
            return stock_item
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adjusting inventory: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not adjust inventory"
            ) from e

    async def transfer_stock(
        self,
        item_id: int,
        quantity: int,
        source_location_id: int,
        target_location_id: int,
        current_user_id: int
    ) -> Tuple[StockItem, StockItem]:
        """Transfer stock between locations"""
        try:
            # Get source stock item
            source_item = await self.get(item_id)
            if not source_item or source_item.location_id != source_location_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source stock item not found"
                )
            
            if source_item.quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient quantity in source location"
                )
            
            # Get or create target stock item
            target_item = await self.db.scalar(
                select(StockItem).where(
                    and_(
                        StockItem.inventory_item_id == source_item.inventory_item_id,
                        StockItem.location_id == target_location_id
                    )
                )
            )
            
            if not target_item:
                target_item = StockItem(
                    inventory_item_id=source_item.inventory_item_id,
                    location_id=target_location_id,
                    quantity=0,
                    status=ItemStatus.AVAILABLE
                )
                self.db.add(target_item)
            
            # Create transfer record
            transfer = StockTransfer(
                source_item_id=source_item.id,
                target_item_id=target_item.id,
                quantity=quantity,
                transferred_by=current_user_id
            )
            self.db.add(transfer)
            
            # Update quantities
            source_item.quantity -= quantity
            target_item.quantity += quantity
            
            await self.db.commit()
            await self.db.refresh(source_item)
            await self.db.refresh(target_item)
            
            logger.info(f"Transferred stock from {source_location_id} to {target_location_id}")
            return source_item, target_item
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error transferring stock: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not transfer stock"
            ) from e

    async def reserve_inventory(
        self,
        item_id: int,
        quantity: int,
        order_id: int,
        current_user_id: int
    ) -> StockItem:
        """Reserve inventory for an order"""
        try:
            stock_item = await self.get(item_id)
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            if stock_item.status != ItemStatus.AVAILABLE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stock item is not available for reservation"
                )
            
            if stock_item.quantity < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient quantity available"
                )
            
            # Create reservation record
            reservation = InventoryReservation(
                stock_item_id=item_id,
                order_id=order_id,
                quantity=quantity,
                reserved_by=current_user_id
            )
            self.db.add(reservation)
            
            # Update stock status and quantity
            stock_item.status = ItemStatus.RESERVED
            stock_item.quantity -= quantity
            
            await self.db.commit()
            await self.db.refresh(stock_item)
            
            logger.info(f"Reserved inventory for order: {order_id}")
            return stock_item
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reserving inventory: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not reserve inventory"
            ) from e

    async def release_reservation(
        self,
        reservation_id: int,
        current_user_id: int
    ) -> StockItem:
        """Release a reserved inventory item"""
        try:
            # Get reservation
            reservation = await self.db.get(InventoryReservation, reservation_id)
            if not reservation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reservation not found"
                )
            
            stock_item = await self.get(reservation.stock_item_id)
            if not stock_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock item not found"
                )
            
            # Update stock status and quantity
            stock_item.status = ItemStatus.AVAILABLE
            stock_item.quantity += reservation.quantity
            
            # Mark reservation as released
            reservation.released = True
            reservation.released_at = datetime.now()
            reservation.released_by = current_user_id
            
            await self.db.commit()
            await self.db.refresh(stock_item)
            
            logger.info(f"Released reservation: {reservation_id}")
            return stock_item
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error releasing reservation: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not release reservation"
            ) from e

    async def calculate_reorder_points(
        self,
        item_id: int,
        location_id: Optional[int] = None
    ) -> Dict[str, Decimal]:
        """Calculate reorder points based on historical data"""
        try:
            # Base query for stock items
            query = select(StockItem).where(
                StockItem.inventory_item_id == item_id
            )
            if location_id:
                query = query.where(StockItem.location_id == location_id)
            
            stock_items = await self.db.scalars(query)
            if not stock_items:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Stock items not found"
                )
            
            # Calculate metrics for each location
            results = {}
            for stock_item in stock_items:
                # Get historical demand data
                demand_query = select(func.avg(OrderDetail.quantity)).where(
                    and_(
                        OrderDetail.inventory_item_id == item_id,
                        OrderDetail.location_id == stock_item.location_id,
                        Order.created_at >= datetime.now() - timedelta(days=90)
                    )
                )
                result = await self.db.execute(demand_query)
                avg_demand = result.scalar_one_or_none() or Decimal('0')
                
                # Calculate lead time demand
                lead_time_days = Decimal('7')  # Assuming 7 days lead time
                lead_time_demand = avg_demand * lead_time_days
                
                # Calculate safety stock (2 weeks worth of average demand)
                safety_stock = avg_demand * Decimal('14')
                
                # Calculate reorder point
                reorder_point = lead_time_demand + safety_stock
                
                results[str(stock_item.location_id)] = {
                    'avg_daily_demand': avg_demand,
                    'lead_time_demand': lead_time_demand,
                    'safety_stock': safety_stock,
                    'reorder_point': reorder_point
                }
            
            logger.info(f"Calculated reorder points for item: {item_id}")
            return results
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calculating reorder points: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not calculate reorder points"
            ) from e

class ManufacturerService(BaseService[Manufacturer, ManufacturerCreate, ManufacturerUpdate]):
    """Service for managing manufacturers"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Manufacturer, db)
    
    async def create(self, schema: ManufacturerCreate, current_user_id: int, **kwargs) -> Manufacturer:
        """Create a new manufacturer"""
        try:
            # Check for duplicate manufacturer
            query = select(Manufacturer).where(
                Manufacturer.name == schema.name
            )
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Manufacturer with this name already exists"
                )
            
            # Create manufacturer
            data = schema.model_dump()
            data.update(kwargs)
            db_manufacturer = Manufacturer(**data)
            self.db.add(db_manufacturer)
            
            await self.db.commit()
            await self.db.refresh(db_manufacturer)
            
            logger.info(f"Created new manufacturer: {db_manufacturer.name}")
            return db_manufacturer
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating manufacturer: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create manufacturer"
            ) from e
    
    async def search_manufacturers(
        self,
        query: str,
        is_active: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> List[Manufacturer]:
        """Search manufacturers with filters"""
        try:
            conditions = []
            if query:
                conditions.append(
                    or_(
                        Manufacturer.name.ilike(f"%{query}%"),
                        Manufacturer.contact_name.ilike(f"%{query}%"),
                        Manufacturer.contact_email.ilike(f"%{query}%")
                    )
                )
            if is_active is not None:
                conditions.append(Manufacturer.is_active == is_active)
            
            query = select(Manufacturer)
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching manufacturers: {str(e)}")
            return []

class MaintenanceScheduleService(BaseService[MaintenanceSchedule, MaintenanceScheduleCreate, MaintenanceScheduleUpdate]):
    """Service for managing maintenance schedules"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(MaintenanceSchedule, db)
    
    async def create(self, schema: MaintenanceScheduleCreate, current_user_id: int, **kwargs) -> MaintenanceSchedule:
        """Create a new maintenance schedule"""
        try:
            # Create schedule
            data = schema.model_dump()
            data.update(kwargs)
            db_schedule = MaintenanceSchedule(**data)
            self.db.add(db_schedule)
            
            await self.db.commit()
            await self.db.refresh(db_schedule)
            
            logger.info(f"Created new maintenance schedule: {db_schedule.name}")
            return db_schedule
            
        except Exception as e:
            logger.error(f"Error creating maintenance schedule: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create maintenance schedule"
            ) from e
    
    async def get_due_maintenance(self, days_ahead: int = 7) -> List[StockItem]:
        """Get items due for maintenance"""
        try:
            future_date = datetime.utcnow() + timedelta(days=days_ahead)
            
            query = select(StockItem).where(
                and_(
                    StockItem.next_maintenance_date <= future_date,
                    StockItem.status != ItemStatus.RETIRED
                )
            ).order_by(StockItem.next_maintenance_date)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting due maintenance: {str(e)}")
            return []

class MaintenanceLogService(BaseService[MaintenanceLog, MaintenanceLogCreate, MaintenanceLogUpdate]):
    """Service for managing maintenance logs"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(MaintenanceLog, db)
    
    async def create(self, schema: MaintenanceLogCreate, current_user_id: int, **kwargs) -> MaintenanceLog:
        """Create a new maintenance log"""
        try:
            # Create log entry
            data = schema.model_dump()
            data.update(kwargs)
            db_log = MaintenanceLog(**data)
            self.db.add(db_log)
            
            # Update stock item maintenance dates
            stock_item = await self.db.get(StockItem, schema.stock_item_id)
            if stock_item:
                stock_item.last_maintenance_date = schema.maintenance_date
                if stock_item.inventory_item.maintenance_interval_days:
                    stock_item.next_maintenance_date = schema.maintenance_date + timedelta(
                        days=stock_item.inventory_item.maintenance_interval_days
                    )
            
            await self.db.commit()
            await self.db.refresh(db_log)
            
            logger.info(f"Created new maintenance log: {db_log.id}")
            return db_log
            
        except Exception as e:
            logger.error(f"Error creating maintenance log: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create maintenance log"
            ) from e
    
    async def get_maintenance_history(
        self,
        stock_item_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[MaintenanceLog]:
        """Get maintenance history for a stock item"""
        try:
            query = select(MaintenanceLog).where(
                MaintenanceLog.stock_item_id == stock_item_id
            ).order_by(MaintenanceLog.maintenance_date.desc())
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving maintenance history: {str(e)}")
            return []

class WarehouseService(BaseService[Warehouse, WarehouseCreate, WarehouseUpdate]):
    """Service for managing warehouses"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Warehouse, db)
    
    async def create(self, schema: WarehouseCreate, current_user_id: int, **kwargs) -> Warehouse:
        """Create a new warehouse"""
        try:
            # Check for duplicate warehouse
            query = select(Warehouse).where(
                Warehouse.name == schema.name
            )
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Warehouse with this name already exists"
                )
            
            # Create warehouse
            data = schema.model_dump()
            data.update(kwargs)
            db_warehouse = Warehouse(**data)
            self.db.add(db_warehouse)
            
            await self.db.commit()
            await self.db.refresh(db_warehouse)
            
            logger.info(f"Created new warehouse: {db_warehouse.name}")
            return db_warehouse
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating warehouse: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create warehouse"
            ) from e
    
    async def get_capacity_info(self, warehouse_id: int) -> dict:
        """Get warehouse capacity information"""
        try:
            warehouse = await self.get(warehouse_id)
            if not warehouse:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Warehouse not found"
                )
            
            # Calculate current usage
            query = select(func.count(StockItem.id)).where(
                and_(
                    StockItem.warehouse_id == warehouse_id,
                    StockItem.status != ItemStatus.RETIRED
                )
            )
            result = await self.db.execute(query)
            current_items = result.scalar()
            
            # Calculate capacity metrics
            total_capacity = warehouse.storage_capacity
            available_capacity = max(0, total_capacity - current_items)
            utilization_percentage = (current_items / total_capacity * 100) if total_capacity > 0 else 0
            
            return {
                "total_capacity": total_capacity,
                "current_items": current_items,
                "available_capacity": available_capacity,
                "utilization_percentage": round(utilization_percentage, 2)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting warehouse capacity info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not get warehouse capacity information"
            ) from e
    
    async def get_warehouse_items(
        self,
        warehouse_id: int,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[StockItem]:
        """Get items in a warehouse with filters"""
        try:
            conditions = [StockItem.warehouse_id == warehouse_id]
            
            if status:
                conditions.append(StockItem.status == status)
            if category_id:
                conditions.append(StockItem.inventory_item.has(category_id=category_id))
            
            query = select(StockItem).where(
                and_(*conditions)
            ).order_by(StockItem.created_at.desc())
            
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting warehouse items: {str(e)}")
            return []
