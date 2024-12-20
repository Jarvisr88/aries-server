"""
Order Processing Procedures

Python implementation of the order_process_2 stored procedure for
processing orders and generating invoices.
"""
from datetime import date
from typing import Dict, Any, Optional
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDetail
from app.models.billing import Invoice, InvoiceDetail
from app.procedures.base import BaseProcedure
from app.procedures.billing.recalculate import InvoiceRecalculation
from app.procedures.billing.pending import UpdatePendingSubmissions
from app.procedures.billing.balance import UpdateInvoiceBalance


class OrderProcess(BaseProcedure):
    """
    Processes orders and generates invoices.
    
    This procedure:
    1. Processes order details
    2. Creates invoice records
    3. Updates balances and submissions
    4. Handles billing flags
    """

    async def _execute(
        self,
        order_id: int,
        billing_month: int,
        billing_flags: int,
        invoice_date: date
    ) -> Dict[str, Any]:
        """Execute the order processing procedure"""
        if not order_id:
            return {
                'success': False,
                'error': 'Order ID required'
            }

        # Process order internally
        invoice_id = await self._process_order(
            order_id=order_id,
            billing_month=billing_month,
            billing_flags=billing_flags,
            invoice_date=invoice_date
        )

        if not invoice_id:
            return {
                'success': False,
                'error': 'Failed to process order'
            }

        # Update invoice calculations
        await self._update_invoice_calculations(invoice_id)

        return {
            'success': True,
            'invoice_id': invoice_id
        }

    async def _process_order(
        self,
        order_id: int,
        billing_month: int,
        billing_flags: int,
        invoice_date: date
    ) -> Optional[int]:
        """Process order and create invoice"""
        # Get order details
        query = (
            select(Order)
            .options(
                joinedload(Order.details)
            )
            .where(Order.id == order_id)
        )
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()

        if not order:
            return None

        # Create invoice
        invoice = Invoice(
            customer_id=order.customer_id,
            order_id=order.id,
            invoice_date=invoice_date,
            billing_month=billing_month,
            billing_flags=billing_flags,
            created_by=order.created_by,
            modified_by=order.modified_by
        )
        self.db.add(invoice)
        await self.db.flush()

        # Create invoice details
        for detail in order.details:
            invoice_detail = InvoiceDetail(
                invoice_id=invoice.id,
                order_detail_id=detail.id,
                inventory_item_id=detail.inventory_item_id,
                quantity=detail.quantity,
                unit_price=detail.unit_price,
                total_amount=detail.total_amount,
                created_by=detail.created_by,
                modified_by=detail.modified_by
            )
            self.db.add(invoice_detail)

        await self.db.flush()
        return invoice.id

    async def _update_invoice_calculations(self, invoice_id: int) -> None:
        """Update all invoice calculations"""
        # Recalculate invoice details
        recalc = InvoiceRecalculation(self.db)
        await recalc.execute(invoice_id)

        # Update pending submissions
        pending = UpdatePendingSubmissions(self.db)
        await pending.execute(invoice_id)

        # Recalculate again after submissions
        await recalc.execute(invoice_id)

        # Update final balance
        balance = UpdateInvoiceBalance(self.db)
        await balance.execute(invoice_id)
