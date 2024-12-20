"""
Inventory Management Domain Models
Version: 2024-12-14_17-51
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.system import TimestampMixin
from app.core.database import Base

class ItemType(str, Enum):
    EQUIPMENT = 'equipment'
    SUPPLY = 'supply'
    ACCESSORY = 'accessory'
    PART = 'part'

class ItemStatus(str, Enum):
    AVAILABLE = 'available'
    IN_USE = 'in_use'
    MAINTENANCE = 'maintenance'
    RETIRED = 'retired'
    LOST = 'lost'
    DAMAGED = 'damaged'

class InventoryCategory(Base, TimestampMixin):
    """Inventory Category model - migrated from c01.tbl_inventory_category"""
    __tablename__ = 'inventory_categories'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)
    parent_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('inventory_categories.id'))
    is_active: Mapped[bool] = Column(Boolean, default=True)

    # Relationships
    parent = relationship("InventoryCategory", remote_side=[id])
    children: Mapped[List["InventoryCategory"]] = relationship("InventoryCategory")
    items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="category")

class Manufacturer(Base, TimestampMixin):
    """Manufacturer model - migrated from c01.tbl_manufacturer"""
    __tablename__ = 'manufacturers'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    contact_name: Mapped[Optional[str]] = Column(String(100))
    contact_email: Mapped[Optional[str]] = Column(String(255))
    contact_phone: Mapped[Optional[str]] = Column(String(20))
    website: Mapped[Optional[str]] = Column(String(255))
    notes: Mapped[Optional[str]] = Column(Text)
    is_active: Mapped[bool] = Column(Boolean, default=True)

    # Relationships
    items: Mapped[List["InventoryItem"]] = relationship("InventoryItem", back_populates="manufacturer")

class InventoryItem(Base, TimestampMixin):
    """Inventory Item model - migrated from c01.tbl_inventory_item"""
    __tablename__ = 'inventory_items'

    id: Mapped[int] = Column(Integer, primary_key=True)
    category_id: Mapped[int] = Column(Integer, ForeignKey('inventory_categories.id'), nullable=False)
    manufacturer_id: Mapped[int] = Column(Integer, ForeignKey('manufacturers.id'), nullable=False)
    
    # Basic Information
    name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)
    model_number: Mapped[str] = Column(String(100), nullable=False)
    item_type: Mapped[ItemType] = Column(SQLEnum(ItemType), nullable=False)
    
    # Pricing Information
    purchase_price: Mapped[Decimal] = Column(Numeric(10, 2))
    rental_price: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    msrp: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    
    # Inventory Management
    reorder_point: Mapped[int] = Column(Integer, default=0)
    reorder_quantity: Mapped[int] = Column(Integer, default=0)
    minimum_stock: Mapped[int] = Column(Integer, default=0)
    
    # Billing Information
    hcpcs_code: Mapped[Optional[str]] = Column(String(20))
    billing_description: Mapped[Optional[str]] = Column(String(255))
    
    # Status
    is_active: Mapped[bool] = Column(Boolean, default=True)
    is_serialized: Mapped[bool] = Column(Boolean, default=False)
    is_rentable: Mapped[bool] = Column(Boolean, default=False)
    requires_maintenance: Mapped[bool] = Column(Boolean, default=False)
    maintenance_interval_days: Mapped[Optional[int]] = Column(Integer)
    
    # Relationships
    category: Mapped[InventoryCategory] = relationship("InventoryCategory", back_populates="items")
    manufacturer: Mapped[Manufacturer] = relationship("Manufacturer", back_populates="items")
    stock_items: Mapped[List["StockItem"]] = relationship("StockItem", back_populates="inventory_item")
    maintenance_schedules: Mapped[List["MaintenanceSchedule"]] = relationship("MaintenanceSchedule", back_populates="inventory_item")

    @hybrid_property
    def total_stock(self) -> int:
        """Total number of items in stock"""
        return sum(1 for item in self.stock_items if item.status == ItemStatus.AVAILABLE)

    @hybrid_property
    def total_in_use(self) -> int:
        """Total number of items currently in use"""
        return sum(1 for item in self.stock_items if item.status == ItemStatus.IN_USE)

class StockItem(Base, TimestampMixin):
    """Stock Item model - migrated from c01.tbl_stock_item"""
    __tablename__ = 'stock_items'

    id: Mapped[int] = Column(Integer, primary_key=True)
    inventory_item_id: Mapped[int] = Column(Integer, ForeignKey('inventory_items.id'), nullable=False)
    
    # Item Information
    serial_number: Mapped[Optional[str]] = Column(String(100), unique=True)
    lot_number: Mapped[Optional[str]] = Column(String(100))
    status: Mapped[ItemStatus] = Column(SQLEnum(ItemStatus), nullable=False, default=ItemStatus.AVAILABLE)
    
    # Location Information
    warehouse_id: Mapped[int] = Column(Integer, ForeignKey('warehouses.id'), nullable=False)
    location_code: Mapped[Optional[str]] = Column(String(50))  # Shelf/Bin location
    
    # Purchase Information
    purchase_date: Mapped[Optional[datetime]] = Column(DateTime)
    purchase_order_number: Mapped[Optional[str]] = Column(String(50))
    purchase_cost: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    
    # Additional Information
    notes: Mapped[Optional[str]] = Column(Text)
    last_maintenance_date: Mapped[Optional[datetime]] = Column(DateTime)
    next_maintenance_date: Mapped[Optional[datetime]] = Column(DateTime)
    
    # Relationships
    inventory_item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="stock_items")
    warehouse: Mapped["Warehouse"] = relationship("Warehouse", back_populates="stock_items")
    maintenance_logs: Mapped[List["MaintenanceLog"]] = relationship("MaintenanceLog", back_populates="stock_item")

class Warehouse(Base, TimestampMixin):
    """Warehouse model - migrated from c01.tbl_warehouse"""
    __tablename__ = 'warehouses'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    code: Mapped[str] = Column(String(20), nullable=False, unique=True)
    
    # Address Information
    address_line1: Mapped[str] = Column(String(255), nullable=False)
    address_line2: Mapped[Optional[str]] = Column(String(255))
    city: Mapped[str] = Column(String(100), nullable=False)
    state: Mapped[str] = Column(String(2), nullable=False)
    zip_code: Mapped[str] = Column(String(10), nullable=False)
    
    # Contact Information
    phone: Mapped[Optional[str]] = Column(String(20))
    email: Mapped[Optional[str]] = Column(String(255))
    manager_name: Mapped[Optional[str]] = Column(String(100))
    
    # Status
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # Relationships
    stock_items: Mapped[List[StockItem]] = relationship("StockItem", back_populates="warehouse")

class MaintenanceSchedule(Base, TimestampMixin):
    """Maintenance Schedule model - migrated from c01.tbl_maintenance_schedule"""
    __tablename__ = 'maintenance_schedules'

    id: Mapped[int] = Column(Integer, primary_key=True)
    inventory_item_id: Mapped[int] = Column(Integer, ForeignKey('inventory_items.id'), nullable=False)
    
    name: Mapped[str] = Column(String(100), nullable=False)
    description: Mapped[Optional[str]] = Column(Text)
    interval_days: Mapped[int] = Column(Integer, nullable=False)
    checklist: Mapped[Optional[str]] = Column(Text)  # JSON string of maintenance checklist
    estimated_duration_minutes: Mapped[int] = Column(Integer, default=60)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    # Relationships
    inventory_item: Mapped[InventoryItem] = relationship("InventoryItem", back_populates="maintenance_schedules")
    maintenance_logs: Mapped[List["MaintenanceLog"]] = relationship("MaintenanceLog", back_populates="maintenance_schedule")

class MaintenanceLog(Base, TimestampMixin):
    """Maintenance Log model - migrated from c01.tbl_maintenance_log"""
    __tablename__ = 'maintenance_logs'

    id: Mapped[int] = Column(Integer, primary_key=True)
    stock_item_id: Mapped[int] = Column(Integer, ForeignKey('stock_items.id'), nullable=False)
    maintenance_schedule_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('maintenance_schedules.id'))
    
    # Maintenance Information
    maintenance_date: Mapped[datetime] = Column(DateTime, nullable=False)
    completed_by: Mapped[str] = Column(String(100), nullable=False)
    duration_minutes: Mapped[int] = Column(Integer)
    
    # Results
    status: Mapped[str] = Column(String(20), nullable=False)  # passed, failed, incomplete
    notes: Mapped[Optional[str]] = Column(Text)
    checklist_results: Mapped[Optional[str]] = Column(Text)  # JSON string of completed checklist
    parts_replaced: Mapped[Optional[str]] = Column(Text)  # JSON string of replaced parts
    
    # Cost Information
    labor_cost: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    parts_cost: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    
    # Relationships
    stock_item: Mapped[StockItem] = relationship("StockItem", back_populates="maintenance_logs")
    maintenance_schedule: Mapped[Optional[MaintenanceSchedule]] = relationship("MaintenanceSchedule", back_populates="maintenance_logs")
