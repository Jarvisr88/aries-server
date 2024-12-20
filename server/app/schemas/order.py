"""
Order Processing Domain Schemas
Version: 2024-12-14_17-49
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

from app.models.order import OrderStatus, SaleRentType

class ShippingMethodBase(BaseModel):
    name: str
    description: Optional[str] = None
    carrier: str
    tracking_url_template: Optional[str] = None
    is_active: bool = True

class ShippingMethodCreate(ShippingMethodBase):
    pass

class ShippingMethodUpdate(ShippingMethodBase):
    pass

class ShippingMethodInDB(ShippingMethodBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AuthorizationTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    requires_number: bool = True
    is_active: bool = True

class AuthorizationTypeCreate(AuthorizationTypeBase):
    pass

class AuthorizationTypeUpdate(AuthorizationTypeBase):
    pass

class AuthorizationTypeInDB(AuthorizationTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrderDetailBase(BaseModel):
    inventory_item_id: int
    sale_rent_type: SaleRentType
    serial_number: Optional[str] = None
    quantity: int = Field(gt=0)
    unit_price: Decimal
    billable_price: Decimal
    allowable_price: Optional[Decimal] = None
    billing_code: str
    modifier1: Optional[str] = None
    modifier2: Optional[str] = None
    modifier3: Optional[str] = None
    modifier4: Optional[str] = None
    dos_from: date
    dos_to: Optional[date] = None
    pickup_date: Optional[date] = None
    authorization_number: Optional[str] = None
    authorization_type_id: Optional[int] = None

class OrderDetailCreate(OrderDetailBase):
    pass

class OrderDetailUpdate(OrderDetailBase):
    pass

class OrderDetailInDB(OrderDetailBase):
    id: int
    order_id: int
    is_completed: bool
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrderStatusHistoryBase(BaseModel):
    status: OrderStatus
    notes: Optional[str] = None

class OrderStatusHistoryCreate(OrderStatusHistoryBase):
    pass

class OrderStatusHistoryUpdate(OrderStatusHistoryBase):
    pass

class OrderStatusHistoryInDB(OrderStatusHistoryBase):
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DeliveryScheduleBase(BaseModel):
    scheduled_date: datetime
    delivery_window_start: datetime
    delivery_window_end: datetime
    status: str
    driver_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    actual_delivery_date: Optional[datetime] = None
    signature_required: bool = True
    signature_obtained: bool = False

class DeliveryScheduleCreate(DeliveryScheduleBase):
    pass

class DeliveryScheduleUpdate(DeliveryScheduleBase):
    pass

class DeliveryScheduleInDB(DeliveryScheduleBase):
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    customer_id: int
    order_date: datetime = Field(default_factory=datetime.utcnow)
    status: OrderStatus = OrderStatus.PENDING
    delivery_date: Optional[datetime] = None
    shipping_method_id: Optional[int] = None
    tracking_number: Optional[str] = None
    bill_date: Optional[datetime] = None
    total_amount: Decimal = Decimal('0.00')
    insurance1_id: Optional[int] = None
    insurance2_id: Optional[int] = None
    icd10_codes: List[str] = Field(default_factory=list)
    prescribing_doctor_id: Optional[int] = None
    special_instructions: Optional[str] = None
    internal_notes: Optional[str] = None

class OrderCreate(OrderBase):
    order_details: List[OrderDetailCreate]
    delivery_schedule: Optional[DeliveryScheduleCreate] = None

class OrderUpdate(OrderBase):
    order_details: Optional[List[OrderDetailUpdate]] = None
    delivery_schedule: Optional[DeliveryScheduleUpdate] = None

class OrderInDB(OrderBase):
    id: int
    order_number: str
    created_at: datetime
    updated_at: datetime
    order_details: List[OrderDetailInDB]
    status_history: List[OrderStatusHistoryInDB]
    delivery_schedule: Optional[DeliveryScheduleInDB] = None
    is_completed: bool
    model_config = ConfigDict(from_attributes=True)
