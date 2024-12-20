"""
Recurring Order Processing Procedure

Python implementation of the process_reoccuring_order stored procedure.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import select, insert, update, and_
from sqlalchemy.sql import func
from app.models.order import Order, OrderDetail
from app.models.customer import Customer
from app.models.inventory import InventoryItem
from app.procedures.base import BaseProcedure


class ProcessRecurringOrder(BaseProcedure):
    """
    Processes recurring orders by creating new orders based on existing ones.
    
    This procedure:
    1. Identifies eligible recurring sales items
    2. Creates a new order with copied details from source
    3. Updates source items to prevent future recurrence
    """

    async def _execute(
        self,
        order_id: int,
        billed_when: str,
        bill_item_on: str
    ) -> Dict[str, Any]:
        """Execute the recurring order process"""
        # Step 1: Get count and new order date for eligible items
        details_info = await self._get_recurring_details_info(
            order_id, billed_when, bill_item_on
        )
        
        if not details_info['count']:
            return {'new_order_id': None}

        # Step 2: Create new order
        new_order_id = await self._create_new_order(
            order_id, details_info['new_order_date']
        )

        # Step 3: Copy order details
        await self._copy_order_details(
            order_id, new_order_id, billed_when, bill_item_on
        )

        # Step 4: Update source items
        await self._update_source_items(
            order_id, billed_when, bill_item_on
        )

        return {'new_order_id': new_order_id}

    async def _get_recurring_details_info(
        self,
        order_id: int,
        billed_when: str,
        bill_item_on: str
    ) -> Dict[str, Any]:
        """Get information about recurring details"""
        query = (
            select(
                func.count().label('count'),
                func.max(
                    func.case(
                        (
                            OrderDetail.billing_month <= 1,
                            # TODO: Implement GetNextDosFrom function
                            func.get_next_dos_from(
                                OrderDetail.dos_from,
                                OrderDetail.dos_to,
                                OrderDetail.actual_billed_when
                            )
                        ),
                        else_=OrderDetail.dos_from
                    )
                ).label('new_order_date')
            )
            .select_from(OrderDetail)
            .join(Order)
            .where(
                and_(
                    OrderDetail.order_id == order_id,
                    OrderDetail.billed_when == billed_when,
                    OrderDetail.billed_when != 'One Time',
                    OrderDetail.actual_bill_item_on == bill_item_on,
                    OrderDetail.sale_rent_type == 'Re-occurring Sale'
                )
            )
        )
        result = await self.db.execute(query)
        row = result.fetchone()
        return {
            'count': row.count,
            'new_order_date': row.new_order_date
        }

    async def _create_new_order(
        self,
        source_order_id: int,
        new_order_date: datetime
    ) -> int:
        """Create new order based on source order"""
        # Get source order
        source_order_query = (
            select(Order)
            .where(Order.id == source_order_id)
        )
        source_order = (await self.db.execute(source_order_query)).scalar_one()

        # Create new order
        new_order = Order(
            customer_id=source_order.customer_id,
            approved=source_order.approved,
            order_date=new_order_date,
            delivery_date=new_order_date,  # May need adjustment
            bill_date=new_order_date,      # May need adjustment
            taken_by=source_order.taken_by,
            shipping_method_id=source_order.shipping_method_id,
            special_instructions=source_order.special_instructions,
            customer_insurance1_id=source_order.customer_insurance1_id,
            customer_insurance2_id=source_order.customer_insurance2_id,
            customer_insurance3_id=source_order.customer_insurance3_id,
            customer_insurance4_id=source_order.customer_insurance4_id,
            icd9_1=source_order.icd9_1,
            icd9_2=source_order.icd9_2,
            icd9_3=source_order.icd9_3,
            icd9_4=source_order.icd9_4,
            icd10_01=source_order.icd10_01,
            icd10_02=source_order.icd10_02,
            icd10_03=source_order.icd10_03,
            icd10_04=source_order.icd10_04,
            icd10_05=source_order.icd10_05,
            icd10_06=source_order.icd10_06,
            icd10_07=source_order.icd10_07,
            icd10_08=source_order.icd10_08
        )
        self.db.add(new_order)
        await self.db.flush()
        return new_order.id

    async def _copy_order_details(
        self,
        source_order_id: int,
        new_order_id: int,
        billed_when: str,
        bill_item_on: str
    ) -> None:
        """Copy eligible details to new order"""
        # Get source details
        details_query = (
            select(OrderDetail)
            .where(
                and_(
                    OrderDetail.order_id == source_order_id,
                    OrderDetail.billed_when == billed_when,
                    OrderDetail.billed_when != 'One Time',
                    OrderDetail.actual_bill_item_on == bill_item_on,
                    OrderDetail.sale_rent_type == 'Re-occurring Sale'
                )
            )
        )
        details = (await self.db.execute(details_query)).scalars().all()

        # Create new details
        for detail in details:
            new_detail = OrderDetail(
                order_id=new_order_id,
                customer_id=detail.customer_id,
                inventory_item_id=detail.inventory_item_id,
                warehouse_id=detail.warehouse_id,
                price_code_id=detail.price_code_id,
                ordered_quantity=detail.ordered_quantity,
                ordered_units=detail.ordered_units,
                ordered_converter=detail.ordered_converter,
                sale_rent_type=detail.sale_rent_type,
                billed_when=detail.billed_when,
                bill_item_on=detail.bill_item_on,
                reoccuring_id=detail.id  # Link to source detail
            )
            self.db.add(new_detail)

    async def _update_source_items(
        self,
        order_id: int,
        billed_when: str,
        bill_item_on: str
    ) -> None:
        """Update source items to prevent future recurrence"""
        update_stmt = (
            update(OrderDetail)
            .where(
                and_(
                    OrderDetail.order_id == order_id,
                    OrderDetail.billed_when == billed_when,
                    OrderDetail.actual_bill_item_on == bill_item_on,
                    OrderDetail.sale_rent_type == 'Re-occurring Sale'
                )
            )
            .values(
                billed_when='One Time',  # Prevent future recurrence
                modified_date=func.now(),
                modified_by='system'
            )
        )
        await self.db.execute(update_stmt)
