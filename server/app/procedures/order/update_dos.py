"""
Order Date of Service Update Procedure

Python implementation of the order_update_dos stored procedure for
updating dates of service and related quantities in orders.
"""
from datetime import date, datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, and_, update, join
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDetail
from app.procedures.base import BaseProcedure
from app.utils.date import get_new_dos_to
from app.utils.quantity import (
    ordered_qty_to_billed_qty,
    ordered_qty_to_delivery_qty
)


class OrderUpdateDOS(BaseProcedure):
    """
    Updates order dates of service and recalculates quantities.
    
    This procedure:
    1. Updates DOS for unapproved orders
    2. Recalculates billed quantities
    3. Recalculates delivery quantities
    """

    async def _execute(
        self,
        order_id: int,
        dos_from: date
    ) -> Dict[str, Any]:
        """Execute the order DOS update procedure"""
        if not order_id:
            return {
                'success': False,
                'error': 'Order ID required'
            }

        if not dos_from:
            return {
                'success': False,
                'error': 'DOS From date required'
            }

        # Update order details
        updated_count = await self._update_order_details(
            order_id,
            dos_from
        )

        return {
            'success': True,
            'details_updated': updated_count
        }

    async def _update_order_details(
        self,
        order_id: int,
        dos_from: date
    ) -> int:
        """Update order details with new DOS"""
        # Get order details to update
        query = (
            select(OrderDetail)
            .join(Order)
            .where(
                and_(
                    Order.id == order_id,
                    Order.approved == False
                )
            )
        )
        result = await self.db.execute(query)
        details = result.scalars().all()

        updated_count = 0
        for detail in details:
            # Calculate new DOS To
            new_dos_to = get_new_dos_to(
                dos_from,
                detail.dos_from,
                detail.dos_to,
                detail.actual_billed_when
            )

            # Calculate new quantities
            new_billed_qty = ordered_qty_to_billed_qty(
                dos_from,
                new_dos_to,
                detail.ordered_quantity,
                detail.ordered_when,
                detail.billed_when,
                detail.ordered_converter,
                detail.delivery_converter,
                detail.billed_converter
            )

            new_delivery_qty = ordered_qty_to_delivery_qty(
                dos_from,
                new_dos_to,
                detail.ordered_quantity,
                detail.ordered_when,
                detail.billed_when,
                detail.ordered_converter,
                detail.delivery_converter,
                detail.billed_converter
            )

            # Update detail
            detail.dos_from = dos_from
            detail.dos_to = new_dos_to
            detail.billed_quantity = new_billed_qty
            detail.delivery_quantity = new_delivery_qty
            updated_count += 1

        await self.db.flush()
        return updated_count
