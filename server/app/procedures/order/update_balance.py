"""
Order balance update procedure that recalculates and updates order totals.

This procedure updates order balance calculations based on invoice and payment data,
ensuring financial accuracy across the system.
"""
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import Session

from app.models.order import Order, OrderDetails
from app.models.invoice import Invoice, InvoiceTransaction
from app.core.logging import logger
from app.procedures.base import BaseProcedure


class OrderBalanceUpdater(BaseProcedure):
    """Updates order balance calculations"""

    def __init__(self, db: Session):
        super().__init__(db)
        self.order: Optional[Order] = None
        self.invoices: List[Invoice] = []

    async def _pre_execute(self, order_id: int) -> None:
        """Load order and related data"""
        # Load order
        stmt = select(Order).where(Order.id == order_id)
        result = await self.db.execute(stmt)
        self.order = result.scalar_one_or_none()
        
        if not self.order:
            raise ValueError(f"Order {order_id} not found")
            
        # Load related invoices
        stmt = select(Invoice).where(Invoice.order_id == order_id)
        result = await self.db.execute(stmt)
        self.invoices = result.scalars().all()

    async def _execute(self, order_id: int) -> None:
        """Update order balance calculations"""
        if not self.order:
            return

        # Calculate total billed amount from invoices
        total_billed = Decimal('0.00')
        total_paid = Decimal('0.00')
        total_adjustments = Decimal('0.00')

        for invoice in self.invoices:
            # Add invoice amount to total billed
            total_billed += invoice.total_amount or Decimal('0.00')

            # Calculate payments and adjustments
            stmt = select(
                func.sum(case(
                    (InvoiceTransaction.type == 'Payment', InvoiceTransaction.amount),
                    else_=0
                )).label('payments'),
                func.sum(case(
                    (InvoiceTransaction.type == 'Adjustment', InvoiceTransaction.amount),
                    else_=0
                )).label('adjustments')
            ).where(InvoiceTransaction.invoice_id == invoice.id)
            
            result = await self.db.execute(stmt)
            row = result.one()
            
            total_paid += row.payments or Decimal('0.00')
            total_adjustments += row.adjustments or Decimal('0.00')

        # Update order totals
        self.order.total_billed = total_billed
        self.order.total_paid = total_paid
        self.order.total_adjustments = total_adjustments
        self.order.balance = total_billed - total_paid - total_adjustments

        # Update order details totals
        for detail in self.order.details:
            detail_billed = Decimal('0.00')
            detail_paid = Decimal('0.00')
            detail_adjustments = Decimal('0.00')

            # Sum up totals from invoice details
            for invoice in self.invoices:
                for inv_detail in invoice.details:
                    if inv_detail.order_detail_id == detail.id:
                        detail_billed += inv_detail.total_amount or Decimal('0.00')
                        detail_paid += inv_detail.paid_amount or Decimal('0.00')
                        detail_adjustments += inv_detail.adjustment_amount or Decimal('0.00')

            detail.total_billed = detail_billed
            detail.total_paid = detail_paid
            detail.total_adjustments = detail_adjustments
            detail.balance = detail_billed - detail_paid - detail_adjustments

        # Add results
        self._results.update({
            'order_id': self.order.id,
            'total_billed': str(self.order.total_billed),
            'total_paid': str(self.order.total_paid),
            'total_adjustments': str(self.order.total_adjustments),
            'balance': str(self.order.balance)
        })

    async def _post_execute(self, order_id: int) -> None:
        """Log the balance update"""
        logger.info(
            f"Updated order {order_id} balance: "
            f"Billed={self.order.total_billed}, "
            f"Paid={self.order.total_paid}, "
            f"Adjustments={self.order.total_adjustments}, "
            f"Balance={self.order.balance}"
        )
