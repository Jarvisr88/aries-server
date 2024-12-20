"""
Inventory Management Domain Schemas
Version: 2024-12-14_17-51
"""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from app.models.inventory import ItemType, ItemStatus

class InventoryCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True

class InventoryCategoryCreate(InventoryCategoryBase):
    pass

class InventoryCategoryUpdate(InventoryCategoryBase):
    pass

class InventoryCategoryInDB(InventoryCategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ManufacturerBase(BaseModel):
    name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class ManufacturerCreate(ManufacturerBase):
    pass

class ManufacturerUpdate(ManufacturerBase):
    pass

class ManufacturerInDB(ManufacturerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InventoryItemBase(BaseModel):
    category_id: int
    manufacturer_id: int
    name: str
    description: Optional[str] = None
    model_number: str
    item_type: ItemType
    purchase_price: Decimal
    rental_price: Optional[Decimal] = None
    msrp: Optional[Decimal] = None
    reorder_point: int = 0
    reorder_quantity: int = 0
    minimum_stock: int = 0
    hcpcs_code: Optional[str] = None
    billing_description: Optional[str] = None
    is_active: bool = True
    is_serialized: bool = False
    is_rentable: bool = False
    requires_maintenance: bool = False
    maintenance_interval_days: Optional[int] = None

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(InventoryItemBase):
    pass

class InventoryItemInDB(InventoryItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    total_stock: int
    total_in_use: int
    model_config = ConfigDict(from_attributes=True)

class StockItemBase(BaseModel):
    inventory_item_id: int
    serial_number: Optional[str] = None
    lot_number: Optional[str] = None
    status: ItemStatus = ItemStatus.AVAILABLE
    warehouse_id: int
    location_code: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_order_number: Optional[str] = None
    purchase_cost: Optional[Decimal] = None
    notes: Optional[str] = None
    last_maintenance_date: Optional[datetime] = None
    next_maintenance_date: Optional[datetime] = None

class StockItemCreate(StockItemBase):
    pass

class StockItemUpdate(StockItemBase):
    pass

class StockItemInDB(StockItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WarehouseBase(BaseModel):
    name: str
    code: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str = Field(min_length=2, max_length=2)
    zip_code: str
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: bool = True

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(WarehouseBase):
    pass

class WarehouseInDB(WarehouseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MaintenanceScheduleBase(BaseModel):
    inventory_item_id: int
    name: str
    description: Optional[str] = None
    interval_days: int
    checklist: Optional[str] = None  # JSON string
    estimated_duration_minutes: int = 60
    is_active: bool = True

class MaintenanceScheduleCreate(MaintenanceScheduleBase):
    pass

class MaintenanceScheduleUpdate(MaintenanceScheduleBase):
    pass

class MaintenanceScheduleInDB(MaintenanceScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MaintenanceLogBase(BaseModel):
    stock_item_id: int
    maintenance_schedule_id: Optional[int] = None
    maintenance_date: datetime
    completed_by: str
    duration_minutes: int
    status: str
    notes: Optional[str] = None
    checklist_results: Optional[str] = None  # JSON string
    parts_replaced: Optional[str] = None  # JSON string
    labor_cost: Optional[Decimal] = None
    parts_cost: Optional[Decimal] = None

class MaintenanceLogCreate(MaintenanceLogBase):
    pass

class MaintenanceLogUpdate(MaintenanceLogBase):
    pass

class MaintenanceLogInDB(MaintenanceLogBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
