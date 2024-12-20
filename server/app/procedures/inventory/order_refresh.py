"""
Inventory Order Refresh Procedure

Python implementation of the inventory_order_refresh stored procedure for
refreshing inventory quantities based on order details.
"""
from typing import Dict, Any, List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import OrderDetail
from app.procedures.base import BaseProcedure
from app.procedures.inventory.refresh import InventoryRefresh


class InventoryOrderRefresh(BaseProcedure):
    """
    Refreshes inventory quantities for all items in an order.
    
    This procedure:
    1. Gets all inventory items from order
    2. Refreshes quantities for each item
    3. Updates inventory status
    """

    async def _execute(
        self,
        order_id: int
    ) -> Dict[str, Any]:
        """Execute the inventory order refresh procedure"""
        if not order_id:
            return {
                'success': False,
                'error': 'Order ID required'
            }

        # Get order details
        items = await self._get_order_items(order_id)
        if not items:
            return {
                'success': False,
                'error': f'No items found for order {order_id}'
            }

        # Refresh each item
        refresh_count = 0
        refresh_proc = InventoryRefresh(self.db)
        
        for warehouse_id, inventory_item_id in items:
            result = await refresh_proc.execute(
                warehouse_id=warehouse_id,
                inventory_item_id=inventory_item_id
            )
            if result.get('success'):
                refresh_count += 1

        return {
            'success': True,
            'items_refreshed': refresh_count
        }

    async def _get_order_items(
        self,
        order_id: int
    ) -> List[Tuple[int, int]]:
        """Get unique warehouse/item combinations from order"""
        query = (
            select(
                OrderDetail.warehouse_id,
                OrderDetail.inventory_item_id
            )
            .where(OrderDetail.order_id == order_id)
            .distinct()
        )
        result = await self.db.execute(query)
        return result.all()
