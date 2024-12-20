"""
Recurring Purchase Order Procedure

Python implementation of the process_reoccuring_purchaseorder stored procedure.
"""
from typing import Dict, Any, Optional
from sqlalchemy import select, insert
from sqlalchemy.sql import func
from app.models.inventory import (
    PurchaseOrder,
    PurchaseOrderDetail,
    Vendor
)
from app.procedures.base import BaseProcedure


class ProcessRecurringPurchaseOrder(BaseProcedure):
    """
    Processes recurring purchase orders by creating new orders based on existing ones.
    
    This procedure:
    1. Creates a new purchase order copying header information
    2. Copies all purchase order details
    3. Updates totals and references
    """

    async def _execute(self, purchase_order_id: int) -> Dict[str, Any]:
        """Execute the recurring purchase order process"""
        # Step 1: Create new purchase order
        new_order_id = await self._create_new_purchase_order(purchase_order_id)
        
        if not new_order_id:
            return {'new_order_id': None}

        # Step 2: Copy order details
        await self._copy_purchase_order_details(
            purchase_order_id,
            new_order_id
        )

        # Step 3: Update totals
        await self._update_purchase_order_totals(new_order_id)

        return {'new_order_id': new_order_id}

    async def _create_new_purchase_order(
        self,
        source_order_id: int
    ) -> Optional[int]:
        """Create new purchase order based on source order"""
        # Get source order
        source_order_query = (
            select(PurchaseOrder)
            .where(PurchaseOrder.id == source_order_id)
        )
        source_order = (await self.db.execute(source_order_query)).scalar_one_or_none()

        if not source_order:
            return None

        # Create new order
        new_order = PurchaseOrder(
            approved=source_order.approved,
            recurring=source_order.recurring,
            cost=source_order.cost,
            freight=source_order.freight,
            tax=source_order.tax,
            total_due=source_order.total_due,
            vendor_id=source_order.vendor_id,
            ship_to_name=source_order.ship_to_name,
            ship_to_address1=source_order.ship_to_address1,
            ship_to_address2=source_order.ship_to_address2,
            ship_to_city=source_order.ship_to_city,
            ship_to_state=source_order.ship_to_state,
            ship_to_zip=source_order.ship_to_zip,
            ship_to_phone=source_order.ship_to_phone,
            order_date=func.now(),  # Use current date
            company_name=source_order.company_name,
            company_address1=source_order.company_address1,
            company_address2=source_order.company_address2,
            company_city=source_order.company_city,
            company_state=source_order.company_state,
            company_zip=source_order.company_zip,
            ship_via=source_order.ship_via,
            fob=source_order.fob,
            vendor_sales_rep=source_order.vendor_sales_rep,
            terms=source_order.terms,
            company_phone=source_order.company_phone,
            tax_rate_id=source_order.tax_rate_id,
            created_date=func.now(),
            created_by='system'
        )
        self.db.add(new_order)
        await self.db.flush()
        return new_order.id

    async def _copy_purchase_order_details(
        self,
        source_order_id: int,
        new_order_id: int
    ) -> None:
        """Copy details from source order to new order"""
        # Get source details
        details_query = (
            select(PurchaseOrderDetail)
            .where(PurchaseOrderDetail.purchase_order_id == source_order_id)
        )
        details = (await self.db.execute(details_query)).scalars().all()

        # Create new details
        for detail in details:
            new_detail = PurchaseOrderDetail(
                purchase_order_id=new_order_id,
                inventory_item_id=detail.inventory_item_id,
                warehouse_id=detail.warehouse_id,
                quantity=detail.quantity,
                unit_cost=detail.unit_cost,
                total_cost=detail.total_cost,
                description=detail.description,
                vendor_item_code=detail.vendor_item_code,
                vendor_item_name=detail.vendor_item_name,
                created_date=func.now(),
                created_by='system'
            )
            self.db.add(new_detail)

    async def _update_purchase_order_totals(
        self,
        purchase_order_id: int
    ) -> None:
        """Update purchase order totals based on details"""
        # Calculate totals from details
        totals_query = (
            select(
                func.sum(PurchaseOrderDetail.total_cost).label('total_cost')
            )
            .where(PurchaseOrderDetail.purchase_order_id == purchase_order_id)
        )
        totals = (await self.db.execute(totals_query)).first()

        if not totals:
            return

        # Get current order
        order_query = (
            select(PurchaseOrder)
            .where(PurchaseOrder.id == purchase_order_id)
        )
        order = (await self.db.execute(order_query)).scalar_one()

        # Update totals
        total_cost = totals.total_cost or 0
        tax_amount = total_cost * (order.tax_rate.rate if order.tax_rate else 0)

        update_stmt = (
            update(PurchaseOrder)
            .where(PurchaseOrder.id == purchase_order_id)
            .values(
                cost=total_cost,
                tax=tax_amount,
                total_due=total_cost + tax_amount + (order.freight or 0),
                modified_date=func.now(),
                modified_by='system'
            )
        )
        await self.db.execute(update_stmt)
