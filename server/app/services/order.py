"""
Order Processing Services
Version: 2024-12-14_19-16

This module implements services for the Order Processing domain.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.service import BaseService
from app.models.order import (
    Order,
    OrderDetail,
    OrderStatusHistory,
    ShippingMethod,
    AuthorizationType,
    DeliverySchedule,
    OrderStatus,
    SaleRentType
)
from app.schemas.order import (
    OrderCreate,
    OrderUpdate,
    OrderDetailCreate,
    OrderDetailUpdate,
    OrderStatusHistoryCreate,
    ShippingMethodCreate,
    ShippingMethodUpdate,
    AuthorizationTypeCreate,
    AuthorizationTypeUpdate,
    DeliveryScheduleCreate,
    DeliveryScheduleUpdate
)
from app.core.logging import logger

class OrderService(BaseService[Order, OrderCreate, OrderUpdate]):
    """Service for managing orders"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Order, db)
    
    async def create(self, schema: OrderCreate, current_user_id: int, **kwargs) -> Order:
        """Create a new order"""
        try:
            # Create order
            data = schema.model_dump(exclude={'order_details', 'delivery_schedule'})
            data.update(kwargs)
            
            # Generate order number
            data['order_number'] = await self._generate_order_number()
            
            db_order = Order(**data)
            self.db.add(db_order)
            await self.db.flush()  # Get order ID
            
            # Create order details
            for detail in schema.order_details:
                detail_data = detail.model_dump()
                detail_data['order_id'] = db_order.id
                db_detail = OrderDetail(**detail_data)
                self.db.add(db_detail)
            
            # Create delivery schedule if provided
            if schema.delivery_schedule:
                schedule_data = schema.delivery_schedule.model_dump()
                schedule_data['order_id'] = db_order.id
                db_schedule = DeliverySchedule(**schedule_data)
                self.db.add(db_schedule)
            
            # Create initial status history
            status_history = OrderStatusHistory(
                order_id=db_order.id,
                status=OrderStatus.PENDING,
                notes="Order created"
            )
            self.db.add(status_history)
            
            await self.db.commit()
            await self.db.refresh(db_order)
            
            logger.info(f"Created new order: {db_order.order_number}")
            return db_order
            
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create order"
            ) from e
    
    async def _generate_order_number(self) -> str:
        """Generate a unique order number"""
        try:
            # Format: ORD-YYYYMMDD-XXXX
            date_part = datetime.utcnow().strftime("%Y%m%d")
            
            # Get the last order number for today
            query = select(Order).where(
                Order.order_number.like(f"ORD-{date_part}-%")
            ).order_by(Order.order_number.desc())
            
            result = await self.db.execute(query)
            last_order = result.scalar_one_or_none()
            
            if last_order:
                last_sequence = int(last_order.order_number.split('-')[-1])
                new_sequence = str(last_sequence + 1).zfill(4)
            else:
                new_sequence = "0001"
            
            return f"ORD-{date_part}-{new_sequence}"
            
        except Exception as e:
            logger.error(f"Error generating order number: {str(e)}")
            raise
    
    async def update_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        notes: Optional[str] = None,
        current_user_id: int = None
    ) -> Order:
        """Update order status"""
        try:
            order = await self.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Update order status
            order.status = new_status
            if new_status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                order.is_completed = True
            
            # Create status history
            status_history = OrderStatusHistory(
                order_id=order.id,
                status=new_status,
                notes=notes
            )
            self.db.add(status_history)
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Updated order status: {order.order_number} -> {new_status}")
            return order
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update order status"
            ) from e
    
    async def get_order_details(self, order_id: int) -> List[OrderDetail]:
        """Get all details for an order"""
        try:
            order = await self.get(order_id)
            return order.order_details
        except Exception as e:
            logger.error(f"Error retrieving order details: {str(e)}")
            return []
    
    async def get_status_history(self, order_id: int) -> List[OrderStatusHistory]:
        """Get status history for an order"""
        try:
            order = await self.get(order_id)
            return order.status_history
        except Exception as e:
            logger.error(f"Error retrieving status history: {str(e)}")
            return []
    
    async def search_orders(
        self,
        customer_id: Optional[int] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Order]:
        """Search orders with filters"""
        try:
            query = select(Order)
            
            # Apply filters
            conditions = []
            if customer_id:
                conditions.append(Order.customer_id == customer_id)
            if status:
                conditions.append(Order.status == status)
            if start_date:
                conditions.append(Order.order_date >= start_date)
            if end_date:
                conditions.append(Order.order_date <= end_date)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(Order.order_date.desc())
            query = query.limit(limit).offset(offset)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching orders: {str(e)}")
            return []

    async def cancel_order(
        self,
        order_id: int,
        reason: str,
        current_user_id: int,
        refund_required: bool = False
    ) -> Order:
        """Cancel an order and optionally initiate refund"""
        try:
            order = await self.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot cancel completed or already cancelled order"
                )
            
            # Update order status
            order = await self.update_status(
                order_id,
                OrderStatus.CANCELLED,
                notes=f"Order cancelled. Reason: {reason}"
            )
            
            # Release reserved inventory
            for detail in order.order_details:
                await self._release_inventory(detail.inventory_item_id, detail.quantity)
            
            # Process refund if required
            if refund_required and order.total_amount > 0:
                await self.process_refund(order_id, reason)
            
            logger.info(f"Cancelled order: {order.order_number}")
            return order
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not cancel order"
            ) from e

    async def apply_discount(
        self,
        order_id: int,
        discount_type: str,
        discount_value: Decimal,
        current_user_id: int
    ) -> Order:
        """Apply a discount to an order"""
        try:
            order = await self.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            if order.status != OrderStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only apply discount to pending orders"
                )
            
            # Calculate discount amount
            if discount_type == "PERCENTAGE":
                if not 0 <= discount_value <= 100:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Percentage discount must be between 0 and 100"
                    )
                discount_amount = (order.subtotal_amount * discount_value) / 100
            else:  # FIXED
                if discount_value > order.subtotal_amount:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Discount amount cannot exceed order subtotal"
                    )
                discount_amount = discount_value
            
            # Apply discount
            order.discount_amount = discount_amount
            order.total_amount = order.subtotal_amount - discount_amount
            
            # Add note to order
            await self.add_note(
                order_id,
                f"Applied {discount_type} discount of {discount_value}"
                f"{' %' if discount_type == 'PERCENTAGE' else ''}"
            )
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Applied discount to order: {order.order_number}")
            return order
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error applying discount: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not apply discount"
            ) from e

    async def calculate_shipping(
        self,
        order_id: int,
        shipping_method_id: int,
        current_user_id: int
    ) -> Decimal:
        """Calculate shipping cost for an order"""
        try:
            order = await self.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Get shipping method
            shipping_method = await self.db.get(ShippingMethod, shipping_method_id)
            if not shipping_method:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Shipping method not found"
                )
            
            # Calculate total weight and volume
            total_weight = Decimal('0')
            total_volume = Decimal('0')
            for detail in order.order_details:
                item = detail.inventory_item
                total_weight += item.weight * detail.quantity
                total_volume += (item.length * item.width * item.height) * detail.quantity
            
            # Calculate base shipping cost
            shipping_cost = shipping_method.base_rate
            
            # Add weight-based cost
            if total_weight > shipping_method.weight_threshold:
                excess_weight = total_weight - shipping_method.weight_threshold
                shipping_cost += (excess_weight * shipping_method.weight_rate)
            
            # Add volume-based cost
            if total_volume > shipping_method.volume_threshold:
                excess_volume = total_volume - shipping_method.volume_threshold
                shipping_cost += (excess_volume * shipping_method.volume_rate)
            
            # Apply shipping zone multiplier
            shipping_cost *= shipping_method.zone_multiplier
            
            # Update order
            order.shipping_method_id = shipping_method_id
            order.shipping_cost = shipping_cost
            order.total_amount = order.subtotal_amount - order.discount_amount + shipping_cost
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Calculated shipping for order: {order.order_number}")
            return shipping_cost
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error calculating shipping: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not calculate shipping"
            ) from e

    async def validate_inventory(
        self,
        order_id: int,
        current_user_id: int
    ) -> bool:
        """Validate inventory availability for an order"""
        try:
            order = await self.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Check each order detail
            for detail in order.order_details:
                # Get available quantity
                query = select(func.sum(StockItem.quantity)).where(
                    and_(
                        StockItem.inventory_item_id == detail.inventory_item_id,
                        StockItem.status == ItemStatus.AVAILABLE
                    )
                )
                result = await self.db.execute(query)
                available_quantity = result.scalar_one_or_none() or 0
                
                if available_quantity < detail.quantity:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient inventory for item {detail.inventory_item_id}"
                    )
            
            logger.info(f"Validated inventory for order: {order.order_number}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating inventory: {str(e)}")
            return False

    async def process_refund(
        self,
        order_id: int,
        reason: str,
        amount: Optional[Decimal] = None,
        current_user_id: int = None
    ) -> None:
        """Process a refund for an order"""
        try:
            order = await self.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            # Determine refund amount
            refund_amount = amount if amount else order.total_amount
            if refund_amount > order.total_amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Refund amount cannot exceed order total"
                )
            
            # Create refund record
            refund = OrderRefund(
                order_id=order_id,
                amount=refund_amount,
                reason=reason,
                processed_by=current_user_id
            )
            self.db.add(refund)
            
            # Update order status
            await self.update_status(
                order_id,
                OrderStatus.REFUNDED,
                notes=f"Refund processed. Amount: {refund_amount}, Reason: {reason}"
            )
            
            await self.db.commit()
            
            logger.info(f"Processed refund for order: {order.order_number}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not process refund"
            ) from e

    async def update_delivery_status(
        self,
        order_id: int,
        delivery_status: str,
        tracking_info: Optional[str] = None,
        delivery_notes: Optional[str] = None,
        current_user_id: int = None
    ) -> Order:
        """Update delivery status for an order"""
        try:
            order = await self.get(order_id)
            if not order:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Order not found"
                )
            
            if not order.delivery_schedule:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Order has no delivery schedule"
                )
            
            # Update delivery schedule
            schedule = order.delivery_schedule
            schedule.status = delivery_status
            if tracking_info:
                schedule.tracking_info = tracking_info
            if delivery_notes:
                schedule.delivery_notes = delivery_notes
            
            # Update order status if delivery is completed
            if delivery_status == "DELIVERED":
                await self.update_status(
                    order_id,
                    OrderStatus.COMPLETED,
                    notes="Order delivered successfully"
                )
            
            await self.db.commit()
            await self.db.refresh(order)
            
            logger.info(f"Updated delivery status for order: {order.order_number}")
            return order
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating delivery status: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not update delivery status"
            ) from e

    async def _release_inventory(self, inventory_item_id: int, quantity: int) -> None:
        """Release reserved inventory"""
        try:
            # Get reserved stock items
            query = select(StockItem).where(
                and_(
                    StockItem.inventory_item_id == inventory_item_id,
                    StockItem.status == ItemStatus.RESERVED
                )
            ).limit(quantity)
            
            result = await self.db.execute(query)
            stock_items = result.scalars().all()
            
            # Release items
            for item in stock_items:
                item.status = ItemStatus.AVAILABLE
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error releasing inventory: {str(e)}")
            await self.db.rollback()
            raise

