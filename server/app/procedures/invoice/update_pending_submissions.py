"""
Invoice Pending Submissions Update Procedure

Python implementation of the Invoice_InternalUpdatePendingSubmissions stored procedure for
updating pending insurance submissions.
"""
from datetime import date
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_, text
from sqlalchemy.orm import Session

from app.models.invoice import (
    Invoice,
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType,
    InvoiceTransactionStatistics
)
from app.procedures.base import BaseProcedure


class InvoicePendingSubmissionsUpdater(BaseProcedure):
    """
    Updates pending insurance submissions for invoices.
    
    This procedure:
    1. Checks current payer status
    2. Creates pending submission transactions
    3. Handles multiple insurance levels
    4. Maintains transaction history
    """
    
    async def _execute(
        self,
        invoice_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute the pending submissions update procedure"""
        # Get transaction types
        transaction_types = await self._get_transaction_types()
        if not transaction_types:
            return {
                'success': False,
                'error': 'Transaction types not found'
            }

        # Get invoice statistics
        stats = await self._get_invoice_statistics(invoice_id)
        if not stats:
            return {
                'success': False,
                'error': 'No invoices found'
            }

        # Process each invoice detail
        transactions_created = []
        for stat in stats:
            transaction = await self._process_invoice_detail(
                stat,
                transaction_types['pending_submission']
            )
            if transaction:
                transactions_created.append(transaction)

        return {
            'success': True,
            'transactions_created': len(transactions_created)
        }

    async def _get_transaction_types(self) -> Dict[str, int]:
        """Get required transaction type IDs"""
        pending_query = (
            select(InvoiceTransactionType.id)
            .where(InvoiceTransactionType.name == 'Pending Submission')
        )
        writeoff_query = (
            select(InvoiceTransactionType.id)
            .where(InvoiceTransactionType.name == 'Writeoff')
        )

        pending_result = await self.db.execute(pending_query)
        writeoff_result = await self.db.execute(writeoff_query)

        return {
            'pending_submission': pending_result.scalar(),
            'writeoff': writeoff_result.scalar()
        }

    async def _get_invoice_statistics(
        self,
        invoice_id: Optional[int]
    ) -> List[InvoiceTransactionStatistics]:
        """Get invoice transaction statistics"""
        query = (
            select(InvoiceTransactionStatistics)
            .where(
                or_(
                    InvoiceTransactionStatistics.invoice_id == invoice_id,
                    invoice_id.is_(None)
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _process_invoice_detail(
        self,
        stat: InvoiceTransactionStatistics,
        pending_submission_type_id: int
    ) -> Optional[InvoiceTransaction]:
        """Process a single invoice detail for pending submissions"""
        # Check current payer and pending submissions
        transaction = None
        
        if (
            stat.current_payer == 'Ins1' and
            stat.insurance1_id and
            not (stat.pending_submissions & 1)
        ):
            # First insurance needs billing
            transaction = await self._create_transaction(
                stat=stat,
                company_id=stat.insurance_company1_id,
                insurance_id=stat.insurance1_id,
                transaction_type_id=pending_submission_type_id,
                comments='Ins1',
                amount=stat.billable_amount
            )

        elif (
            stat.current_payer == 'Ins2' and
            stat.insurance2_id and
            not (stat.pending_submissions & 2)
        ):
            # Second insurance needs billing
            transaction = await self._create_transaction(
                stat=stat,
                company_id=stat.insurance_company2_id,
                insurance_id=stat.insurance2_id,
                transaction_type_id=pending_submission_type_id,
                comments='Ins2',
                amount=stat.billable_amount - stat.payment_amount - stat.writeoff_amount
            )

        elif (
            stat.current_payer == 'Ins3' and
            stat.insurance3_id and
            not (stat.pending_submissions & 4)
        ):
            # Third insurance needs billing
            transaction = await self._create_transaction(
                stat=stat,
                company_id=stat.insurance_company3_id,
                insurance_id=stat.insurance3_id,
                transaction_type_id=pending_submission_type_id,
                comments='Ins3',
                amount=stat.billable_amount - stat.payment_amount - stat.writeoff_amount
            )

        elif (
            stat.current_payer == 'Ins4' and
            stat.insurance4_id and
            not (stat.pending_submissions & 8)
        ):
            # Fourth insurance needs billing
            transaction = await self._create_transaction(
                stat=stat,
                company_id=stat.insurance_company4_id,
                insurance_id=stat.insurance4_id,
                transaction_type_id=pending_submission_type_id,
                comments='Ins4',
                amount=stat.billable_amount - stat.payment_amount - stat.writeoff_amount
            )

        elif (
            stat.current_payer == 'Patient' and
            not (stat.pending_submissions & 16)
        ):
            # Patient needs billing
            transaction = await self._create_transaction(
                stat=stat,
                company_id=None,
                insurance_id=None,
                transaction_type_id=pending_submission_type_id,
                comments='Patient',
                amount=stat.billable_amount - stat.payment_amount - stat.writeoff_amount
            )

        return transaction

    async def _create_transaction(
        self,
        stat: InvoiceTransactionStatistics,
        company_id: Optional[int],
        insurance_id: Optional[int],
        transaction_type_id: int,
        comments: str,
        amount: Decimal
    ) -> InvoiceTransaction:
        """Create a new invoice transaction"""
        transaction = InvoiceTransaction(
            invoice_details_id=stat.invoice_details_id,
            invoice_id=stat.invoice_id,
            customer_id=stat.customer_id,
            insurance_company_id=company_id,
            customer_insurance_id=insurance_id,
            transaction_type_id=transaction_type_id,
            transaction_date=date.today(),
            comments=comments,
            amount=amount,
            quantity=stat.quantity or 0
        )
        self.db.add(transaction)
        await self.db.flush()
        return transaction
