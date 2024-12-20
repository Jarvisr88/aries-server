"""
Medical Information Record (MIR) Order Details Update Procedure

Updates MIR flags and validation status for order details.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_, update, func, text
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDetail
from app.models.customer import Customer, CustomerInsurance
from app.models.inventory import InventoryItem, PriceCodeItem
from app.models.facility import Facility, POSType
from app.models.cmn import CMNForm
from app.procedures.base import BaseProcedure


class MIRUpdateOrderDetails(BaseProcedure):
    """
    Updates Medical Information Record flags for order details.
    
    This procedure:
    1. Validates order details
    2. Updates MIR flags
    3. Checks billing requirements
    4. Maintains compliance
    """

    async def _execute(
        self,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute the MIR order details update procedure"""
        # Parse order ID parameter
        active_only = False
        target_order_id = None

        if order_id == 'ActiveOnly':
            active_only = True
        elif order_id and order_id.replace('-', '').replace('+', '').isdigit():
            target_order_id = int(order_id)

        # Update base MIR flags
        await self._update_base_mir_flags(target_order_id, active_only)

        # Update common MIR flags
        await self._update_common_mir_flags(target_order_id, active_only)

        # Update ICD codes validation
        await self._update_icd_validation(target_order_id, active_only)

        return {
            'success': True,
            'order_id': order_id
        }

    async def _update_base_mir_flags(
        self,
        order_id: Optional[int],
        active_only: bool
    ) -> None:
        """Update base MIR validation flags"""
        conditions = []
        if order_id:
            conditions.append(Order.id == order_id)
        if active_only:
            conditions.append(OrderDetail.is_active == True)

        update_stmt = (
            update(OrderDetail)
            .where(and_(*conditions) if conditions else True)
            .values(
                mir_flags=func.concat_ws(
                    ',',
                    func.case(
                        (InventoryItem.id.is_(None), 'InventoryItemID'),
                        else_=None
                    ),
                    func.case(
                        (PriceCodeItem.id.is_(None), 'PriceCodeID'),
                        else_=None
                    ),
                    func.case(
                        (
                            and_(
                                OrderDetail.sale_rent_type == 'Medicare Oxygen Rental',
                                OrderDetail.is_oxygen != True
                            ),
                            'SaleRentType'
                        ),
                        (OrderDetail.actual_sale_rent_type == '', 'SaleRentType'),
                        else_=None
                    ),
                    func.case(
                        (OrderDetail.actual_bill_item_on == '', 'BillItemOn'),
                        else_=None
                    ),
                    func.case(
                        (OrderDetail.actual_billed_when == '', 'BilledWhen'),
                        else_=None
                    ),
                    func.case(
                        (OrderDetail.actual_ordered_when == '', 'OrderedWhen'),
                        else_=None
                    ),
                    func.case(
                        (
                            and_(
                                OrderDetail.is_active == True,
                                OrderDetail.end_date < Order.bill_date
                            ),
                            'EndDate.Invalid'
                        ),
                        else_=None
                    ),
                    func.case(
                        (
                            and_(
                                OrderDetail.state == 'Pickup',
                                OrderDetail.end_date.is_(None)
                            ),
                            'EndDate.Unconfirmed'
                        ),
                        else_=None
                    ),
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
                    func.case(
                        (
                            and_(
                                OrderDetail.sale_rent_type.in_(['Capped Rental', 'Parental Capped Rental']),
                                Order.delivery_date < datetime(2006, 1, 1),
                                OrderDetail.billing_month.between(12, 13),
                                ~OrderDetail.modifier3.in_(['BP', 'BR', 'BU'])
                            ),
                            'Modifier3'
                        ),
                        else_=None
                    ),
                    func.case(
                        (
                            and_(
                                OrderDetail.sale_rent_type.in_(['Capped Rental', 'Parental Capped Rental']),
                                Order.delivery_date < datetime(2006, 1, 1),
                                OrderDetail.billing_month.between(14, 15),
                                ~OrderDetail.modifier3.in_(['BR', 'BU'])
                            ),
                            'Modifier3'
                        ),
                        else_=None
                    )
                ),
                mir_order_flags=''
            )
            .execution_options(synchronize_session=False)
        )
        await self.db.execute(update_stmt)

    async def _update_common_mir_flags(
        self,
        order_id: Optional[int],
        active_only: bool
    ) -> None:
        """Update common MIR validation flags"""
        conditions = []
        if order_id:
            conditions.append(Order.id == order_id)
        if active_only:
            conditions.append(OrderDetail.is_active == True)

        update_stmt = (
            update(OrderDetail)
            .where(and_(*conditions) if conditions else True)
            .values(
                mir_flags=func.concat_ws(
                    ',',
                    OrderDetail.mir_flags,
                    func.case(
                        (func.coalesce(OrderDetail.ordered_quantity, 0) == 0, 'OrderedQuantity'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.ordered_units, '') == '', 'OrderedUnits'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.ordered_converter, 0) == 0, 'OrderedConverter'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.billed_quantity, 0) == 0, 'BilledQuantity'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.billed_units, '') == '', 'BilledUnits'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.billed_converter, 0) == 0, 'BilledConverter'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.delivery_quantity, 0) == 0, 'DeliveryQuantity'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.delivery_units, '') == '', 'DeliveryUnits'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.delivery_converter, 0) == 0, 'DeliveryConverter'),
                        else_=None
                    ),
                    func.case(
                        (func.coalesce(OrderDetail.billing_code, '') == '', 'BillingCode'),
                        else_=None
                    )
                )
            )
            .execution_options(synchronize_session=False)
        )
        await self.db.execute(update_stmt)

    async def _update_icd_validation(
        self,
        order_id: Optional[int],
        active_only: bool
    ) -> None:
        """Update ICD codes validation flags"""
        conditions = []
        if order_id:
            conditions.append(Order.id == order_id)
        if active_only:
            conditions.append(OrderDetail.is_active == True)

        # Update ICD-9 validation
        update_stmt = (
            update(OrderDetail)
            .where(and_(*conditions) if conditions else True)
            .values(
                mir_order_flags=func.concat_ws(
                    ',',
                    OrderDetail.mir_order_flags,
                    func.case(
                        (Order.icd9_1 != '', None),
                        (Order.icd9_2 != '', None),
                        (Order.icd9_3 != '', None),
                        else_='ICD9'
                    )
                )
            )
            .execution_options(synchronize_session=False)
        )
        await self.db.execute(update_stmt)

        # Update ICD-10 validation
        update_stmt = (
            update(OrderDetail)
            .where(and_(*conditions) if conditions else True)
            .values(
                mir_order_flags=func.concat_ws(
                    ',',
                    OrderDetail.mir_order_flags,
                    func.case(
                        (Order.icd10_01 != '', None),
                        (Order.icd10_02 != '', None),
                        (Order.icd10_03 != '', None),
                        else_='ICD10'
                    )
                )
            )
            .execution_options(synchronize_session=False)
        )
        await self.db.execute(update_stmt)
