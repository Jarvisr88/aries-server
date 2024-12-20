"""
MIR Update Order Details Procedure

Python implementation of the mir_update_orderdetails stored procedure.
"""
from typing import Optional, List
from sqlalchemy import select, update, and_, or_, func
from app.models.order import Order, OrderDetail
from app.models.inventory import InventoryItem
from app.models.pricing import PriceCodeItem
from app.procedures.base import BaseProcedure


class MirUpdateOrderDetails(BaseProcedure):
    """
    Updates Medical Information Records (MIR) for order details.
    
    This procedure validates and updates MIR fields for:
    - Inventory items
    - Price codes
    - Sale/Rent types
    - Billing dates
    - Modifiers
    - Order quantities
    - Medicare requirements
    """

    async def _execute(self, order_id: Optional[str] = None) -> None:
        """Execute the MIR update procedure"""
        # Determine execution mode based on order_id
        active_only = order_id == 'ActiveOnly'
        specific_order = order_id.isdigit() if order_id else False
        order_id_int = int(order_id) if specific_order else None

        # Build base query
        base_query = (
            select(OrderDetail)
            .join(Order)
        )

        # Apply filters based on execution mode
        if active_only:
            base_query = base_query.where(OrderDetail.state != 'Closed')
        elif specific_order:
            base_query = base_query.where(OrderDetail.order_id == order_id_int)

        # Execute updates
        await self._update_inventory_mir(base_query)
        await self._update_pricing_mir(base_query)
        await self._update_sale_rent_mir(base_query)
        await self._update_billing_mir(base_query)
        await self._update_medicare_mir(base_query)

    async def _update_inventory_mir(self, base_query):
        """Update MIR flags for inventory-related issues"""
        update_stmt = (
            update(OrderDetail)
            .where(OrderDetail.id.in_(base_query.with_only_columns([OrderDetail.id])))
            .values({
                'mir': func.concat_ws(
                    ',',
                    func.nullif(
                        func.case(
                            (InventoryItem.id.is_(None), 'InventoryItemID'),
                            else_=None
                        ),
                        ''
                    )
                )
            })
        )
        await self.db.execute(update_stmt)

    async def _update_pricing_mir(self, base_query):
        """Update MIR flags for pricing-related issues"""
        update_stmt = (
            update(OrderDetail)
            .where(OrderDetail.id.in_(base_query.with_only_columns([OrderDetail.id])))
            .values({
                'mir': func.concat_ws(
                    ',',
                    OrderDetail.mir,  # Keep existing MIR flags
                    func.nullif(
                        func.case(
                            (PriceCodeItem.id.is_(None), 'PriceCodeID'),
                            else_=None
                        ),
                        ''
                    )
                )
            })
        )
        await self.db.execute(update_stmt)

    async def _update_sale_rent_mir(self, base_query):
        """Update MIR flags for sale/rent type issues"""
        update_stmt = (
            update(OrderDetail)
            .where(OrderDetail.id.in_(base_query.with_only_columns([OrderDetail.id])))
            .values({
                'mir': func.concat_ws(
                    ',',
                    OrderDetail.mir,  # Keep existing MIR flags
                    func.nullif(
                        func.case(
                            (
                                and_(
                                    OrderDetail.sale_rent_type == 'Medicare Oxygen Rental',
                                    OrderDetail.is_oxygen != 1
                                ),
                                'SaleRentType'
                            ),
                            else_=None
                        ),
                        ''
                    )
                )
            })
        )
        await self.db.execute(update_stmt)

    async def _update_billing_mir(self, base_query):
        """Update MIR flags for billing-related issues"""
        update_stmt = (
            update(OrderDetail)
            .where(OrderDetail.id.in_(base_query.with_only_columns([OrderDetail.id])))
            .values({
                'mir': func.concat_ws(
                    ',',
                    OrderDetail.mir,  # Keep existing MIR flags
                    func.nullif(
                        func.case(
                            (OrderDetail.actual_bill_item_on == '', 'BillItemOn'),
                            (OrderDetail.actual_billed_when == '', 'BilledWhen'),
                            else_=None
                        ),
                        ''
                    )
                )
            })
        )
        await self.db.execute(update_stmt)

    async def _update_medicare_mir(self, base_query):
        """Update MIR flags for Medicare-specific requirements"""
        update_stmt = (
            update(OrderDetail)
            .where(OrderDetail.id.in_(base_query.with_only_columns([OrderDetail.id])))
            .values({
                'mir': func.concat_ws(
                    ',',
                    OrderDetail.mir,  # Keep existing MIR flags
                    func.nullif(
                        func.case(
                            (
                                and_(
                                    OrderDetail.sale_rent_type.in_(['Capped Rental', 'Parental Capped Rental']),
                                    func.coalesce(OrderDetail.modifier1, '') == ''
                                ),
                                'Modifier1'
                            ),
                            else_=None
                        ),
                        ''
                    )
                )
            })
        )
        await self.db.execute(update_stmt)
