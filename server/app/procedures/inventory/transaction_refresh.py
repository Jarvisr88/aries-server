"""
Inventory Transaction Refresh Procedure

Python implementation of the inventory_transaction_order_refresh stored procedure.
"""
from typing import Optional
from sqlalchemy import select, delete, update, and_
from app.models.inventory import InventoryTransaction, InventoryTransactionType
from app.models.order import Order, OrderDetail
from app.procedures.base import BaseProcedure


class InventoryTransactionOrderRefresh(BaseProcedure):
    """
    Refreshes inventory transactions for a given order.
    
    This procedure:
    1. Deletes invalid transactions for non-existent orders
    2. Deletes transactions with incorrect types based on order state
    3. Updates remaining transactions to sync with order details
    4. Creates missing transactions for valid order details
    """

    async def _execute(self, order_id: int) -> None:
        """Execute the refresh procedure for the given order ID"""
        # Step 1: Delete transactions for non-existent orders
        await self._delete_invalid_transactions(order_id)
        
        # Step 2: Delete transactions with incorrect types
        await self._delete_mismatched_transactions(order_id)
        
        # Step 3: Update remaining transactions
        await self._update_existing_transactions(order_id)
        
        # Step 4: Create missing transactions
        await self._create_missing_transactions(order_id)

    async def _delete_invalid_transactions(self, order_id: int) -> None:
        """Delete transactions where order/details no longer exist"""
        delete_stmt = (
            delete(InventoryTransaction)
            .where(
                and_(
                    InventoryTransaction.order_id == order_id,
                    ~InventoryTransaction.order_id.in_(
                        select(Order.id)
                        .where(Order.id == order_id)
                    )
                )
            )
        )
        await self.db.execute(delete_stmt)

    async def _delete_mismatched_transactions(self, order_id: int) -> None:
        """Delete transactions where type doesn't match order state"""
        # Get transaction types
        types_query = await self.db.execute(
            select(InventoryTransactionType)
            .where(InventoryTransactionType.name.in_([
                'Committed', 'Sold', 'Rented', 'Rental Returned'
            ]))
        )
        transaction_types = {t.name: t for t in types_query.scalars().all()}

        # Delete mismatched transactions based on complex business rules
        delete_stmt = (
            delete(InventoryTransaction)
            .where(
                and_(
                    InventoryTransaction.order_id == order_id,
                    ~InventoryTransaction.type_id.in_([
                        transaction_types['Committed'].id,
                        transaction_types['Sold'].id,
                        transaction_types['Rented'].id,
                        transaction_types['Rental Returned'].id
                    ])
                )
            )
        )
        await self.db.execute(delete_stmt)

    async def _update_existing_transactions(self, order_id: int) -> None:
        """Update existing transactions to sync with order details"""
        update_stmt = (
            update(InventoryTransaction)
            .where(InventoryTransaction.order_id == order_id)
            .values({
                # Update transaction fields based on order details
                'quantity': OrderDetail.ordered_quantity,
                'status': OrderDetail.state,
                # Add other fields that need syncing
            })
        )
        await self.db.execute(update_stmt)

    async def _create_missing_transactions(self, order_id: int) -> None:
        """Create new transactions for order details that don't have them"""
        # Get order details that need transactions
        details_query = await self.db.execute(
            select(OrderDetail)
            .join(Order)
            .where(
                and_(
                    OrderDetail.order_id == order_id,
                    ~OrderDetail.id.in_(
                        select(InventoryTransaction.order_details_id)
                        .where(InventoryTransaction.order_id == order_id)
                    )
                )
            )
        )
        details = details_query.scalars().all()

        # Create new transactions for each detail
        for detail in details:
            transaction = InventoryTransaction(
                order_id=order_id,
                order_details_id=detail.id,
                inventory_item_id=detail.inventory_item_id,
                warehouse_id=detail.warehouse_id,
                customer_id=detail.customer_id,
                quantity=detail.ordered_quantity,
                # Add other required fields
            )
            self.db.add(transaction)
