"""
Invoice Recalculation Procedure

Python implementation of the InvoiceDetails_RecalculateInternals_Single stored procedure
for recalculating invoice totals and balances.
"""
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import Session

from app.models.billing import (
    Invoice,
    InvoiceDetail,
    InvoicePayment,
    InvoiceSubmission
)
from app.procedures.base import BaseProcedure


class InvoiceRecalculation(BaseProcedure):
    """
    Recalculates invoice totals and balances.
    
    This procedure:
    1. Calculates payments and adjustments
    2. Updates submission statuses
    3. Updates invoice totals
    """

    async def _execute(
        self,
        invoice_id: int,
        detail_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the invoice recalculation procedure"""
        if not invoice_id:
            return {
                'success': False,
                'error': 'Invoice ID required'
            }

        # Get invoice details
        details = await self._get_invoice_details(invoice_id, detail_id)
        if not details:
            return {
                'success': False,
                'error': 'No invoice details found'
            }

        # Process each detail
        for detail in details:
            await self._recalculate_detail(detail.id)

        # Update invoice totals
        await self._update_invoice_totals(invoice_id)

        return {'success': True}

    async def _get_invoice_details(
        self,
        invoice_id: int,
        detail_id: Optional[int]
    ) -> List[InvoiceDetail]:
        """Get invoice details to recalculate"""
        query = select(InvoiceDetail).where(InvoiceDetail.invoice_id == invoice_id)
        if detail_id:
            query = query.where(InvoiceDetail.id == detail_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _recalculate_detail(self, detail_id: int) -> None:
        """Recalculate totals for a single invoice detail"""
        # Get payments and adjustments
        payments_query = (
            select(func.sum(InvoicePayment.amount))
            .where(InvoicePayment.invoice_detail_id == detail_id)
        )
        payments = (await self.db.execute(payments_query)).scalar() or Decimal('0.00')

        # Get submissions
        submissions_query = (
            select(func.sum(InvoiceSubmission.submitted_amount))
            .where(InvoiceSubmission.invoice_detail_id == detail_id)
        )
        submitted = (await self.db.execute(submissions_query)).scalar() or Decimal('0.00')

        # Get detail
        detail_query = select(InvoiceDetail).where(InvoiceDetail.id == detail_id)
        detail = (await self.db.execute(detail_query)).scalar_one()

        # Calculate remaining balance
        balance = detail.total_amount - payments

        # Update detail
        update_stmt = (
            update(InvoiceDetail)
            .where(InvoiceDetail.id == detail_id)
            .values(
                total_paid=payments,
                total_submitted=submitted,
                remaining_balance=balance,
                modified_date=func.now()
            )
        )
        await self.db.execute(update_stmt)

    async def _update_invoice_totals(self, invoice_id: int) -> None:
        """Update invoice header totals"""
        # Calculate totals from details
        totals_query = (
            select(
                func.sum(InvoiceDetail.total_amount).label('total_amount'),
                func.sum(InvoiceDetail.total_paid).label('total_paid'),
                func.sum(InvoiceDetail.total_submitted).label('total_submitted'),
                func.sum(InvoiceDetail.remaining_balance).label('remaining_balance')
            )
            .where(InvoiceDetail.invoice_id == invoice_id)
        )
        totals = (await self.db.execute(totals_query)).first()

        # Update invoice
        update_stmt = (
            update(Invoice)
            .where(Invoice.id == invoice_id)
            .values(
                total_amount=totals.total_amount or Decimal('0.00'),
                total_paid=totals.total_paid or Decimal('0.00'),
                total_submitted=totals.total_submitted or Decimal('0.00'),
                remaining_balance=totals.remaining_balance or Decimal('0.00'),
                modified_date=func.now()
            )
        )
        await self.db.execute(update_stmt)
