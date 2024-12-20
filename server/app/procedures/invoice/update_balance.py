"""
Invoice Balance Update Procedure

Python implementation of the Invoice_InternalUpdateBalance stored procedure for
updating invoice balances based on their details.
"""
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceDetail
from app.procedures.base import BaseProcedure


class InvoiceBalanceUpdater(BaseProcedure):
    """
    Updates invoice balances based on their details.
    
    This procedure:
    1. Calculates total balance from invoice details
    2. Updates invoice balance
    3. Handles null balances
    """
    
    async def _execute(
        self,
        invoice_id: int
    ) -> Dict[str, Any]:
        """Execute the invoice balance update procedure"""
        if not invoice_id:
            return {
                'success': False,
                'error': 'Invoice ID required'
            }

        # Calculate total balance from details
        balance = await self._calculate_balance(invoice_id)

        # Update invoice balance
        await self._update_invoice_balance(invoice_id, balance)

        return {
            'success': True,
            'invoice_id': invoice_id,
            'new_balance': balance
        }

    async def _calculate_balance(
        self,
        invoice_id: int
    ) -> Decimal:
        """Calculate total balance from invoice details"""
        query = (
            select(func.sum(InvoiceDetail.balance))
            .join(Invoice)
            .where(
                and_(
                    Invoice.id == invoice_id,
                    InvoiceDetail.invoice_id == invoice_id
                )
            )
        )
        result = await self.db.scalar(query)
        return result or Decimal('0.00')

    async def _update_invoice_balance(
        self,
        invoice_id: int,
        balance: Decimal
    ) -> None:
        """Update invoice balance"""
        query = (
            update(Invoice)
            .where(Invoice.id == invoice_id)
            .values(invoice_balance=balance)
            .execution_options(synchronize_session=False)
        )
        await self.db.execute(query)

    @classmethod
    def execute(cls, invoice_id: int) -> None:
        """Execute the invoice balance update procedure.
        
        Args:
            invoice_id: ID of invoice to update
        """
        updater = cls()
        with get_session() as session:
            updater._execute(invoice_id)
            session.commit()
