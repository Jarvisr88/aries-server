"""
Order Processing Domain Models
Version: 2024-12-14_17-49
"""
from datetime import date, datetime
from typing import Optional, List
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Table, Boolean, Numeric, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.ext.hybrid import hybrid_property

from app.models.system import TimestampMixin
from app.models.customer import Customer
from app.core.database import Base

class OrderStatus(str, Enum):
    PENDING = 'pending'
    APPROVED = 'approved'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    ON_HOLD = 'on_hold'

class SaleRentType(str, Enum):
    SALE = 'sale'
    RENTAL = 'rental'
    RECURRING = 'recurring'

class Order(Base, TimestampMixin):
    """Order model - migrated from c01.tbl_order"""
    __tablename__ = 'orders'

    id: Mapped[int] = Column(Integer, primary_key=True)
    customer_id: Mapped[int] = Column(Integer, ForeignKey('customers.id'), nullable=False)
    
    # Order Information
    order_number: Mapped[str] = Column(String(50), unique=True, nullable=False)
    order_date: Mapped[datetime] = Column(DateTime, nullable=False, default=datetime.utcnow)
    status: Mapped[OrderStatus] = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    
    # Delivery Information
    delivery_date: Mapped[Optional[datetime]] = Column(DateTime)
    shipping_method_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('shipping_methods.id'))
    tracking_number: Mapped[Optional[str]] = Column(String(100))
    
    # Billing Information
    bill_date: Mapped[Optional[datetime]] = Column(DateTime)
    total_amount: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False, default=0)
    insurance1_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('customer_insurances.id'))
    insurance2_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('customer_insurances.id'))
    
    # Medical Information
    icd10_codes: Mapped[List[str]] = Column(String(500))  # Comma-separated ICD-10 codes
    prescribing_doctor_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('doctors.id'))
    
    # Additional Information
    special_instructions: Mapped[Optional[str]] = Column(Text)
    internal_notes: Mapped[Optional[str]] = Column(Text)
    
    # Relationships
    customer: Mapped[Customer] = relationship("Customer", back_populates="orders")
    shipping_method: Mapped["ShippingMethod"] = relationship("ShippingMethod")
    prescribing_doctor = relationship("Doctor")
    order_details: Mapped[List["OrderDetail"]] = relationship("OrderDetail", back_populates="order")
    status_history: Mapped[List["OrderStatusHistory"]] = relationship("OrderStatusHistory", back_populates="order")
    
    @hybrid_property
    def is_completed(self) -> bool:
        return self.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]

class OrderDetail(Base, TimestampMixin):
    """Order Detail model - migrated from c01.tbl_orderdetails"""
    __tablename__ = 'order_details'

    id: Mapped[int] = Column(Integer, primary_key=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey('orders.id'), nullable=False)
    inventory_item_id: Mapped[int] = Column(Integer, ForeignKey('inventory_items.id'), nullable=False)
    
    # Item Information
    sale_rent_type: Mapped[SaleRentType] = Column(SQLEnum(SaleRentType), nullable=False)
    serial_number: Mapped[Optional[str]] = Column(String(50))
    quantity: Mapped[int] = Column(Integer, nullable=False)
    
    # Pricing Information
    unit_price: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    billable_price: Mapped[Decimal] = Column(Numeric(10, 2), nullable=False)
    allowable_price: Mapped[Optional[Decimal]] = Column(Numeric(10, 2))
    
    # Billing Information
    billing_code: Mapped[str] = Column(String(20), nullable=False)
    modifier1: Mapped[Optional[str]] = Column(String(2))
    modifier2: Mapped[Optional[str]] = Column(String(2))
    modifier3: Mapped[Optional[str]] = Column(String(2))
    modifier4: Mapped[Optional[str]] = Column(String(2))
    
    # Dates
    dos_from: Mapped[date] = Column(Date, nullable=False)  # Date of Service From
    dos_to: Mapped[Optional[date]] = Column(Date)  # Date of Service To
    pickup_date: Mapped[Optional[date]] = Column(Date)
    
    # Authorization
    authorization_number: Mapped[Optional[str]] = Column(String(50))
    authorization_type_id: Mapped[Optional[int]] = Column(Integer, ForeignKey('authorization_types.id'))
    
    # Status
    is_completed: Mapped[bool] = Column(Boolean, default=False)
    is_cancelled: Mapped[bool] = Column(Boolean, default=False)
    
    # Relationships
    order: Mapped[Order] = relationship("Order", back_populates="order_details")
    inventory_item = relationship("InventoryItem")  # Will be defined in Inventory domain
    authorization_type: Mapped["AuthorizationType"] = relationship("AuthorizationType")

class OrderStatusHistory(Base, TimestampMixin):
    """Order Status History model - migrated from c01.tbl_order_status_history"""
    __tablename__ = 'order_status_history'

    id: Mapped[int] = Column(Integer, primary_key=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey('orders.id'), nullable=False)
    status: Mapped[OrderStatus] = Column(SQLEnum(OrderStatus), nullable=False)
    notes: Mapped[Optional[str]] = Column(Text)
    
    order: Mapped[Order] = relationship("Order", back_populates="status_history")

class ShippingMethod(Base, TimestampMixin):
    """Shipping Method model - migrated from c01.tbl_shipping_method"""
    __tablename__ = 'shipping_methods'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(50), nullable=False)
    description: Mapped[Optional[str]] = Column(String(255))
    carrier: Mapped[str] = Column(String(50), nullable=False)
    is_active: Mapped[bool] = Column(Boolean, default=True)
    
    tracking_url_template: Mapped[Optional[str]] = Column(String(255))  # Template for tracking URLs

class AuthorizationType(Base, TimestampMixin):
    """Authorization Type model - migrated from c01.tbl_authorization_type"""
    __tablename__ = 'authorization_types'

    id: Mapped[int] = Column(Integer, primary_key=True)
    name: Mapped[str] = Column(String(50), nullable=False)
    description: Mapped[Optional[str]] = Column(String(255))
    requires_number: Mapped[bool] = Column(Boolean, default=True)
    is_active: Mapped[bool] = Column(Boolean, default=True)

class DeliverySchedule(Base, TimestampMixin):
    """Delivery Schedule model - migrated from c01.tbl_delivery_schedule"""
    __tablename__ = 'delivery_schedules'

    id: Mapped[int] = Column(Integer, primary_key=True)
    order_id: Mapped[int] = Column(Integer, ForeignKey('orders.id'), nullable=False)
    scheduled_date: Mapped[datetime] = Column(DateTime, nullable=False)
    delivery_window_start: Mapped[datetime] = Column(DateTime, nullable=False)
    delivery_window_end: Mapped[datetime] = Column(DateTime, nullable=False)
    
    status: Mapped[str] = Column(String(20), nullable=False)
    driver_notes: Mapped[Optional[str]] = Column(Text)
    customer_notes: Mapped[Optional[str]] = Column(Text)
    
    actual_delivery_date: Mapped[Optional[datetime]] = Column(DateTime)
    signature_required: Mapped[bool] = Column(Boolean, default=True)
    signature_obtained: Mapped[bool] = Column(Boolean, default=False)
    
    order: Mapped[Order] = relationship("Order")
