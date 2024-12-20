"""
Inventory Purchase Order Refresh Procedure

Python implementation of the inventory_po_refresh stored procedure for
refreshing inventory quantities based on purchase order details.
"""
from typing import Dict, Any, List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.purchase_order import PurchaseOrderDetail
from app.procedures.base import BaseProcedure
from app.procedures.inventory.refresh import InventoryRefresh


class InventoryPORefresh(BaseProcedure):
    """
    Refreshes inventory quantities for all items in a purchase order.
    
    This procedure:
    1. Gets all inventory items from purchase order
    2. Refreshes quantities for each item
    3. Updates inventory status
    """

    async def _execute(
        self,
        purchase_order_id: int
    ) -> Dict[str, Any]:
        """Execute the inventory PO refresh procedure"""
        if not purchase_order_id:
            return {
                'success': False,
                'error': 'Purchase Order ID required'
            }

        # Get PO details
        items = await self._get_po_items(purchase_order_id)
        if not items:
            return {
                'success': False,
                'error': f'No items found for PO {purchase_order_id}'
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

    async def _get_po_items(
        self,
        purchase_order_id: int
    ) -> List[Tuple[int, int]]:
        """Get unique warehouse/item combinations from purchase order"""
        query = (
            select(
                PurchaseOrderDetail.warehouse_id,
                PurchaseOrderDetail.inventory_item_id
            )
            .where(PurchaseOrderDetail.purchase_order_id == purchase_order_id)
            .distinct()
        )
        result = await self.db.execute(query)
        return result.all()
