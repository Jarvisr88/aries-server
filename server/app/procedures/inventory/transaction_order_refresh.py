"""
Inventory Transaction Order Refresh Procedure

Refreshes inventory transactions based on order status and details.
"""
from datetime import date, datetime
from typing import Dict, Any, List
from sqlalchemy import select, and_, or_, delete, update, func
from sqlalchemy.orm import Session

from app.models.inventory import (
    InventoryTransaction,
    InventoryTransactionType
)
from app.models.order import Order, OrderDetail
from app.procedures.base import BaseProcedure


class InventoryTransactionOrderRefresh(BaseProcedure):
    """
    Refreshes inventory transactions for an order.
    
    This procedure:
    1. Removes invalid transactions
    2. Updates existing transactions
    3. Creates new transactions
    4. Maintains transaction history
    """

    async def _execute(
        self,
        order_id: int
    ) -> Dict[str, Any]:
        """Execute the inventory transaction order refresh procedure"""
        if not order_id:
            return {
                'success': False,
                'error': 'Order ID required'
            }

        # Delete invalid transactions
        await self._delete_invalid_transactions(order_id)

        # Update existing transactions
        await self._update_transactions(order_id)

        # Create new transactions
        await self._create_transactions(order_id)

        return {
            'success': True,
            'order_id': order_id
        }

    async def _delete_invalid_transactions(self, order_id: int) -> None:
        """Delete invalid transactions for order"""
        # Delete orphaned transactions
        delete_stmt = (
            delete(InventoryTransaction)
            .where(
                and_(
                    InventoryTransaction.order_id == order_id,
                    ~InventoryTransaction.order_detail_id.in_(
                        select(OrderDetail.id)
                        .join(Order)
                        .where(
                            and_(
                                OrderDetail.order_id == order_id,
                                OrderDetail.customer_id == Order.customer_id
                            )
                        )
                    )
                )
            )
        )
        await self.db.execute(delete_stmt)

        # Delete transactions with invalid type
        delete_stmt = (
            delete(InventoryTransaction)
            .where(
                and_(
                    InventoryTransaction.order_id == order_id,
                    ~InventoryTransaction.type_id.in_(
                        select(InventoryTransactionType.id)
                        .where(
                            InventoryTransactionType.name.in_([
                                'Committed',
                                'Sold',
                                'Rented',
                                'Rental Returned'
                            ])
                        )
                    )
                )
            )
        )
        await self.db.execute(delete_stmt)

    async def _update_transactions(self, order_id: int) -> None:
        """Update existing transactions for order"""
        update_stmt = (
            update(InventoryTransaction)
            .where(
                and_(
                    InventoryTransaction.order_id == order_id,
                    InventoryTransaction.order_detail_id.in_(
                        select(OrderDetail.id)
                        .join(Order)
                        .where(Order.id == order_id)
                    )
                )
            )
            .values(
                transaction_date=func.coalesce(Order.order_date, func.current_date()),
                quantity=OrderDetail.delivery_quantity,
                description=func.concat('Order #', OrderDetail.order_id),
                cost=0,
                serial_id=None,
                vendor_id=None,
                invoice_id=None,
                manufacturer_id=None,
                last_update_user_id=Order.last_update_user_id
            )
        )
        await self.db.execute(update_stmt)

    async def _create_transactions(self, order_id: int) -> None:
        """Create new transactions for order"""
        # Get order details needing transactions
        query = (
            select(
                OrderDetail.warehouse_id,
                OrderDetail.inventory_item_id,
                OrderDetail.delivery_quantity,
                OrderDetail.customer_id,
                OrderDetail.id.label('order_detail_id'),
                Order.order_date,
                Order.last_update_user_id,
                InventoryTransactionType.id.label('type_id')
            )
            .join(Order)
            .join(
                InventoryTransactionType,
                InventoryTransactionType.name.in_([
                    'Committed',
                    'Sold',
                    'Rented',
                    'Rental Returned'
                ])
            )
            .outerjoin(
                InventoryTransaction,
                and_(
                    InventoryTransaction.warehouse_id == OrderDetail.warehouse_id,
                    InventoryTransaction.inventory_item_id == OrderDetail.inventory_item_id,
                    InventoryTransaction.order_id == OrderDetail.order_id,
                    InventoryTransaction.order_detail_id == OrderDetail.id
                )
            )
            .where(
                and_(
                    OrderDetail.order_id == order_id,
                    InventoryTransaction.id.is_(None)
                )
            )
        )
        result = await self.db.execute(query)

        # Create new transactions
        for row in result:
            transaction = InventoryTransaction(
                warehouse_id=row.warehouse_id,
                inventory_item_id=row.inventory_item_id,
                type_id=row.type_id,
                transaction_date=row.order_date or date.today(),
                quantity=row.delivery_quantity,
                cost=0,
                description=f'Order #{order_id}',
                customer_id=row.customer_id,
                order_id=order_id,
                order_detail_id=row.order_detail_id,
                last_update_user_id=row.last_update_user_id
            )
            self.db.add(transaction)

        await self.db.flush()
