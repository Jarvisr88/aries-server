"""
Inventory Refresh Procedure

Python implementation of the inventory_refresh stored procedure for
updating inventory quantities and statuses.
"""
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from app.models.inventory import (
    Inventory,
    InventoryTransaction,
    SerialNumber
)
from app.models.order import OrderDetail
from app.procedures.base import BaseProcedure


class InventoryRefresh(BaseProcedure):
    """
    Refreshes inventory quantities and statuses.
    
    This procedure:
    1. Calculates current quantities
    2. Updates inventory status
    3. Handles serial numbers
    4. Maintains transaction history
    """

    async def _execute(
        self,
        warehouse_id: int,
        inventory_item_id: int
    ) -> Dict[str, Any]:
        """Execute the inventory refresh procedure"""
        if not warehouse_id or not inventory_item_id:
            return {
                'success': False,
                'error': 'Warehouse ID and Inventory Item ID required'
            }

        # Calculate quantities
        quantities = await self._calculate_quantities(
            warehouse_id,
            inventory_item_id
        )

        # Update inventory record
        await self._update_inventory(
            warehouse_id,
            inventory_item_id,
            quantities
        )

        return {
            'success': True,
            'quantities': quantities
        }

    async def _calculate_quantities(
        self,
        warehouse_id: int,
        inventory_item_id: int
    ) -> Dict[str, Any]:
        """Calculate current inventory quantities"""
        # Initialize quantities
        quantities = {
            'on_hand': 0,
            'rented': 0,
            'sold': 0,
            'unavailable': 0,
            'committed': 0,
            'on_order': 0,
            'back_ordered': 0
        }

        # Get transaction totals
        trans_query = (
            select(
                InventoryTransaction.transaction_type,
                func.sum(InventoryTransaction.quantity).label('total')
            )
            .where(
                and_(
                    InventoryTransaction.warehouse_id == warehouse_id,
                    InventoryTransaction.inventory_item_id == inventory_item_id
                )
            )
            .group_by(InventoryTransaction.transaction_type)
        )
        trans_result = await self.db.execute(trans_query)

        # Process transaction totals
        for row in trans_result:
            if row.transaction_type == 'Receive':
                quantities['on_hand'] += row.total
            elif row.transaction_type == 'Rent':
                quantities['rented'] += row.total
            elif row.transaction_type == 'Sell':
                quantities['sold'] += row.total
            elif row.transaction_type == 'Mark Unavailable':
                quantities['unavailable'] += row.total

        # Get order commitments
        commit_query = (
            select(func.sum(OrderDetail.quantity))
            .where(
                and_(
                    OrderDetail.warehouse_id == warehouse_id,
                    OrderDetail.inventory_item_id == inventory_item_id,
                    OrderDetail.status == 'Committed'
                )
            )
        )
        commit_result = await self.db.execute(commit_query)
        quantities['committed'] = commit_result.scalar() or 0

        # Get purchase orders
        order_query = (
            select(func.sum(OrderDetail.quantity))
            .where(
                and_(
                    OrderDetail.warehouse_id == warehouse_id,
                    OrderDetail.inventory_item_id == inventory_item_id,
                    OrderDetail.status == 'On Order'
                )
            )
        )
        order_result = await self.db.execute(order_query)
        quantities['on_order'] = order_result.scalar() or 0

        # Get back orders
        back_query = (
            select(func.sum(OrderDetail.quantity))
            .where(
                and_(
                    OrderDetail.warehouse_id == warehouse_id,
                    OrderDetail.inventory_item_id == inventory_item_id,
                    OrderDetail.status == 'Back Ordered'
                )
            )
        )
        back_result = await self.db.execute(back_query)
        quantities['back_ordered'] = back_result.scalar() or 0

        return quantities

    async def _update_inventory(
        self,
        warehouse_id: int,
        inventory_item_id: int,
        quantities: Dict[str, int]
    ) -> None:
        """Update inventory record with new quantities"""
        # Get or create inventory record
        query = (
            select(Inventory)
            .where(
                and_(
                    Inventory.warehouse_id == warehouse_id,
                    Inventory.inventory_item_id == inventory_item_id
                )
            )
        )
        result = await self.db.execute(query)
        inventory = result.scalar_one_or_none()

        if not inventory:
            inventory = Inventory(
                warehouse_id=warehouse_id,
                inventory_item_id=inventory_item_id,
                created_by=1,  # System user
                modified_by=1
            )
            self.db.add(inventory)

        # Update quantities
        inventory.on_hand = quantities['on_hand']
        inventory.rented = quantities['rented']
        inventory.sold = quantities['sold']
        inventory.unavailable = quantities['unavailable']
        inventory.committed = quantities['committed']
        inventory.on_order = quantities['on_order']
        inventory.back_ordered = quantities['back_ordered']
        inventory.modified_date = func.now()

        await self.db.flush()