class ShippingMethodService(BaseService[ShippingMethod, ShippingMethodCreate, ShippingMethodUpdate]):
    """Service for managing shipping methods"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(ShippingMethod, db)
    
    async def create(self, schema: ShippingMethodCreate, current_user_id: int, **kwargs) -> ShippingMethod:
        """Create a new shipping method"""
        try:
            # Check for duplicate name
            query = select(ShippingMethod).where(ShippingMethod.name == schema.name)
            result = await self.db.execute(query)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Shipping method with this name already exists"
                )
            
            # Create shipping method
            data = schema.model_dump()
            data.update(kwargs)
            db_method = ShippingMethod(**data)
            self.db.add(db_method)
            
            await self.db.commit()
            await self.db.refresh(db_method)
            
            logger.info(f"Created new shipping method: {db_method.name}")
            return db_method
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating shipping method: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create shipping method"
            ) from e
    
    async def get_active_methods(self) -> List[ShippingMethod]:
        """Get all active shipping methods"""
        try:
            query = select(ShippingMethod).where(ShippingMethod.is_active == True)
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error retrieving active shipping methods: {str(e)}")
            return []

class DeliveryScheduleService(BaseService[DeliverySchedule, DeliveryScheduleCreate, DeliveryScheduleUpdate]):
    """Service for managing delivery schedules"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(DeliverySchedule, db)
    
    async def create(self, schema: DeliveryScheduleCreate, current_user_id: int, **kwargs) -> DeliverySchedule:
        """Create a new delivery schedule"""
        try:
            # Validate delivery window
            if schema.delivery_window_end <= schema.delivery_window_start:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Delivery window end must be after start time"
                )
            
            # Create delivery schedule
            data = schema.model_dump()
            data.update(kwargs)
            db_schedule = DeliverySchedule(**data)
            self.db.add(db_schedule)
            
            await self.db.commit()
            await self.db.refresh(db_schedule)
            
            logger.info(f"Created new delivery schedule for order: {db_schedule.order_id}")
            return db_schedule
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating delivery schedule: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not create delivery schedule"
            ) from e
    
    async def complete_delivery(
        self,
        schedule_id: int,
        signature: Optional[str] = None,
        delivery_notes: Optional[str] = None,
        current_user_id: int = None
    ) -> DeliverySchedule:
        """Mark a delivery as completed"""
        try:
            schedule = await self.get(schedule_id)
            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Delivery schedule not found"
                )
            
            # Update schedule
            schedule.status = "COMPLETED"
            schedule.actual_delivery_date = datetime.utcnow()
            if signature:
                schedule.signature_obtained = True
            if delivery_notes:
                schedule.driver_notes = delivery_notes
            
            await self.db.commit()
            await self.db.refresh(schedule)
            
            logger.info(f"Completed delivery for order: {schedule.order_id}")
            return schedule
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing delivery: {str(e)}")
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not complete delivery"
            ) from e
    
    async def get_daily_schedule(
        self,
        date: datetime,
        driver_id: Optional[int] = None
    ) -> List[DeliverySchedule]:
        """Get delivery schedule for a specific date"""
        try:
            query = select(DeliverySchedule).where(
                and_(
                    DeliverySchedule.scheduled_date >= date.replace(hour=0, minute=0),
                    DeliverySchedule.scheduled_date < date.replace(hour=23, minute=59),
                    DeliverySchedule.status != "COMPLETED"
                )
            )
            
            if driver_id:
                query = query.where(DeliverySchedule.driver_id == driver_id)
            
            query = query.order_by(DeliverySchedule.delivery_window_start)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error retrieving daily schedule: {str(e)}")
            return []
