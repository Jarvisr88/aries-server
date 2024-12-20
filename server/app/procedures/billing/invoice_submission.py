"""
Invoice Submission Procedure

Python implementation of the Invoice_AddSubmitted stored procedure for
handling insurance claim submissions.
"""
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.billing import (
    Invoice,
    InvoiceDetail,
    InvoiceSubmission
)
from app.procedures.base import BaseProcedure
from app.procedures.billing.recalculate import InvoiceRecalculation


class InvoiceSubmission(BaseProcedure):
    """
    Handles the submission of invoices to insurance payers.
    
    This procedure:
    1. Validates invoice and payer information
    2. Creates submission records for each detail
    3. Recalculates invoice totals
    """

    async def _execute(
        self,
        invoice_id: int,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ) -> Dict[str, Any]:
        """Execute the invoice submission procedure"""
        if not invoice_id or not submitted_to:
            return {
                'success': False,
                'error': 'Invoice ID and Submission Target required'
            }

        # First recalculation
        recalc = InvoiceRecalculation(self.db)
        await recalc.execute(invoice_id)

        # Get invoice details for this payer
        details = await self._get_invoice_details(invoice_id, submitted_to)
        if not details:
            return {
                'success': False,
                'error': f'No invoice details found for payer {submitted_to}'
            }

        # Process each detail
        for detail in details:
            await self._add_detail_submission(
                detail_id=detail.id,
                submitted_amount=Decimal('0.00'),
                submitted_to=submitted_to,
                submitted_by=submitted_by,
                submitted_batch=submitted_batch,
                last_update_user_id=last_update_user_id
            )

        # Final recalculation
        await recalc.execute(invoice_id)

        return {
            'success': True,
            'details_submitted': len(details)
        }

    async def _get_invoice_details(
        self,
        invoice_id: int,
        payer: str
    ) -> List[InvoiceDetail]:
        """Get invoice details for specific payer"""
        query = (
            select(InvoiceDetail)
            .where(
                and_(
                    InvoiceDetail.invoice_id == invoice_id,
                    InvoiceDetail.current_payer == payer
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _add_detail_submission(
        self,
        detail_id: int,
        submitted_amount: Decimal,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ) -> None:
        """Add submission record for invoice detail"""
        # Create submission record
        submission = InvoiceSubmission(
            invoice_detail_id=detail_id,
            submitted_amount=submitted_amount,
            submitted_to=submitted_to,
            submitted_by=submitted_by,
            submitted_batch=submitted_batch,
            status='Submitted',
            created_by=last_update_user_id,
            modified_by=last_update_user_id
        )
        self.db.add(submission)

        # Update invoice detail
        detail_update = (
            update(InvoiceDetail)
            .where(InvoiceDetail.id == detail_id)
            .values(
                submission_status='Submitted',
                last_submission_date=func.now(),
                modified_by=last_update_user_id,
                modified_date=func.now()
            )
        )
        await self.db.execute(detail_update)
