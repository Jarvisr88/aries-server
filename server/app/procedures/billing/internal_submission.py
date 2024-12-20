"""
Internal Invoice Submission Procedure

Python implementation of the InvoiceDetails_InternalAddSubmitted stored procedure
for creating internal submission transactions.
"""
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.billing import (
    InvoiceDetail,
    InvoiceTransaction,
    InvoiceTransactionType,
    InsuranceCompany,
    CustomerInsurance
)
from app.procedures.base import BaseProcedure


class InternalSubmission(BaseProcedure):
    """
    Handles internal submission transactions for invoice details.
    
    This procedure:
    1. Validates submission details
    2. Creates appropriate transaction records
    3. Updates submission status
    4. Handles different payer types (Patient, Insurance)
    """

    SUBMIT_TYPE = 'Submit'

    async def _execute(
        self,
        invoice_detail_id: int,
        amount: Decimal,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ) -> Dict[str, Any]:
        """Execute the internal submission procedure"""
        if not invoice_detail_id or not submitted_to:
            return {
                'success': False,
                'error': 'Invoice Detail ID and Submission Target required'
            }

        # Get transaction type
        tran_type = await self._get_transaction_type()
        if not tran_type:
            return {
                'success': False,
                'error': f'Transaction type {self.SUBMIT_TYPE} not found'
            }

        # Get invoice detail
        detail = await self._get_invoice_detail(invoice_detail_id)
        if not detail:
            return {
                'success': False,
                'error': f'Invoice detail {invoice_detail_id} not found'
            }

        # Create transaction based on submission target
        transaction = await self._create_transaction(
            detail=detail,
            tran_type=tran_type,
            amount=amount,
            submitted_to=submitted_to,
            submitted_by=submitted_by,
            submitted_batch=submitted_batch,
            last_update_user_id=last_update_user_id
        )

        return {
            'success': True,
            'transaction_id': transaction.id
        }

    async def _get_transaction_type(self) -> Optional[InvoiceTransactionType]:
        """Get Submit transaction type"""
        query = select(InvoiceTransactionType).where(
            InvoiceTransactionType.name == self.SUBMIT_TYPE
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_invoice_detail(self, detail_id: int) -> Optional[InvoiceDetail]:
        """Get invoice detail record"""
        query = select(InvoiceDetail).where(InvoiceDetail.id == detail_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _create_transaction(
        self,
        detail: InvoiceDetail,
        tran_type: InvoiceTransactionType,
        amount: Decimal,
        submitted_to: str,
        submitted_by: str,
        submitted_batch: str,
        last_update_user_id: int
    ) -> InvoiceTransaction:
        """Create submission transaction record"""
        # Base transaction data
        transaction_data = {
            'invoice_detail_id': detail.id,
            'invoice_id': detail.invoice_id,
            'customer_id': detail.customer_id,
            'transaction_type_id': tran_type.id,
            'amount': amount,
            'quantity': detail.quantity,
            'transaction_date': datetime.now().date(),
            'batch_number': submitted_batch,
            'comments': f'Submitted by {submitted_by}',
            'created_by': last_update_user_id,
            'modified_by': last_update_user_id
        }

        # Handle different submission targets
        if submitted_to == 'Patient':
            # Patient submission - no insurance info needed
            transaction_data.update({
                'insurance_company_id': None,
                'customer_insurance_id': None
            })
        else:
            # Insurance submission - get insurance info
            insurance_info = await self._get_insurance_info(
                detail.customer_id,
                submitted_to
            )
            if insurance_info:
                transaction_data.update({
                    'insurance_company_id': insurance_info.insurance_company_id,
                    'customer_insurance_id': insurance_info.id
                })

        # Create and save transaction
        transaction = InvoiceTransaction(**transaction_data)
        self.db.add(transaction)
        await self.db.flush()

        return transaction

    async def _get_insurance_info(
        self,
        customer_id: int,
        insurance_level: str
    ) -> Optional[CustomerInsurance]:
        """Get customer insurance information for specified level"""
        query = (
            select(CustomerInsurance)
            .where(
                and_(
                    CustomerInsurance.customer_id == customer_id,
                    CustomerInsurance.level == insurance_level
                )
            )
            .order_by(CustomerInsurance.effective_date.desc())
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
