"""
Inventory Adjustment Procedure

Python implementation of the inventory_adjust_2 stored procedure for
adjusting inventory quantities and costs.
"""
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import select, update, and_
from sqlalchemy.orm import Session

from app.models.inventory import (
    Inventory,
    InventoryTransaction,
    InventoryTransactionType
)
from app.procedures.base import BaseProcedure
from app.procedures.inventory.refresh import InventoryRefresh


class InventoryAdjustment(BaseProcedure):
    """
    Adjusts inventory quantities and costs for a specific item in a warehouse.
    
    This procedure:
    1. Refreshes current inventory status
    2. Calculates deltas for each quantity type
    3. Creates adjustment transactions
    4. Updates inventory records
    """

    async def _execute(
        self,
        warehouse_id: int,
        inventory_item_id: int,
        last_update_user_id: int,
        on_hand: Optional[int] = None,
        rented: Optional[int] = None,
        sold: Optional[int] = None,
        unavailable: Optional[int] = None,
        committed: Optional[int] = None,
        on_order: Optional[int] = None,
        back_ordered: Optional[int] = None,
        reorder_point: Optional[int] = None,
        cost_per_unit: Optional[Decimal] = None,
    ) -> Dict[str, Any]:
        """Execute the inventory adjustment procedure"""
        if not warehouse_id or not inventory_item_id:
            return {
                'success': False,
                'error': 'Warehouse ID and Inventory Item ID required'
            }

        # Refresh inventory first
        refresh_proc = InventoryRefresh(self.db)
        await refresh_proc.execute(warehouse_id, inventory_item_id)

        # Get current inventory record
        current = await self._get_current_inventory(warehouse_id, inventory_item_id)
        if not current:
            # Initialize with zeros if no record exists
            current = {
                'on_hand': 0,
                'rented': 0,
                'sold': 0,
                'unavailable': 0,
                'committed': 0,
                'on_order': 0,
                'back_ordered': 0,
                'cost_per_unit': Decimal('0.00')
            }

        # Calculate deltas
        deltas = self._calculate_deltas(
            current=current,
            on_hand=on_hand,
            rented=rented,
            sold=sold,
            unavailable=unavailable,
            committed=committed,
            on_order=on_order,
            back_ordered=back_ordered
        )

        # Create adjustment transactions
        await self._create_adjustment_transactions(
            warehouse_id=warehouse_id,
            inventory_item_id=inventory_item_id,
            deltas=deltas,
            cost_per_unit=cost_per_unit,
            last_update_user_id=last_update_user_id
        )

        # Update inventory record
        await self._update_inventory(
            warehouse_id=warehouse_id,
            inventory_item_id=inventory_item_id,
            deltas=deltas,
            reorder_point=reorder_point,
            cost_per_unit=cost_per_unit,
            last_update_user_id=last_update_user_id
        )

        return {'success': True, 'deltas': deltas}

    async def _get_current_inventory(
        self,
        warehouse_id: int,
        inventory_item_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get current inventory record"""
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
            return None

        return {
            'on_hand': inventory.on_hand,
            'rented': inventory.rented,
            'sold': inventory.sold,
            'unavailable': inventory.unavailable,
            'committed': inventory.committed,
            'on_order': inventory.on_order,
            'back_ordered': inventory.back_ordered,
            'cost_per_unit': inventory.cost_per_unit
        }

    def _calculate_deltas(
        self,
        current: Dict[str, Any],
        on_hand: Optional[int],
        rented: Optional[int],
        sold: Optional[int],
        unavailable: Optional[int],
        committed: Optional[int],
        on_order: Optional[int],
        back_ordered: Optional[int]
    ) -> Dict[str, Optional[int]]:
        """Calculate deltas between current and new values"""
        def calc_delta(new_val: Optional[int], current_val: int) -> Optional[int]:
            return new_val - current_val if new_val is not None and new_val >= 0 else None

        return {
            'on_hand': calc_delta(on_hand, current['on_hand']),
            'rented': calc_delta(rented, current['rented']),
            'sold': calc_delta(sold, current['sold']),
            'unavailable': calc_delta(unavailable, current['unavailable']),
            'committed': calc_delta(committed, current['committed']),
            'on_order': calc_delta(on_order, current['on_order']),
            'back_ordered': calc_delta(back_ordered, current['back_ordered'])
        }

    async def _create_adjustment_transactions(
        self,
        warehouse_id: int,
        inventory_item_id: int,
        deltas: Dict[str, Optional[int]],
        cost_per_unit: Optional[Decimal],
        last_update_user_id: int
    ) -> None:
        """Create inventory adjustment transactions"""
        # Map delta types to transaction types
        type_mapping = {
            'on_hand': 'Adjustment - On Hand',
            'rented': 'Adjustment - Rented',
            'sold': 'Adjustment - Sold',
            'unavailable': 'Adjustment - Unavailable',
            'committed': 'Adjustment - Committed',
            'on_order': 'Adjustment - On Order',
            'back_ordered': 'Adjustment - Back Ordered'
        }

        for delta_type, delta in deltas.items():
            if delta is not None and delta != 0:
                # Get transaction type
                tran_type_query = (
                    select(InventoryTransactionType)
                    .where(InventoryTransactionType.name == type_mapping[delta_type])
                )
                tran_type = (await self.db.execute(tran_type_query)).scalar_one()

                # Create transaction
                transaction = InventoryTransaction(
                    warehouse_id=warehouse_id,
                    inventory_item_id=inventory_item_id,
                    transaction_type_id=tran_type.id,
                    quantity=delta,
                    unit_cost=cost_per_unit,
                    created_by=last_update_user_id,
                    modified_by=last_update_user_id
                )
                self.db.add(transaction)

    async def _update_inventory(
        self,
        warehouse_id: int,
        inventory_item_id: int,
        deltas: Dict[str, Optional[int]],
        reorder_point: Optional[int],
        cost_per_unit: Optional[Decimal],
        last_update_user_id: int
    ) -> None:
        """Update inventory record with new values"""
        # Build update values
        update_values = {
            'modified_by': last_update_user_id,
            'modified_date': func.now()
        }

        # Add quantity updates
        for field, delta in deltas.items():
            if delta is not None:
                update_values[field] = Inventory.__table__.c[field] + delta

        # Add optional updates
        if reorder_point is not None and reorder_point >= 0:
            update_values['reorder_point'] = reorder_point
        if cost_per_unit is not None:
            update_values['cost_per_unit'] = cost_per_unit

        # Update inventory record
        update_stmt = (
            update(Inventory)
            .where(
                and_(
                    Inventory.warehouse_id == warehouse_id,
                    Inventory.inventory_item_id == inventory_item_id
                )
            )
            .values(**update_values)
        )
        await self.db.execute(update_stmt)
