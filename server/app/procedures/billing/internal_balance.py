"""
Invoice Internal Balance Update Procedure

Python implementation of the Invoice_InternalUpdateBalance stored procedure for
updating invoice balances based on invoice details.
"""
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session, aliased

from app.models.invoice import Invoice, InvoiceDetail
from app.procedures.base import BaseProcedure


class InvoiceInternalBalance(BaseProcedure):
    """
    Updates invoice balance based on sum of invoice details.
    
    This procedure:
    1. Calculates total balance from invoice details
    2. Updates invoice balance
    3. Maintains data consistency
    """

    async def _execute(
        self,
        invoice_id: int
    ) -> Dict[str, Any]:
        """Execute the invoice internal balance update procedure"""
        if not invoice_id:
            return {
                'success': False,
                'error': 'Invoice ID required'
            }

        # Calculate total balance
        total_balance = await self._calculate_total_balance(invoice_id)

        # Update invoice balance
        await self._update_invoice_balance(invoice_id, total_balance)

        return {
            'success': True,
            'invoice_id': invoice_id,
            'new_balance': total_balance
        }

    async def _calculate_total_balance(
        self,
        invoice_id: int
    ) -> Decimal:
        """Calculate total balance from invoice details"""
        query = (
            select(func.sum(InvoiceDetail.balance))
            .join(
                Invoice,
                (InvoiceDetail.customer_id == Invoice.customer_id) &
                (InvoiceDetail.invoice_id == Invoice.id)
            )
            .where(Invoice.id == invoice_id)
            .group_by(InvoiceDetail.invoice_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or Decimal('0')

    async def _update_invoice_balance(
        self,
        invoice_id: int,
        new_balance: Decimal
    ) -> None:
        """Update invoice with new balance"""
        query = (
            select(Invoice)
            .where(Invoice.id == invoice_id)
        )
        result = await self.db.execute(query)
        invoice = result.scalar_one_or_none()

        if invoice:
            invoice.invoice_balance = new_balance
            await self.db.flush()
